# Codex Task Delegate — Execution Protocol

このドキュメントはサブエージェントに渡す実行手順。

## スクリプトパス

`{{SCRIPT}}` をスキルから渡されたスクリプトの絶対パスに読み替える。

## Standard Flow

1. `delegate` で新規スレッドを開始する。
2. 返却 JSON の `thread_id` と `phase` を読む。
3. `phase` で分岐する。
4. `completed` なら結果を返す。
5. `running` なら `reconnect` か `cancel` を選ぶ。
6. `failed` なら `stderr_log` を確認して失敗を返す。
7. 継続修正が必要なら `feedback` で同じ `thread_id` に追加指示する。

## Step 1: Delegate (新規委譲)

1. ユーザー入力からタスク文を作る。
2. 次で新規委譲する（`<task>` にファイルパスを含めてもよい）。

```bash
{{SCRIPT}} delegate --cwd "<workspace>" --check-in-seconds 180 "<task>"
```

3. 返ってきた JSON の `thread_id` を必ず保持して返答する。

## Step 2: Phase Branching

`delegate` / `reconnect` の返却 `phase` を基準に分岐する。

- `phase=completed`:
  - `summary` / `agent_message` / `touched_files` を返す
  - 追加依頼が来たら `feedback`
- `phase=running`:
  - 返却内容（`summary` / `agent_message` / `stderr_log`）が意図どおりなら `reconnect --wait-seconds 180`
  - 意図とズレている、危険な変更をしそう、前提が崩れている場合は `cancel`
- `phase=failed`:
  - `stderr_log` を提示して停止
- `phase=canceled`:
  - キャンセル済みとして終了。必要なら新規 `delegate` を案内

## Step 3: Reconnect / Cancel

- 途中経過からの再接続（完了まで待つ秒数は任意）:

```bash
{{SCRIPT}} reconnect --thread-id "<thread_id>" --wait-seconds 180
```

- reconnect ループは **最大 10 回**（合計最大約 30 分）を上限とする。超過したら `cancel` してユーザーに報告する。
- 問題があればキャンセル:

```bash
{{SCRIPT}} cancel --thread-id "<thread_id>"
```

## Step 4: Feedback / Status / Result

- フィードバック:

```bash
{{SCRIPT}} feedback --thread-id "<thread_id>" "<feedback message>"
```

- 状態確認:

```bash
{{SCRIPT}} status --thread-id "<thread_id>"
```

- 結果確認:

```bash
{{SCRIPT}} result --thread-id "<thread_id>"
```

## Output Contract

すべての応答で最低限次を扱う:

- `thread_id`
- `phase`
- `summary`
- `next_action`

`phase=completed` のときは追加で次を優先:

- `agent_message`
- `touched_files`
- `usage`

## Notes

- `--check-in-seconds` は、Codex が意図どおりに進んでいるかを途中で検査するためのセーフティチェック。
- チェック時点で意図とズレていれば `cancel`、問題なければ `reconnect` で継続する。
- `--check-in-seconds 0` はセーフティチェック無効化。意図ズレ検知ができなくなるため、低リスク作業でのみ使う。
- `phase=running` が返った場合は、`reconnect` で継続確認、または `cancel` で停止できる。
- `--thread-id` を使えば、`feedback/status/result` は `--cwd` を省略して実行できる。
- ファイルパスを指示に含める場合は、`--cwd` から到達できるパスにする。
- **worktree 併用時**: `--cwd` には worktree のパスを指定する。メインディレクトリを指定すると Codex がメイン側を編集する。また、worktree にはコミット済みファイルのみ存在するため、untracked ファイルの編集が必要なら先にコミットすること。
