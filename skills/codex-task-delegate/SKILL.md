---
name: codex-task-delegate
description: >
  ファイルに書かれたタスク、または直接渡されたテキストタスクを Codex に委譲する。
  次の依頼で使う:
  - "codexでXXX.mdのタスクを実施して"
  - "codexでXXX.txtの手順を実施して"
  - "このmdをcodexに投げて"
  - "この指示をcodexに投げて"
  - "thread_id にフィードバックして"
  - "Codexの結果を確認して"
---

# Codex Task Delegate

この skill は Agent tool（サブエージェント）を起動して Codex への委譲を実行する。

## 実行手順

1. ユーザー入力からタスク文を組み立てる（ファイル指定ならファイルを読む）。
2. `references/execution-protocol.md` を Read する。
3. 下記テンプレートで Agent tool を呼ぶ。

### Agent tool 呼び出しテンプレート

```
Agent({
  description: "Codex delegate: <タスク概要>",
  prompt: <下記で構成>,
})
```

**prompt の構成:**

```
あなたは Codex タスク委譲エージェントです。

## スクリプト
SCRIPT = "<このスキルの絶対パス>/scripts/codex_wrapper.py"

## ワークスペース
WORKSPACE = "<作業ディレクトリ（worktree 使用時は worktree のパス）>"

## タスク
<ユーザーのタスク文>

## 実行プロトコル
<references/execution-protocol.md の内容（{{SCRIPT}} を実際のパスに置換済み）>
```

4. サブエージェントの結果を受け取り、`thread_id`・`phase`・`summary` をユーザーに返す。
5. フィードバック・reconnect・status・result も同様にサブエージェントを起動して実行する。

### バックグラウンド実行テンプレート

メインで別作業を並行する場合は `run_in_background: true` を使う:

```
Agent({
  description: "Codex delegate: <タスク概要>",
  run_in_background: true,
  prompt: <上記と同じ構成>,
})
```

### feedback / status / result テンプレート

既存 thread_id に対する操作もサブエージェントで実行する。prompt 内のタスク部分を以下に差し替え:

- **feedback**: `thread_id <ID> に対して次のフィードバックを送れ: "<メッセージ>"`
- **status**: `thread_id <ID> の状態を確認して報告せよ`
- **result**: `thread_id <ID> の結果を取得して報告せよ`

## スキルディレクトリの解決

このスキルのベースディレクトリはスキルロード時にシステムから通知される。
そのパスを使って `scripts/codex_wrapper.py` の絶対パスを構成する。

## Worktree 使用時の注意

- `--cwd` には **worktree のパス**を渡すこと。メインの作業ディレクトリを渡すと Codex がメイン側を編集してしまう。
- worktree には **コミット済みファイルしか存在しない**。untracked のファイルを Codex に編集させたい場合は、先にコミットしてから worktree を作成する。

## Notes

- サブエージェントはメインコンテキストを消費しないため、長時間の delegate/reconnect ループに適する。
- `phase=running` の reconnect ループはサブエージェント内で完結させる。
- 結果の要約のみメインに返す。
