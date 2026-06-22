# ch10 · Agent Frameworks

本章目标：横向比较主流 agent 框架，理解它们在**抽象层次、状态模型、trace 设计**上的取舍，并建立一个判断：**框架是脚手架，不是替你想清楚架构。**

走到这一章，前面的概念都已具备：harness、tool、memory、feedback、sub-agent、team、协作、评估、协议。这一章把它们对照到真实框架上——看别人是怎么把这些抽象落地的，以及各自的代价。

## 本章要回答的问题

1. 这些框架处在什么抽象层次？低层和高层各有什么代价？
2. 状态模型有哪几类（SDK / 图 / 角色-任务）？
3. 为什么说 trace 设计是选框架时最该看的一点？
4. CrewAI 这类高层抽象的风险是什么？
5. 为什么要专门读 mini-SWE-agent / OpenHarness 这类“透明”实现？
6. 怎么选框架——或者说，什么时候根本不需要框架？

## 必读论文 / 资料

- Large Language Model based Multi-Agents: A Survey of Progress and Challenges  
  https://arxiv.org/abs/2402.01680

- Multi-Agent Collaboration Mechanisms: A Survey of LLMs  
  https://arxiv.org/abs/2501.06322

- A Communication-Centric Survey of LLM-Based Multi-Agent Systems  
  https://arxiv.org/abs/2502.14321

- LangChain: The Anatomy of an Agent Harness  
  https://www.langchain.com/blog/the-anatomy-of-an-agent-harness

- OpenAI Agents SDK multi-agent design patterns  
  https://openai.github.io/openai-agents-python/agents/

## 1. 抽象层次光谱

把框架按“透明度 vs 便利度”排开：

| 框架 | 抽象层次 | 状态模型 | 特点 |
|---|---|---|---|
| mini-SWE-agent | 极低 | 线性轨迹 | 代码路径短，最适合看清最小 agent loop |
| OpenHarness | 低 | 显式 harness | 研究 harness 底层怎么搭 |
| OpenAI Agents SDK | 中（轻量） | session + handoff | tools / handoffs / guardrails / tracing 的最小现代抽象 |
| LangGraph | 中低（显式图） | 状态机 / 图 | 复杂状态、循环、长任务 |
| Microsoft Agent Framework | 中 | AutoGen + SK 后继 | AutoGen 已维护模式，新项目看 MAF |
| Google ADK | 中高 | 偏生产部署 | 多语言、企业工作流 |
| CrewAI | 高 | role / task / crew | 易上手，但易退化成“LLM workflow” |

核心权衡：

```text
抽象越高 -> 上手越快，但越看不清底下发生了什么，越难 debug 和定制。
抽象越低 -> 写得越多，但对 loop / 上下文 / trace 的控制越强。
```

## 2. 三类状态模型

不同框架对“agent 的状态怎么存、怎么流转”有不同答案：

- **SDK / session 式**（OpenAI Agents SDK）：以会话和 handoff 为单位，状态相对隐式，适合理解现代 SDK 的最小抽象。
- **图 / 状态机式**（LangGraph）：把 agent 流程显式建成节点和边，状态在图里流转。适合复杂循环、长任务、需要精确控制流转的场景。
- **角色-任务式**（CrewAI / MetaGPT / ChatDev）：以 role / task / crew 或 SOP 组织，贴近“团队分工”的直觉，但容易把自治 agent 写成固定 workflow。

选哪类，取决于任务是“一段对话流”“一张状态图”还是“一个分工团队”。

## 3. Trace 设计：选框架最该看的一点

呼应 ch08——**没有 trace 就无法评估和归因**。所以选框架时，trace 能力是第一梯队的考量:

- OpenAI Agents SDK、LangGraph 都**内置** tracing：每个 agent 的输入、tool 调用、输出、token、耗时，以及 agent 间消息，都能记录回放。
- 高层框架如果把执行过程藏得太深、trace 不透明，出问题时你只能干瞪眼。
- 判断一个框架是否“能用来做严肃工作”，先问：**它的 trace 够不够我做失败归因？**

## 4. 高层抽象的风险

CrewAI 这类高层 role/task 抽象上手快，但有个反复出现的陷阱：

```text
把「自治 agent」写成了「固定的 LLM workflow」
```

也就是说，表面是“多个角色 agent 协作”，实际只是一串预定义的 LLM 调用，agent 并没有真正自主规划、调用工具、应对意外。这未必是坏事（很多任务确实只需要 workflow），但要**诚实地知道自己在做哪个**——别把一个 if-else 流程包装成“多智能体系统”。

这正是 ch07 那个警惕的框架版：**很多“multi-agent”其实是 workflow + 多花 token。**

## 5. 为什么要读透明实现

光用高层框架，学不到 harness 的真本事。要真正理解 agent 怎么运转，得读“透明”实现：

- **mini-SWE-agent**：代码路径极短，最适合看清最小可运行 loop、线性轨迹、沙箱执行。
- **OpenHarness**：专门展示 harness 底层怎么搭。
- **Aider / SWE-agent / OpenHands**：研究 repo map、diff 驱动编辑、agent-computer interface、完整开发 harness。

读它们的目的不是抄，而是看清楚：**上下文怎么喂、工具怎么执行、沙箱怎么做、trace 怎么记、失败怎么恢复。** 这些正是本卷 ch01–ch08 讲的机制在真实代码里的样子。

## 6. 怎么选——以及何时不用框架

选型判断（与本卷一贯立场一致）：

```text
先问：这个任务真的需要框架吗？
  - 一个会用工具、会管上下文的单 agent 就够 -> 可能连框架都不需要
  - 需要复杂状态 / 循环 / 长任务      -> LangGraph 这类显式图
  - 需要快速搭多角色协作原型          -> CrewAI 这类高层（但认清是不是 workflow）
  - 要研究 harness 本身                -> 读 mini-SWE-agent / OpenHarness
```

不变的原则：

- **先把 single-agent harness 做扎实**，再在确有并行 / 隔离 / 多视角需求时引入 multi-agent（见 ch07）。
- 框架解决的是工程脚手架，**不替你想清楚“要不要 multi-agent、通信怎么设计、怎么评估”**——这些是本卷前九章的内容。
- AutoGen 已进入维护模式，新项目优先看 Microsoft Agent Framework；但**理解 AutoGen 的 conversation pattern 仍有价值**。

## 配套资源

本章不写代码实验，而是给一份“对照阅读”清单——把本卷学到的机制对到真实框架/项目上：

| 想看清的机制 | 去读 |
|---|---|
| 最小 agent loop（ch01） | mini-SWE-agent |
| 工具执行 / 沙箱（ch02） | SWE-agent、Aider |
| 上下文 / 记忆（ch03） | OpenHands、Agent Zero |
| 反馈 / 修正（ch04） | SWE-agent、OpenHands |
| sub-agent / team（ch05–06） | OpenAI Agents SDK、Agency Swarm、AutoGen |
| trace / 评估（ch08） | LangGraph tracing、MAST |
| harness 全貌 | OpenHarness |

详细项目链接见 `../papers/multi-agent-research.md` 第 5 节。

## 完成标准

学完本章后，你应该能解释：

- 框架的抽象层次光谱，以及高层 / 低层各自的代价
- SDK 式、图式、角色-任务式三类状态模型的区别
- 为什么 trace 设计是选框架时的第一梯队考量
- 高层抽象“把自治 agent 写成固定 workflow”的风险
- 为什么要读 mini-SWE-agent / OpenHarness 这类透明实现
- 怎么按任务选框架，以及什么时候根本不需要框架

一句话总结：

```text
框架是脚手架，按抽象层次和状态模型选，trace 透明度是硬指标。但框架不替你想清楚「要不要 multi-agent、通信怎么设计、怎么评估」——那是本卷前九章的事。理解机制（读透明实现）比会用某个框架更值钱。
```

---

## 全卷收尾

到这里，Agent 卷十章走完一条完整路径：

```text
ch01 harness 起手  ->  ch02 工具  ->  ch03 记忆/状态  ->  ch04 反馈/规划
   ->  ch05 sub-agent  ->  ch06 agent team  ->  ch07 多体协作
   ->  ch08 评估/trace  ->  ch09 协议层  ->  ch10 框架对比
```

贯穿全卷的一条主线：

```text
先把 single-agent harness 做扎实；
multi-agent 不是默认更强，只在对齐预算、可观测 trace、可复现评估下
证明有结构性收益时才用；
框架和协议是工程脚手架，不替代对机制的理解。
```
