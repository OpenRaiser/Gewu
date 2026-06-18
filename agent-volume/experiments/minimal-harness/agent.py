from __future__ import annotations

import argparse
import json
import os
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

from tools import format_tool_specs, run_tool


ROOT = Path(__file__).resolve().parents[3]
TRACE_PATH = Path(__file__).with_name("trace.jsonl")


SYSTEM_PROMPT_PREFIX = """You are a minimal ReAct-style file-research agent.

You can inspect only the local workspace through tools. Do not invent file contents.

Tool schemas:
"""

SYSTEM_PROMPT_SUFFIX = """
Action format:
- {"action":"list_files","args":{"path":"."},"reason":"short reason"}
- {"action":"read_file","args":{"path":"relative/path.md"},"reason":"short reason"}
- {"action":"search_text","args":{"pattern":"text","path":"."},"reason":"short reason"}
- {"action":"final","answer":"your final answer"}

Rules:
- Return exactly one JSON object and no markdown.
- Use relative paths only.
- Prefer search_text before reading very large files.
- Use final only when the task is answered with enough evidence.
- If a tool fails, use the observation to recover or explain the blocker.
"""


def build_system_prompt() -> str:
    return SYSTEM_PROMPT_PREFIX + format_tool_specs() + SYSTEM_PROMPT_SUFFIX


def _default_study_path() -> str:
    candidates = [
        "agent-volume/roadmap.md",
        "learning/roadmap.md",
        "roadmap.md",
        "README.md",
    ]
    for path in candidates:
        if (ROOT / path).exists():
            return path
    return "."


def scripted_model_response(step: int) -> str:
    study_path = _default_study_path()
    study_dir = str(Path(study_path).parent)
    if study_dir == ".":
        study_dir = "."
    actions = [
        {
            "action": "read_file",
            "args": {"path": study_path, "max_chars": 5000},
            "reason": "先读取学习路线，获取 Phase 01 的上下文",
        },
        {
            "action": "search_text",
            "args": {"pattern": "Phase 01", "path": study_dir},
            "reason": "再用搜索确认 Phase 01 在相关文档中的位置",
        },
        {
            "action": "final",
            "answer": (
                "脚本演示完成：harness 先读取路线文件，再搜索 Phase 01，"
                "最后在已有 observation 足够时输出 final。真实模型模式下，"
                "这些 action 会由模型根据上下文动态决定。"
            ),
        },
    ]
    if step <= len(actions):
        return json.dumps(actions[step - 1], ensure_ascii=False)
    return json.dumps(actions[-1], ensure_ascii=False)


def call_model(messages: list[dict[str, str]]) -> str:
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY is not set")

    base_url = os.environ.get("OPENAI_BASE_URL", "https://api.openai.com/v1").rstrip("/")
    model = os.environ.get("OPENAI_MODEL", "gpt-4.1-mini")
    url = f"{base_url}/chat/completions"

    body = {
        "model": model,
        "messages": messages,
        "temperature": 0,
    }
    data = json.dumps(body).encode("utf-8")
    request = urllib.request.Request(
        url,
        data=data,
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        method="POST",
    )

    try:
        with urllib.request.urlopen(request, timeout=120) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        details = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"model request failed: HTTP {exc.code}: {details}") from exc
    except urllib.error.URLError as exc:
        raise RuntimeError(f"model request failed: {exc}") from exc

    return payload["choices"][0]["message"]["content"]


def parse_action(text: str) -> dict[str, Any]:
    stripped = text.strip()
    if stripped.startswith("```"):
        lines = stripped.splitlines()
        stripped = "\n".join(lines[1:-1]).strip()
    try:
        action = json.loads(stripped)
    except json.JSONDecodeError as exc:
        raise ValueError(f"model did not return valid JSON: {text}") from exc
    if not isinstance(action, dict) or "action" not in action:
        raise ValueError(f"model response is not an action object: {text}")
    return action


def append_trace(event: dict[str, Any]) -> None:
    event = {"time": time.strftime("%Y-%m-%dT%H:%M:%S%z"), **event}
    with TRACE_PATH.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(event, ensure_ascii=False) + "\n")


def run(task: str, max_steps: int, *, scripted_demo: bool = False) -> str:
    messages = [
        {"role": "system", "content": build_system_prompt()},
        {"role": "user", "content": task},
    ]
    append_trace({"type": "task", "task": task, "workspace": str(ROOT)})

    seen_tool_calls: dict[str, int] = {}

    for step in range(1, max_steps + 1):
        raw = scripted_model_response(step) if scripted_demo else call_model(messages)
        append_trace({"type": "model", "step": step, "raw": raw})
        print(f"\n[step {step}] model: {raw}")

        try:
            action = parse_action(raw)
        except ValueError as exc:
            observation = json.dumps({"ok": False, "error": str(exc)}, ensure_ascii=False)
            messages.append({"role": "assistant", "content": raw})
            messages.append({"role": "user", "content": f"Observation: {observation}"})
            append_trace({"type": "parse_error", "step": step, "observation": observation})
            continue

        name = action["action"]
        if name == "final":
            answer = str(action.get("answer", ""))
            append_trace({"type": "final", "step": step, "answer": answer})
            return answer

        args = action.get("args", {})
        if not isinstance(args, dict):
            args = {}

        tool_key = json.dumps({"action": name, "args": args}, sort_keys=True, ensure_ascii=False)
        seen_tool_calls[tool_key] = seen_tool_calls.get(tool_key, 0) + 1
        if seen_tool_calls[tool_key] > 2:
            observation = json.dumps(
                {"ok": False, "error": "repeated identical tool call; choose a different action or final"},
                ensure_ascii=False,
            )
        else:
            observation = run_tool(str(name), args)

        append_trace({"type": "tool", "step": step, "action": name, "args": args, "observation": observation})
        print(f"[step {step}] observation: {observation[:1000]}")

        messages.append({"role": "assistant", "content": json.dumps(action, ensure_ascii=False)})
        messages.append({"role": "user", "content": f"Observation: {observation}"})

    append_trace({"type": "stopped", "reason": "max_steps", "max_steps": max_steps})
    return f"Stopped after {max_steps} steps without final answer."


def main() -> int:
    parser = argparse.ArgumentParser(description="Run a minimal ReAct-style harness.")
    parser.add_argument("task", help="Task for the agent")
    parser.add_argument("--max-steps", type=int, default=8)
    parser.add_argument(
        "--scripted-demo",
        action="store_true",
        help="Use a deterministic scripted model so the harness can run without an API key.",
    )
    parser.add_argument(
        "--reset-trace",
        action="store_true",
        help="Delete the previous trace.jsonl before running.",
    )
    args = parser.parse_args()

    try:
        if args.reset_trace and TRACE_PATH.exists():
            TRACE_PATH.unlink()
        answer = run(args.task, args.max_steps, scripted_demo=args.scripted_demo)
    except Exception as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    print("\nFinal answer:")
    print(answer)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
