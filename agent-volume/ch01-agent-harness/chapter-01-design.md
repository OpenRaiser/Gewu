# 第一章设计：从一次回答到可执行循环

## 章节定位

Agent 卷第一章不直接讲 multi-agent。它先建立一个判断基准：如果一个 single-agent harness 都不可观察、不可停止、不可调试，那么把它扩成多个 agent 只会放大混乱。

本章的主线是：

```text
一次性回答
  -> 缺少外部证据
  -> 引入工具调用
  -> 形成 Thought / Action / Observation 闭环
  -> 外部 harness 负责执行、记录和停止
```

读完本章，读者应该能把“模型在回答”与“agent 在执行任务”区分开。

## 读者目标

读者完成本章后应该能够：

- 解释 agent、tool、observation、trace、harness 的关系。
- 画出一个最小 ReAct-style agent loop。
- 说明为什么工具调用必须由 harness 执行，而不是由模型自己“假装执行”。
- 说明 observation 如何改变下一轮决策。
- 说清楚 agent loop 的停止条件和失控风险。
- 读懂并运行一个只包含文件工具的 minimal harness。

## 章节标题建议

首选标题：

```text
第 1 章：从一次回答到可执行循环
```

备选标题：

- `第 1 章：Agent 的最小闭环`
- `第 1 章：Harness 是 Agent 的身体`
- `第 1 章：Thought、Action 与 Observation`

首选标题更适合整卷开篇，因为它强调从普通 LLM 应用到 agent 系统的范式变化。

## 核心观点

本章只讲一个中心观点：

```text
Agent = Model + Harness + Tools + Stateful Loop
```

其中模型负责根据上下文选择下一步，harness 负责把下一步变成真实环境中的动作，并把结果作为 observation 回注给模型。

不要把 agent 讲成“更聪明的模型”。更准确的说法是：agent 是一个让模型能够持续感知、行动、修正和停止的运行系统。

## 概念边界

### Model

Model 是决策器。它根据当前上下文输出下一步：

- 直接回答
- 调用工具
- 请求更多信息
- 停止并给出 final

本章不展开模型训练、推理优化和 prompt 技巧，只关心它在 loop 中扮演什么角色。

### Tool

Tool 是外部能力。工具可以读取文件、搜索文本、访问网页、执行命令、查询数据库。

本章只使用文件类工具：

- `list_files(path)`
- `read_file(path)`
- `search_text(pattern, path)`

限制工具范围是有意的：第一章要让读者看清 loop，而不是被复杂工具生态分散注意力。

### Observation

Observation 是工具执行后的环境反馈。它不是装饰性的日志，而是下一轮推理的证据。

一个关键表达：

```text
没有 observation，agent 只能猜。
有 observation，agent 才能根据外部事实修正判断。
```

### Harness

Harness 是模型外部的运行系统。它不是“胶水代码”，而是 agent 能否可靠工作的核心。

它至少负责：

- 构造上下文
- 暴露工具 schema
- 解析模型 action
- 校验 action 参数
- 执行工具
- 截断或结构化 observation
- 记录 trace
- 控制最大 step / token / 时间
- 处理失败和重复动作

## 推荐章节结构

### 1.1 为什么普通问答不够

目标：把读者从“模型回答问题”的直觉切换到“模型需要外部证据”的直觉。

内容要点：

- 普通 LLM 回答依赖已有上下文和参数记忆。
- 当任务需要读取文件、检查环境、比较状态时，一次性回答会变成猜测。
- 真实任务需要“先获取证据，再回答”。

建议示例：

```text
用户：总结这个目录里的实验代码。
普通回答：模型如果没读文件，只能猜目录里有什么。
Agent 回答：先 list_files，再 read_file，再根据 observation 总结。
```

### 1.2 ReAct 的基本循环

目标：引入 `Thought -> Action -> Observation`。

内容要点：

- Thought：当前缺什么信息。
- Action：调用什么工具获取信息。
- Observation：工具返回什么事实。
- 下一轮 Thought：这个事实如何改变决策。

建议图：

```text
Goal
  |
  v
Thought: 我缺什么信息？
  |
  v
Action: 调用哪个工具？
  |
  v
Observation: 工具返回了什么？
  |
  v
Thought: 现在能回答了吗？还要继续吗？
```

注意：正式实现里不一定暴露完整 thought。为了教学，可以讲“推理意图”，但代码实验里让模型输出 `reason` 字段即可。

### 1.3 Harness：模型外面的执行系统

目标：解释为什么必须有 harness。

内容要点：

- 模型不能真的读取文件，它只能提出读取请求。
- harness 负责验证、执行和回注。
- harness 决定工具边界、安全边界和预算边界。
- harness 的质量决定 agent 是否可控。

最小伪代码：

```text
messages = [system_prompt, user_goal]

for step in range(max_steps):
    action = model(messages)
    if action.name == "final":
        return action.answer

    observation = run_tool(action.name, action.args)
    trace.append(action, observation)
    messages.append(action)
    messages.append(observation)

return stopped_by_budget
```

### 1.4 工具 schema 与 action 解析

目标：把“模型说要做什么”和“程序能执行什么”连接起来。

内容要点：

- 工具必须有清晰名字和参数。
- 模型输出必须是机器可解析格式。
- 无效 JSON、未知工具、非法路径都应该变成 observation，而不是让程序崩掉。

本章实验使用 JSON action：

```json
{"action":"read_file","args":{"path":"README.md"},"reason":"需要读取项目说明"}
```

结束动作：

```json
{"action":"final","answer":"..."}
```

### 1.5 Observation 回注与 trace

目标：说明 agent 为什么可调试。

内容要点：

- 每一步 action / observation 都应该进入 trace。
- trace 是复盘 agent 行为的证据链。
- 如果 agent 答错，先看 trace：它读了什么、漏了什么、是否重复调用、是否忽略错误。

建议 trace 结构：

```json
{"type":"model","step":1,"raw":"..."}
{"type":"tool","step":1,"action":"read_file","args":{"path":"README.md"},"observation":"..."}
{"type":"final","step":3,"answer":"..."}
```

### 1.6 停止条件

目标：让读者理解 stop condition 是工程问题，不是哲学问题。

内容要点：

- 完成任务后输出 final。
- 证据足够时停止。
- 达到 `max_steps` 时硬停止。
- 重复相同工具调用时干预。
- 工具持续失败时上报 blocker。

要强调：

```text
不能只靠“模型觉得自己想完了”来停止。
```

### 1.7 最小实验：文件研究 agent

目标：让读者跑通一个能做真实工作的最小 agent。

实验路径：

```text
learning/experiments/minimal-harness/
```

实验能力：

- 列目录
- 读文件
- 搜索文本
- 追加 trace
- 设置最大 step

建议任务：

```bash
python3 agent.py "读取 learning/roadmap.md，找出 Phase 01 的目标、必读论文和完成标准，并用三段话总结。"
```

如果从 `experiments/minimal-harness/` 目录运行，任务里的路径应相对 workspace 根目录 `/Volumes/T7/multi-agent`。

## 第一章叙事顺序

建议按下面顺序写正文：

1. 用一个失败案例开场：模型被要求总结本地文件，但没有读取文件。
2. 提出问题：模型缺少外部证据。
3. 引入工具：模型可以请求工具，但工具必须由 harness 执行。
4. 引入 ReAct loop：每一步都让 observation 改变下一步。
5. 抽象出 harness：执行、状态、trace、停止条件。
6. 落到代码：读 `experiments/minimal-harness/agent.py`。
7. 复盘 trace：说明这个 agent 为什么可调试。
8. 收束到下一章：如果单 agent 会根据失败反馈修正，就进入 Reflexion / Self-Refine。

## 章节中的关键图

### 图 1：普通 LLM 与 Agent 的差别

```text
普通 LLM:
User Goal -> Model -> Answer

Agent:
User Goal -> Model -> Action -> Harness -> Tool -> Observation -> Model -> ... -> Final
```

### 图 2：Harness 分层

```text
User Goal
   |
System Prompt / Policy
   |
Model
   |
Action Parser
   |
Tool Executor
   |
Observation Formatter
   |
Trace / State / Stop Controller
```

### 图 3：失败恢复

```text
Action fails
   |
Observation includes error
   |
Model chooses revised action
   |
Harness records both failure and recovery
```

## 需要避免的误解

- 不要把 agent 等同于“会调用工具的 prompt”。
- 不要把 harness 当成附属代码；它是 agent 系统的主体工程。
- 不要在第一章引入 sub-agent，否则主线会散。
- 不要讨论复杂 memory；第一章只需要当前 loop state。
- 不要让工具输出无边界地塞回上下文；即使是最小实验，也要有 `max_chars`。
- 不要把 final 当成自然语言结束语；它应该是明确的结束动作。

## 论文映射

本章主要承接三篇论文：

| 论文 | 本章使用方式 |
|---|---|
| ReAct | 提供 Thought / Action / Observation 的基本范式 |
| MRKL | 强调 LLM 与外部模块组合，而不是只靠模型内部知识 |
| Toolformer | 说明模型可以学习何时使用工具，但工程系统仍要负责执行工具 |

本章不需要完整复述论文实验结果。重点是把它们转译为 harness 设计原则。

## 练习设计

### 练习 1：画 loop

让读者画出下面任务的 action / observation 序列：

```text
总结 learning/roadmap.md 中 Phase 01 和 Phase 02 的区别。
```

期望步骤：

1. `read_file("learning/roadmap.md")`
2. 从 observation 中定位 Phase 01 / Phase 02
3. 输出 final

### 练习 2：找 bug

给读者一个错误 trace，让他判断 agent 为什么卡住：

```text
step 1: search_text("Phase 01", ".")
step 2: search_text("Phase 01", ".")
step 3: search_text("Phase 01", ".")
```

答案：重复相同工具调用，没有利用 observation 进入下一步。harness 应该检测重复并干预。

### 练习 3：改 stop condition

让读者给 minimal harness 增加一个规则：

```text
同一个 tool call 连续出现两次后，第三次返回错误 observation。
```

当前实验代码已经实现这个机制，可以让读者定位相关代码并解释。

## 章节产物

第一章结束时应产出：

- 一篇正文：解释 single-agent harness 的最小闭环。
- 一张 loop 图：普通回答 vs agent loop。
- 一个可运行实验：`experiments/minimal-harness/`。
- 一份 trace 样例：展示 action / observation / final。
- 一组复盘问题：为什么停、为什么继续、为什么失败。

## 完成标准

本章写完后，用下面问题自检：

- 读者是否能区分 model、agent、harness？
- 读者是否知道 tool call 由谁执行？
- 读者是否知道 observation 如何进入下一轮？
- 读者是否知道 trace 有什么用？
- 读者是否知道至少 3 种停止条件？
- 读者是否能运行 minimal harness 并解释每一行 trace？

如果这些问题都能回答，第一章就达到了进入第二章的标准。
