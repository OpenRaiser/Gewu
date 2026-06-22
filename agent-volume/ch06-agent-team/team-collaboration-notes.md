# Agent Team 阅读笔记（shared task list + peer messaging）

## 资料

- AutoGen: Enabling Next-Gen LLM Applications via Multi-Agent Conversation  
  https://arxiv.org/abs/2308.08155
- MetaGPT: Meta Programming for A Multi-Agent Collaborative Framework  
  https://arxiv.org/abs/2308.00352
- Addy Osmani: The Code Agent Orchestra  
  https://addyosmani.com/blog/code-agent-orchestra/

## 1. team 是一个术语松散的概念

“agent team” 不是严格学术术语，更多来自 Claude、OpenHarness、社区实践。它通常指：

```text
多个独立 agent 进程 + 共享任务列表 + 依赖关系 + 直接消息
```

关键区别于 manager-worker 的，是 worker 之间也能通信、也能自己领任务，而不是只向主 agent 汇报。

## 2. 把团队当成分布式系统看

一旦从星形（manager-worker）走向网状（team），分布式系统的老问题全部回来：

```text
共享状态 -> 并发写、加锁、版本
直接通信 -> 消息乱序、风暴、追踪
同时改文件 -> 工作区冲突、合并
任务依赖 -> 调度、DAG、就绪判定
```

所以 team 的难点不在“prompt 里写几个角色”，而在 harness 要不要实现这些机制。没实现就用，结果往往比单 agent 更乱。

## 3. AutoGen / MetaGPT 给的启发

- AutoGen：把多 agent 对话做成**可编程的 conversation pattern**，团队协作本质是“可控的消息流”，而不是自由聊天。
- MetaGPT：用 **SOP / 角色分工**约束流程——规定输入输出格式、流程顺序、交付物、谁审查谁、失败如何回退。角色必须落到 harness 和 workflow，不能只停在 prompt。

两者都在说同一件事：**team 要可控，就得给通信和协作加结构**。

## 4. 通信成本是 team 的隐藏账单

- 全连接 team：N 个 agent，通信边 O(N²)，每条边一轮就是一次完整 prompt+completion。
- AgentPrune / Cut the Crap（2410.02506）专门研究剪掉冗余通信边降本。
- 实务收敛：限制拓扑、消息结构化、保留 message log，而不是放任全连接自由聊天。

## 5. 本阶段理解小结

```text
1. team = 共享任务表 + agent 间直接通信，去掉了 manager 这个中心瓶颈。
2. 代价是并发写、消息风暴、工作区冲突、合并裁决——分布式协作的老问题。
3. 工作区隔离（每 agent 一份副本）+ 集中合并，是同时改文件的主流解法。
4. 通信成本随 agent 数量平方增长，必须显式控制拓扑和消息结构。
5. 默认仍从 manager-worker 起步，确有去中心化协作需求时再上 team。
```
