# ch02 · Tool Use

本章目标：理解 **Action 如何变成可靠的工具调用**，以及工具返回的 `Observation` 应该如何进入下一轮推理。

上一章我们只关心最小闭环：

```text
task -> model action -> harness executes tool -> observation -> next action -> final
```

这一章开始拆开中间最关键的部分：

```text
model action -> tool schema -> argument validation -> execution -> structured observation
```

## 本章要回答的问题

读 MRKL 和 Toolformer 时先抓 6 个问题（下文各节依次作答）：

1. 为什么工具要模块化？
2. LLM 在 agent 系统里更像“决策器”还是“执行器”？
3. 工具 schema 为什么比纯自然语言说明更可靠？
4. 工具调用失败时应该怎么办？
5. 工具调用结果应该如何进入下一轮上下文？
6. 工具越多是否一定越好？

## 必读论文

- MRKL Systems: A modular, neuro-symbolic architecture that combines large language models, external knowledge sources and discrete reasoning  
  https://arxiv.org/abs/2205.00445

- Toolformer: Language Models Can Teach Themselves to Use Tools  
  https://arxiv.org/abs/2302.04761

## 1. 工具为什么要模块化？

模型本身擅长语言、归纳和决策，但不擅长可靠执行外部操作。

比如：

- 读文件
- 查数据库
- 调 API
- 跑测试
- 计算精确数学结果
- 搜索文档
- 操作浏览器

这些事情应该交给工具，模型负责决定：

```text
现在缺什么信息？
该调用哪个工具？
参数应该是什么？
看到 observation 后下一步怎么做？
```

也就是说：

```text
LLM = 决策器 / 路由器 / 推理器
Tool = 可验证的外部能力
Harness = 翻译、执行、校验、回注的系统
```

## 2. LLM 更像决策器还是执行器？

在 agent harness 里，LLM 主要是**决策器**，不是执行器。它负责：

- 判断当前缺什么信息
- 在可用工具中选择一个
- 生成工具参数
- 解释返回的 observation
- 决定继续还是停止

真正的执行交给 harness 和 tools。这个分工很关键：模型不直接读文件、不直接跑命令，它只产出一个“我想调用某工具、参数是这些”的意图，由 harness 校验后执行。

```text
模型说：我要 read_file，path 是 roadmap.md
harness 做：校验 path -> 真实读取 -> 把结果包成 observation 回注
```

把模型当执行器（让它“假装”自己读到了内容）会直接导致幻觉；把它当决策器，配合可验证的工具，才能让每一步都落到真实证据上。

## 3. Tool Schema 是什么？

Tool schema 是工具的机器可读说明。它至少应该描述：

- 工具名
- 工具用途
- 参数名
- 参数类型
- 参数是否必填
- 默认值
- 取值范围
- 返回格式

例如：

```json
{
  "name": "read_file",
  "description": "Read a UTF-8 text file from the workspace.",
  "args": {
    "path": {
      "type": "string",
      "required": true,
      "description": "Workspace-relative file path."
    },
    "max_chars": {
      "type": "integer",
      "required": false,
      "default": 12000,
      "min": 1,
      "max": 30000
    }
  }
}
```

没有 schema 时，模型只能“猜”工具怎么用。有 schema 后，harness 可以做参数校验，把错误明确回注给模型。

## 4. 工具调用失败时应该怎么办？

不要让 harness 静默吞错，也不要让模型自己编一个结果。

正确做法是把失败包装成结构化 observation：

```json
{
  "ok": false,
  "error_type": "validation_error",
  "error": "missing required argument for read_file: path",
  "tool": "read_file",
  "args": {}
}
```

这样模型下一轮可以恢复：

```text
Observation 告诉我缺 path 参数。
下一步我应该重新调用 read_file，并给出 path。
```

## 5. Observation 应该如何返回？

Observation 不是越多越好。工具结果需要经过 harness 管理。

常见策略：

- **结构化返回**：用 JSON 包装 `ok`、`error_type`、`content`、`truncated` 等字段。
- **截断返回**：大文件、大搜索结果不能完整塞回上下文。
- **保留元信息**：返回路径、行号、字符数、是否截断。
- **错误可恢复**：失败时返回具体错误，而不是只说 failed。

一个好的 observation 应该满足：

```text
模型能据此判断下一步；
人能据此 debug；
harness 能据此做统计和归因。
```

## 6. 工具越多越好吗？

不一定。

工具越多，模型的选择空间越大，也越容易：

- 选错工具
- 参数写错
- 在相似工具之间摇摆
- 多轮无效调用
- 增加 prompt token 成本
- 增加权限和安全风险

实务原则：

```text
先给少量高质量工具；
工具职责要清晰；
工具返回要稳定；
再按任务需要扩展工具集。
```

## 配套实验

实验目录：

- `../experiments/minimal-harness/`

本章已把第一章的工具层升级为：

- `TOOL_SPECS`：集中定义工具 schema
- `format_tool_specs()`：自动把 schema 注入 system prompt
- `_validate_args()`：执行前做参数校验
- 结构化错误：`error_type` + `error` + `tool` + `args`

关键文件：

- `../experiments/minimal-harness/tools.py`
- `../experiments/minimal-harness/agent.py`

## 推荐实验

### 1. 正常工具调用

```bash
cd agent-volume/experiments/minimal-harness
python3 agent.py "演示工具 schema 和 observation 回注" --scripted-demo --reset-trace
```

看 `trace.jsonl`：

```bash
cat trace.jsonl
```

重点看：

- model 输出了哪个 action
- args 是否符合 schema
- observation 是否结构化
- final 是否在证据足够后出现

### 2. 参数校验失败

直接调用工具层：

```bash
cd agent-volume/experiments/minimal-harness
python3 - <<'PY'
from tools import run_tool
print(run_tool("read_file", {}))
print(run_tool("read_file", {"path": "README.md", "max_chars": 999999}))
print(run_tool("missing_tool", {}))
PY
```

你应该看到：

- `validation_error`
- `unknown_tool`
- 带有具体错误原因的 JSON observation

## 完成标准

学完本章后，你应该能解释：

- 为什么 agent 需要工具，而不是让模型直接回答
- tool schema 解决了什么问题
- harness 为什么必须校验参数
- observation 为什么要结构化和截断
- 工具失败时模型如何恢复
- 为什么工具越多不一定越好

一句话总结：

```text
工具调用不是“模型说要做什么就直接做什么”；
而是 harness 把模型的意图翻译成经过 schema 约束、参数校验、权限限制和可观测 trace 的外部执行。
```

