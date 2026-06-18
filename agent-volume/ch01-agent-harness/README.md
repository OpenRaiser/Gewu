# ch01 · Agent Harness

本章目标：从 ReAct 开始，理解并实现最小 single-agent harness。

## 本章要回答的问题

1. 模型为什么不能只输出最终答案？
2. `Thought -> Action -> Observation` 这个循环解决了什么？
3. 工具返回的 `Observation` 如何改变下一步推理？
4. 什么情况下 agent 应该停止？

## 核心概念

### Agent

Agent 是模型在一个任务目标下，基于上下文和工具进行决策的执行单元。

### Harness

Harness 是模型外面的运行系统，负责：

- 组织 prompt / context
- 暴露工具
- 解析模型动作
- 执行工具
- 回注 observation
- 记录 trace
- 控制循环停止
- 处理错误和预算

### 最小 Loop

```text
User Goal
  -> LLM decides next action
  -> Harness executes tool
  -> Tool observation returns to LLM
  -> LLM decides continue or finish
```

## 必读论文

- ReAct: Synergizing Reasoning and Acting in Language Models  
  https://arxiv.org/abs/2210.03629
- MRKL Systems  
  https://arxiv.org/abs/2205.00445
- Toolformer  
  https://arxiv.org/abs/2302.04761

## 配套实验

- `../experiments/minimal-harness/`

实验支持：

- `read_file(path)`
- `list_files(path)`
- `search_text(pattern, path)`
- `final(answer)`

## 完成标准

- 能解释 agent 和 harness 的区别
- 能解释 ReAct loop 为什么有效
- 能解释 observation 如何影响下一步决策
- 能解释 stop condition 为什么不能只靠“模型想完了”
- 能跑通一个最小任务：读取并总结本项目中的某个 Markdown 文件

