# Multi-Agent / Agent Harness 调研笔记

日期：2026-06-18

## 1. 核心概念

截至 2026-06-18，multi-agent 不是“多个模型聊天”这么简单，它本质上是 **harness engineering**，也就是围绕模型构建执行、状态、工具、权限、通信、调度和验证系统。

### Agent

Agent 通常可以理解为：

- 模型
- 指令 / 角色
- 上下文
- 工具
- 状态 / 记忆
- 运行循环

OpenAI 的定义也强调 agent 是会规划、调用工具、跨专家协作并保持足够状态的应用。

参考：

- https://developers.openai.com/api/docs/guides/agents

### Harness

Harness 是模型外面的完整运行系统，包括：

- system prompt
- 工具 / MCP
- 文件系统、浏览器、沙箱
- 状态
- 记忆
- approval
- trace
- 子 agent 调度
- 错误恢复

LangChain 的说法很直接：

```text
Agent = Model + Harness
```

参考：

- https://www.langchain.com/blog/the-anatomy-of-an-agent-harness

### Sub-agent

Sub-agent 是主 agent 把一个明确子任务交给隔离上下文中的 worker，worker 完成后回报结果。

Codex 官方文档说明 subagent 由 Codex 负责创建、路由、等待和汇总，而且只在用户显式要求时启用。

参考：

- https://developers.openai.com/codex/subagents

### Agent Team

`Agent team` 不是严格学术统一术语，更多来自 Claude、OpenHarness、社区实践。通常指多个独立 agent 进程，有共享任务列表、依赖关系、直接消息，而不是只向主 agent 汇报。

Addy Osmani 的文章把它描述为共享 task list + peer-to-peer messaging。

参考：

- https://addyosmani.com/blog/code-agent-orchestra/

## 2. 一个最小 Agent Loop

一个底层 agent loop 可以理解成：

```text
while not done:
  context = build_context(goal, state, memory, tools, observations)
  action = model(context)
  if action is tool_call:
      validate -> approve if needed -> execute in sandbox -> observe
  if action is spawn_subagent:
      create isolated run loop -> wait/merge result
  update_state_trace_memory()
  verify_progress_or_stop()
```

Multi-agent 是在这个 loop 外面再加：

- 任务拆分
- 调度器
- 消息协议
- 共享状态
- 权限边界
- 结果聚合
- 冲突解决
- 评价器

## 2.5 Harness 的真正难点（机制层，非清单）

第 1 节列了 harness 的“组成部分”，但决定一个 harness 好坏的不是清单，而是下面这几个工程机制。这部分是“搞清楚 harness 原理”的核心。

### 上下文管理 / 压缩（context engineering）

模型的 context window 有限，而 agent loop 会不断追加 observation、tool output、子 agent 回报，长任务必然溢出。harness 必须主动管理上下文：

- **截断与摘要**：当历史接近窗口上限时，把早期轮次压缩成摘要（summarization），保留目标、关键决策、未完成事项，丢弃冗余 tool 输出。Claude Code / Codex 这类系统都内置了“自动压缩”机制。
- **记忆落盘再回灌**：把跨轮次需要的信息写到外部文件 / 向量库，下一轮按需检索回灌，而不是全塞进 prompt。这是“memory”与“context window”的分工。
- **分层上下文**：system prompt（稳定）、任务状态（中频更新）、当前观察（高频）分层组织，避免每轮重发不变内容（也利于 prompt caching 降本）。

要点：**上下文管理是 harness 最难、最影响实际表现的部分**。同一个模型，配一个会压缩/检索的 harness 和一个只会无脑追加的 harness，长任务表现天差地别。

### 工具结果如何回注 loop

tool output 不是直接拼回 prompt 就完事：

- **截断策略**：一个 `grep` 可能返回上万行。harness 要决定截断长度、保留头尾、还是结构化摘要，否则单次 tool 输出就撑爆上下文。
- **结构化 vs 原始**：把 stdout/stderr/exit code 结构化呈现，比塞一坨纯文本更利于模型判断成败。
- **错误可恢复性**：工具失败时，要把**有信息量的错误**（stderr、报错行号）回注，让模型能据此修正，而不是只回一句 “tool failed”。

### 停止条件 / 防死循环

伪代码里的 `verify_progress_or_stop()` 是 harness 的核心难题，实际要处理：

- **完成判定**：任务“做完了”往往没有明确信号，需要靠显式 stop 工具、或让模型自评、或外部 verifier 判定。
- **无进展检测**：模型可能反复调用同一个失败的工具、或在两个状态间循环。harness 需要检测“重复动作 / 无新信息”并干预。
- **预算上限**：硬性的 step 数、token 数、wall-clock、花费上限作为兜底，防止失控（已有论文专门统计 agent 预算超支事故，见 2606.04056）。

### 错误恢复

不是“列在清单里”就够了，要明确策略：

- **重试 vs 回退 vs 上报**：瞬时错误重试，逻辑错误让模型看到 stderr 自行修正，无法处理的上报给用户/主 agent。
- **让模型看见失败**：多数情况下，把真实报错回注让模型自我纠正，比 harness 静默兜底更有效。
- **检查点 / 回滚**：危险或不可逆操作前做备份（PaperFit 的 `data/backups/` 就是这个思路），失败可回滚。

## 2.6 并行 / 协同的工程现实

“并行/协同”在概念上简单，真正卡住人的是下面这些工程问题——它们决定了 multi-agent 是不是“纸面上更强、跑起来更糟”。

### 上下文：隔离 vs 共享

- **隔离上下文（subagent 主流做法）**：每个 worker 独立 context，好处是省 token（主 agent 不必背负 worker 的全部中间过程）、防止上下文互相污染、可并行。代价是主 agent 只能看到 worker 的**总结**，丢失细节，可能漏掉关键信息。
- **共享上下文 / blackboard**：多 agent 读写同一状态池，信息完整但 token 成本高、易互相干扰、需要并发控制。
- 实务上的权衡：**探索/搜索类任务适合隔离并行**（各查各的，最后汇总）；**强耦合、需要彼此中间结果的任务**，隔离反而要靠反复传递摘要，得不偿失。

### 状态一致性与并发

多个 worker 同时动手时，传统并发问题全部回来：

- **文件 / 工作区冲突**：两个 agent 同时改同一文件会互相覆盖。常见解法是**工作区隔离**（每个 worker 一份 git worktree / 沙箱副本），最后再合并——这正是“隔离副本”范式的价值。
- **共享状态竞争**：写同一个 task list / state.json 需要加锁或串行化写入，否则状态错乱。
- **顺序依赖**：有依赖关系的子任务不能盲目并行，需要调度器维护 DAG（哪些能并行、哪些必须等前置完成）。

### 结果聚合与冲突裁决

并行省了时间，但**合并是新成本**：

- **合并策略**：多个 worker 产出如何 merge——拼接？去重？取最优？投票？
- **冲突裁决**：worker A 和 worker B 给出矛盾结论时谁说了算，需要一个 reducer / judge / 主 agent 来裁决，而不是简单拼接。
- **质量参差**：并行 worker 质量不一，聚合层要能识别并丢弃低质量产出，否则“最差的那个”会拖垮整体。

### 成本 / 延迟模型（必须显式算账）

- 并行优化的是 **wall-clock 时延**（多个 worker 同时跑），但 **token 总成本通常翻倍甚至更多**（每个 worker 都要重建上下文、主 agent 还要消化汇报）。
- 通信本身有成本：agent 间每多一轮消息就是一次完整的 prompt+completion。已有工作（AgentPrune、AgentDropout 等）专门研究**剪掉冗余通信边**来降本。
- 选型判断：**当任务可真正并行、且每个子任务足够重**（值回上下文重建的开销）时，并行才划算；琐碎任务并行只是徒增 token 和协调成本。

## 3. 主流架构模式

LangChain 和 OpenAI 的文档基本把工程模式收敛到几类：subagents、handoffs、skills、router、自定义 workflow。OpenAI Agents SDK 也明确区分 manager / agents-as-tools 和 handoffs 两大常见模式。

参考：

- https://docs.langchain.com/oss/python/langchain/multi-agent
- https://openai.github.io/openai-agents-python/agents/

| 模式 | 解释 | 适用 |
|---|---|---|
| Single agent + tools | 一个 agent 自己规划和调用工具 | 起点，最容易 debug |
| Router | 先分类，再派给专门 agent | 客服、查询、任务入口 |
| Manager / agents-as-tools | 主 agent 调多个专家 agent | 子任务可并行、结果需汇总 |
| Handoff | 当前 agent 把控制权移交给另一个 agent | 多轮对话、不同职责接管 |
| Debate / critic | 多个 agent 给答案、互评、judge 汇总 | 需要多视角，但成本高 |
| Blackboard / shared memory | 多 agent 写同一状态池 | 长任务、团队协作 |
| Agent team / swarm | 多进程、共享任务表、直接通信 | 编程、研究、复杂项目执行 |
| A2A / MCP / ACP | 标准化工具和跨 agent 通信协议 | 企业集成、跨平台 agent |

### 协议层：四个协议各自解决什么（别混为一谈）

表里最后一行把 A2A / MCP / ACP 一笔带过，但它们解决的是**不同层次**的问题，研究时必须区分（综述见 2505.02279）：

- **MCP（Model Context Protocol）**：解决 **agent ↔ 工具 / 数据源** 的接入。它是“纵向”的——让一个 agent 用统一方式连接文件系统、数据库、API 等外部能力。**不解决 agent 之间怎么通信**。
- **A2A（Agent-to-Agent，Google）**：解决 **agent ↔ agent** 的横向通信——不同厂商/框架做的 agent 如何互相发现、协商、委派任务。靠 Agent Card 描述能力。
- **ACP（Agent Communication Protocol）**：同样面向 agent 间通信，更偏 REST/消息式的标准化交互，定位与 A2A 有重叠，是另一条演进路线。
- **ANP（Agent Network Protocol）**：面向更开放的“agent 互联网”场景，强调去中心化的身份与发现。

一句话记忆：**MCP 接工具（纵向），A2A / ACP / ANP 接 agent（横向）**。这个领域还在快速洗牌、标准未定，了解“各自解决哪一层”比记细节更重要。

## 4. 近期论文阅读地图

建议先读 survey，再读代表系统，再读反例和评价。

| 方向 | 重点资料 | 价值 |
|---|---|---|
| 总览 | Large Language Model based Multi-Agents, 2024 | LLM-MAS 基础综述 |
| 协作机制 | Multi-Agent Collaboration Mechanisms: A Survey of LLMs, 2025 | 从 actor、协作类型、结构、策略、协议分析 MAS |
| 通信视角 | A Communication-Centric Survey of LLM-Based Multi-Agent Systems, 2025（2502.14321） | 把 communication 当成 MAS 核心问题。注：“Beyond Self-Talk”这一副标题及“已被 Frontiers of Computer Science 接收”均未核实，已删去 |
| 编排架构 | The Orchestration of Multi-Agent Systems: Architectures, Protocols, and Enterprise Adoption, 2026（2601.13671） | 讨论从单 agent 到松耦合多 agent、企业采用和协议 |
| 闭环演化 | Surveying Collaboration, Failure Attribution, and Self-Evolution in LLM-based Multi-Agent Systems, 2026（2605.14892） | 把能力、协作、失败归因、自演化连成 LIFE 框架（“Beyond Individual Intelligence”为意译标题，非论文真实标题） |
| 协议互操作 | A Survey of Agent Interoperability Protocols..., 2025 | 比较 MCP、ACP、A2A、ANP |
| 经典系统 | CAMEL、AutoGen、MetaGPT、ChatDev | 分别代表角色扮演、可编程多 agent 对话、SOP 工作流、软件开发团队 |
| 通信效率 | Cut the Crap / AgentPrune, ICLR 2025（2410.02506） | 指出多 agent 通信冗余和 token 成本问题 |
| 反例 / 警惕 | Single-Agent LLMs Outperform Multi-Agent Systems on Multi-Hop Reasoning Under Equal Thinking Token Budgets, 2026（2604.02460） | 很多 MAS 提升可能只是多花了 token，不是架构天然更强 |
| debate 反思 | ICLR Blogposts 2025: Multi-LLM-Agents Debate | 多 agent debate 不稳定，常不如简单 single-agent test-time compute |
| credit assignment | Credit Assignment for Cooperative LLM Agents, 2026（2603.06859） | 研究多 agent 中谁贡献了什么，适合理解评价和训练（原报告“Exact Is Easier”标题有误） |

### 论文链接

- Large Language Model based Multi-Agents: A Survey of Progress and Challenges: https://arxiv.org/abs/2402.01680
- Multi-Agent Collaboration Mechanisms: A Survey of LLMs: https://arxiv.org/abs/2501.06322
- A Communication-Centric Survey of LLM-Based Multi-Agent Systems: https://arxiv.org/abs/2502.14321
- The Orchestration of Multi-Agent Systems (Architectures, Protocols, and Enterprise Adoption): https://arxiv.org/abs/2601.13671
- Surveying Collaboration, Failure Attribution, and Self-Evolution in LLM-based Multi-Agent Systems（提出 LIFE 框架）: https://arxiv.org/abs/2605.14892
- A Survey of Agent Interoperability Protocols: MCP, ACP, A2A, and ANP: https://arxiv.org/abs/2505.02279
- CAMEL: Communicative Agents for "Mind" Exploration of Large Language Model Society: https://arxiv.org/abs/2303.17760
- AutoGen: Enabling Next-Gen LLM Applications via Multi-Agent Conversation: https://arxiv.org/abs/2308.08155
- MetaGPT: Meta Programming for A Multi-Agent Collaborative Framework: https://arxiv.org/abs/2308.00352
- ChatDev: Communicative Agents for Software Development: https://arxiv.org/abs/2307.07924
- Cut the Crap (AgentPrune): An Economical Communication Pipeline for LLM-based Multi-Agent Systems, ICLR 2025: https://arxiv.org/abs/2410.02506
- Single-Agent LLMs Outperform Multi-Agent Systems on Multi-Hop Reasoning Under Equal Thinking Token Budgets: https://arxiv.org/abs/2604.02460
- Multi-LLM-Agents Debate (ICLR 2025 Blogposts): https://d2jud02ci9yv69.cloudfront.net/2025-04-28-mad-159/blog/mad/
- Credit Assignment for Cooperative LLM Agents: https://arxiv.org/abs/2603.06859
- When Single-Agent with Skills Replace Multi-Agent Systems and When They Fail（单 agent 基线对照）: https://arxiv.org/abs/2601.04748
- An Empirical Catalog of 63 LLM-Agent Budget-Overrun Incidents（预算超支事故，呼应停止条件/预算上限）: https://arxiv.org/abs/2606.04056

## 5. 开源项目和框架

建议不要一开始就全学。按“底层透明度”和“工程成熟度”分层看：

| 项目 | 定位 | 备注 |
|---|---|---|
| OpenAI Agents SDK | 轻量 agent SDK，支持 tools、handoffs、guardrails、sessions、tracing | 适合理解现代 SDK 最小抽象 |
| LangGraph | 低层、状态机 / 图式 agent orchestration | 适合研究复杂状态、循环、长期任务 |
| CrewAI | 高层 role / task / crew 抽象 | 易上手，但要警惕变成“LLM workflow”而非真正自治 agent |
| Microsoft Agent Framework | AutoGen + Semantic Kernel 后继 | AutoGen 已进入维护模式，新项目应看 MAF |
| Google ADK | Google 开源 agent dev kit | 多语言、偏生产部署和企业工作流 |
| LlamaIndex AgentWorkflow | RAG / 数据场景中的 multi-agent workflow | 适合结合文档检索、handoff |
| CAMEL | 多 agent 角色扮演和社会模拟 | 适合研究 agent society |
| MetaGPT / ChatDev | 软件工程团队范式 | 适合理解 SOP、角色分工、瀑布式 agent 团队 |
| OpenHarness | 开源 harness 实现 | 很适合研究 agent harness 底层怎么搭 |

### 项目链接

- OpenAI Agents SDK: https://github.com/openai/openai-agents-python
- LangGraph: https://github.com/langchain-ai/langgraph
- CrewAI: https://github.com/crewaiinc/crewai
- Microsoft AutoGen: https://github.com/microsoft/autogen
- Microsoft Agent Framework: https://learn.microsoft.com/en-us/agent-framework/overview/
- Google ADK: https://github.com/google/adk-python
- LlamaIndex AgentWorkflow: https://developers.llamaindex.ai/typescript/framework/modules/agents/agent_workflow/
- CAMEL: https://www.camel-ai.org/
- MetaGPT: https://github.com/foundationagents/metagpt
- ChatDev: https://github.com/OpenBMB/ChatDev
- OpenHarness: https://github.com/HKUDS/OpenHarness

### 社区 / 研究型开源项目

上面的表偏“官方框架 / SDK”。如果目标是研究 agent 与 harness 的真实工程形态，还应该读一些社区和研究型项目的代码。它们未必都适合作为生产基座，但很适合观察：上下文怎么喂、工具怎么执行、沙箱怎么做、trace 怎么记、失败怎么恢复。

| 项目 | 关注点 | 为什么值得看 |
|---|---|---|
| mini-SWE-agent | 极简 coding agent / bash-only harness | 代码路径短，适合理解最小可运行 agent loop、线性轨迹、沙箱执行 |
| SWE-agent | Agent-computer interface / 自动修 GitHub issue | 研究 agent 与命令行、编辑器、测试系统之间的接口设计 |
| OpenHands | 通用软件开发 agent | 可看浏览器、终端、文件系统、前端 UI、任务状态如何组合成完整 harness |
| Cline | IDE 内 autonomous coding agent | 适合研究人机协同、工具 approval、MCP、编辑器上下文 |
| Aider | 终端 pair-programming agent | 适合研究 repo map、diff/patch 驱动编辑、开发者可控性 |
| OpenCode | 终端 coding agent | 适合对比不同 CLI agent 的 session、工具、补丁和权限设计 |
| AutoGPT | 早期自主 agent / 平台化尝试 | 适合看“长任务自治”范式的演化，也适合反思过度自治的问题 |
| BabyAGI | 早期 task-list agent | 适合理解任务生成、优先级队列、记忆检索这一类最小 autonomous loop |
| Agent Zero | 通用可扩展 agent framework | 适合看工具、长期记忆、可组合 agent 行为如何落地 |
| Agency Swarm | 角色化 multi-agent orchestration | 适合研究 directional communication flows、agent role、共享 instructions |
| AgentVerse | 多 agent task-solving / simulation | 适合研究 task-solving 与 simulation 两类 multi-agent 场景的差异 |
| Langroid | multi-agent programming | 适合研究以消息、任务、工具为核心的多 agent 编程抽象 |
| OpenManus | Manus 风格开源 agent | 适合观察浏览器自动化、A2A/MCP、sandbox、通用任务执行的组合 |
| Continue | 开源 coding agent / IDE assistant | 适合研究开发环境上下文、检索、编辑循环与 human-in-the-loop |
| Sim | agent workflow orchestration | 适合看低代码/工作流式 agent 编排与部署 |
| MAST | multi-agent 失败分类 / 标注数据 | 适合研究失败归因、trace 标注、LLM-as-judge |
| AgentBench | agent benchmark | 适合研究 OS、数据库、Web、游戏等环境中的 agent 评估 |
| ToolBench | tool-use benchmark / ToolLLM | 适合研究真实 API 调用、工具学习、工具选择评估 |
| SWE-bench | coding benchmark | 适合研究真实 GitHub issue 修复、Docker 评测、patch 验证 |
| GAIA | general AI assistant benchmark | 适合研究需要工具、检索、文件处理的通用 agent 任务 |

链接：

- mini-SWE-agent: https://github.com/SWE-agent/mini-swe-agent
- SWE-agent: https://github.com/SWE-agent/SWE-agent
- OpenHands: https://github.com/OpenHands/OpenHands
- Cline: https://github.com/cline/cline
- Aider: https://github.com/Aider-AI/aider
- OpenCode: https://github.com/anomalyco/opencode
- AutoGPT: https://github.com/Significant-Gravitas/AutoGPT
- BabyAGI: https://github.com/yoheinakajima/babyagi
- Agent Zero: https://github.com/agent0ai/agent-zero
- Agency Swarm: https://github.com/VRSEN/agency-swarm
- AgentVerse: https://github.com/OpenBMB/AgentVerse
- Langroid: https://github.com/langroid/langroid
- OpenManus: https://github.com/FoundationAgents/OpenManus
- Continue: https://github.com/continuedev/continue
- Sim: https://github.com/simstudioai/sim
- MAST: https://github.com/multi-agent-systems-failure-taxonomy/MAST
- AgentBench: https://github.com/THUDM/AgentBench
- ToolBench: https://github.com/OpenBMB/ToolBench
- SWE-bench: https://github.com/swe-bench/SWE-bench
- GAIA dataset: https://huggingface.co/datasets/gaia-benchmark/GAIA

## 6. 博客 / 工程实践优先读

- LangChain: The Anatomy of an Agent Harness  
  https://www.langchain.com/blog/the-anatomy-of-an-agent-harness

- OpenAI Codex subagents 官方文档  
  https://developers.openai.com/codex/subagents

- OpenAI Agents SDK multi-agent design patterns  
  https://openai.github.io/openai-agents-python/agents/

- Addy Osmani: The Code Agent Orchestra  
  https://addyosmani.com/blog/code-agent-orchestra/

- Google A2A: A new era of agent interoperability  
  https://developers.googleblog.com/en/a2a-a-new-era-of-agent-interoperability/

- Agent Interoperability Protocols survey  
  https://arxiv.org/abs/2505.02279

## 7. 建议学习路线

下面把每一步都挂上“必读论文”。顺序按实现难度递进：先理解 single-agent harness，再引入 sub-agent / team，再做评估和协议层。

| 步骤 | 学习目标 | 必读论文 | 可配套看的项目 |
|---|---|---|---|
| 1. 最小 single-agent harness | model call、tool schema、tool execution、trace、stop condition | ReAct: Synergizing Reasoning and Acting in Language Models（2210.03629）；MRKL Systems（2205.00445）；Toolformer: Language Models Can Teach Themselves to Use Tools（2302.04761） | mini-SWE-agent、Aider、OpenAI Agents SDK |
| 2. 带反馈的单 agent | 学会让 agent 从工具反馈、环境反馈、失败中迭代，而不是一次性回答 | Reflexion: Language Agents with Verbal Reinforcement Learning（2303.11366）；Self-Refine: Iterative Refinement with Self-Feedback（2303.17651）；Language Agent Tree Search Unifies Reasoning Acting and Planning in Language Models（2310.04406） | SWE-agent、OpenHands、Cline |
| 3. 记忆 / 长期状态 / 环境 | 理解 memory、reflection、skill library、长期任务状态如何进入 harness | Generative Agents: Interactive Simulacra of Human Behavior（2304.03442）；Voyager: An Open-Ended Embodied Agent with Large Language Models（2305.16291） | BabyAGI、Agent Zero、OpenManus |
| 4. 加 sub-agent / manager-worker | 主 agent 拆任务，多个 worker 隔离上下文并行执行，主 agent 汇总 | AutoGen: Enabling Next-Gen LLM Applications via Multi-Agent Conversation（2308.08155）；MetaGPT: Meta Programming for A Multi-Agent Collaborative Framework（2308.00352）；ChatDev: Communicative Agents for Software Development（2307.07924）；CAMEL: Communicative Agents for "Mind" Exploration of Large Language Model Society（2303.17760） | AutoGen、MetaGPT、ChatDev、Agency Swarm、AgentVerse、Langroid |
| 5. 加 evaluator / critic / verifier | 让一个 agent 或 verifier 专门检查结果、定位失败，而不是直接相信 worker | Why Do Multi-Agent LLM Systems Fail?（2503.13657）；Credit Assignment for Cooperative LLM Agents（2603.06859）；Surveying Collaboration, Failure Attribution, and Self-Evolution in LLM-based Multi-Agent Systems（2605.14892） | LangGraph tracing、OpenAI Agents SDK tracing、MAST repo |
| 6. 做 ablation 和基线 | 同样 token budget 下比较 single-agent、parallel subagents、debate、manager-worker | Single-Agent LLMs Outperform Multi-Agent Systems on Multi-Hop Reasoning Under Equal Thinking Token Budgets（2604.02460）；When Single-Agent with Skills Replace Multi-Agent Systems and When They Fail（2601.04748）；AgentPrune / Cut the Crap（2410.02506） | mini-SWE-agent、SWE-agent、OpenHands、AgentBench |
| 7. agent benchmark / coding benchmark | 学会可复现实验：成功率、token、wall-clock、trace、失败归因 | AgentBench: Evaluating LLMs as Agents（2308.03688）；ToolLLM: Facilitating Large Language Models to Master 16000+ Real-world APIs（2307.16789）；SWE-bench: Can Language Models Resolve Real-World GitHub Issues?（2310.06770）；GAIA: a benchmark for General AI Assistants（2311.12983）；SWE-agent: Agent-Computer Interfaces Enable Automated Software Engineering（2405.15793） | SWE-bench、SWE-agent、OpenHands、AgentBench |
| 8. 成熟框架横向对比 | 比较 SDK、graph workflow、team orchestration、状态机、trace 设计 | Large Language Model based Multi-Agents: A Survey of Progress and Challenges（2402.01680）；Multi-Agent Collaboration Mechanisms: A Survey of LLMs（2501.06322）；A Communication-Centric Survey of LLM-Based Multi-Agent Systems（2502.14321） | OpenAI Agents SDK、LangGraph、Microsoft Agent Framework、OpenHarness、CrewAI |
| 9. 协议层 | MCP 解决工具 / 上下文接入；A2A / ACP / ANP 解决 agent-to-agent 通信 | A Survey of Agent Interoperability Protocols: MCP, ACP, A2A, and ANP（2505.02279）；The Orchestration of Multi-Agent Systems: Architectures, Protocols, and Enterprise Adoption（2601.13671） | MCP servers、A2A samples、OpenManus、OpenHarness |

### 第 7 节新增论文链接

- ReAct: Synergizing Reasoning and Acting in Language Models: https://arxiv.org/abs/2210.03629
- MRKL Systems: A modular, neuro-symbolic architecture that combines large language models, external knowledge sources and discrete reasoning: https://arxiv.org/abs/2205.00445
- Toolformer: Language Models Can Teach Themselves to Use Tools: https://arxiv.org/abs/2302.04761
- Reflexion: Language Agents with Verbal Reinforcement Learning: https://arxiv.org/abs/2303.11366
- Self-Refine: Iterative Refinement with Self-Feedback: https://arxiv.org/abs/2303.17651
- Language Agent Tree Search Unifies Reasoning Acting and Planning in Language Models: https://arxiv.org/abs/2310.04406
- Generative Agents: Interactive Simulacra of Human Behavior: https://arxiv.org/abs/2304.03442
- Voyager: An Open-Ended Embodied Agent with Large Language Models: https://arxiv.org/abs/2305.16291
- Why Do Multi-Agent LLM Systems Fail?: https://arxiv.org/abs/2503.13657
- AgentBench: Evaluating LLMs as Agents: https://arxiv.org/abs/2308.03688
- ToolLLM: Facilitating Large Language Models to Master 16000+ Real-world APIs: https://arxiv.org/abs/2307.16789
- SWE-bench: Can Language Models Resolve Real-World GitHub Issues?: https://arxiv.org/abs/2310.06770
- GAIA: a benchmark for General AI Assistants: https://arxiv.org/abs/2311.12983
- SWE-agent: Agent-Computer Interfaces Enable Automated Software Engineering: https://arxiv.org/abs/2405.15793

## 8. 评估方法论（怎么测，而不只是怎么搭）

第 10 节的关键判断（“相同预算下是否有结构性收益”）只有配上**可执行的测法**才站得住。这是全报告最该有、原稿却缺失的一块。

### 控变量：token / 成本预算对齐

multi-agent 几乎总能靠“多花 token”刷出更高分，所以任何 “MAS 更强” 的结论都必须在**对齐预算**下才有意义：

- 固定**总 token 预算**（含所有 agent 的 prompt+completion + 通信），而不是固定“agent 数量”或“轮数”。
- 对照基线要给 single-agent **同等预算**（比如允许它做更长的 thinking / 更多次采样），否则比较不公平。2604.02460 正是用这个方法论得出“同等思考 token 下单 agent 反而更优”。
- 同时报告**延迟（wall-clock）**和**花费（$）**，区分“并行省了时间”和“整体花了更多钱”。

### 可观测：trace 是评估的前提

没有 trace 就无法归因，只能看最终对错：

- 记录每个 agent 的输入上下文、tool 调用、输出、token 数、耗时。
- 记录 agent 间的每一条消息（谁在什么时候对谁说了什么）。
- OpenAI Agents SDK、LangGraph 等都内置 tracing，研究自建 harness 时这应是第一优先级，而非事后补。

### 失败归因（failure attribution）

MAS 失败往往不是“模型不行”，而是协作机制坏掉。需要把失败归类，而不是只记一个准确率：

- 典型失败模式：任务跑偏、agent 间信息丢失、无限循环、过早终止、聚合阶段把对的答案合错。
- 已有专门的多 agent 失败分类工作（MAST，Multi-Agent System failure Taxonomy；以及 2605.14892 的 LIFE 框架把“失败归因”单列一环），可作为给失败打标签的现成体系。
- 做法：人工或用 LLM-judge 给每条失败 trace 打上“在哪个环节、哪个 agent、什么类型”的标签，再统计分布——这比单一准确率信息量大得多。

### 一个最小可复现评估清单

1. 选一个有明确对错的任务集（多跳问答、代码任务等），固定数据集与随机种子。
2. 对齐总 token 预算，跑：single-agent、parallel subagents、debate、manager-worker 四种配置。
3. 每种配置记录：准确率 / 通过率、总 token、$、wall-clock、完整 trace。
4. 对失败 trace 做归因打标，统计失败模式分布。
5. 结论只在“同预算、同数据、可复现”前提下成立——这正是第 10 节判断的落地方式。

## 9. 单 agent 基线：别忘了对照组

整份报告重心在 multi，但既然核心判断是“很多 MAS 收益其实是 token 假象”，那**一个强 single-agent + 好 harness 能走多远**就是不可省略的对照基线。

- 很多被称作“multi-agent”的系统，其实是**单 agent + 多技能 / 多工具**就能等价实现的（见 2601.04748“何时单 agent 配 skills 可替代 MAS”）。先问：这个任务真的需要多个独立 agent，还是一个会用工具、会管上下文的单 agent 就够？
- single-agent 的能力天花板主要由 **harness 质量**决定（见 2.5 节）：上下文管理、工具回注、停止条件做好了，单 agent 在很多任务上就是更省、更可控、更易 debug 的选择。
- 实务默认顺序：**先把 single-agent harness 做扎实，再在确有并行 / 隔离 / 多视角需求时引入 multi-agent**，并始终用单 agent 作为对照基线衡量增量是否真实。

## 10. 关键判断

Multi-agent 适合：

- 并行搜索
- 角色隔离
- 工具权限隔离
- 不同专业能力协作
- 长任务分治
- 多视角验证

Multi-agent 不应默认用于：

- 单纯提升推理准确率
- 用更多 token 包装成架构优势
- 没有清晰任务边界的“多角色聊天”

近期研究已经反复提醒：很多“多 agent 更强”的结果，本质可能只是更多 token、更多采样、更多工具调用。真正值得研究的是：**在相同预算、可复现流程、可观测 trace 下，multi-agent 是否带来结构性收益。**

## 11. 链接验证记录

验证时间：2026-06-18

- 已用 `curl -L -I` 检查文档中的 arXiv、OpenReview / ICLR blog、GitHub、LangChain、Microsoft Learn、LlamaIndex、CAMEL 等链接，核心论文与开源项目链接均返回 200。
- OpenAI Developers 文档对命令行请求返回 403，但浏览器页面可打开，按浏览器验证通过处理。
- Google Developers Blog 的 A2A 文章和 Hugging Face 的 GAIA dataset 对命令行检查未返回稳定状态码，但浏览器页面可打开，按浏览器验证通过处理。
- OpenCode 的历史入口会重定向，文档使用的是当前可打开的 `anomalyco/opencode` 地址。
