# ch07 · Multi-Agent Collaboration

本章目标：跳出具体形态（manager-worker、team），系统理解 **multi-agent 协作的通信结构、冲突裁决、并行成本和失败模式**，并建立一个核心警惕：**很多“多 agent 更强”的结果，本质只是多花了 token。**

前两章讲了“怎么搭”：

```text
ch05 sub-agent：manager 派活，worker 隔离执行
ch06 agent team：共享任务表 + agent 间通信
```

这一章讲“值不值、会怎么坏”：协作模式有哪些、成本怎么算、为什么 multi-agent 系统经常失败。

## 本章要回答的问题

1. multi-agent 的协作模式有哪几类，各自适合什么？
2. 通信是协作的核心问题——为什么？通信冗余怎么砍？
3. 并行省的是时间，多花的是什么？成本怎么显式算账？
4. multi-agent 系统为什么失败？典型失败模式有哪些？
5. 冲突裁决为什么不能简单投票？
6. 什么时候 multi-agent 带来的是结构性收益，什么时候只是 token 幻觉？

## 必读论文

- Why Do Multi-Agent LLM Systems Fail?  
  https://arxiv.org/abs/2503.13657

- A Communication-Centric Survey of LLM-Based Multi-Agent Systems  
  https://arxiv.org/abs/2502.14321

- Multi-Agent Collaboration Mechanisms: A Survey of LLMs  
  https://arxiv.org/abs/2501.06322

- Cut the Crap / AgentPrune: An Economical Communication Pipeline for LLM-based Multi-Agent Systems（ICLR 2025）  
  https://arxiv.org/abs/2410.02506

- Single-Agent LLMs Outperform Multi-Agent Systems on Multi-Hop Reasoning Under Equal Thinking Token Budgets  
  https://arxiv.org/abs/2604.02460

## 1. 协作模式光谱

把常见模式按“中心化程度”排开：

| 模式 | 结构 | 适用 | 主要风险 |
|---|---|---|---|
| Router | 先分类，再派给专门 agent | 任务入口、客服 | 分类错就全错 |
| Manager / agents-as-tools | 主 agent 调专家 agent | 子任务可并行、需汇总 | manager 瓶颈 |
| Handoff | 控制权移交给另一 agent | 多轮、职责接管 | 上下文交接丢失 |
| Debate / critic | 多 agent 给答案、互评、judge 汇总 | 需要多视角 | 成本高、不稳定 |
| Blackboard / shared memory | 多 agent 读写同一状态池 | 长任务、团队 | 并发、噪声 |
| Agent team / swarm | 多进程、共享任务表、直接通信 | 复杂项目执行 | O(N²) 通信、冲突 |

没有“最好的模式”，只有“匹配任务的模式”。默认顺序仍是：**先单 agent，再在确有并行 / 隔离 / 多视角需求时升级。**

## 2. 通信是核心问题

A Communication-Centric Survey 的核心主张：**multi-agent 系统的关键问题是通信，不是模型本身。**

通信决定了：

- 信息能不能到达需要它的 agent
- 噪声会不会淹没有用信号
- token 成本和延迟有多高

通信冗余的代价很具体：

```text
全连接 N 个 agent -> O(N²) 条边
每条边每轮 -> 一次完整 prompt + completion
```

AgentPrune / Cut the Crap 证明：很多 multi-agent 系统的通信图里有大量**冗余边**，剪掉它们能在几乎不掉分的前提下大幅降本。结论很反直觉但重要：**更多通信 ≠ 更好协作，常常只是更贵。**

## 3. 成本必须显式算账

并行优化的是 **wall-clock 时延**（多 agent 同时跑），但 **token 总成本通常翻倍甚至更多**：

```text
单 agent：       1 份上下文
N 个并行 worker：N 份上下文重建 + manager 消化 N 份汇报 + 通信开销
```

所以任何“multi-agent 更强”的结论，都必须问三件事：

1. 是不是只是多花了 token？（给单 agent 同等预算会怎样）
2. 省的是时间还是钱？（wall-clock vs $ 要分开报）
3. 通信本身花了多少？（每轮消息都是成本）

2604.02460 正是用“对齐思考 token 预算”的方法，得出**同等预算下单 agent 在多跳推理上反而更优**——这不是说 multi-agent 没用，而是说**比较必须公平**。

## 4. 为什么 Multi-Agent 系统会失败

Why Do Multi-Agent LLM Systems Fail? 给出一个关键洞察：**MAS 失败往往不是“模型不行”，而是协作机制坏掉。** 典型失败模式：

```text
任务跑偏        agent 误解或偏离原始目标
信息丢失        agent 间交接时关键约束没传到
无限循环        agent 反复来回、无新进展
过早终止        某 agent 误判完成，整体停下
聚合出错        各 agent 都对，合并阶段把对的合错了
角色混乱        职责边界不清，互相等待或重复劳动
```

重点：这些失败大多发生在**协作的接缝处**，而不是单个 agent 的推理能力上。这也是为什么单纯换更强的模型常常救不了一个设计糟糕的 MAS。

## 5. 冲突裁决：别简单投票

多个 agent 给出矛盾结论时，**投票是最差的裁决之一**——因为错误可能是系统性的（多个 agent 共享同一个错误前提）。更可靠的做法：

- 看谁给出了**可验证证据**，而不是谁声音大
- 看来源是否更新、范围是否更匹配任务
- 必要时派一个 **verifier agent** 专门复核，而不是在错误集合里投票
- 把裁决交给一个有明确标准的 **reducer / judge**，而不是简单多数

一句话：**裁决要基于证据和验证，不是基于人数。**

## 6. 结构性收益 vs Token 幻觉

把全章收成一个判断框架。multi-agent 带来**结构性收益**的场景：

- 并行搜索 / 探索多个独立方向
- 角色隔离、工具权限隔离
- 不同专业能力的真实协作
- 长任务分治
- 多视角验证（且裁决基于证据）

multi-agent **不应**默认用于：

- 单纯提升推理准确率（先给单 agent 同等预算试试）
- 用更多 token 包装成“架构优势”
- 没有清晰任务边界的“多角色聊天”

判断口诀：

```text
在相同预算、可复现流程、可观测 trace 下，
multi-agent 是否仍带来收益？
是 -> 结构性收益；否 -> token 幻觉。
```

这个判断怎么落地（怎么对齐预算、怎么记 trace、怎么做失败归因），正是下一章 ch08 的内容。

## 完成标准

学完本章后，你应该能解释：

- 常见协作模式光谱及各自的适用与风险
- 为什么通信（而非模型）是 multi-agent 的核心问题，冗余通信怎么砍
- 并行省时间但多花 token——成本怎么显式算账
- MAS 的典型失败模式，以及它们多发生在“协作接缝处”
- 为什么冲突裁决要基于证据而非投票
- 如何区分 multi-agent 的结构性收益和 token 幻觉

一句话总结：

```text
Multi-agent 协作的真正难点是通信、成本和失败接缝，而不是“多几个模型”。判断它是否值得，唯一公平的标准是：在对齐预算、可复现、可观测 trace 的前提下，相比强单 agent 是否还有结构性收益。
```
