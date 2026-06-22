# ch03 · Memory and State

本章目标：理解 agent harness 中的 **context、state、memory、trace** 分别是什么，以及为什么长任务不能只靠把历史全部塞进 prompt。

上一章我们解决了：

```text
model action -> tool schema -> argument validation -> execution -> structured observation
```

这一章开始处理长任务的核心问题：

```text
history keeps growing -> context window is limited -> harness must persist, summarize, and recover state
```

## 本章要回答的问题

读 Generative Agents 和 Voyager 时先抓 5 个问题：

1. context、state、memory、trace 有什么区别？
2. 为什么不能把所有历史都塞进模型上下文？
3. 什么信息应该留在当前 context，什么信息应该落盘？
4. trace 和 state 为什么要分开？
5. 长任务中 agent 如何恢复进度？

## 必读论文

- Generative Agents: Interactive Simulacra of Human Behavior  
  https://arxiv.org/abs/2304.03442

- Voyager: An Open-Ended Embodied Agent with Large Language Models  
  https://arxiv.org/abs/2305.16291

## 1. 四个概念先分清

### Context

Context 是每一轮发给模型的输入。

它通常包括：

- system prompt
- 当前用户任务
- 工具 schema
- 最近几轮 action / observation
- 必要的状态摘要

Context 的问题是：它有窗口上限，不能无限增长。

### State

State 是当前任务的工作状态。

比如：

- 当前任务是什么
- 跑到第几步
- 最后调用了哪个工具
- 最后 observation 的摘要
- 当前是否完成
- final answer 是什么

State 通常应该落盘，比如 `state.json`。

### Memory

Memory 是跨任务、跨会话还能复用的信息。

比如：

- 用户偏好
- 已学过的结论
- 可复用 skill
- 项目长期背景
- 历史经验总结

Memory 不应该每轮全塞进 context，而应该按需检索和回灌。

### Trace

Trace 是完整执行流水账。

比如：

- 每一轮模型输出
- 每一次工具调用
- 每次 observation
- 每个错误
- 最终停止原因

Trace 用于 debug、审计、评估和失败归因。它通常比 state 更完整，也更大。

## 2. 为什么不能把所有历史都塞进 prompt？

因为长任务会不断产生：

- tool output
- search result
- 文件内容
- 错误信息
- 子任务报告
- 模型中间决策

如果全部追加进 prompt，会出现：

- 超出 context window
- token 成本持续升高
- 早期关键信息被淹没
- 模型被无关历史干扰
- 工具大输出污染后续推理

因此 harness 必须做：

```text
完整历史 -> trace.jsonl
当前状态 -> state.json
必要摘要 -> context
长期经验 -> memory
```

## 3. 什么应该进入 context？

进入 context 的应该是“当前决策所必需的信息”：

- 当前目标
- 可用工具
- 最近 observation
- 当前状态摘要
- 与下一步决策直接相关的检索结果

不应该每轮都塞：

- 全量 trace
- 大文件全文
- 旧的无关 observation
- 所有历史搜索结果
- 大量重复工具输出

一句话：

```text
context 是模型下一步决策的工作台，不是数据库。
```

## 4. State 和 Trace 为什么要分开？

`trace.jsonl` 是完整流水账：

```text
task event
model event
tool event
model event
tool event
final event
```

它适合：

- debug
- 审计
- 重放
- 失败归因
- 评估统计

`state.json` 是当前状态摘要（字段与实验代码一致）：

```json
{
  "updated_at": "2026-06-18T22:28:24+0800",
  "runs": 1,
  "current_task": "演示 state 和 trace 的区别",
  "steps": 3,
  "last_action": "final",
  "last_observation_summary": "{\"ok\": true, \"truncated\": false, \"matches\": [...], \"match_count_shown\": 3}",
  "final_answer": "...",
  "status": "done"
}
```

注意几点：

- `last_action` 是字符串（工具名或 `final`），不是完整 action 对象。
- `last_observation_summary` 是被 `summarize_observation()` 压缩过的摘要，不是完整大输出。
- `status` 取值为 `new` / `running` / `done` / `stopped`。
- `runs` 记录累计运行次数，`updated_at` 由 `save_state()` 自动写入。

它适合：

- 恢复进度
- UI 展示
- 快速读取
- 下一轮 prompt 摘要

这两个文件解决的问题不同，不能混用。

## 5. 长任务如何恢复？

最小恢复策略：

1. 读取 `state.json`
2. 判断上次是否 `done`、`running` 或 `stopped`
3. 如果未完成，读取必要的 `trace.jsonl` 尾部事件
4. 把 state 摘要和最近 observation 回注给模型
5. 继续执行

更复杂的系统会增加：

- checkpoint
- rollback
- memory retrieval
- summary compaction
- task graph / DAG
- worker state isolation

## 配套实验

实验目录：

- `../experiments/minimal-harness/`

本章已把实验升级为：

- `state.json`：当前状态摘要
- `trace.jsonl`：完整事件流水
- `load_state()` / `save_state()`：状态落盘
- `summarize_observation()`：把大 observation 压成摘要
- `--reset-state`：清空上次状态

关键文件：

- `../experiments/minimal-harness/agent.py`

## 推荐实验

```bash
cd agent-volume/experiments/minimal-harness
python3 agent.py "演示 state 和 trace 的区别" --scripted-demo --reset-trace --reset-state
cat state.json
cat trace.jsonl
```

观察重点：

- `trace.jsonl` 是否保留每一步事件
- `state.json` 是否只保留当前状态摘要
- `last_observation_summary` 是否避免保存完整大输出
- `status` 是否从 `running` 变成 `done`

## 完成标准

学完本章后，你应该能解释：

- context、state、memory、trace 的区别
- 为什么不能把完整历史都塞进 prompt
- 为什么 trace 和 state 要分离
- 什么信息应该落盘，什么信息应该回注给模型
- 长任务恢复最小需要哪些信息

一句话总结：

```text
Context 是模型下一步决策的工作台；
state 是当前任务进度；
memory 是跨任务经验；
trace 是完整可审计历史。
```

