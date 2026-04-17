# Plan: codex_wrapper.py にドライランモードを追加

## 概要

`codex_wrapper.py` の `delegate` コマンドに `--dry-run` フラグを追加し、
実際に Codex を呼ばずにコマンド構築結果を JSON で出力する機能を作る。

## 実装方針

各タスクの実装は **codex-task-delegate スキルを使って Codex に委譲すること**。
レビューは Claude Code のサブエージェントで実施する。

## Tasks

### Task 1: --dry-run フラグの追加

**ファイル:** `skills/codex-task-delegate/scripts/codex_wrapper.py`

1. `delegate` サブパーサーに `--dry-run` フラグ（`store_true`）を追加
2. `run_delegate` の先頭で `args.dry_run` を判定
3. `dry_run=True` の場合、`run_codex` / `run_codex_delegate_with_check_in` を呼ばずに以下を JSON 出力して return 0:
   - `mode: "dry-run"`
   - `command`: 構築された codex コマンド（リスト）
   - `workspace`: 解決済みワークスペースパス
   - `prompt`: 組み立てたプロンプト
   - `check_in_seconds`: 設定値

**検証:** `python3 scripts/codex_wrapper.py delegate --dry-run "test task"` が JSON を返すこと。

### Task 2: --dry-run のテスト

**ファイル:** `skills/codex-task-delegate/scripts/test_dry_run.py`

1. `subprocess.run` で `codex_wrapper.py delegate --dry-run "hello"` を実行
2. stdout が valid JSON であることを確認
3. `mode` が `"dry-run"` であることを確認
4. `command` に `"codex"` と `"hello"` が含まれることを確認

**検証:** `python3 -m pytest scripts/test_dry_run.py -v` が pass すること。
