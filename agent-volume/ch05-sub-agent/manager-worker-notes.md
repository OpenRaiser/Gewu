# AutoGen / MetaGPT / ChatDev / CAMEL 阅读笔记

## 论文

- AutoGen: Enabling Next-Gen LLM Applications via Multi-Agent Conversation  
  https://arxiv.org/abs/2308.08155

- MetaGPT: Meta Programming for A Multi-Agent Collaborative Framework  
  https://arxiv.org/abs/2308.00352

- ChatDev: Communicative Agents for Software Development  
  https://arxiv.org/abs/2307.07924

- CAMEL: Communicative Agents for "Mind" Exploration of Large Language Model Society  
  https://arxiv.org/abs/2303.17760

## 1. 四篇论文分别看什么？

```text
AutoGen = 多 agent 对话和可编程 conversation pattern
MetaGPT = 用 SOP / 角色分工组织软件工程流程
ChatDev = 软件公司式角色协作，展示 agent team 工作流
CAMEL   = role-playing agents，关注角色设定和协作对话
```

它们的共同点是：不再把 LLM 只当成一次性回答器，而是把多个 LLM 调用组织成可协作的流程。

## 2. Manager-worker 是最小可控形态

最容易落地的 sub-agent 结构不是自由聊天，而是：

```text
manager -> worker tasks -> worker reports -> reducer
```

优点：

- 任务边界清楚
- 权限容易控制
- trace 容易审计
- 汇总逻辑可控

自由对话式 multi-agent 更灵活，但也更容易失控。

## 3. SOP 和角色不是装饰

MetaGPT / ChatDev 里角色分工的价值不只是 prompt 里写“你是产品经理 / 工程师”。

真正有价值的是：

- 规定输入输出格式
- 规定流程顺序
- 规定交付物
- 规定谁审查谁
- 规定失败如何回退

也就是说，角色必须落实到 harness 和 workflow。

## 4. Sub-agent 的关键风险

- worker 误解任务
- worker 看不到全局约束
- manager 过度相信 worker 汇报
- 多 worker 输出冲突
- token 成本和延迟增加
- 中间过程不可见导致难 debug

所以必须保留：

- manager trace
- worker trace
- report schema
- reducer 逻辑

## 5. 本阶段理解修正版

```text
1. sub-agent 是隔离上下文中的小 agent，不是普通工具函数。
2. manager 负责分解、授权、汇总和裁决。
3. worker 负责独立完成窄任务，并输出结构化 report。
4. worker report 是给 manager 消化的摘要，worker trace 是给人 debug 的证据。
5. manager-worker 比自由 agent 聊天更适合作为工程起点。
```

