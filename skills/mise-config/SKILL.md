---
name: mise-config
description: >
  Add or edit mise tasks and environment variables in `mise.toml`.
  Use when the user asks to:
  - configure environment variables in mise
  - add or edit a mise task
  - make something runnable with `mise run`
  - pass arguments to a mise task
  - "miseに環境変数を設定して"
  - "miseにtaskを書いて"
  - "mise runで○○できるようにして"
  - "mise taskに引数を渡せるようにして"
  - "miseについて教えて"
---

# mise config

## Principles

- monorepo前提。タスクは積極的に細かく分割し、ルートの mise.toml で `run = [{ tasks = [...] }]` を使って並列集約する
- 引数定義は `usage` フィールドを使う
- 設定ファイルは `mise.toml` を使う（`.mise.toml` ではなく）
- `description` は簡潔に日本語で書く
- 直接呼び出さないタスク（共通の前処理等）は `_` をタスク名に含め、`hide = true` にする

## Gotchas

- **monorepo 有効化は2箇所必要**: ルート mise.toml に `experimental_monorepo_root = true` と `[settings]` に `experimental = true` の両方
- **monorepo タスク参照**: `//path:task` 構文。`//` プレフィックス + `:` 区切り。ルートで `run = [{ tasks = ["//backend:lint", "//frontend:lint"] }]` のように並列集約
- **config_roots は明示指定**: `[monorepo]` セクションで `config_roots = ["backend", "frontend"]` のようにパスを列挙。再帰 glob (`**`) 非対応、単一レベル glob (`*`) のみ
- **run は配列も可**: 文字列だけでなく `[{ task = "build" }, "echo done"]` のようにタスク参照・スクリプトを混在できる
- **`task` vs `tasks`**: `{ task = "x", args = [...] }` は逐次・引数指定可。`{ tasks = ["x", "y"] }` は並列だが **args/env 指定不可**。並列 + 引数転送が必要な場合は `depends` の構造化形式を使う
- **depends の構造化形式**: `depends = [{ task = "setup", args = ["--prod"], env = { NODE_ENV = "production" } }]` で args/env を渡せる
- **env は依存に渡されない**: タスクの `env` はそのタスク専用。依存タスクに渡すには depends の構造化形式を使う
- **sources/outputs でスキップ**: `outputs = { auto = true }` がデフォルト。sources 変更なしならタスクをスキップ
- **usage 引数のアクセス**: `run` 内では `usage_` プレフィックスの環境変数（`$usage_name`）を使う。Tera（`{{ usage.name }}`）は flag 未指定時にエラーになるため `run` では使わない。Tera は `depends` の引数フォワーディング（`args = ["{{usage.app}}"]`）等シェルを通さない場面で使う
- **usage の flag 名変換**: `--dry-run` → `$usage_dry_run`（ハイフンをアンダースコア）
- **タスク実行時の環境変数**: `$MISE_PROJECT_ROOT`（プロジェクトルート）、`$MISE_CONFIG_ROOT`（タスク定義ファイルのディレクトリ）、`$MISE_ORIGINAL_CWD`（`mise run` 実行時の cwd）、`$MISE_TASK_NAME`（タスク名）が渡される
- **`{{config_root}}` はサブパッケージのルート**: monorepo のサブパッケージ（例: `backend/mise.toml`）内で `{{config_root}}` を使うと `$MISE_CONFIG_ROOT` と同じ（`backend/`）。プロジェクトルートではない。サブパッケージのタスクをルートから `mise run //backend:dev` で呼んでも cwd はサブパッケージになる
- **`dir` でタスク実行時環境変数は使えない**: `dir` は Tera テンプレートで評価されるが、`MISE_PROJECT_ROOT` 等のタスク実行時注入変数はまだ未定義のためエラーになる。サブパッケージからプロジェクトルートを参照するには、ルートの `[env]` で `PROJECT_ROOT = "{{config_root}}"` を定義し、サブパッケージで `dir = "{{env.PROJECT_ROOT}}"` とする（ルートの `{{config_root}}` = プロジェクトルート）
- **usage 構文はコマンド名を含めない**: `usage = 'arg "<tag>"'` が正しい。`usage = "push <tag>"` のようにコマンド名を含めるとパースエラーになる

## References

詳細構文は以下を参照:

- タスクプロパティ全般 → [references/task-config.md](references/task-config.md)
- monorepo設定・集約パターン → [references/monorepo.md](references/monorepo.md)
- 引数定義（usage構文） → [references/arguments.md](references/arguments.md)
- Tera テンプレート（関数・フィルター・変数） → [references/templates.md](references/templates.md)
- 環境変数（[env] セクション） → [references/environments.md](references/environments.md)
