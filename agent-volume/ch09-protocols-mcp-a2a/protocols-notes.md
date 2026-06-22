# Protocols 阅读笔记（MCP / A2A / ACP / ANP）

## 资料

- A Survey of Agent Interoperability Protocols: MCP, ACP, A2A, and ANP  
  https://arxiv.org/abs/2505.02279
- The Orchestration of Multi-Agent Systems: Architectures, Protocols, and Enterprise Adoption  
  https://arxiv.org/abs/2601.13671
- Google A2A: A new era of agent interoperability  
  https://developers.googleblog.com/en/a2a-a-new-era-of-agent-interoperability/

## 1. 唯一必须记牢的一句

```text
MCP 接工具（纵向），A2A / ACP / ANP 接 agent（横向）。
```

其余细节都会过时，这个分层不会。

## 2. 四个协议速记

```text
MCP  纵向  agent -> 工具/数据源，统一接入，不管 agent 间通信
A2A  横向  agent <-> agent，Agent Card 描述能力，Google 主推
ACP  横向  agent <-> agent，REST/消息式，定位与 A2A 重叠
ANP  横向  agent <-> agent，去中心化身份与发现，开放网络
```

## 3. 最该避免的误解

- “该用 MCP 还是 A2A？” —— 错问题。一个接工具一个接 agent，正交，可同时用。
- 把四个当成“选一个”的竞品 —— 只有 A2A/ACP/ANP 之间才有竞争。
- 花时间背某版本的消息 schema —— 标准还在洗牌，会过期。

## 4. 组合范式

```text
每个 agent：
  向下用 MCP 接自己的工具
  向外用 A2A/ACP/ANP 接别的 agent
纵横两层正交。
```

## 5. 学习取舍

```text
抓：每个协议解决哪一层（纵向 vs 横向）—— 稳定
放：字段、格式、版本实现细节 —— 易过时
```

## 6. 本阶段理解小结

```text
1. 协议分两层：纵向接工具（MCP）、横向接 agent（A2A/ACP/ANP）。
2. MCP 与 A2A 正交，不是竞品。
3. A2A 靠 Agent Card 做能力发现与委派。
4. ACP 偏 REST/消息，ANP 偏去中心化身份。
5. 领域标准未定，记分层心智模型胜过记 schema。
```
