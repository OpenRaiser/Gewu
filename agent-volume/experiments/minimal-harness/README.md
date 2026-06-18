# Minimal Harness 实验

这个目录用于实现 Phase 01 的最小 single-agent harness。

文件：

```text
agent.py
tools.py
trace.jsonl
README.md
```

第一版支持：

- `read_file(path)`
- `list_files(path)`
- `search_text(pattern, path)`
- `final(answer)`

第一版暂不引入：

- sub-agent
- browser
- database
- MCP
- long-term memory

目标是先跑通最小 ReAct loop。

## 运行方式

这个实验使用 OpenAI-compatible Chat Completions 接口。

需要环境变量：

```bash
export OPENAI_API_KEY="..."
export OPENAI_BASE_URL="https://api.openai.com/v1"  # 可选，兼容网关可改这里
export OPENAI_MODEL="gpt-4.1-mini"                  # 可选
```

示例：

```bash
python3 agent.py "读取 multi-agent-research.md，找出第 7 节中第一步推荐的论文，并总结每篇为什么属于 single-agent harness 基础。"
```

运行后会生成或追加：

```text
trace.jsonl
```

## 实现要点

- `agent.py` 负责 agent loop、模型调用、动作解析、trace、停止条件。
- `tools.py` 负责本地工具实现，并限制工具只能访问当前 workspace。
- 模型每轮必须输出一个 JSON action。
- harness 执行工具后，把 observation 作为下一轮上下文回注给模型。
- `--max-steps` 是硬停止条件，防止循环失控。
