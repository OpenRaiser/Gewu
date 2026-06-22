# ch04 · ReAct / Reflexion / Planning

本章目标：理解 agent 如何利用反馈改进下一步行动。到这一章为止，我们已经有了：

```text
ReAct loop -> tool schema -> state / trace
```

现在要补上 agent 真正变得“能修正”的机制：

```text
action -> observation / error / critique -> revise plan -> next action
```

## 本章要回答的问题

读 Reflexion、Self-Refine 和 LATS 时先抓 6 个问题：

1. ReAct、Reflexion、Self-Refine、LATS 分别解决什么问题？
2. 什么叫反馈？反馈一定来自外部环境吗？
3. 工具错误如何变成下一步修正，而不是直接失败？
4. 自我反思和真正验证有什么区别？
5. planning 和一步一步 ReAct 有什么区别？
6. 树搜索为什么可能提升效果，也为什么会更贵？

## 必读论文

- Reflexion: Language Agents with Verbal Reinforcement Learning  
  https://arxiv.org/abs/2303.11366

- Self-Refine: Iterative Refinement with Self-Feedback  
  https://arxiv.org/abs/2303.17651

- Language Agent Tree Search Unifies Reasoning Acting and Planning in Language Models  
  https://arxiv.org/abs/2310.04406

## 1. ReAct 到底解决了什么？

ReAct 的核心是把推理和行动交替起来：

```text
Thought -> Action -> Observation -> Thought -> ...
```

它让模型不必一次性猜答案，而是能通过工具获取证据。

但 ReAct 本身不保证：

- 每次 action 都对
- 错误后能总结教训
- 多条可能路径里能选最优
- 会保留跨任务经验

所以后续方法围绕“反馈”和“规划”继续增强。

## 2. Reflexion：把失败变成经验

Reflexion 的关键思想是：失败后不一定立刻改模型参数，而是把失败原因用语言总结成 memory，下一次尝试时回灌。

可以理解成：

```text
attempt -> feedback -> reflection -> memory -> next attempt
```

它适合：

- 任务可以多次尝试
- 有明确 success / failure 信号
- 失败经验能用自然语言总结

注意：reflection 不是魔法。它需要真实反馈支撑，否则只是模型自言自语。

## 3. Self-Refine：生成、批评、修改

Self-Refine 更像一个自我编辑循环：

```text
draft -> feedback -> revise -> feedback -> revise
```

它不一定依赖外部工具，反馈可以由模型自己给出。

适合：

- 写作
- 总结
- 代码草稿
- 结构化答案优化

风险：

- 自评不等于正确
- 可能越改越偏
- 没有外部验证时容易形成自洽幻觉

## 4. LATS：把行动空间当成搜索树

LATS 把 reasoning、acting、planning 统一成树搜索：

```text
state
  -> possible action A -> observation -> score
  -> possible action B -> observation -> score
  -> choose better branch
```

它比线性 ReAct 更强的地方是：可以探索多条路径，而不是一步错就一路错下去。

代价也很明显：

- 更多模型调用
- 更多工具调用
- 更复杂的状态管理
- 更高 token 和时间成本

因此 LATS 这类方法必须和预算控制一起看。

## 5. 三类反馈

### 环境反馈

来自工具、测试、数据库、浏览器、文件系统等外部环境。

例子：

```json
{"ok": false, "error_type": "validation_error", "error": "missing required argument: path"}
```

这是最可靠的一类反馈。

### 自我反馈

模型自己批评自己的输出。

适合改进表达和结构，但不能替代外部事实验证。

### Verifier / Critic 反馈

由另一个模型、规则系统、测试器或评估器给出。

比纯自评更可靠，但也有成本和偏差。

## 6. 工程上的恢复策略

一个 harness 不能只把错误打印出来，它要让模型能恢复：

```text
tool error -> structured observation -> model sees error -> corrected action
```

最小恢复机制：

- 错误必须结构化
- 错误必须进入下一轮 context
- trace 记录失败和修正
- state 记录错误次数
- 超过重复失败阈值后停止或请求用户帮助

## 配套实验

实验目录：

- `../experiments/minimal-harness/`

本章新增：

- `--scripted-scenario recover`
- `observation_has_error()`
- `state.json` 中的 `error_count`

推荐运行：

```bash
cd agent-volume/experiments/minimal-harness
python3 agent.py "演示失败后恢复" --scripted-demo --scripted-scenario recover --reset-trace --reset-state
cat trace.jsonl
cat state.json
```

你应该看到：

1. 第一步故意调用 `read_file` 但不给 `path`
2. harness 返回 `validation_error`
3. 第二步改用带完整参数的 `search_text`
4. 第三步输出 `final`
5. `state.json` 中 `error_count` 为 1

## 完成标准

学完本章后，你应该能解释：

- ReAct、Reflexion、Self-Refine、LATS 的区别
- 为什么“反馈”比“多想一会儿”更关键
- 为什么工具错误要结构化回注
- 自我反馈为什么不能替代外部验证
- 树搜索为什么更强也更贵
- harness 如何记录失败次数并防止无限重试

一句话总结：

```text
Feedback-driven agent 的关键不是“模型会反思”，而是 harness 能把环境反馈、错误、验证结果变成下一步可用的决策信号。
```

