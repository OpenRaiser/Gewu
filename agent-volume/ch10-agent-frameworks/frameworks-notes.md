# Agent Frameworks 阅读笔记（横向对比）

## 资料

- Large Language Model based Multi-Agents: A Survey — https://arxiv.org/abs/2402.01680
- Multi-Agent Collaboration Mechanisms: A Survey of LLMs — https://arxiv.org/abs/2501.06322
- A Communication-Centric Survey — https://arxiv.org/abs/2502.14321
- LangChain: The Anatomy of an Agent Harness — https://www.langchain.com/blog/the-anatomy-of-an-agent-harness
- OpenAI Agents SDK patterns — https://openai.github.io/openai-agents-python/agents/

## 1. 核心立场

```text
框架是脚手架，不替你想清楚架构。
理解机制（读透明实现）> 会用某个框架。
```

## 2. 抽象层次速记

```text
透明/低层：mini-SWE-agent、OpenHarness        -> 学 harness 本身
中层：    OpenAI Agents SDK、LangGraph        -> 现代抽象 / 显式图
高层：    CrewAI、Google ADK                  -> 上手快，易变 workflow
```

权衡：抽象越高越快上手、越难看清和 debug；越低越费手、控制越强。

## 3. 三类状态模型

```text
session/handoff 式  -> OpenAI Agents SDK
图/状态机式         -> LangGraph
角色-任务/SOP 式    -> CrewAI / MetaGPT / ChatDev
```

按任务是“对话流 / 状态图 / 分工团队”来选。

## 4. trace 是硬指标

- 呼应 ch08：没 trace 无法评估归因。
- 选框架先问：trace 够不够做失败归因？
- OpenAI SDK、LangGraph 内置 tracing；高层框架若藏得太深，出事只能干瞪眼。

## 5. 高层抽象的陷阱

```text
把「自治 agent」写成「固定 LLM workflow」
```

很多“multi-agent”其实是 workflow + 多花 token（ch07 的框架版）。不是不能用 workflow，而是要**诚实知道自己在做哪个**。

## 6. AutoGen 现状

- 已进入维护模式，新项目看 Microsoft Agent Framework。
- 但 AutoGen 的 conversation pattern 仍值得理解。

## 7. 本阶段理解小结

```text
1. 框架按抽象层次和状态模型选，没有银弹。
2. trace 透明度是选型第一梯队考量。
3. 高层框架当心退化成固定 workflow。
4. 读 mini-SWE-agent / OpenHarness 学机制，胜过只会调框架。
5. 先做扎实单 agent，确有需求再上 multi-agent 和框架。
```
