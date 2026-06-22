# 格物 · Agent 卷

> **格物 · Agent 卷**：从 single-agent harness 到 multi-agent 协同系统的动手学习记录。
>
> 大模型卷回答“模型如何被训练、推理和对齐”；Agent 卷回答“模型如何被组织成能行动、协作和验证的系统”。

---

## 这门教程适合谁

- 已经知道大模型基本概念，想继续理解 Agent、工具调用、记忆、协作和评估
- 想从底层实现理解 agent harness，而不是只会调用框架
- 想研究 sub-agent、agent team、multi-agent 并行 / 协同的真实工程问题
- 想把论文、开源项目和可运行代码连起来学习

---

## 你将收获什么

学完整卷，你会：

1. 写出一个最小 single-agent harness
2. 理解 `Thought -> Action -> Observation` 的闭环
3. 搞懂 tool schema、tool execution、observation 回注和 trace
4. 理解 memory、context compression、stop condition 和错误恢复
5. 实现 sub-agent / manager-worker 的基本模式
6. 理解 agent team、共享状态、并行调度和冲突裁决
7. 能用预算对齐、trace 和失败归因评估 multi-agent 是否真的有效
8. 理解 MCP、A2A、ACP、ANP 各自解决哪一层问题

---

## 章节地图

| 章节 | 内容 |
|------|------|
| [ch01 Agent Harness](./ch01-agent-harness/) | 从 ReAct 开始，写出最小 agent loop |
| [ch02 Tool Use](./ch02-tool-use/) | 工具 schema、工具选择、工具结果回注 |
| [ch03 Memory and State](./ch03-memory-and-state/) | 上下文压缩、记忆落盘、状态管理 |
| [ch04 ReAct / Reflexion / Planning](./ch04-react-reflexion-planning/) | 反馈、自我修正、树搜索与规划 |
| [ch05 Sub-Agent](./ch05-sub-agent/) | 主 agent 分派子任务，隔离上下文并汇总 |
| [ch06 Agent Team](./ch06-agent-team/) | 共享任务表、peer messaging、团队协同 |
| [ch07 Multi-Agent Collaboration](./ch07-multi-agent-collaboration/) | 通信、协作、冲突裁决和并行成本 |
| [ch08 Evaluation and Trace](./ch08-evaluation-and-trace/) | benchmark、trace、预算对齐、失败归因 |
| [ch09 Protocols: MCP / A2A](./ch09-protocols-mcp-a2a/) | 工具协议和 agent 间协议 |
| [ch10 Agent Frameworks](./ch10-agent-frameworks/) | OpenAI Agents SDK、LangGraph、AutoGen、OpenHarness 等 |

---

## 配套目录

```text
agent-volume/
  README.md
  roadmap.md
  项目文档.md
  WEB_INTEGRATION.md
  ch01-agent-harness/
  ...
  ch10-agent-frameworks/
  experiments/
  papers/
  projects/
  notes/
```

- `papers/`：调研笔记、论文路线、开源项目索引
- `experiments/`：可运行实验
- `projects/`：后续完整小项目
- `notes/`：过程笔记和阶段总结

---

## 当前进度

- 已完成：multi-agent / harness 初始调研
- 已完成：ch01 Agent Harness
- 已完成：ch02 Tool Use
- 已完成：ch03 Memory and State
- 已完成：ch04 ReAct / Reflexion / Planning
- 已完成：ch05 Sub-Agent
- 下一步：ch06 Agent Team
