# ch01 · Agent Harness

本章标题：**从 ReAct 四问到可执行循环**。

不从框架 API 起手，而从论文起手：先把 ReAct 的四个问题逐一问清、答透，再把答案翻译成 harness 心法、trace 演武场和最小代码实验。后续 sub-agent、agent team、multi-agent 调度，都是在这个闭环外面继续加隔离、通信、并行和验证。

```text
Multi-agent 不是起点。起点是一个可观察、可停止、可调试的 single-agent harness。
```

---

## 一、论文起手：ReAct 四问逐一作答

主论文：

- ReAct: Synergizing Reasoning and Acting in Language Models  
  https://arxiv.org/abs/2210.03629

本章的核心不是“介绍 ReAct 这个框架”，而是**把四个问题问清楚并回答**。完整推导见 [react-reading-notes.md](./react-reading-notes.md)，这里给出可直接复述的答案。

### 一问：为什么不能只输出最终答案？

因为很多任务需要**外部证据**。模型没读文件、没查环境、没跑工具时，它只能凭已有上下文和参数记忆生成，结果就是：缺证据时猜测、难以调试、难以发现错误、容易幻觉、无法处理依赖外部状态的任务。

```text
只回答   = 模型凭已有上下文生成
行动后答 = 模型先获取外部证据，再基于证据生成
```

> 答案一句话：**先取证，再回答。**

### 二问：`Thought -> Action -> Observation` 解决了什么？

它解决了推理与外部世界之间的**闭环**问题，让 agent 从“一次性押答案”变成“边查、边想、边修正”。

```text
Thought:     我现在缺什么信息？
Action:      我该调用哪个工具去拿信息？
Observation: 工具返回了什么事实？
Thought:     这个事实改变了我的判断吗？下一步做什么？
```

> 答案一句话：**想、做、看，再想。**

### 三问：Observation 如何改变下一步推理？

Observation 是环境返回的新**证据**，不是装饰性日志。harness 把它注入当前 state，模型下一轮据此改判：

- 成功结果 → 补充事实
- 失败结果 → 推翻假设
- 空结果 → 迫使换路线

```text
Observation = 环境反馈 / 证据
```

> 答案一句话：**环境反馈会改写计划。**

### 四问：agent 什么时候应该停止？

停止是工程问题，不能只靠“模型觉得想完了”。应停止的条件：目标已完成、证据已足够、再调用也不会带来新信息、达到预算上限、出现不可恢复错误、需要用户补充信息或授权。

核心停止条件 + 硬性保护：

```text
核心：当前 observation 与 state 足以完成用户目标 -> 输出 final
保护：max_steps / max_tokens / max_runtime / 重复动作检测 / 无新 observation 检测
```

> 答案一句话：**final + 预算 + 防循环。**

### 辅助论文

- MRKL Systems — https://arxiv.org/abs/2205.00445
- Toolformer — https://arxiv.org/abs/2302.04761

三篇分工：**ReAct 给闭环，MRKL 给模块化工具观，Toolformer 说明模型可学习何时用工具**；但真实执行、权限、trace 和停止条件，仍由 harness 承担。

---

## 二、从四问到核心概念

### Agent

Agent 是模型在一个任务目标下，基于上下文、工具和运行状态进行决策的执行单元。它不是“更会说的模型”，而是被 harness 组织起来、能取证和改判的执行循环。

### Harness

Harness 是模型外面的运行系统。它不是胶水代码，而是 agent 能否可靠工作的主体工程，负责：

- 组织 prompt / context
- 暴露工具 schema
- 解析模型 action 并校验参数
- 执行工具、回注 observation
- 记录 trace
- 控制循环停止、处理错误、重复动作和预算

### 最小 Loop

```text
User Goal
  -> Model 决定下一步动作        (对应一问：要不要取证)
  -> Harness 校验并执行工具       (对应二问：Action 由谁执行)
  -> Observation 回流给 Model     (对应三问：证据改判)
  -> Model 决定 continue 或 final (对应四问：何时停止)
```

四个问题正好对应这条 loop 的四个环节，这就是本章把“四问”作为主线的原因。

---

## 三、本章心法

```text
四问定纲
  一问 -> 缺证据，所以不能只答
  二问 -> Thought 判缺口、Action 请工具、Observation 带回事实
  三问 -> Observation 回注，成功补证 / 失败改判 / 空结果换路线
  四问 -> final、预算、防循环共同决定停止
```

一句话：

```text
Agent = Model + Harness + Tools + Stateful Loop
```

---

## 四、配套材料

- [react-reading-notes.md](./react-reading-notes.md)：ReAct 四问的完整阅读笔记（答案出处）。
- [chapter-01-design.md](./chapter-01-design.md)：第一章正文设计稿（章节结构、图、练习）。
- [../experiments/minimal-harness/](../experiments/minimal-harness/)：配套最小代码实验。

---

## 五、配套代码实验

实验目录：

```text
agent-volume/experiments/minimal-harness/
```

脚本化演示（无需 API key）：

```bash
cd agent-volume/experiments/minimal-harness
python3 agent.py "演示 Agent 卷第一章的最小 harness" --scripted-demo --reset-trace
```

真实模型模式：

```bash
export OPENAI_API_KEY="..."
export OPENAI_BASE_URL="https://api.openai.com/v1"
export OPENAI_MODEL="gpt-4.1-mini"

python3 agent.py "读取 agent-volume/roadmap.md，找出 Phase 01 的目标、必读论文和完成标准，并用三段话总结。" --reset-trace
```

实验支持的工具：

- `read_file(path)`
- `list_files(path)`
- `search_text(pattern, path)`
- `final(answer)`

跑完后读 `trace.jsonl`，对照四问检查：每一步为什么取证、Action 由谁执行、Observation 如何改判、最后凭什么停止。

---

## 六、Web 演武场

格物 Web 中对应：

```text
Agent 卷 -> 卷一 · Harness 起手 -> 第一式 · 想做相生
```

演武场分两段演示：

1. **四问段**：逐一点亮 ReAct 四问，给出每一问的答案要点与心法。
2. **trace 段**：把 `Thought -> Action -> Observation` 展开成可复盘轨迹，演示“取证成功”和“失败恢复”两条小剧场，并落到 `final / blocker / budget` 的停止判断。

---

## 七、完成标准

- 能逐一回答 ReAct 四问，而不只是复述问题。
- 能解释 agent 与 harness 的区别。
- 能解释 observation 如何影响下一步决策。
- 能解释 stop condition 为什么不能只靠“模型想完了”。
- 能运行 minimal harness 并读懂 `trace.jsonl`。
- 能在 Web 演武场里讲清楚 `Action -> Observation -> Final` 的路径。
