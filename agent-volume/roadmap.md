# Agent 卷学习路线

目标：从 single-agent harness 开始，逐步理解 sub-agent、agent team、multi-agent 协同、评估方法和协议层。

## Phase 01: Single-Agent Harness 基础

目标：理解 agent loop 的最小闭环。

需要掌握：

- model call
- tool schema
- tool execution
- observation 回注
- trace
- stop condition

必读论文：

- ReAct: Synergizing Reasoning and Acting in Language Models  
  https://arxiv.org/abs/2210.03629
- MRKL Systems: A modular, neuro-symbolic architecture that combines large language models, external knowledge sources and discrete reasoning  
  https://arxiv.org/abs/2205.00445
- Toolformer: Language Models Can Teach Themselves to Use Tools  
  https://arxiv.org/abs/2302.04761

阶段完成标准：

- 能解释 `Thought -> Action -> Observation` 的闭环。
- 能说明 agent 和 harness 的区别。
- 能实现或读懂一个最小 agent loop。
- 能说清楚 agent 什么时候应该继续，什么时候应该停止。

## Phase 02: Tool Use

目标：理解工具调用如何从模型 action 变成可靠、可校验、可恢复的外部执行。

需要掌握：

- tool schema
- tool selection
- argument validation
- structured observation
- error recovery
- output truncation

必读论文：

- MRKL Systems: A modular, neuro-symbolic architecture that combines large language models, external knowledge sources and discrete reasoning  
  https://arxiv.org/abs/2205.00445
- Toolformer: Language Models Can Teach Themselves to Use Tools  
  https://arxiv.org/abs/2302.04761

阶段完成标准：

- 能解释为什么工具要模块化。
- 能说明 LLM 在工具系统中更像决策器，而不是执行器。
- 能定义一个最小 tool schema。
- 能解释参数校验和结构化 observation 的必要性。
- 能在 minimal harness 中看懂 schema -> validation -> execution -> observation 的路径。

## Phase 03: Feedback-Driven Single Agent

必读论文：

- Reflexion: Language Agents with Verbal Reinforcement Learning  
  https://arxiv.org/abs/2303.11366
- Self-Refine: Iterative Refinement with Self-Feedback  
  https://arxiv.org/abs/2303.17651
- Language Agent Tree Search Unifies Reasoning Acting and Planning in Language Models  
  https://arxiv.org/abs/2310.04406

## Phase 04: Memory / Long-Term State / Environment

必读论文：

- Generative Agents: Interactive Simulacra of Human Behavior  
  https://arxiv.org/abs/2304.03442
- Voyager: An Open-Ended Embodied Agent with Large Language Models  
  https://arxiv.org/abs/2305.16291

## Phase 05: Sub-Agent / Manager-Worker

必读论文：

- AutoGen: Enabling Next-Gen LLM Applications via Multi-Agent Conversation  
  https://arxiv.org/abs/2308.08155
- MetaGPT: Meta Programming for A Multi-Agent Collaborative Framework  
  https://arxiv.org/abs/2308.00352
- ChatDev: Communicative Agents for Software Development  
  https://arxiv.org/abs/2307.07924
- CAMEL: Communicative Agents for "Mind" Exploration of Large Language Model Society  
  https://arxiv.org/abs/2303.17760

## Phase 06: Evaluator / Critic / Verifier

必读论文：

- Why Do Multi-Agent LLM Systems Fail?  
  https://arxiv.org/abs/2503.13657
- Credit Assignment for Cooperative LLM Agents  
  https://arxiv.org/abs/2603.06859
- Surveying Collaboration, Failure Attribution, and Self-Evolution in LLM-based Multi-Agent Systems  
  https://arxiv.org/abs/2605.14892

## Phase 07: Ablation / Baseline

必读论文：

- Single-Agent LLMs Outperform Multi-Agent Systems on Multi-Hop Reasoning Under Equal Thinking Token Budgets  
  https://arxiv.org/abs/2604.02460
- When Single-Agent with Skills Replace Multi-Agent Systems and When They Fail  
  https://arxiv.org/abs/2601.04748
- Cut the Crap: An Economical Communication Pipeline for LLM-based Multi-Agent Systems  
  https://arxiv.org/abs/2410.02506

## Phase 08: Benchmarks

必读论文：

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

## Phase 09: Framework Comparison

必读论文：

- Large Language Model based Multi-Agents: A Survey of Progress and Challenges  
  https://arxiv.org/abs/2402.01680
- Multi-Agent Collaboration Mechanisms: A Survey of LLMs  
  https://arxiv.org/abs/2501.06322
- A Communication-Centric Survey of LLM-Based Multi-Agent Systems  
  https://arxiv.org/abs/2502.14321

## Phase 10: Protocol Layer

必读论文：

- A Survey of Agent Interoperability Protocols: MCP, ACP, A2A, and ANP  
  https://arxiv.org/abs/2505.02279
- The Orchestration of Multi-Agent Systems: Architectures, Protocols, and Enterprise Adoption  
  https://arxiv.org/abs/2601.13671
