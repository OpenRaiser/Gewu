# ch08 · Evaluation and Trace

本章目标：把上一章的关键判断——“在相同预算、可复现流程、可观测 trace 下，multi-agent 是否真有收益”——变成**可执行的测法**。

ch07 给了判断标准，ch08 给落地工具：

```text
预算对齐  -> 比较才公平
trace     -> 失败才可归因
benchmark -> 结论才可复现
失败归因  -> 知道坏在哪，而不只是知道分数
```

不会测，前面所有“值不值”的讨论都只是嘴上功夫。

## 本章要回答的问题

1. 为什么 multi-agent 的评估必须先对齐 token / 成本预算？
2. trace 要记什么？为什么说没有 trace 就无法做归因？
3. 失败归因（failure attribution）怎么做，比单一准确率强在哪？
4. 有哪些 agent benchmark，各自测什么能力？
5. 一个最小可复现评估流程长什么样？
6. agent 预算超支为什么是个真实工程问题？

## 必读论文

- AgentBench: Evaluating LLMs as Agents  
  https://arxiv.org/abs/2308.03688

- ToolLLM: Facilitating Large Language Models to Master 16000+ Real-world APIs  
  https://arxiv.org/abs/2307.16789

- SWE-bench: Can Language Models Resolve Real-World GitHub Issues?  
  https://arxiv.org/abs/2310.06770

- GAIA: a benchmark for General AI Assistants  
  https://arxiv.org/abs/2311.12983

- SWE-agent: Agent-Computer Interfaces Enable Automated Software Engineering  
  https://arxiv.org/abs/2405.15793

- Why Do Multi-Agent LLM Systems Fail?（失败归因视角）  
  https://arxiv.org/abs/2503.13657

## 1. 预算对齐：评估的第一原则

multi-agent 几乎总能靠“多花 token”刷高分。所以任何 “MAS 更强” 的结论，只有在**对齐预算**下才有意义。

对齐什么：

```text
固定总 token 预算（所有 agent 的 prompt+completion + 通信），
而不是固定 agent 数量或轮数。
```

为什么：

- 固定“agent 数量”不公平——3 个 agent 当然比 1 个花更多 token。
- 正确做法是给单 agent **同等预算**（允许更长 thinking、更多次采样），再比。
- 2604.02460 正是这么做，才得出“同等思考 token 下单 agent 反而更优”。

必须分开报的两个成本：

- **wall-clock（时延）**：并行能省。
- **$（花费）**：并行通常更贵。

把这两个混成一个“性能”数字，是评估里最常见的误导。

## 2. Trace：归因的前提

没有 trace，就只能看最终对错，无法知道**为什么**对、**哪里**错。

trace 至少要记：

```text
每个 agent：
  - 输入上下文
  - tool 调用（参数 + 结果）
  - 输出
  - token 数、耗时
agent 之间：
  - 每一条消息（谁、何时、对谁、说了什么、引用哪个任务）
```

要点：

- OpenAI Agents SDK、LangGraph 等都**内置** tracing；自建 harness 时，trace 应是第一优先级，不是事后补。
- 本仓库 `experiments/sub-agent-runner/run/` 下的 `manager.jsonl` / `worker-*.jsonl` 就是最小 trace 实践：manager 和每个 worker 各一份 jsonl，可独立复盘。
- trace 的价值不只是 debug，更是**评估的数据源**——失败归因全靠它。

## 3. 失败归因（Failure Attribution）

单一准确率信息量太低：它只告诉你“错了”，不告诉你“错在哪个环节、哪个 agent、什么类型”。失败归因就是给失败 trace 打标签。

做法：

```text
对每条失败 trace：
  在哪个环节失败？（规划 / 执行 / 通信 / 聚合 / 终止）
  哪个 agent？
  什么类型？（任务跑偏 / 信息丢失 / 循环 / 过早终止 / 聚合错）
再统计分布。
```

价值：

- 比单一准确率信息量大得多——能告诉你**改哪里**。
- 已有专门工作：MAST（Multi-Agent System failure Taxonomy）提供现成的失败分类体系；2605.14892 的 LIFE 框架把“失败归因”单列一环。
- 可人工打标，也可用 LLM-as-judge 打标（但 judge 本身要校验）。

## 4. Benchmark 地图

| benchmark | 测什么 | 特点 |
|---|---|---|
| AgentBench | OS、数据库、Web、游戏等环境中的 agent 能力 | 多环境综合评估 |
| ToolLLM / ToolBench | 真实 API 调用、工具选择 | 16000+ API，偏工具学习 |
| SWE-bench | 真实 GitHub issue 修复 | Docker 评测、patch 验证，难且真实 |
| GAIA | 通用助手任务（需工具 + 检索 + 文件） | 人类容易、模型难 |
| SWE-agent | agent-computer interface | 强调 agent 与命令行/编辑器/测试的接口设计 |

选 benchmark 的原则：**先明确要测的能力**（工具调用？长任务？真实代码？），再选对应 benchmark，而不是哪个有名跑哪个。

## 5. 最小可复现评估流程

把全章收成一张可执行清单：

```text
1. 选一个有明确对错的任务集（多跳问答 / 代码任务），固定数据集与随机种子。
2. 对齐总 token 预算，跑四种配置：
     single-agent / parallel subagents / debate / manager-worker
3. 每种配置记录：
     准确率或通过率、总 token、$、wall-clock、完整 trace
4. 对失败 trace 做归因打标，统计失败模式分布。
5. 结论只在「同预算、同数据、可复现」前提下成立。
```

这正是 ch07 那个判断（“是否有结构性收益”）的落地方式。**没有这套流程，关于架构优劣的争论都不可证伪。**

## 6. 预算超支是真实问题

agent 不只是“跑不准”，还会“跑不停、跑超支”：

- 反复调用失败的工具、在状态间循环、无止境探索。
- 已有专门统计：An Empirical Catalog of 63 LLM-Agent Budget-Overrun Incidents（2606.04056）记录了真实的预算超支事故。
- 这呼应 ch01 的停止条件 / 预算上限：**硬性的 step 数、token 数、wall-clock、花费上限是兜底防线**，评估时也要把“是否超预算 / 是否中途失控”作为一项指标，而不只看成功的那些 run。

## 完成标准

学完本章后，你应该能解释：

- 为什么 MAS 评估必须对齐总 token 预算，而不是对齐 agent 数量
- wall-clock 和 $ 为什么要分开报
- trace 要记哪些字段，为什么是归因和评估的前提
- 失败归因怎么做，比单一准确率强在哪
- 主流 agent benchmark 各测什么能力
- 一个最小可复现评估流程的五个步骤
- 为什么预算超支要作为独立评估指标

一句话总结：

```text
评估 agent 不是只报一个准确率，而是在对齐预算、完整 trace、可复现流程下，同时报准确率、token、$、wall-clock，并对失败 trace 做归因——只有这样，关于「single vs multi、哪个架构更好」的结论才可证伪。
```
