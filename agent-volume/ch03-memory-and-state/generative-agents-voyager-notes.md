# Generative Agents / Voyager 阅读笔记

## 论文

- Generative Agents: Interactive Simulacra of Human Behavior  
  https://arxiv.org/abs/2304.03442

- Voyager: An Open-Ended Embodied Agent with Large Language Models  
  https://arxiv.org/abs/2305.16291

## 1. context、state、memory、trace 有什么区别？

```text
context = 当前轮发给模型的输入
state   = 当前任务进度摘要
memory  = 跨任务可复用经验
trace   = 完整执行流水账
```

最容易混淆的是 memory 和 trace：

- trace 是“发生过什么”
- memory 是“哪些经验值得以后复用”

不是所有 trace 都应该变成 memory。

## 2. 为什么不能把所有历史都塞进 context？

因为 context window 有上限，而且模型注意力不是无限可靠。

全部塞入会带来：

- token 成本过高
- 无关历史干扰当前决策
- 大工具输出污染上下文
- 早期关键目标被稀释

所以 harness 必须主动做筛选、摘要、检索和落盘。

## 3. 什么信息应该落盘？

应该落盘的信息：

- 当前任务状态
- 关键决策
- 工具调用结果
- 错误和恢复过程
- 可复用经验
- final answer

但落盘也要分层：

- `trace.jsonl` 保存完整历史
- `state.json` 保存当前摘要
- memory store 保存跨任务经验

## 4. Generative Agents 给我们的启发

Generative Agents 的重点不是“角色扮演”，而是 memory pipeline：

```text
observation -> memory stream -> retrieval -> reflection -> planning
```

关键启发：

- agent 需要把经历存下来
- 不是所有经历都等权重要
- 需要检索相关记忆，而不是全量回放
- reflection 可以把零散经历压缩成高层结论

## 5. Voyager 给我们的启发

Voyager 的重点是长期开放式学习：

```text
exploration -> skill acquisition -> skill library -> reuse
```

关键启发：

- 长任务 agent 需要积累可复用技能
- 成功经验要从一次性 trace 中抽象出来
- skill library 是一种长期 memory
- 环境反馈决定下一步学习方向

## 本阶段理解修正版

```text
1. context 不是 memory；context 是当前 prompt 的工作空间。
2. state 不是 trace；state 是当前进度摘要，trace 是完整历史。
3. memory 不是所有历史；memory 是经过筛选和抽象的可复用经验。
4. 长任务 agent 必须落盘，否则无法可靠恢复和复盘。
5. 好 harness 的关键能力之一，就是决定“什么进 prompt，什么进 state，什么进 memory，什么只留 trace”。
```

