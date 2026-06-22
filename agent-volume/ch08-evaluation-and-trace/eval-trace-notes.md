# Evaluation and Trace 阅读笔记（怎么测，不只怎么搭）

## 论文

- AgentBench: Evaluating LLMs as Agents — https://arxiv.org/abs/2308.03688
- ToolLLM — https://arxiv.org/abs/2307.16789
- SWE-bench — https://arxiv.org/abs/2310.06770
- GAIA — https://arxiv.org/abs/2311.12983
- SWE-agent — https://arxiv.org/abs/2405.15793
- Why Do Multi-Agent LLM Systems Fail? — https://arxiv.org/abs/2503.13657

## 1. 一句话立场

```text
不会测，前面所有「值不值」的讨论都是嘴上功夫。
评估 = 对齐预算 + 完整 trace + 失败归因 + 可复现。
```

## 2. 预算对齐是最容易被绕过的环节

- 错误做法：固定 agent 数量 / 轮数比性能。
- 正确做法：固定**总 token 预算**，给单 agent 同等预算（更长 thinking / 更多采样）。
- wall-clock 和 $ 分开报，别混成一个“性能”。

记住：MAS 刷分最常见的“作弊”就是偷偷多花 token。

## 3. trace 是数据源不是日志

trace 不是 debug 时才看的副产品，它是评估的**输入数据**：

```text
没有 trace -> 只能看对错 -> 无法归因 -> 无法改进
```

自建 harness 时 tracing 第一优先级。本仓库 sub-agent-runner 的 `run/*.jsonl` 是最小范例。

## 4. 失败归因 > 准确率

- 准确率只说“错了”，归因说“错在哪个环节 / 哪个 agent / 什么类型”。
- 现成体系：MAST 失败分类、LIFE 框架（2605.14892）把失败归因单列一环。
- LLM-as-judge 可打标，但 judge 自身要校验，别无限套娃。

## 5. benchmark 按能力选

```text
工具调用     -> ToolLLM / ToolBench
真实改代码   -> SWE-bench / SWE-agent
通用助手     -> GAIA
多环境综合   -> AgentBench
```

先定要测什么能力，再选 benchmark；别哪个有名跑哪个。

## 6. 预算超支要单独记

- agent 会跑不停（循环、无止境探索）。
- 2606.04056 记录了 63 个真实预算超支事故。
- 评估指标里要包含“是否超预算 / 是否中途失控”，不能只统计成功 run。

## 7. 本阶段理解小结

```text
1. 对齐总 token 预算，否则比较不公平。
2. wall-clock 与 $ 分开报。
3. trace 是归因和评估的数据源，第一优先级。
4. 失败归因给失败 trace 打标，比单一准确率信息量大。
5. benchmark 按要测的能力选。
6. 预算超支 / 失控作为独立指标。
7. 结论只在「同预算、同数据、可复现」下成立。
```
