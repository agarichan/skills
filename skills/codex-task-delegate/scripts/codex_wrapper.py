#!/usr/bin/env python3
"""Thin wrapper around `codex exec` with local status tracking and fixed JSON output.

This wrapper intentionally stays small:
- delegate: fresh `codex exec`
- feedback: `codex exec resume <thread_id>`
- status/result: read persisted local state

State files are written under .codex-wrapper in the target workspace.
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import shlex
import shutil
import signal
import subprocess
import sys
import tempfile
import textwrap
import time
import uuid
from pathlib import Path
from typing import Any

STATE_DIR_NAME = ".codex-wrapper"
STATE_FILE_NAME = "state.json"
JOBS_DIR_NAME = "jobs"
GLOBAL_INDEX_DIR = Path.home() / ".codex" / "memories" / "codex-wrapper"
GLOBAL_INDEX_FILE_NAME = "thread-index.json"
MAX_THREADS = 100
MAX_INDEX_THREADS = 2000
DEFAULT_CHECK_IN_SECONDS = 180


class WrapperError(Exception):
    pass


def now_iso() -> str:
    return dt.datetime.now(dt.timezone.utc).isoformat()


def ensure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def atomic_write(path: Path, data: str) -> None:
    ensure_dir(path.parent)
    fd, tmp = tempfile.mkstemp(dir=str(path.parent), suffix=".tmp")
    closed = False
    try:
        os.write(fd, data.encode("utf-8"))
        os.close(fd)
        closed = True
        os.replace(tmp, str(path))
    except BaseException:
        if not closed:
            os.close(fd)
        try:
            os.unlink(tmp)
        except OSError:
            pass
        raise


def state_dir(workspace: Path) -> Path:
    return workspace / STATE_DIR_NAME


def jobs_dir(workspace: Path) -> Path:
    return state_dir(workspace) / JOBS_DIR_NAME


def state_file(workspace: Path) -> Path:
    return state_dir(workspace) / STATE_FILE_NAME


def global_index_file() -> Path:
    return GLOBAL_INDEX_DIR / GLOBAL_INDEX_FILE_NAME


def default_state() -> dict[str, Any]:
    return {
        "version": 2,
        "updated_at": now_iso(),
        "latest_thread_id": None,
        "threads": [],
    }


def default_global_index() -> dict[str, Any]:
    return {
        "version": 1,
        "updated_at": now_iso(),
        "threads": {},
    }


def load_global_index() -> dict[str, Any]:
    file_path = global_index_file()
    if not file_path.exists():
        return default_global_index()

    try:
        data = json.loads(file_path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return default_global_index()

    if not isinstance(data, dict):
        return default_global_index()

    raw_threads = data.get("threads")
    normalized_threads: dict[str, dict[str, str]] = {}
    if isinstance(raw_threads, dict):
        for thread_id, info in raw_threads.items():
            if not isinstance(thread_id, str) or not thread_id.strip():
                continue
            if not isinstance(info, dict):
                continue
            workspace = info.get("workspace")
            if not isinstance(workspace, str) or not workspace.strip():
                continue
            normalized_threads[thread_id.strip()] = {
                "workspace": workspace.strip(),
                "updated_at": str(info.get("updated_at") or now_iso()),
            }

    return {
        "version": 1,
        "updated_at": data.get("updated_at") or now_iso(),
        "threads": normalized_threads,
    }


def save_global_index(index: dict[str, Any]) -> None:
    try:
        ensure_dir(GLOBAL_INDEX_DIR)
    except OSError as exc:
        raise WrapperError(f"Failed to create global index directory: {exc}") from exc

    index["updated_at"] = now_iso()

    threads = index.get("threads")
    if isinstance(threads, dict) and len(threads) > MAX_INDEX_THREADS:
        items = sorted(
            threads.items(),
            key=lambda x: str(x[1].get("updated_at") if isinstance(x[1], dict) else ""),
            reverse=True,
        )
        index["threads"] = dict(items[:MAX_INDEX_THREADS])

    try:
        atomic_write(
            global_index_file(),
            json.dumps(index, ensure_ascii=False, indent=2) + "\n",
        )
    except OSError as exc:
        raise WrapperError(f"Failed to write global thread index: {exc}") from exc


def remember_thread_workspace(thread_id: str, workspace: Path) -> None:
    tid = thread_id.strip()
    if not tid:
        return
    index = load_global_index()
    threads = index.get("threads")
    if not isinstance(threads, dict):
        threads = {}
    threads[tid] = {"workspace": str(workspace.resolve()), "updated_at": now_iso()}
    index["threads"] = threads
    save_global_index(index)


def find_workspace_for_thread(thread_id: str) -> Path | None:
    tid = thread_id.strip()
    if not tid:
        return None
    index = load_global_index()
    threads = index.get("threads")
    if not isinstance(threads, dict):
        return None
    info = threads.get(tid)
    if not isinstance(info, dict):
        return None
    workspace = info.get("workspace")
    if not isinstance(workspace, str) or not workspace.strip():
        return None
    return Path(workspace).resolve()


def resolve_workspace(
    *,
    cwd: str | None,
    thread_id: str | None,
    fallback_current: bool,
) -> Path:
    if isinstance(cwd, str) and cwd.strip():
        return Path(cwd).resolve()

    if isinstance(thread_id, str) and thread_id.strip():
        by_thread = find_workspace_for_thread(thread_id)
        if by_thread:
            return by_thread
        raise WrapperError(
            f"Workspace for thread_id '{thread_id}' was not found. "
            "Pass --cwd once to register it."
        )

    if fallback_current:
        return Path(".").resolve()

    raise WrapperError("Workspace could not be resolved. Pass --cwd.")


def _normalize_thread_entry(entry: Any) -> dict[str, Any] | None:
    if not isinstance(entry, dict):
        return None
    thread_id = entry.get("thread_id")
    if not isinstance(thread_id, str) or not thread_id.strip():
        return None
    thread_id = thread_id.strip()

    run_pid = entry.get("run_pid")
    if not isinstance(run_pid, int) or run_pid <= 0:
        run_pid = None

    run_token = entry.get("run_token")
    if not isinstance(run_token, str) or not run_token.strip():
        run_token = None
    else:
        run_token = run_token.strip()

    exit_code_file = entry.get("exit_code_file")
    if not isinstance(exit_code_file, str) or not exit_code_file.strip():
        exit_code_file = None
    else:
        exit_code_file = exit_code_file.strip()

    check_in_seconds = entry.get("check_in_seconds")
    if isinstance(check_in_seconds, int) and check_in_seconds >= 0:
        normalized_check_in = check_in_seconds
    else:
        normalized_check_in = None

    return {
        "thread_id": thread_id,
        "created_at": entry.get("created_at") or entry.get("started_at") or now_iso(),
        "updated_at": entry.get("updated_at") or entry.get("ended_at") or now_iso(),
        "kind": entry.get("kind"),
        "phase": entry.get("phase"),
        "exit_code": entry.get("exit_code"),
        "workspace": entry.get("workspace"),
        "last_prompt": entry.get("last_prompt") or entry.get("prompt") or "",
        "last_command": entry.get("last_command") or entry.get("command") or [],
        "summary": entry.get("summary") or "",
        "agent_message": entry.get("agent_message") or "",
        "touched_files": entry.get("touched_files") or [],
        "usage": entry.get("usage"),
        "stdout_log": entry.get("stdout_log"),
        "stderr_log": entry.get("stderr_log"),
        "events_count": entry.get("events_count"),
        "turn_completed": bool(entry.get("turn_completed")),
        "run_pid": run_pid,
        "run_token": run_token,
        "exit_code_file": exit_code_file,
        "check_in_seconds": normalized_check_in,
    }


def load_state(workspace: Path) -> dict[str, Any]:
    file_path = state_file(workspace)
    if not file_path.exists():
        return default_state()

    try:
        data = json.loads(file_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return default_state()

    if not isinstance(data, dict):
        return default_state()

    threads_source = data.get("threads")
    threads: list[dict[str, Any]] = []
    if isinstance(threads_source, list):
        seen: set[str] = set()
        for item in threads_source:
            normalized = _normalize_thread_entry(item)
            if not normalized:
                continue
            thread_id = normalized["thread_id"]
            if thread_id in seen:
                continue
            seen.add(thread_id)
            threads.append(normalized)

    latest_thread_id = data.get("latest_thread_id")
    if not isinstance(latest_thread_id, str) or not latest_thread_id.strip():
        latest_thread_id = None
    else:
        latest_thread_id = latest_thread_id.strip()

    if latest_thread_id and latest_thread_id not in {t["thread_id"] for t in threads}:
        latest_thread_id = None
    if latest_thread_id is None and threads:
        latest_thread_id = threads[0]["thread_id"]

    return {
        "version": 2,
        "updated_at": data.get("updated_at") or now_iso(),
        "latest_thread_id": latest_thread_id,
        "threads": threads,
    }


def _remove_log_files(thread: dict[str, Any]) -> None:
    for key in ("stdout_log", "stderr_log", "exit_code_file"):
        value = thread.get(key)
        if isinstance(value, str) and value.strip():
            try:
                Path(value).unlink(missing_ok=True)
            except OSError:
                pass


def save_state(workspace: Path, state: dict[str, Any]) -> None:
    state["updated_at"] = now_iso()

    threads = state.get("threads", [])
    if isinstance(threads, list) and len(threads) > MAX_THREADS:
        for evicted in threads[MAX_THREADS:]:
            if isinstance(evicted, dict):
                _remove_log_files(evicted)
        state["threads"] = threads[:MAX_THREADS]

    atomic_write(
        state_file(workspace),
        json.dumps(state, ensure_ascii=False, indent=2) + "\n",
    )


def upsert_thread(workspace: Path, record: dict[str, Any]) -> None:
    thread_id = record.get("thread_id")
    if not isinstance(thread_id, str) or not thread_id.strip():
        raise WrapperError("Cannot save state without thread_id.")
    thread_id = thread_id.strip()

    state = load_state(workspace)
    threads = state["threads"]
    assert isinstance(threads, list)

    existing_idx = next(
        (
            i
            for i, item in enumerate(threads)
            if isinstance(item, dict) and item.get("thread_id") == thread_id  # ty:ignore[invalid-argument-type]
        ),
        None,
    )

    normalized = _normalize_thread_entry(record)
    if not normalized:
        raise WrapperError("Invalid thread record.")

    if existing_idx is None:
        normalized["created_at"] = normalized.get("created_at") or now_iso()
        threads.insert(0, normalized)
    else:
        existing = threads[existing_idx]
        if isinstance(existing, dict):
            normalized["created_at"] = existing.get("created_at") or normalized.get(
                "created_at"
            )
        threads[existing_idx] = normalized

    state["latest_thread_id"] = thread_id
    save_state(workspace, state)


def short_summary(text: str, limit: int = 120) -> str:
    one_line = " ".join(text.split())
    if len(one_line) <= limit:
        return one_line
    return one_line[: limit - 3] + "..."


def read_prompt(prompt_parts: list[str]) -> str:
    prompt = " ".join(prompt_parts).strip()
    if prompt:
        if not sys.stdin.isatty():
            stdin_text = sys.stdin.read()
            if stdin_text.strip():
                prompt = prompt + "\n\n<stdin>\n" + stdin_text
        return prompt

    if not sys.stdin.isatty():
        stdin_text = sys.stdin.read()
        if stdin_text.strip():
            return stdin_text

    raise WrapperError("Prompt is required. Pass text or pipe stdin.")


def require_codex() -> None:
    if shutil.which("codex") is None:
        raise WrapperError("`codex` command was not found in PATH.")


def parse_jsonl(stdout_text: str) -> tuple[list[dict[str, Any]], list[str]]:
    events: list[dict[str, Any]] = []
    non_json_lines: list[str] = []
    for line in stdout_text.splitlines():
        raw = line.strip()
        if not raw:
            continue
        try:
            parsed = json.loads(raw)
        except json.JSONDecodeError:
            non_json_lines.append(line)
            continue
        if isinstance(parsed, dict):
            events.append(parsed)
        else:
            non_json_lines.append(line)
    return events, non_json_lines


def extract_result(events: list[dict[str, Any]]) -> dict[str, Any]:
    thread_id: str | None = None
    message_parts: list[str] = []
    touched_files: set[str] = set()
    usage: dict[str, Any] | None = None

    for event in events:
        etype = event.get("type")
        if etype == "thread.started":
            value = event.get("thread_id")
            if isinstance(value, str):
                thread_id = value
            continue

        if etype == "item.completed":
            item = event.get("item")
            if not isinstance(item, dict):
                continue
            if item.get("type") == "agent_message":
                text = item.get("text")
                if isinstance(text, str) and text.strip():
                    message_parts.append(text)

            changes = item.get("changes")
            if isinstance(changes, list):
                for change in changes:
                    if isinstance(change, dict):
                        path_value = change.get("path")
                        if isinstance(path_value, str) and path_value:
                            touched_files.add(path_value)

            path_value = item.get("path")
            if isinstance(path_value, str) and path_value:
                touched_files.add(path_value)
            continue

        if etype == "turn.completed":
            maybe_usage = event.get("usage")
            if isinstance(maybe_usage, dict):
                usage = maybe_usage

    full_message = "\n\n".join(part for part in message_parts if part)
    return {
        "thread_id": thread_id,
        "agent_message": full_message,
        "summary": short_summary(full_message) if full_message else "",
        "touched_files": sorted(touched_files),
        "usage": usage,
    }


def read_text_safe(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except OSError:
        return ""


def parse_stdout_log(stdout_log: Path) -> dict[str, Any]:
    stdout_text = read_text_safe(stdout_log)
    events, non_json_lines = parse_jsonl(stdout_text)
    extracted = extract_result(events)
    has_turn_completed = any(
        isinstance(event, dict) and event.get("type") == "turn.completed"
        for event in events
    )

    if non_json_lines and not extracted.get("agent_message"):
        fallback_message = "\n".join(non_json_lines)
        extracted["agent_message"] = fallback_message
        extracted["summary"] = short_summary(fallback_message)

    return {
        **extracted,
        "events_count": len(events),
        "non_json_stdout": non_json_lines,
        "turn_completed": has_turn_completed,
    }


def read_exit_code_file(path: str | None) -> int | None:
    if not path:
        return None
    file_path = Path(path)
    if not file_path.exists():
        return None
    text = read_text_safe(file_path).strip()
    if not text:
        return None
    try:
        return int(text)
    except ValueError:
        return None


def is_pid_alive(pid: int | None) -> bool:
    if not isinstance(pid, int) or pid <= 0:
        return False
    try:
        os.kill(pid, 0)
        return True
    except OSError:
        return False


def run_codex(*, workspace: Path, cmd: list[str]) -> dict[str, Any]:
    ensure_dir(jobs_dir(workspace))
    run_token = f"run-{uuid.uuid4().hex[:10]}"
    stdout_log = jobs_dir(workspace) / f"{run_token}.stdout.log"
    stderr_log = jobs_dir(workspace) / f"{run_token}.stderr.log"

    proc = subprocess.run(
        cmd,
        cwd=str(workspace),
        capture_output=True,
        text=True,
        encoding="utf-8",
    )

    stdout_log.write_text(proc.stdout or "", encoding="utf-8")
    stderr_log.write_text(proc.stderr or "", encoding="utf-8")

    parsed = parse_stdout_log(stdout_log)
    return {
        "exit_code": int(proc.returncode),
        "stdout_log": str(stdout_log),
        "stderr_log": str(stderr_log),
        **parsed,
    }


def run_codex_delegate_with_check_in(
    *,
    workspace: Path,
    cmd: list[str],
    check_in_seconds: int,
) -> dict[str, Any]:
    ensure_dir(jobs_dir(workspace))
    run_token = f"run-{uuid.uuid4().hex[:10]}"
    stdout_log = jobs_dir(workspace) / f"{run_token}.stdout.log"
    stderr_log = jobs_dir(workspace) / f"{run_token}.stderr.log"
    exit_code_file = jobs_dir(workspace) / f"{run_token}.exit-code"

    shell_cmd = (
        f"{shlex.join(cmd)} > {shlex.quote(str(stdout_log))} "
        f"2> {shlex.quote(str(stderr_log))}; "
        f'rc=$?; printf "%s\\n" "$rc" > {shlex.quote(str(exit_code_file))}'
    )
    proc = subprocess.Popen(
        ["/bin/sh", "-c", shell_cmd],
        cwd=str(workspace),
        start_new_session=True,
    )

    deadline = time.monotonic() + max(check_in_seconds, 0)
    latest_partial = {
        "thread_id": None,
        "summary": "",
        "agent_message": "",
        "touched_files": [],
        "usage": None,
        "events_count": 0,
        "turn_completed": False,
    }
    while True:
        latest_partial = parse_stdout_log(stdout_log)
        if proc.poll() is not None:
            break
        if time.monotonic() >= deadline:
            break
        time.sleep(1)

    latest_partial = parse_stdout_log(stdout_log)
    exit_code = read_exit_code_file(str(exit_code_file))
    still_running = proc.poll() is None and exit_code is None

    return {
        "running": still_running,
        "pid": proc.pid if still_running else None,
        "run_token": run_token,
        "stdout_log": str(stdout_log),
        "stderr_log": str(stderr_log),
        "exit_code_file": str(exit_code_file),
        "exit_code": exit_code
        if exit_code is not None
        else (None if still_running else 1),
        **latest_partial,
    }


def build_exec_base(args: argparse.Namespace) -> list[str]:
    cmd = ["codex", "exec", "--json"]
    if args.model:
        cmd.extend(["--model", args.model])
    if args.sandbox:
        cmd.extend(["--sandbox", args.sandbox])
    if args.profile:
        cmd.extend(["--profile", args.profile])
    if args.output_schema:
        cmd.extend(["--output-schema", args.output_schema])
    if args.full_auto:
        cmd.append("--full-auto")
    if args.skip_git_repo_check:
        cmd.append("--skip-git-repo-check")
    if args.ephemeral:
        cmd.append("--ephemeral")
    return cmd


def _build_thread_record(
    *,
    thread_id: str,
    kind: str,
    phase: str,
    exit_code: int | None,
    workspace: Path,
    prompt: str,
    command: list[str],
    result: dict[str, Any],
    started_at: str,
    run_pid: int | None = None,
    run_token: str | None = None,
    exit_code_file: str | None = None,
    check_in_seconds: int | None = None,
) -> dict[str, Any]:
    return {
        "thread_id": thread_id,
        "created_at": started_at,
        "updated_at": now_iso(),
        "kind": kind,
        "phase": phase,
        "exit_code": exit_code,
        "workspace": str(workspace),
        "last_prompt": prompt,
        "last_command": command,
        "summary": result.get("summary") or "",
        "agent_message": result.get("agent_message") or "",
        "touched_files": result.get("touched_files") or [],
        "usage": result.get("usage"),
        "stdout_log": result["stdout_log"],
        "stderr_log": result["stderr_log"],
        "events_count": result["events_count"],
        "turn_completed": bool(result.get("turn_completed")),
        "run_pid": run_pid,
        "run_token": run_token,
        "exit_code_file": exit_code_file,
        "check_in_seconds": check_in_seconds,
    }


def _thread_payload(
    thread: dict[str, Any], include_next_action: bool = False
) -> dict[str, Any]:
    phase = thread.get("phase")
    payload = {
        "thread_id": thread.get("thread_id"),
        "kind": thread.get("kind"),
        "phase": phase,
        "exit_code": thread.get("exit_code"),
        "summary": thread.get("summary") or "",
        "agent_message": thread.get("agent_message") or "",
        "touched_files": thread.get("touched_files") or [],
        "usage": thread.get("usage"),
        "stdout_log": thread.get("stdout_log"),
        "stderr_log": thread.get("stderr_log"),
    }
    if include_next_action:
        if phase == "running":
            payload["next_action"] = (
                "Run `reconnect --thread-id <thread_id>` to poll again, "
                "or `cancel --thread-id <thread_id>` to stop."
            )
        elif phase == "completed":
            payload["next_action"] = (
                'Run `feedback --thread-id <thread_id> "<message>"` to continue.'
            )
        elif phase == "canceled":
            payload["next_action"] = "Canceled. Run `delegate` to start a new thread."
        else:
            payload["next_action"] = "Inspect stderr_log and retry."
    return payload


def refresh_running_thread(
    *,
    workspace: Path,
    thread: dict[str, Any],
    wait_seconds: int = 0,
) -> dict[str, Any]:
    phase = thread.get("phase")
    if phase != "running":
        return thread

    thread_id = thread.get("thread_id")
    if not isinstance(thread_id, str) or not thread_id.strip():
        return thread

    wait_until = time.monotonic() + max(wait_seconds, 0)
    while True:
        exit_code = read_exit_code_file(thread.get("exit_code_file"))
        stdout_log_value = thread.get("stdout_log")
        stdout_log = (
            Path(stdout_log_value).resolve()
            if isinstance(stdout_log_value, str) and stdout_log_value
            else None
        )
        partial = (
            parse_stdout_log(stdout_log)
            if stdout_log
            else {
                "thread_id": thread_id,
                "summary": thread.get("summary") or "",
                "agent_message": thread.get("agent_message") or "",
                "touched_files": thread.get("touched_files") or [],
                "usage": thread.get("usage"),
                "events_count": thread.get("events_count") or 0,
                "turn_completed": bool(thread.get("turn_completed")),
            }
        )

        if exit_code is not None or partial.get("turn_completed"):
            if exit_code is None:
                exit_code = 0
            updated = dict(thread)
            updated["updated_at"] = now_iso()
            updated["phase"] = "completed" if exit_code == 0 else "failed"
            updated["exit_code"] = exit_code
            updated["summary"] = partial.get("summary") or ""
            updated["agent_message"] = partial.get("agent_message") or ""
            updated["touched_files"] = partial.get("touched_files") or []
            updated["usage"] = partial.get("usage")
            updated["events_count"] = partial.get("events_count")
            updated["turn_completed"] = bool(partial.get("turn_completed"))
            updated["run_pid"] = None
            updated["run_token"] = None
            updated["exit_code_file"] = None
            upsert_thread(workspace, updated)
            remember_thread_workspace(thread_id, workspace)
            return updated

        if time.monotonic() >= wait_until:
            updated_running = dict(thread)
            updated_running["updated_at"] = now_iso()
            if partial.get("thread_id"):
                updated_running["thread_id"] = partial["thread_id"]
            updated_running["summary"] = partial.get("summary") or ""
            updated_running["agent_message"] = partial.get("agent_message") or ""
            updated_running["touched_files"] = partial.get("touched_files") or []
            updated_running["usage"] = partial.get("usage")
            updated_running["events_count"] = partial.get("events_count")
            updated_running["turn_completed"] = bool(partial.get("turn_completed"))
            upsert_thread(workspace, updated_running)
            return updated_running

        time.sleep(1)


def run_delegate(args: argparse.Namespace) -> int:
    workspace = resolve_workspace(cwd=args.cwd, thread_id=None, fallback_current=True)
    prompt = read_prompt(args.prompt)

    cmd = build_exec_base(args)
    cmd.append(prompt)

    check_in_seconds = max(int(args.check_in_seconds), 0)

    if args.dry_run:
        output = {
            "mode": "dry-run",
            "command": cmd,
            "workspace": str(workspace),
            "prompt": prompt,
            "check_in_seconds": check_in_seconds if check_in_seconds > 0 else None,
        }
        print(json.dumps(output, ensure_ascii=False, indent=2))
        return 0

    started_at = now_iso()
    if check_in_seconds > 0:
        result = run_codex_delegate_with_check_in(
            workspace=workspace,
            cmd=cmd,
            check_in_seconds=check_in_seconds,
        )
    else:
        sync_result = run_codex(workspace=workspace, cmd=cmd)
        result = {
            "running": False,
            "pid": None,
            "run_token": None,
            "exit_code_file": None,
            **sync_result,
        }
    phase = (
        "running"
        if result["running"]
        else ("completed" if result["exit_code"] == 0 else "failed")
    )

    thread_id = result.get("thread_id")
    if isinstance(thread_id, str) and thread_id.strip():
        thread_id = thread_id.strip()
        record = _build_thread_record(
            thread_id=thread_id,
            kind="delegate",
            phase=phase,
            exit_code=result["exit_code"],
            workspace=workspace,
            prompt=prompt,
            command=cmd,
            result=result,
            started_at=started_at,
            run_pid=result.get("pid"),
            run_token=result.get("run_token"),
            exit_code_file=result.get("exit_code_file"),
            check_in_seconds=check_in_seconds if check_in_seconds > 0 else None,
        )
        upsert_thread(workspace, record)
        remember_thread_workspace(thread_id, workspace)
    else:
        thread_id = None

    output = _thread_payload(
        {
            "thread_id": thread_id,
            "kind": "delegate",
            "phase": phase,
            "exit_code": result["exit_code"],
            "summary": result.get("summary") or "",
            "agent_message": result.get("agent_message") or "",
            "touched_files": result.get("touched_files") or [],
            "usage": result.get("usage"),
            "stdout_log": result["stdout_log"],
            "stderr_log": result["stderr_log"],
        },
        include_next_action=True,
    )
    output["check_in_seconds"] = check_in_seconds if check_in_seconds > 0 else None
    print(json.dumps(output, ensure_ascii=False, indent=2))
    return 0 if phase in {"completed", "running"} else 1


def run_feedback(args: argparse.Namespace) -> int:
    target_thread_id = args.thread_id.strip()

    if not target_thread_id:
        raise WrapperError("--thread-id is required.")

    workspace = resolve_workspace(
        cwd=args.cwd,
        thread_id=target_thread_id,
        fallback_current=False,
    )
    prompt = read_prompt(args.prompt)
    started_at = now_iso()

    cmd = build_exec_base(args)
    cmd.extend(["resume", target_thread_id, prompt])

    result = run_codex(workspace=workspace, cmd=cmd)
    phase = "completed" if result["exit_code"] == 0 else "failed"

    result_thread_id = result.get("thread_id")
    if isinstance(result_thread_id, str) and result_thread_id.strip():
        resolved_thread_id = result_thread_id.strip()
    else:
        resolved_thread_id = target_thread_id

    record = _build_thread_record(
        thread_id=resolved_thread_id,
        kind="feedback",
        phase=phase,
        exit_code=result["exit_code"],
        workspace=workspace,
        prompt=prompt,
        command=cmd,
        result=result,
        started_at=started_at,
    )
    upsert_thread(workspace, record)
    remember_thread_workspace(resolved_thread_id, workspace)

    output = _thread_payload(
        {
            "thread_id": resolved_thread_id,
            "kind": "feedback",
            "phase": phase,
            "exit_code": result["exit_code"],
            "summary": result.get("summary") or "",
            "agent_message": result.get("agent_message") or "",
            "touched_files": result.get("touched_files") or [],
            "usage": result.get("usage"),
            "stdout_log": result["stdout_log"],
            "stderr_log": result["stderr_log"],
        },
        include_next_action=True,
    )
    print(json.dumps(output, ensure_ascii=False, indent=2))
    return 0 if phase == "completed" else 1


def run_reconnect(args: argparse.Namespace) -> int:
    thread_id = args.thread_id.strip()
    if not thread_id:
        raise WrapperError("--thread-id is required.")

    workspace = resolve_workspace(
        cwd=args.cwd,
        thread_id=thread_id,
        fallback_current=False,
    )
    state = load_state(workspace)
    thread = find_thread(state, thread_id)
    if not thread:
        print(
            json.dumps(
                {"workspace": str(workspace), "message": "No thread found."},
                ensure_ascii=False,
                indent=2,
            )
        )
        return 1

    refreshed = refresh_running_thread(
        workspace=workspace,
        thread=thread,
        wait_seconds=max(int(args.wait_seconds), 0),
    )
    payload = _thread_payload(refreshed, include_next_action=True)
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    phase = refreshed.get("phase")
    return 0 if phase in {"completed", "running"} else 1


def run_cancel(args: argparse.Namespace) -> int:
    thread_id = args.thread_id.strip()
    if not thread_id:
        raise WrapperError("--thread-id is required.")

    workspace = resolve_workspace(
        cwd=args.cwd,
        thread_id=thread_id,
        fallback_current=False,
    )
    state = load_state(workspace)
    thread = find_thread(state, thread_id)
    if not thread:
        print(
            json.dumps(
                {"workspace": str(workspace), "message": "No thread found."},
                ensure_ascii=False,
                indent=2,
            )
        )
        return 1

    refreshed = refresh_running_thread(
        workspace=workspace, thread=thread, wait_seconds=0
    )
    if refreshed.get("phase") != "running":
        payload = _thread_payload(refreshed, include_next_action=True)
        print(json.dumps(payload, ensure_ascii=False, indent=2))
        return 0

    run_pid = refreshed.get("run_pid")
    if isinstance(run_pid, int) and run_pid > 0 and is_pid_alive(run_pid):
        try:
            os.kill(run_pid, signal.SIGTERM)
        except OSError:
            pass
        for _ in range(20):
            if not is_pid_alive(run_pid):
                break
            time.sleep(0.25)
        if is_pid_alive(run_pid):
            try:
                os.kill(run_pid, signal.SIGKILL)
            except OSError:
                pass

    updated = dict(refreshed)
    updated["phase"] = "canceled"
    updated["exit_code"] = 130
    updated["updated_at"] = now_iso()
    updated["run_pid"] = None
    updated["run_token"] = None
    updated["exit_code_file"] = None
    upsert_thread(workspace, updated)

    payload = _thread_payload(updated, include_next_action=True)
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0


def find_thread(
    state: dict[str, Any], thread_id: str | None = None
) -> dict[str, Any] | None:
    threads = state.get("threads")
    if not isinstance(threads, list):
        return None

    if thread_id:
        tid = thread_id.strip()
        for thread in threads:
            if isinstance(thread, dict) and thread.get("thread_id") == tid:
                return thread
        return None

    latest_tid = state.get("latest_thread_id")
    if isinstance(latest_tid, str) and latest_tid.strip():
        for thread in threads:
            if isinstance(thread, dict) and thread.get("thread_id") == latest_tid:
                return thread

    return threads[0] if threads else None


def run_status(args: argparse.Namespace) -> int:
    workspace = resolve_workspace(
        cwd=args.cwd,
        thread_id=args.thread_id,
        fallback_current=True,
    )
    state = load_state(workspace)
    threads = state.get("threads", [])

    if args.all:
        if isinstance(threads, list):
            refreshed_threads: list[dict[str, Any]] = []
            for item in threads:
                if isinstance(item, dict) and item.get("phase") == "running":
                    refreshed_threads.append(
                        refresh_running_thread(
                            workspace=workspace, thread=item, wait_seconds=0
                        )
                    )
                elif isinstance(item, dict):
                    refreshed_threads.append(item)
            threads = refreshed_threads
        payload = {
            "workspace": str(workspace),
            "latest_thread_id": state.get("latest_thread_id"),
            "count": len(threads) if isinstance(threads, list) else 0,
            "threads": threads,
        }
        print(json.dumps(payload, ensure_ascii=False, indent=2))
        return 0

    thread = find_thread(state, args.thread_id)
    if not thread:
        print(
            json.dumps(
                {"workspace": str(workspace), "message": "No thread found."},
                ensure_ascii=False,
                indent=2,
            )
        )
        return 1

    if thread.get("phase") == "running":
        thread = refresh_running_thread(
            workspace=workspace, thread=thread, wait_seconds=0
        )
    print(json.dumps(thread, ensure_ascii=False, indent=2))
    return 0


def run_result(args: argparse.Namespace) -> int:
    workspace = resolve_workspace(
        cwd=args.cwd,
        thread_id=args.thread_id,
        fallback_current=True,
    )
    state = load_state(workspace)
    thread = find_thread(state, args.thread_id)

    if not thread:
        print(
            json.dumps(
                {"workspace": str(workspace), "message": "No thread found."},
                ensure_ascii=False,
                indent=2,
            )
        )
        return 1

    if thread.get("phase") == "running":
        thread = refresh_running_thread(
            workspace=workspace, thread=thread, wait_seconds=0
        )

    if args.raw:
        print(thread.get("agent_message", ""))
        return 0

    payload = {
        "thread_id": thread.get("thread_id"),
        "kind": thread.get("kind"),
        "phase": thread.get("phase"),
        "summary": thread.get("summary"),
        "agent_message": thread.get("agent_message"),
        "touched_files": thread.get("touched_files", []),
        "usage": thread.get("usage"),
        "stdout_log": thread.get("stdout_log"),
        "stderr_log": thread.get("stderr_log"),
        "updated_at": thread.get("updated_at"),
    }
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0


def add_common_options(
    parser: argparse.ArgumentParser,
    *,
    cwd_default: str | None,
    cwd_help: str,
) -> None:
    parser.add_argument(
        "--cwd",
        default=cwd_default,
        help=cwd_help,
    )
    parser.add_argument("--model", help="Pass-through model for codex exec")
    parser.add_argument(
        "--sandbox",
        choices=["read-only", "workspace-write", "danger-full-access"],
        help="Pass-through sandbox for codex exec",
    )
    parser.add_argument("--profile", help="Pass-through profile for codex exec")
    parser.add_argument(
        "--output-schema", help="Pass-through output schema file for codex exec"
    )
    parser.add_argument(
        "--full-auto", action="store_true", help="Pass-through --full-auto"
    )
    parser.add_argument(
        "--skip-git-repo-check",
        action="store_true",
        help="Pass-through --skip-git-repo-check",
    )
    parser.add_argument(
        "--ephemeral", action="store_true", help="Pass-through --ephemeral"
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="codex-wrapper",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        description=textwrap.dedent(
            """
            Thin wrapper for Codex CLI with local state tracking and fixed JSON output.

            Examples:
              codex-wrapper delegate "Investigate failing tests and propose smallest fix"
              codex-wrapper feedback --thread-id <thread_id> "Apply option 2 and run targeted tests"
              codex-wrapper reconnect --thread-id <thread_id> --wait-seconds 180
              codex-wrapper cancel --thread-id <thread_id>
              codex-wrapper status
              codex-wrapper result --raw
            """
        ).strip(),
    )

    sub = parser.add_subparsers(dest="command", required=True)

    delegate = sub.add_parser("delegate", help="Run a fresh codex exec task")
    add_common_options(
        delegate,
        cwd_default=".",
        cwd_help="Workspace directory (default: current directory)",
    )
    delegate.add_argument(
        "prompt", nargs=argparse.REMAINDER, help="Prompt text (or pipe via stdin)"
    )
    delegate.add_argument(
        "--dry-run",
        action="store_true",
        help="Print the command, workspace, and prompt as JSON without running codex. Must appear before the prompt text.",
    )
    delegate.add_argument(
        "--check-in-seconds",
        type=int,
        default=DEFAULT_CHECK_IN_SECONDS,
        help=(
            "If still running after N seconds, return phase=running and keep process alive "
            "(default: 180, set 0 to wait until completion)."
        ),
    )
    delegate.set_defaults(func=run_delegate)

    feedback = sub.add_parser(
        "feedback", help="Resume a specific codex thread with feedback"
    )
    add_common_options(
        feedback,
        cwd_default=None,
        cwd_help=(
            "Workspace directory (optional; omitted means resolve from --thread-id index)"
        ),
    )
    feedback.add_argument(
        "--thread-id",
        required=True,
        help="Target thread id returned by delegate/result/status",
    )
    feedback.add_argument(
        "prompt", nargs=argparse.REMAINDER, help="Feedback text (or pipe via stdin)"
    )
    feedback.set_defaults(func=run_feedback)

    reconnect = sub.add_parser(
        "reconnect",
        help="Poll a running thread and return final result when available",
    )
    reconnect.add_argument(
        "--cwd",
        default=None,
        help=(
            "Workspace directory (optional; omitted means resolve from --thread-id index)"
        ),
    )
    reconnect.add_argument(
        "--thread-id",
        required=True,
        help="Target running thread id",
    )
    reconnect.add_argument(
        "--wait-seconds",
        type=int,
        default=0,
        help="Wait up to N seconds for completion before returning running status.",
    )
    reconnect.set_defaults(func=run_reconnect)

    cancel = sub.add_parser("cancel", help="Cancel a running thread by thread id")
    cancel.add_argument(
        "--cwd",
        default=None,
        help=(
            "Workspace directory (optional; omitted means resolve from --thread-id index)"
        ),
    )
    cancel.add_argument(
        "--thread-id",
        required=True,
        help="Target running thread id",
    )
    cancel.set_defaults(func=run_cancel)

    status = sub.add_parser(
        "status", help="Show latest thread or all threads from local state"
    )
    status.add_argument(
        "--cwd",
        default=None,
        help=(
            "Workspace directory (optional; omitted means current directory, "
            "or resolve from --thread-id)"
        ),
    )
    status.add_argument("--all", action="store_true", help="Show all threads")
    status.add_argument("--thread-id", help="Show specific thread")
    status.set_defaults(func=run_status)

    result = sub.add_parser(
        "result", help="Show latest or specific thread result payload"
    )
    result.add_argument(
        "--cwd",
        default=None,
        help=(
            "Workspace directory (optional; omitted means current directory, "
            "or resolve from --thread-id)"
        ),
    )
    result.add_argument("--thread-id", help="Target thread id")
    result.add_argument("--raw", action="store_true", help="Print only agent_message")
    result.set_defaults(func=run_result)

    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    if not getattr(args, "dry_run", False):
        require_codex()
    try:
        return int(args.func(args))
    except WrapperError as exc:
        print(
            json.dumps({"error": str(exc)}, ensure_ascii=False, indent=2),
            file=sys.stderr,
        )
        return 2
    except KeyboardInterrupt:
        print(
            json.dumps({"error": "Interrupted."}, ensure_ascii=False, indent=2),
            file=sys.stderr,
        )
        return 130


if __name__ == "__main__":
    raise SystemExit(main())
