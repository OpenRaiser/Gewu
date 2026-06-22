# ch06 · Agent Team

本章目标：理解 **从 manager-worker 再往前一步——多个 agent 共享任务表、彼此直接通信的 agent team**。

上一章的 sub-agent 是单向的：

```text
manager -> worker -> report -> manager 汇总
```

worker 之间不说话，只对 manager 负责。这一章要处理的是另一种形态：

```text
shared task list
  agent A <-> agent B <-> agent C
  每个 agent 都能领任务、改状态、给别人发消息
```

也就是 Addy Osmani 说的 **shared task list + peer-to-peer messaging**。它更接近“一个团队在协作”，而不是“一个老板派活”。

## 本章要回答的问题

1. agent team 和 manager-worker 到底差在哪？
2. 共享任务表（shared task list）解决了什么，又带来了什么并发问题？
3. peer messaging 为什么比“都向 manager 汇报”更灵活，也更危险？
4. 多个 agent 同时动手，工作区怎么隔离才不互相覆盖？
5. 任务依赖（谁等谁）怎么表达和调度？
6. 什么任务真的需要 team，什么任务 team 只是更贵的 manager-worker？

## 必读论文 / 资料

- AutoGen: Enabling Next-Gen LLM Applications via Multi-Agent Conversation  
  https://arxiv.org/abs/2308.08155

- MetaGPT: Meta Programming for A Multi-Agent Collaborative Framework  
  https://arxiv.org/abs/2308.00352

- Addy Osmani: The Code Agent Orchestra（shared task list + peer messaging 的工程描述）  
  https://addyosmani.com/blog/code-agent-orchestra/

## 1. Agent Team 和 Manager-Worker 的区别

两者都是 multi-agent，但通信拓扑不同：

| 维度 | Manager-Worker | Agent Team |
|---|---|---|
| 通信方向 | 星形，worker 只对 manager | 网状，agent 之间可直接通信 |
| 任务来源 | manager 分派 | 共享任务表，agent 自己领 |
| 状态 | manager 持有 | 共享状态池 / 任务表 |
| 协调 | 中心化 | 部分去中心化 |
| 适合 | 任务能干净拆分、结果好汇总 | 任务边界模糊、需要边做边协商 |
| 风险 | manager 成为瓶颈 | 并发冲突、消息风暴、状态错乱 |

一句话：

```text
manager-worker 是“派活 + 汇总”，agent team 是“共享看板 + 互相喊话”。
```

agent team 不是更高级的版本，而是另一种权衡：拿掉中心瓶颈，换来并发和协调的复杂度。

## 2. 共享任务表（Shared Task List）

team 的核心数据结构是一张所有 agent 都能读写的任务表：

```text
task = {
  id,
  subject,
  status: pending | in_progress | completed | blocked,
  owner: agent_id | null,
  blocked_by: [task_id, ...],
  result,
}
```

它解决的问题：

- 谁在做什么，一张表看清
- agent 可以自己认领 `pending` 任务，不必等派发
- 依赖关系（`blocked_by`）显式化，调度有据可依
- 进度可观测，便于人和其他 agent 对齐

它带来的问题（这才是难点）：

- **并发写**：两个 agent 同时把同一个任务标成 `in_progress`，到底谁在做？
- **认领竞争**：需要原子性的“认领”操作（claim），否则重复劳动。
- **状态漂移**：agent 各自基于过期的任务表做决策。

所以共享任务表必须配上**串行化写入 / 加锁 / 版本号**，否则就是分布式系统里那套老问题重演。

## 3. Peer Messaging

manager-worker 里信息只在“worker→manager”这一条边流动。team 允许 agent 之间直接发消息：

```text
agent A -> agent B: "接口我定成这样了，你按这个写实现"
agent B -> agent A: "这个字段类型对不上，改一下"
```

好处：

- 不必所有信息都绕经 manager，减少瓶颈
- agent 能就局部问题直接对齐，迭代更快
- 更接近真实团队协作

代价（很现实）：

- **消息风暴**：N 个 agent 两两通信，边数是 O(N²)，token 成本和噪声同步爆炸。
- **顺序 / 一致性**：消息乱序到达，agent 可能基于半截信息行动。
- **难追踪**：没有中心化 trace 时，“谁在什么时候对谁说了什么”很难复盘。

工程上的常见收敛：限制通信拓扑（不是全连接）、给消息加结构（收件人、类型、引用的任务 id）、保留完整 message log。AgentPrune / Cut the Crap 那条线就是专门研究**剪掉冗余通信边**来降本。

## 4. 工作区隔离（避免互相覆盖）

多个 agent 同时改代码 / 文件，传统并发冲突全部回来：两个 agent 同时改同一文件会互相覆盖。

主流解法是**工作区隔离**：

```text
每个 agent 一份独立副本（git worktree / 沙箱目录）
  -> 各自改各自的
  -> 最后用 merge / reducer 合并
```

这正是“隔离副本”范式的价值：

- 写阶段互不干扰
- 冲突推迟到**合并阶段**集中处理，而不是运行中随机覆盖
- 合并阶段可以引入 verifier / 人来裁决

对应到本仓库 `experiments/sub-agent-runner/` 的思路：worker 各写各的 trace 和结果文件，manager 在聚合阶段统一读取——这就是隔离 + 集中合并的最小形态。

## 5. 任务依赖与调度

team 里任务不是全都能并行。有依赖的任务构成一张 DAG：

```text
task1 (定接口)
   └─> task2 (写实现)  依赖 task1
   └─> task3 (写测试)  依赖 task1
task4 (写文档) 独立，可并行
```

调度器要做的：

- 维护 `blocked_by` 关系
- 只把**就绪**（前置已完成）的任务放进可认领池
- 避免把强依赖的任务塞给不同 agent 并行（否则要靠反复传摘要补齐，得不偿失）

判断原则和上一章一致：**能真正并行、且每个子任务足够重**时并行才划算；强耦合任务硬拆成 team，只是把协调成本搬到了消息和合并阶段。

## 6. 什么时候值得用 Agent Team

适合：

- 任务能拆成多个**较重**且**相对独立**的子任务
- 子任务之间需要少量、明确的协商（而非全程紧耦合）
- 需要角色分工 + 并行推进（如多人写一个项目的不同模块）
- 工作区能干净隔离、最后能可靠合并

不适合：

- 任务很小，manager-worker 甚至单 agent 就够
- 子任务强依赖彼此的中间状态，必须串行
- 没有可靠的并发控制和合并机制（会比单 agent 更糟）
- 只是为了“看起来像个团队”

## 配套实验

本章不新增实验，复用上一章的 sub-agent-runner 来对照理解：

- `../experiments/sub-agent-runner/`

阅读 `manager.py` 时，重点对比本章内容：

- 它是**星形 manager-worker**，worker 之间不通信——这正是 team 的“前一步”。
- 想象把它改成 team：需要加共享任务表、claim 机制、agent 间消息、合并阶段——每加一项，复杂度和成本都上一个台阶。

这种“从 manager-worker 到 team 要补哪些机制”的对照，比直接堆一个复杂 team 框架更能看清代价。

## 完成标准

学完本章后，你应该能解释：

- agent team 和 manager-worker 在通信拓扑、任务来源、状态归属上的区别
- 共享任务表解决了什么、又引入了哪些并发问题
- peer messaging 的灵活性为什么伴随 O(N²) 通信成本和追踪困难
- 工作区隔离 + 集中合并为什么是多 agent 同时改文件的主流解法
- 任务依赖 DAG 在调度中的作用
- 什么任务值得上 team，什么任务 team 只是更贵的 manager-worker

一句话总结：

```text
Agent team 是用“共享任务表 + agent 间直接通信”换掉 manager 这个中心瓶颈，代价是要自己处理并发写、消息风暴、工作区冲突和合并裁决——这些都是分布式协作的老问题在 agent 上重演。
```
