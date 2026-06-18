# MRKL / Toolformer 阅读笔记

## 论文

- MRKL Systems  
  https://arxiv.org/abs/2205.00445

- Toolformer  
  https://arxiv.org/abs/2302.04761

## 1. 为什么工具要模块化？

模块化的核心价值是把“语言推理”和“外部能力”拆开：

```text
模型负责理解问题、选择路径、组织答案；
工具负责检索、计算、执行和验证。
```

这能减少模型直接猜测的空间，也让系统更容易调试和扩展。

## 2. LLM 更像决策器还是执行器？

在 agent harness 里，LLM 更像决策器：

- 判断当前缺什么信息
- 选择哪个工具
- 生成工具参数
- 解释 observation
- 决定继续还是停止

真正的执行由 harness 和 tools 完成。

## 3. Tool Schema 为什么重要？

自然语言工具说明容易含糊，schema 能提供更硬的约束：

- 参数名固定
- 参数类型固定
- 必填项明确
- 默认值明确
- 范围可校验
- 错误可结构化

没有 schema，工具调用很容易退化成“模型猜 API 怎么用”。

## 4. Observation 如何进入下一轮上下文？

Observation 应该作为外部证据回注给模型，但不能无节制塞入上下文。

好的 observation 通常包括：

- `ok`
- `content` 或 `matches`
- `error_type`
- `error`
- `truncated`
- `path` / `line` / `chars` 等元信息

模型下一轮根据 observation 更新决策。

## 5. 工具越多越好吗？

不是。

工具越多，选择空间越大，prompt 成本越高，错误组合越多。

实务上应该优先保证：

- 工具少而清晰
- 每个工具职责单一
- 参数 schema 稳定
- observation 可恢复
- trace 可审计

## 本阶段理解修正版

```text
1. 工具是模型外部的可靠能力，不是 prompt 装饰。
2. LLM 在 harness 中主要是决策器，执行由工具完成。
3. Tool schema 是模型意图和真实执行之间的契约。
4. Observation 是结构化环境反馈，需要可截断、可恢复、可调试。
5. 工具数量要受控；工具质量、边界和返回格式比数量更重要。
```

