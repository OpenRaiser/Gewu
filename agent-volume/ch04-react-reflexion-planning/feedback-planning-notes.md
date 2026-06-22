# Reflexion / Self-Refine / LATS 阅读笔记

## 论文

- Reflexion: Language Agents with Verbal Reinforcement Learning  
  https://arxiv.org/abs/2303.11366

- Self-Refine: Iterative Refinement with Self-Feedback  
  https://arxiv.org/abs/2303.17651

- Language Agent Tree Search Unifies Reasoning Acting and Planning in Language Models  
  https://arxiv.org/abs/2310.04406

## 1. ReAct、Reflexion、Self-Refine、LATS 的关系

```text
ReAct       = 边想边行动，用 observation 更新下一步
Reflexion  = 失败后总结经验，下次尝试时使用
Self-Refine = 生成 -> 自评 -> 修改的迭代优化
LATS       = 把多条行动路径当成搜索树来探索和评分
```

它们不是互斥关系，而是可以叠加在 harness 里的不同机制。

## 2. 反馈不等于模型自言自语

反馈来源至少有三种：

- 环境反馈：工具结果、测试结果、文件系统错误、API 错误
- 自我反馈：模型自己评价自己的输出
- Verifier 反馈：规则、测试器、另一个模型或人工检查

可靠性一般是：

```text
环境反馈 / 测试反馈 > verifier 反馈 > 纯自我反馈
```

## 3. Reflexion 的关键

Reflexion 的价值在于把失败压缩成可复用语言经验：

```text
I failed because I searched the wrong file.
Next time, inspect the directory first and then read the exact file.
```

工程上对应：

- 失败 trace
- reflection summary
- memory store
- next attempt prompt

## 4. Self-Refine 的关键

Self-Refine 适合没有明确外部环境、但输出可以迭代改进的任务。

例如：

- 文案润色
- 结构化总结
- 草稿代码审查
- 答案组织优化

但它不应该用来替代事实验证。

## 5. LATS 的关键

LATS 把 “下一步做什么” 变成搜索问题：

```text
当前状态 -> 候选行动 -> observation -> 打分 -> 选择 / 回溯
```

它能降低单一路径错误的风险，但成本会显著上升。

工程上必须配：

- max branches
- max depth
- score function
- budget limit
- branch trace

## 本阶段理解修正版

```text
1. ReAct 让 agent 能用 observation 继续行动。
2. Reflexion 让失败经验跨尝试复用。
3. Self-Refine 让输出可以被自评和修改，但不能替代验证。
4. LATS 让 agent 探索多条行动路径，但成本更高。
5. 真正可靠的 feedback-driven agent，需要 harness 把错误、测试、验证和反思都变成可追踪的状态变化。
```

