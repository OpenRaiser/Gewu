# Agent 卷 Web 接入计划

现有 `web/` 是大模型卷的可视化演武场，核心入口：

- `web/src/App.jsx`
- `web/src/components/Codex.jsx`
- `web/src/demos/*.jsx`

当前策略：Web 已经改成 `BOOKS -> volumes -> scrolls` 的分卷接口；Agent 卷第一章已接入真实演武场。

## 当前已接入

已接入：

```text
Agent 卷
  -> 卷一 · Harness 起手
  -> 第一式 · 想做相生
  -> web/src/demos/agentHarness.jsx
```

第一章 demo 仍复用 `Codex.jsx` 的三栏结构，但内容已切换为 agent harness 语义：model action、tool observation、trace、stop condition。

## 建议接入路径

### Step 1: 保持内容独立

先完成：

- `ch01-agent-harness/README.md`
- `experiments/minimal-harness/`
- 一个真实 trace 示例

状态：已完成第一版，实验代码支持 `--scripted-demo` 无 key 演示。

### Step 2: 新增 Agent demo 组件

建议新增：

```text
web/src/demos/agentHarness.jsx
```

状态：已完成。第一版直接在 demo 的 SVG 中展示 trace 卡片。

### Step 3: 注册 Agent 卷目录

`web/src/App.jsx` 已经具备分卷接口。后续把 Agent 卷从占位状态改成真实目录即可：

```js
const BOOKS = [
  { id: "llm", title: "大模型卷", volumes: LLM_VOLUMES },
  { id: "agent", title: "Agent 卷", volumes: AGENT_VOLUMES },
];
```

状态：已完成。

### Step 4: 接入第一个 Agent 演武场

第一版只接：

```text
Agent 卷 · 卷一 · Harness 起手
第一式 · 想做相生
```

展示内容来自：

- `agent-volume/experiments/minimal-harness/agent.py`
- `agent-volume/experiments/minimal-harness/trace.jsonl` 的结构

状态：已完成静态可交互版。后续可以把真实 `trace.jsonl` 转成前端数据。

## 验收标准

- `npm run build` 通过
- 大模型卷原有 14 卷不受影响
- Agent 卷至少有一个 harness demo
- 页面能清楚展示 `Action -> Observation -> Next Action -> Final`
