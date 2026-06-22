from __future__ import annotations

import argparse
import json
import shutil
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any


WORKSPACE_ROOT = Path(__file__).resolve().parents[3]
RUN_DIR = Path(__file__).with_name("run")


@dataclass(frozen=True)
class WorkerTask:
    worker_id: str
    title: str
    file_path: str
    keywords: tuple[str, ...]


TASKS = [
    WorkerTask(
        worker_id="worker-roadmap",
        title="Extract Phase 05 roadmap facts",
        file_path="agent-volume/roadmap.md",
        keywords=("Phase 05", "Sub-Agent", "manager", "worker"),
    ),
    WorkerTask(
        worker_id="worker-ch05",
        title="Extract ch05 chapter claims",
        file_path="agent-volume/ch05-sub-agent/README.md",
        keywords=("Sub-agent", "Manager", "Worker", "隔离上下文", "聚合"),
    ),
]


def now() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%S%z")


def append_jsonl(path: Path, event: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps({"time": now(), **event}, ensure_ascii=False) + "\n")


def read_workspace_file(path: str) -> str:
    target = (WORKSPACE_ROOT / path).resolve()
    if target != WORKSPACE_ROOT and WORKSPACE_ROOT not in target.parents:
        raise ValueError(f"path escapes workspace: {path}")
    return target.read_text(encoding="utf-8", errors="replace")


def extract_evidence(text: str, keywords: tuple[str, ...], limit: int = 8) -> list[dict[str, Any]]:
    evidence = []
    lowered_keywords = tuple(keyword.lower() for keyword in keywords)
    for line_no, line in enumerate(text.splitlines(), start=1):
        lowered = line.lower()
        if any(keyword in lowered for keyword in lowered_keywords):
            evidence.append({"line": line_no, "text": line[:220]})
        if len(evidence) >= limit:
            break
    return evidence


def run_worker(task: WorkerTask) -> dict[str, Any]:
    trace_path = RUN_DIR / f"{task.worker_id}.jsonl"
    append_jsonl(
        trace_path,
        {
            "type": "worker_start",
            "worker_id": task.worker_id,
            "title": task.title,
            "allowed_file": task.file_path,
        },
    )
    text = read_workspace_file(task.file_path)
    append_jsonl(
        trace_path,
        {
            "type": "read_file",
            "path": task.file_path,
            "chars": len(text),
            "context_isolation": "worker only reads its assigned file",
        },
    )
    evidence = extract_evidence(text, task.keywords)
    append_jsonl(trace_path, {"type": "extract_evidence", "keywords": task.keywords, "evidence": evidence})

    report = {
        "worker_id": task.worker_id,
        "title": task.title,
        "files_read": [task.file_path],
        "evidence": evidence,
        "conclusion": summarize_conclusion(task, evidence),
        "uncertainty": [] if evidence else ["No matching evidence found for assigned keywords."],
    }
    append_jsonl(trace_path, {"type": "worker_report", "report": report})
    return report


def summarize_conclusion(task: WorkerTask, evidence: list[dict[str, Any]]) -> str:
    if task.worker_id == "worker-roadmap":
        return "Roadmap frames Phase 05 as Sub-Agent / Manager-Worker with decomposition, isolated context, traces, aggregation, and conflict handling."
    if task.worker_id == "worker-ch05":
        return "Chapter 05 explains sub-agent as manager-worker delegation with isolated worker context and reducer-based aggregation."
    return f"{task.title}: found {len(evidence)} evidence lines."


def aggregate_reports(reports: list[dict[str, Any]]) -> dict[str, Any]:
    files_read = sorted({path for report in reports for path in report["files_read"]})
    evidence_count = sum(len(report["evidence"]) for report in reports)
    return {
        "task": "Demonstrate manager-worker sub-agent orchestration",
        "worker_count": len(reports),
        "files_read": files_read,
        "evidence_count": evidence_count,
        "reports": reports,
        "manager_conclusion": (
            "Sub-agent orchestration is useful when the manager can assign narrow, independent tasks "
            "to isolated workers, then aggregate structured reports instead of ingesting every worker detail."
        ),
    }


def run(reset: bool) -> dict[str, Any]:
    if reset and RUN_DIR.exists():
        shutil.rmtree(RUN_DIR)
    RUN_DIR.mkdir(parents=True, exist_ok=True)

    manager_trace = RUN_DIR / "manager.jsonl"
    append_jsonl(manager_trace, {"type": "manager_start", "worker_count": len(TASKS)})

    reports = []
    for task in TASKS:
        append_jsonl(
            manager_trace,
            {
                "type": "dispatch",
                "worker_id": task.worker_id,
                "title": task.title,
                "file_path": task.file_path,
                "keywords": task.keywords,
            },
        )
        report = run_worker(task)
        reports.append(report)
        append_jsonl(manager_trace, {"type": "worker_completed", "worker_id": task.worker_id})

    result = aggregate_reports(reports)
    result_path = RUN_DIR / "result.json"
    result_path.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    append_jsonl(manager_trace, {"type": "aggregate", "result_path": str(result_path), "worker_count": len(reports)})
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description="Run a deterministic manager-worker sub-agent demo.")
    parser.add_argument("--reset", action="store_true", help="Remove the previous run/ directory before running.")
    args = parser.parse_args()

    result = run(reset=args.reset)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

