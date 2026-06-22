# ch09 · Protocols: MCP / A2A / ACP / ANP

本章目标：搞清楚 **四个协议各自解决哪一层问题**，不要把它们混为一谈。

前面几章都在“一个团队 / 一个系统内部”讨论协作。一旦 agent 要跨进程、跨厂商、跨平台连接工具和别的 agent，就需要**标准化的协议**。最常被混在一起的四个是 MCP、A2A、ACP、ANP，但它们解决的是**不同层次**的问题。

一句话先记住：

```text
MCP 接工具（纵向），A2A / ACP / ANP 接 agent（横向）。
```

## 本章要回答的问题

1. MCP 解决的是什么？为什么说它是“纵向”的？
2. A2A 解决的是什么？为什么说它是“横向”的？
3. ACP、ANP 和 A2A 有什么区别和重叠？
4. 为什么把这四个混为一谈是错的？
5. 一个真实系统里，这些协议怎么组合使用？
6. 这个领域标准未定，学习时该抓什么、放什么？

## 必读论文 / 资料

- A Survey of Agent Interoperability Protocols: MCP, ACP, A2A, and ANP  
  https://arxiv.org/abs/2505.02279

- The Orchestration of Multi-Agent Systems: Architectures, Protocols, and Enterprise Adoption  
  https://arxiv.org/abs/2601.13671

- Google A2A: A new era of agent interoperability  
  https://developers.googleblog.com/en/a2a-a-new-era-of-agent-interoperability/

## 1. MCP：agent ↔ 工具（纵向）

**MCP（Model Context Protocol）** 解决的是 **agent 连接工具 / 数据源** 的问题。

```text
一个 agent
  ├─ MCP -> 文件系统
  ├─ MCP -> 数据库
  ├─ MCP -> 某个 API
  └─ MCP -> 浏览器 / 沙箱
```

要点：

- 它是**纵向**的：让一个 agent 用统一方式接入外部能力。
- 解决的是“工具接入碎片化”——以前每个工具一套自定义集成，现在用统一协议。
- 它**不解决 agent 之间怎么通信**。这是最常见的误解。

类比：MCP 像是给 agent 配了一个标准化的“USB 接口”，各种工具/数据源都能插上来。

## 2. A2A：agent ↔ agent（横向）

**A2A（Agent-to-Agent，Google 提出）** 解决的是 **不同 agent 之间的横向通信**。

```text
agent A（厂商 X 做的）  <--A2A-->  agent B（厂商 Y 做的）
  互相发现能力、协商、委派任务
```

要点：

- 它是**横向**的：让不同厂商 / 框架做的 agent 能互相发现、协商、委派。
- 靠 **Agent Card** 描述每个 agent 的能力（“我能做什么、怎么调我”）。
- 解决的是“agent 各做各的、互不相通”——跨平台 agent 协作的标准。

类比：MCP 是 agent 连工具，A2A 是 agent 连 agent。一个向下，一个横向。

## 3. ACP 和 ANP：另外两条横向路线

A2A 不是唯一的 agent 间通信方案：

- **ACP（Agent Communication Protocol）**：同样面向 agent 间通信，更偏 REST / 消息式的标准化交互。定位与 A2A 有重叠，是另一条演进路线。
- **ANP（Agent Network Protocol）**：面向更开放的“agent 互联网”场景，强调**去中心化的身份与发现**。

把横向这三个放一起看：

| 协议 | 层次 | 侧重 |
|---|---|---|
| A2A | agent ↔ agent | 能力发现（Agent Card）、任务委派，Google 主推 |
| ACP | agent ↔ agent | REST / 消息式标准化交互 |
| ANP | agent ↔ agent | 去中心化身份与发现，开放网络 |

它们都在解决“agent 怎么互联”，但风格和侧重不同，且**标准还在洗牌**。

## 4. 为什么不能混为一谈

最常见的错误是把这四个当成“竞品里挑一个”。正确的心智模型是**分层**：

```text
纵向（接工具）：MCP
横向（接 agent）：A2A / ACP / ANP
```

- MCP 和 A2A **不是竞争关系**——一个解决工具接入，一个解决 agent 互通，可以同时用。
- A2A / ACP / ANP 之间才有重叠和竞争，但定位、生态、侧重各不同。
- 问“该用 MCP 还是 A2A”本身就是个错问题，等于问“该用 USB 还是用网线”。

## 5. 真实系统里怎么组合

一个跨平台的 agent 系统可能同时用到：

```text
agent A
  ├─ MCP 连本地工具（文件、DB、API）        <- 纵向
  └─ A2A 把子任务委派给 agent B             <- 横向
        agent B
          └─ MCP 连它自己的工具集            <- 纵向
```

也就是说：**每个 agent 用 MCP 向下接自己的工具，用 A2A（或 ACP/ANP）向外接别的 agent。** 纵横两层正交，各管一摊。

The Orchestration of Multi-Agent Systems（2601.13671）讨论的正是这种从单 agent 到松耦合多 agent、再到企业级编排的演进，协议层是其中关键一环。

## 6. 这个领域怎么学

现状：**标准未定，生态在快速洗牌。** 所以：

- **抓**：每个协议“解决哪一层”的心智模型（纵向 vs 横向）——这个稳定，不会过时。
- **放**：具体字段、消息格式、某个版本的实现细节——这些还在变，记了也会过期。
- 了解“MCP 接工具、A2A/ACP/ANP 接 agent”这个分层，比背任何一个协议的 schema 都重要。

## 完成标准

学完本章后，你应该能解释：

- MCP 解决 agent ↔ 工具（纵向），且不解决 agent 间通信
- A2A 解决 agent ↔ agent（横向），靠 Agent Card 描述能力
- ACP、ANP 是另外两条横向路线，与 A2A 有重叠但侧重不同
- 为什么 MCP 和 A2A 不是竞品，而是正交的两层
- 真实系统里纵向（MCP）和横向（A2A）如何组合
- 这个领域该记“分层心智模型”，而非易过时的协议细节

一句话总结：

```text
四个协议分两层：MCP 让 agent 用统一方式接工具（纵向），A2A / ACP / ANP 让 agent 之间互相发现和协作（横向）。它们大多正交而非竞争，记住「纵向接工具、横向接 agent」比背任何 schema 都管用。
```
