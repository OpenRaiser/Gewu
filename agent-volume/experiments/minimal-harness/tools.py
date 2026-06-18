from __future__ import annotations

import json
from pathlib import Path


WORKSPACE_ROOT = Path(__file__).resolve().parents[3]


def _resolve_workspace_path(path: str) -> Path:
    candidate = (WORKSPACE_ROOT / path).resolve()
    if candidate != WORKSPACE_ROOT and WORKSPACE_ROOT not in candidate.parents:
        raise ValueError(f"path escapes workspace: {path}")
    return candidate


def _result(ok: bool, **payload: object) -> str:
    return json.dumps({"ok": ok, **payload}, ensure_ascii=False)


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

        files = [target] if target.is_file() else [
            item for item in target.rglob("*")
            if item.is_file() and not item.name.startswith("._")
        ]

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
        return _result(False, error=f"unknown tool: {name}")
    try:
        return TOOLS[name](**args)
    except TypeError as exc:
        return _result(False, error=f"invalid arguments for {name}: {exc}")

