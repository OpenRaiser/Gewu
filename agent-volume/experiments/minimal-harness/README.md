# Minimal Harness 实验

这个目录是 Agent 卷第一章的配套代码：用最少的代码跑通一个 ReAct-style single-agent harness。

本实验故意只保留文件工具，不引入 sub-agent、browser、database、MCP 或长期记忆。目标是先看清楚最小闭环：

```text
task -> model action -> harness executes tool -> observation -> next action -> final
```

## 文件

```text
agent.py       # agent loop、模型调用、动作解析、trace、停止条件
tools.py       # 本地文件工具与 workspace 边界
trace.jsonl    # 运行后生成；每行一个事件
README.md
```

## 工具

第一版支持：

- `list_files(path)`
- `read_file(path, max_chars=12000)`
- `search_text(pattern, path, max_matches=50)`
- `final(answer)`

`final` 不是 Python 工具，而是模型输出的明确停止动作。

## 快速运行：无 API key 脚本演示

先用脚本模式理解 harness。这个模式不调用模型，但复用同一套 action 解析、工具执行、observation 回注和 trace 记录。

```bash
cd agent-volume/experiments/minimal-harness
python3 agent.py "演示 Agent 卷第一章的最小 harness" --scripted-demo --reset-trace
```

运行后查看：

```bash
cat trace.jsonl
```

你应该能看到：

1. `task`
2. `model` 输出 JSON action
3. `tool` 执行并返回 observation
4. `final` 停止

## 真实模型模式

这个实验使用 OpenAI-compatible Chat Completions 接口。

需要环境变量：

```bash
export OPENAI_API_KEY="..."
export OPENAI_BASE_URL="https://api.openai.com/v1"  # 第三方兼容网关可改这里
export OPENAI_MODEL="gpt-4.1-mini"                  # 按网关支持情况调整
```

示例：

```bash
cd agent-volume/experiments/minimal-harness
python3 agent.py "读取 agent-volume/roadmap.md，找出 Phase 01 的目标、必读论文和完成标准，并用三段话总结。" --reset-trace
```

如果在 `/Volumes/T7/multi-agent/learning` 的学习目录运行，对应任务可以写成：

```bash
python3 agent.py "读取 learning/roadmap.md，找出 Phase 01 的目标、必读论文和完成标准，并用三段话总结。" --reset-trace
```

## 实现要点

- `agent.py` 负责 agent loop、模型调用、动作解析、trace、停止条件。
- `tools.py` 负责本地工具实现、tool schema、参数校验，并限制工具只能访问当前 workspace。
- 模型每轮必须输出一个 JSON action。
- harness 执行工具后，把 observation 作为下一轮上下文回注给模型。
- `--max-steps` 是硬停止条件，防止循环失控。
- 重复相同 tool call 超过两次会被 harness 干预。
- tool 失败、JSON 解析失败都被包装成 observation，让模型有机会恢复。
- system prompt 中的工具说明由 `TOOL_SPECS` 自动生成，避免 prompt 和真实工具定义漂移。

## 第一章对应关系

| 章节概念 | 代码位置 |
|---|---|
| Model | `call_model()` 或 `scripted_model_response()` |
| Action | `parse_action()` 返回的 JSON 对象 |
| Tool | `tools.py` 中的 `TOOLS` |
| Observation | `run_tool()` 返回的 JSON 字符串 |
| Trace | `append_trace()` 写入 `trace.jsonl` |
| Stop condition | `final`、`--max-steps`、重复 tool call 检测 |

## 第二章对应关系

| 章节概念 | 代码位置 |
|---|---|
| Tool schema | `tools.py` 中的 `TOOL_SPECS` |
| Schema prompt injection | `format_tool_specs()` + `build_system_prompt()` |
| Argument validation | `tools.py` 中的 `_validate_args()` |
| Structured error | `tools.py` 中的 `_error()` |
| Output truncation | `read_file(max_chars)`、`search_text(max_matches)` |

## 第二章实验：参数校验失败

```bash
cd agent-volume/experiments/minimal-harness
python3 - <<'PY'
from tools import run_tool

print(run_tool("read_file", {}))
print(run_tool("read_file", {"path": "README.md", "max_chars": 999999}))
print(run_tool("missing_tool", {}))
PY
```

观察重点：

- 缺少必填参数会返回 `validation_error`
- 超出参数范围会返回 `validation_error`
- 未知工具会返回 `unknown_tool`
- 错误不是异常崩溃，而是可回注给模型的 observation

## 推荐复盘问题

跑完后不要只看最终答案，先读 `trace.jsonl`：

- 模型第一步为什么选择这个工具？
- observation 是否真的改变了下一步？
- 如果工具失败，错误有没有回注给模型？
- final 是因为证据足够，还是因为预算用尽？
- 有没有重复 tool call 或无进展迹象？
