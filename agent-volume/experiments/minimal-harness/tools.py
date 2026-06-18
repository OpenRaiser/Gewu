from __future__ import annotations

import json
from pathlib import Path
from typing import Any


WORKSPACE_ROOT = Path(__file__).resolve().parents[3]
SKIP_DIRS = {".git", "node_modules", "dist", "__pycache__"}
SKIP_FILES = {"trace.jsonl"}


TOOL_SPECS: dict[str, dict[str, Any]] = {
    "list_files": {
        "description": "List files and directories under a workspace-relative directory.",
        "args": {
            "path": {
                "type": "string",
                "required": False,
                "default": ".",
                "description": "Workspace-relative directory path.",
            },
        },
    },
    "read_file": {
        "description": "Read a UTF-8 text file from the workspace, with bounded output.",
        "args": {
            "path": {
                "type": "string",
                "required": True,
                "description": "Workspace-relative file path.",
            },
            "max_chars": {
                "type": "integer",
                "required": False,
                "default": 12000,
                "min": 1,
                "max": 30000,
                "description": "Maximum number of characters to return.",
            },
        },
    },
    "search_text": {
        "description": "Search case-insensitively for text inside one file or directory.",
        "args": {
            "pattern": {
                "type": "string",
                "required": True,
                "description": "Text pattern to search for.",
            },
            "path": {
                "type": "string",
                "required": False,
                "default": ".",
                "description": "Workspace-relative file or directory path.",
            },
            "max_matches": {
                "type": "integer",
                "required": False,
                "default": 50,
                "min": 1,
                "max": 200,
                "description": "Maximum number of matches to return.",
            },
        },
    },
}


def _resolve_workspace_path(path: str) -> Path:
    candidate = (WORKSPACE_ROOT / path).resolve()
    if candidate != WORKSPACE_ROOT and WORKSPACE_ROOT not in candidate.parents:
        raise ValueError(f"path escapes workspace: {path}")
    return candidate


def _result(ok: bool, **payload: object) -> str:
    return json.dumps({"ok": ok, **payload}, ensure_ascii=False)


def _error(error_type: str, message: str, **payload: object) -> str:
    return _result(False, error_type=error_type, error=message, **payload)


def _validate_args(tool_name: str, args: dict[str, object]) -> tuple[bool, dict[str, object] | str]:
    spec = TOOL_SPECS.get(tool_name)
    if spec is None:
        return False, f"unknown tool: {tool_name}"

    fields = spec["args"]
    unknown = sorted(set(args) - set(fields))
    if unknown:
        return False, f"unknown arguments for {tool_name}: {', '.join(unknown)}"

    validated: dict[str, object] = {}
    for name, field in fields.items():
        if name not in args:
            if field.get("required"):
                return False, f"missing required argument for {tool_name}: {name}"
            if "default" in field:
                validated[name] = field["default"]
            continue

        value = args[name]
        expected = field["type"]
        if expected == "string":
            if not isinstance(value, str):
                return False, f"argument {name} must be a string"
            if value == "":
                return False, f"argument {name} must not be empty"
            validated[name] = value
        elif expected == "integer":
            if isinstance(value, bool):
                return False, f"argument {name} must be an integer"
            if isinstance(value, str) and value.isdigit():
                value = int(value)
            if not isinstance(value, int):
                return False, f"argument {name} must be an integer"
            if "min" in field and value < field["min"]:
                return False, f"argument {name} must be >= {field['min']}"
            if "max" in field and value > field["max"]:
                return False, f"argument {name} must be <= {field['max']}"
            validated[name] = value
        else:
            return False, f"unsupported schema type for {name}: {expected}"

    return True, validated


def format_tool_specs() -> str:
    lines = []
    for name, spec in TOOL_SPECS.items():
        lines.append(f"- {name}: {spec['description']}")
        for arg_name, arg_spec in spec["args"].items():
            required = "required" if arg_spec.get("required") else f"optional, default={arg_spec.get('default')!r}"
            lines.append(
                f"  - {arg_name} ({arg_spec['type']}, {required}): {arg_spec['description']}"
            )
    return "\n".join(lines)


def list_files(path: str = ".") -> str:
    try:
        target = _resolve_workspace_path(path)
        if not target.exists():
            return _result(False, error=f"path does not exist: {path}")
        if not target.is_dir():
            return _result(False, error=f"path is not a directory: {path}")

        entries = []
        for item in sorted(target.iterdir(), key=lambda p: (not p.is_dir(), p.name.lower())):
            if item.name.startswith("._"):
                continue
            rel = item.relative_to(WORKSPACE_ROOT).as_posix()
            entries.append({"path": rel, "type": "dir" if item.is_dir() else "file"})
        return _result(True, entries=entries)
    except Exception as exc:
        return _result(False, error=str(exc))


def read_file(path: str, max_chars: int = 12000) -> str:
    try:
        target = _resolve_workspace_path(path)
        if not target.exists():
            return _result(False, error=f"file does not exist: {path}")
        if not target.is_file():
            return _result(False, error=f"path is not a file: {path}")

        text = target.read_text(encoding="utf-8", errors="replace")
        truncated = len(text) > max_chars
        return _result(
            True,
            path=target.relative_to(WORKSPACE_ROOT).as_posix(),
            content=text[:max_chars],
            truncated=truncated,
            chars=len(text),
        )
    except Exception as exc:
        return _result(False, error=str(exc))


def search_text(pattern: str, path: str = ".", max_matches: int = 50) -> str:
    try:
        target = _resolve_workspace_path(path)
        if not target.exists():
            return _result(False, error=f"path does not exist: {path}")

        if target.is_file():
            files = [target]
        else:
            files = []
            for item in target.rglob("*"):
                if not item.is_file() or item.name.startswith("._") or item.name in SKIP_FILES:
                    continue
                if any(part in SKIP_DIRS for part in item.relative_to(WORKSPACE_ROOT).parts):
                    continue
                files.append(item)

        matches = []
        for file_path in files:
            try:
                lines = file_path.read_text(encoding="utf-8", errors="replace").splitlines()
            except OSError:
                continue
            for line_number, line in enumerate(lines, start=1):
                if pattern.lower() in line.lower():
                    matches.append(
                        {
                            "path": file_path.relative_to(WORKSPACE_ROOT).as_posix(),
                            "line": line_number,
                            "text": line[:300],
                        }
                    )
                    if len(matches) >= max_matches:
                        return _result(True, matches=matches, truncated=True)

        return _result(True, matches=matches, truncated=False)
    except Exception as exc:
        return _result(False, error=str(exc))


TOOLS = {
    "list_files": list_files,
    "read_file": read_file,
    "search_text": search_text,
}


def run_tool(name: str, args: dict[str, object]) -> str:
    if name not in TOOLS:
        return _error("unknown_tool", f"unknown tool: {name}")
    ok, validated_or_error = _validate_args(name, args)
    if not ok:
        return _error("validation_error", str(validated_or_error), tool=name, args=args)
    try:
        return TOOLS[name](**validated_or_error)
    except TypeError as exc:
        return _error("type_error", f"invalid arguments for {name}: {exc}", tool=name, args=args)
