# skills

Claude Code 向け Agent Skills リポジトリ。

## スキル一覧

| スキル | 概要 |
|---|---|
| `mise-config` | mise.toml のタスク・環境変数の追加・編集 |
| `codex-task-delegate` | タスクを Codex CLI (`codex exec`) へ委譲・管理 |
| `skill-authoring` | Agent Skill (SKILL.md) の作成・編集・改善 |

## インストール

```bash
npx skills add agarichan/skills
```

特定のスキルだけ入れる場合:

```bash
npx skills add agarichan/skills --skill mise-config
```

リポジトリ内のスキル一覧を確認:

```bash
npx skills add agarichan/skills --list
```

## Codex ラッパー

`skills/codex-task-delegate/scripts/codex_wrapper.py` は `codex exec` の薄いラッパー。ローカル状態管理と出力の JSON 整形を行う。

```bash
# 新規タスク委譲
./scripts/codex_wrapper.py delegate --cwd "<workspace>" --check-in-seconds 180 "<task>"

# 途中経過から再接続
./scripts/codex_wrapper.py reconnect --thread-id <thread_id> --wait-seconds 180

# キャンセル
./scripts/codex_wrapper.py cancel --thread-id <thread_id>

# フィードバック
./scripts/codex_wrapper.py feedback --thread-id <thread_id> "案2で実装して"

# 状態確認
./scripts/codex_wrapper.py status

# 最終メッセージだけ表示
./scripts/codex_wrapper.py result --raw
```

## スキルの追加方法

`skills/<skill-name>/` に新しいフォルダを作成し、`SKILL.md`（YAML frontmatter に `name` と `description`）を用意する。必要に応じて `references/`、`scripts/`、`assets/` を追加。
