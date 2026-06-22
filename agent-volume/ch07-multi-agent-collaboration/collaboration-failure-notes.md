# Multi-Agent Collaboration 阅读笔记（通信 / 成本 / 失败）

## 论文

- Why Do Multi-Agent LLM Systems Fail?  
  https://arxiv.org/abs/2503.13657
- A Communication-Centric Survey of LLM-Based Multi-Agent Systems  
  https://arxiv.org/abs/2502.14321
- Multi-Agent Collaboration Mechanisms: A Survey of LLMs  
  https://arxiv.org/abs/2501.06322
- Cut the Crap / AgentPrune（ICLR 2025）  
  https://arxiv.org/abs/2410.02506
- Single-Agent LLMs Outperform Multi-Agent Systems on Multi-Hop Reasoning Under Equal Thinking Token Budgets  
  https://arxiv.org/abs/2604.02460

## 1. 三个最该记住的结论

```text
1. 通信是 MAS 的核心问题，不是模型本身（communication-centric survey）。
2. 很多 MAS 收益是 token 假象，同等预算下单 agent 可能更强（2604.02460）。
3. MAS 失败多在协作接缝，不在单 agent 推理（why MAS fail）。
```

这三条放在一起，构成对 multi-agent 的健康怀疑态度：先证明它真的需要，再用它。

## 2. 通信冗余是可量化的浪费

AgentPrune 的价值在于把“通信冗余”从直觉变成可优化对象：

- 把 agent 通信建模成图，边 = 一次消息交换。
- 很多边是冗余的，剪掉后分数几乎不掉，成本大降。
- 启发：设计 MAS 时通信拓扑应是**被设计的**，不是默认全连接。

## 3. 失败模式清单（debug MAS 时对照）

```text
任务跑偏 / 信息丢失 / 无限循环 / 过早终止 / 聚合出错 / 角色混乱
```

记忆方式：大多数发生在 agent **之间**（交接、合并、终止判定），而不是 agent **内部**（推理）。所以修 MAS 先看接缝，而不是急着换模型。

## 4. 裁决不要投票

- 投票假设错误是独立的；但 agent 常共享同一错误前提，错误是系统性的。
- 更好：基于可验证证据、来源新旧、任务匹配度裁决，必要时派 verifier。
- 这条直接连到 ch08 的 verifier / critic 和失败归因。

## 5. 成本账本模板

| 指标 | 单 agent | N 并行 worker |
|---|---|---|
| 上下文份数 | 1 | N + 汇总 |
| token 总量 | 基线 | 常 2x+ |
| wall-clock | 基线 | 可能更短 |
| 通信成本 | 0 | 随边数增长 |

结论：**报告 MAS 效果必须同时给准确率、总 token、$、wall-clock 四个数**，只报准确率等于隐藏成本。

## 6. 本阶段理解小结

```text
1. 协作模式是光谱，按中心化程度和任务匹配选，没有银弹。
2. 通信是核心问题：冗余通信只是更贵，不是更好。
3. 并行省时间、不省钱，成本必须四项一起报。
4. MAS 失败多在协作接缝，换模型救不了坏设计。
5. 裁决基于证据不基于人数。
6. multi-agent 是否值得，看对齐预算下相比强单 agent 的结构性增量。
```
