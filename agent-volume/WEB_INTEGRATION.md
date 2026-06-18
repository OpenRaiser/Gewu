# Agent 卷 Web 接入计划

现有 `web/` 是大模型卷的可视化演武场，核心入口：

- `web/src/App.jsx`
- `web/src/components/Codex.jsx`
- `web/src/demos/*.jsx`

当前策略：Web 已经改成 `BOOKS -> volumes -> scrolls` 的分卷接口；Agent 卷先显示占位入口，等 ch01 有稳定 demo 后再接入真实演武场。

## 为什么暂不直接接入

现有 Web 结构是：

```text
App.jsx
  -> BOOKS: 大模型卷 / Agent 卷
  -> book.volumes: 每个分卷自己的卷目录
  -> 每卷 scrolls: 若干 demo
  -> Codex.jsx: 三栏演武场
```

Agent 卷需要展示的不是单纯数值推导，而是：

- tool call
- observation
- trace
- state
- stop condition
- 多 agent 并行时间线
- worker 汇报与主 agent 聚合

这需要在 `Codex.jsx` 之外设计新的展示组件，不能简单复用所有旧 demo 形态。

## 建议接入路径

### Step 1: 保持内容独立

先完成：

- `ch01-agent-harness/README.md`
- `experiments/minimal-harness/`
- 一个真实 trace 示例

### Step 2: 新增 Agent demo 组件

建议新增：

```text
web/src/components/AgentTrace.jsx
web/src/demos/agentHarness.jsx
```

`AgentTrace.jsx` 负责展示：

- 用户目标
- 每轮 action
- 工具参数
- observation 摘要
- final answer

### Step 3: 注册 Agent 卷目录

`web/src/App.jsx` 已经具备分卷接口。后续把 Agent 卷从占位状态改成真实目录即可：

```js
const BOOKS = [
  { id: "llm", title: "大模型卷", volumes: LLM_VOLUMES },
  { id: "agent", title: "Agent 卷", volumes: AGENT_VOLUMES },
];
```

### Step 4: 接入第一个 Agent 演武场

第一版只接：

```text
Agent 卷 · 卷一 · Harness 起手
第一式 · 想做相生
```

展示内容来自：

- `agent-volume/experiments/minimal-harness/trace.jsonl`

## 验收标准

- `npm run build` 通过
- 大模型卷原有 14 卷不受影响
- Agent 卷至少有一个真实 trace 驱动的 demo
- 页面能清楚展示 `Action -> Observation -> Next Action -> Final`
