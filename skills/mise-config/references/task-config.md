# Task Configuration Reference

mise.toml の `[tasks]` セクションで使える全プロパティ。

公式ドキュメント: https://mise.jdx.dev/tasks/task-configuration.html

## run

タスクの実行内容。文字列または配列。

```toml
# 文字列
[tasks.build]
run = "cargo build --release"

# 配列: スクリプトとタスク参照を混在可
[tasks.deploy]
run = [
  { task = "build" },
  { task = "test", args = ["--release"], env = { CI = "true" } },
  { tasks = ["lint", "typecheck"] },  # 並列実行
  "echo 'deploying...'",
]
```

**`task` (単数) vs `tasks` (複数) の違い:**

| 形式 | 実行 | `args` / `env` |
|------|------|-----------------|
| `{ task = "x" }` | 逐次（1つ） | 指定可 |
| `{ tasks = ["x", "y"] }` | 並列 | **指定不可** |

並列 + 引数転送が必要な場合は `depends` の構造化形式を使う:

```toml
[tasks."push:all"]
usage = 'arg "<tag>"'
depends = [
  { task = "push", args = ["{{usage.tag}}"] },
  { task = "other:push", args = ["{{usage.tag}}"] },
]
```

`run_windows` でWindows固有のコマンドを指定可。

## depends / depends_post / wait_for

```toml
# 文字列・配列
[tasks.test]
depends = ["build", "lint"]

# インライン環境変数
[tasks.test]
depends = ["NODE_ENV=test setup"]

# 構造化形式: args/env を渡す
[tasks.deploy]
depends = [
  { task = "build", args = ["--release"], env = { NODE_ENV = "production" } }
]

# 親引数のフォワーディング
[tasks.deploy]
usage = 'arg "<app>"'
depends = [{ task = "build", args = ["{{usage.app}}"] }]

# depends_post: タスク完了後に実行
[tasks.build]
depends_post = ["notify"]

# wait_for: 同じ mise run 内で対象が走っていれば完了を待つ。
# depends と違い対象を自動起動しない。単独実行時は何も待たない。
[tasks.test]
wait_for = ["setup"]
```

## env

タスク固有の環境変数。**依存タスクには渡されない**。

```toml
[tasks.test]
env = { NODE_ENV = "test", DEBUG = "true" }
run = "npm test"
```

## tools

タスク固有のツール。そのタスクのみにスコープ。

```toml
[tasks.build]
tools = { node = "20", python = "3.12" }
run = "npm run build"
```

## dir

実行ディレクトリ。デフォルトは `{{ config_root }}`。

```toml
[tasks.frontend-build]
dir = "{{ config_root }}/frontend"
run = "npm run build"
```

## sources / outputs

ファイルベースのタスクスキップ。sources が変更されていなければスキップ。

```toml
[tasks.build]
sources = ["src/**/*.rs", "Cargo.toml"]
outputs = ["target/release/myapp"]
run = "cargo build --release"

# auto outputs (デフォルト): 内部的にハッシュで追跡
[tasks.lint]
sources = ["src/**/*.ts"]
outputs = { auto = true }
run = "eslint src/"
```

依存タスクの sources が変更されて再実行された場合、依存元タスクも再実行される。

## description / alias

```toml
[tasks.build]
description = "Build the project for production"
alias = ["b", "compile"]
run = "cargo build --release"
```

## shell

シェルの指定。デフォルトはプラットフォーム依存。

```toml
[tasks.script]
shell = "python"
run = "print('hello')"
```

## 出力制御

```toml
[tasks.quiet-task]
quiet = true   # mise自体の出力を抑制、タスク出力は表示

[tasks.silent-task]
silent = true           # 全出力を抑制
# silent = "stdout"     # stdout のみ抑制
# silent = "stderr"     # stderr のみ抑制

[tasks.hidden-task]
hide = true    # mise tasks の一覧に表示しない
```

## raw / interactive

```toml
[tasks.repl]
raw = true          # stdin/stdout/stderr を直接接続（並列実行に注意）

[tasks.wizard]
interactive = true  # 排他的にstdin/stdout/stderrをロック
```

## confirm

実行前の確認プロンプト。依存タスクは確認**前**に実行される。

```toml
[tasks.deploy]
confirm = "Deploy to production?"

[tasks.deploy]
confirm = { message = "Deploy {{usage.env}}?", default = "n" }
```

## vars

タスク間で共有する変数。環境変数としては渡されない。

```toml
[vars]
e2e_args = "--headless"

[tasks.test]
vars = { e2e_args = "--headed" }  # タスクレベルで上書き
run = './scripts/test-e2e.sh {{vars.e2e_args}}'
```

## task_config

```toml
[task_config]
dir = "{{cwd}}"  # デフォルトの実行ディレクトリ

# ファイルタスクの検索パス追加
includes = [
  "custom-tasks",                    # ローカルディレクトリ
  "shared-tasks.toml",              # TOML ファイル
  # Remote (experimental)
  "git::https://github.com/org/tasks.git//tasks?ref=main",
]
```

デフォルト検索ディレクトリ: `mise-tasks`, `.mise-tasks`, `.mise/tasks`, `.config/mise/tasks`, `mise/tasks`

## redactions (experimental)

センシティブ情報を出力からマスク。

```toml
redactions = ["API_KEY", "PASSWORD"]
redactions = ["SECRETS_*"]  # glob 対応
```

## 設定項目

`[settings]` または `~/.config/mise/config.toml` で設定:

| 設定 | デフォルト | 説明 |
|------|-----------|------|
| `task.output` | — | `prefix`, `interleave`, `keep-order`, `replacing`, `timed`, `quiet`, `silent` |
| `task.timeout` | — | グローバルタイムアウト |
| `task.timings` | — | タスクごとの経過時間を表示 |
| `task.skip` | `[]` | スキップするタスク名 |
| `task.skip_depends` | `false` | 依存タスクをスキップ |
| `task.show_full_cmd` | `false` | コマンド全文を表示 |
| `task.run_auto_install` | `true` | ツール自動インストール |
