# ch05 · Sub-Agent

本章目标：理解 **主 agent 如何把任务拆给多个隔离 worker，并把结果汇总回来**。

前四章我们一直在做 single-agent harness：

```text
one task -> one loop -> tools -> observation -> final
```

这一章开始进入 multi-agent 的第一步，但先不要上来就做复杂“团队”。先理解最基础的 manager-worker / sub-agent：

```text
manager
  -> spawn worker A with isolated context
  -> spawn worker B with isolated context
  -> collect reports
  -> aggregate / resolve conflicts
  -> final
```

## 本章要回答的问题

读 AutoGen、MetaGPT、ChatDev、CAMEL 时先抓 6 个问题：

1. sub-agent 和普通 tool call 有什么区别？
2. 为什么 worker 要有隔离上下文？
3. manager 应该把什么交给 worker，什么留给自己？
4. worker 的中间过程要不要全部回传给 manager？
5. 多个 worker 结果冲突时怎么裁决？
6. sub-agent 什么时候值得用，什么时候只是浪费 token？

## 必读论文

- AutoGen: Enabling Next-Gen LLM Applications via Multi-Agent Conversation  
  https://arxiv.org/abs/2308.08155

- MetaGPT: Meta Programming for A Multi-Agent Collaborative Framework  
  https://arxiv.org/abs/2308.00352

- ChatDev: Communicative Agents for Software Development  
  https://arxiv.org/abs/2307.07924

- CAMEL: Communicative Agents for "Mind" Exploration of Large Language Model Society  
  https://arxiv.org/abs/2303.17760

## 1. Sub-agent 和 Tool Call 的区别

Tool call 是一次外部能力调用：

```text
read_file(path) -> observation
search_text(pattern) -> observation
run_test() -> observation
```

Sub-agent 是一个独立的小 agent loop：

```text
worker task -> worker context -> worker tools / reasoning -> worker report
```

区别在于：

| 维度 | Tool Call | Sub-Agent |
|---|---|---|
| 执行单位 | 一个函数 / API | 一个小 agent |
| 上下文 | 主 agent 当前上下文 | 隔离 worker 上下文 |
| 输出 | 原始 observation | 汇总报告 / patch / 结论 |
| 成本 | 通常低 | 通常高 |
| 适合任务 | 明确、短、可函数化 | 需要探索、归纳、局部判断的子任务 |

## 2. 为什么要隔离上下文？

隔离上下文的好处：

- worker 只看和自己任务相关的信息
- 避免主上下文被大段中间过程污染
- worker 可以并行执行
- 不同 worker 可以承担不同角色
- 失败范围可控

代价：

- manager 只能看到 worker 报告，不一定看到全部细节
- worker 可能漏掉全局背景
- 需要额外的任务描述和结果聚合
- token 总成本会上升

一句话：

```text
隔离上下文换来并行和降噪，但带来信息损失和协调成本。
```

## 3. Manager 应该做什么？

Manager 的职责不是亲自完成所有事，而是：

- 分解任务
- 明确 worker 输入和输出格式
- 控制 worker 权限和范围
- 收集 worker 报告
- 判断报告是否冲突
- 汇总成最终结果

一个好的 worker 任务应该是：

```text
具体、边界清楚、能独立完成、输出格式明确。
```

坏任务：

```text
“你去看看这个项目怎么样”
```

好任务：

```text
“只阅读 agent-volume/roadmap.md，提取 Phase 05 的目标、必读论文和完成标准，输出 JSON。”
```

## 4. Worker 应该回传什么？

worker 不应该把全部中间上下文都回传给 manager。

更合理的是：

- conclusion：结论
- evidence：关键证据
- files_read：读过哪些文件
- uncertainty：不确定点
- errors：遇到的错误

这也是为什么 sub-agent 系统需要 worker trace：

```text
manager 看 report；
debug 时再看 worker trace。
```

## 5. 聚合和冲突裁决

多个 worker 报告可能：

- 互相补充
- 重复
- 矛盾
- 质量参差

manager 需要 reducer：

```text
reports -> normalize -> deduplicate -> compare evidence -> final
```

如果 worker A 和 B 冲突，不应该简单投票。更可靠的做法是看：

- 谁给出了可验证证据
- 谁的来源更新
- 谁的任务范围更匹配
- 是否需要再派一个 verifier worker

## 6. 什么时候值得用 Sub-agent？

适合：

- 子任务可以独立完成
- 需要并行探索多个方向
- 需要角色隔离
- worker 输出比完整过程更重要
- 主上下文已经很拥挤

不适合：

- 子任务很小，tool call 就够
- 子任务强依赖彼此中间过程
- 聚合成本超过并行收益
- 只是为了“看起来更智能”

## 配套实验

实验目录：

- `../experiments/sub-agent-runner/`

这个实验不用真实模型，先演示 sub-agent harness 的结构：

```text
manager.py
  -> worker-roadmap
  -> worker-ch05
  -> aggregate reports
  -> write run/result.json
```

推荐运行：

```bash
cd agent-volume/experiments/sub-agent-runner
python3 manager.py --reset
find run -maxdepth 2 -type f | sort
cat run/result.json
```

你应该看到：

- `run/manager.jsonl`：manager 的分派与聚合 trace
- `run/worker-roadmap.jsonl`：worker-roadmap 的隔离 trace
- `run/worker-ch05.jsonl`：worker-ch05 的隔离 trace
- `run/result.json`：聚合结果

## 完成标准

学完本章后，你应该能解释：

- sub-agent 和 tool call 的区别
- 隔离上下文的收益和代价
- manager / worker / reducer 各自的职责
- worker report 为什么不等于完整 trace
- 并行 sub-agent 为什么会增加总 token 成本
- 什么任务适合拆给 sub-agent，什么任务不适合

一句话总结：

```text
Sub-agent 的本质不是“多几个模型聊天”，而是 manager 用隔离上下文把可独立完成的子任务分派出去，再用 reducer 把报告合成可用结果。
```

