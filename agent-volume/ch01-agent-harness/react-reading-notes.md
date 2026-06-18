# ReAct 阅读笔记

论文：

- ReAct: Synergizing Reasoning and Acting in Language Models  
  https://arxiv.org/abs/2210.03629

## 1. 模型为什么不能只输出最终答案？

只输出最终答案的问题不是单纯“没有过程”，更核心的是：很多任务需要外部证据。

如果模型没有读取文件、查询环境、调用工具、验证结果，它只能基于已有上下文和参数记忆生成答案。这会导致：

- 缺证据时猜测
- 难以调试
- 难以发现错误
- 容易幻觉
- 无法处理需要外部状态的任务

ReAct 的转变是：

```text
只回答 = 模型凭已有上下文生成
行动后回答 = 模型先获取外部证据，再基于证据生成
```

## 2. Thought -> Action -> Observation 解决了什么？

它解决的是推理和外部世界交互之间的闭环问题。

```text
Thought: 我现在缺什么信息？
Action: 我该调用哪个工具去拿信息？
Observation: 工具返回了什么事实？
Thought: 这个事实改变了我的判断吗？下一步做什么？
```

这个循环让 agent 从“一次性猜答案”变成“边查、边想、边修正”。

它带来的价值：

- 缺信息时可以主动获取信息
- 工具结果能约束模型，减少幻觉
- 复杂任务可以分多步完成
- 每一步有可观察轨迹，方便 debug
- 失败后可以根据 observation 调整策略

## 3. Observation 如何改变下一步推理？

Observation 是外部环境返回的新证据。它不是最终答案，也不只是简单的上下文检索结果。

Harness 会把 observation 加入当前 agent state / context，模型下一轮基于它更新判断。

例子：

```text
Thought: 我需要知道文件里第 7 节写了什么。
Action: read_file("multi-agent-research.md")
Observation: 第 7 节包含 ReAct、MRKL、Toolformer...
Thought: 现在我知道第 7 节内容了，可以总结第一步学习路线。
```

Observation 的作用：

- 补充信息
- 纠正假设
- 决定下一步动作

一句话：

```text
Observation = 环境反馈 / 证据
```

## 4. 什么情况下 agent 应该停止？

不能只说“思维链的终点”。工程上需要明确 stop condition。

agent 应该在以下条件之一满足时停止：

- 任务目标已经完成
- 已有足够证据可以回答
- 再调用工具不会带来新信息
- 达到预算上限：step / token / time / cost
- 出现不可恢复错误，需要向用户汇报
- 需要用户补充信息或授权

在 ReAct 式 harness 里，最核心的停止条件是：

```text
当 agent 判断当前 observation 和已有状态足以完成用户目标时，输出 Final Answer。
```

但生产系统还需要硬性保护：

- `max_steps`
- `max_tokens`
- `max_runtime`
- 重复 action 检测
- 无新 observation 检测

## 当前理解修正版

```text
1. 只输出最终答案容易在缺证据时猜测，且不可调试。
2. TAO 把推理、行动、环境反馈连成闭环。
3. Observation 是外部证据，会更新 agent 的状态和下一步决策。
4. agent 应在目标完成、证据足够、无法继续推进或预算耗尽时停止。
```

