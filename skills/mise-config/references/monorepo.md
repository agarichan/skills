# Monorepo Task Reference

mise の monorepo モードでタスクを分散定義し、ルートで集約する。

公式ドキュメント: https://mise.jdx.dev/tasks/monorepo.html

## 有効化

ルート mise.toml に以下の**両方**が必要:

```toml
experimental_monorepo_root = true

[settings]
experimental = true
```

## config_roots

サブディレクトリを明示的に列挙する。自動検出は非推奨。

```toml
[monorepo]
config_roots = [
  "packages/frontend",
  "packages/backend",
  "services/*",       # 単一レベル glob のみ対応
]
```

- 再帰 glob (`**`) は**非対応**
- 新しいサブディレクトリに mise.toml を追加したら config_roots にも追加する

## タスク名前空間

サブディレクトリのタスクは自動的に `//path:task` でプレフィックスされる:

```
myproject/
├── mise.toml                    # ルート
├── packages/
│   ├── frontend/
│   │   └── mise.toml            # [tasks.build], [tasks.test], [tasks.lint]
│   └── backend/
│       └── mise.toml            # [tasks.build], [tasks.test], [tasks.lint]
```

生成されるタスク名:
- `//packages/frontend:build`
- `//packages/frontend:test`
- `//packages/backend:build`
- `//packages/backend:test`

## ルートでの集約パターン

**積極的に細かくタスク分割し、ルートで集約する。**

```toml
# ルート mise.toml — run の { tasks } で並列集約
[tasks.lint]
run = [{ tasks = ["//packages/frontend:lint", "//packages/backend:lint"] }]

[tasks.test]
run = [{ tasks = ["//packages/frontend:test", "//packages/backend:test"] }]

[tasks.build]
run = [{ tasks = ["//packages/frontend:build", "//packages/backend:build"] }]

[tasks.check]
run = [{ tasks = ["lint", "test", "build"] }]
```

## 現在の config root 参照

サブディレクトリ内で同じ config root のタスクを参照するには `:task` プレフィックス:

```toml
# packages/frontend/mise.toml
[tasks.build]
depends = [":lint"]  # 同じ config root の lint を参照（推奨）
# depends = ["lint"]  # これも動くが : を付ける方が明示的
run = "webpack build"
```

## ワイルドカード

### パスワイルドカード (`...`)

```bash
mise //...:test              # 全プロジェクトの test
mise //packages/...:build    # packages/ 配下全ての build
mise //.../api:build         # api を含む全パスの build
```

### タスク名ワイルドカード (`*`)

```bash
mise '//packages/frontend:*'       # frontend の全タスク
mise '//packages/frontend:test:*'  # test: で始まる全タスク
```

### 組み合わせ

```bash
mise '//...:*'        # 全プロジェクトの全タスク
mise '//...:test*'    # 全プロジェクトの test 系タスク
```

## ツール・環境変数のレイヤリング

優先順位: ルート < サブディレクトリ < タスク固有

```toml
# ルート mise.toml
[tools]
node = "20"
[env]
LOG_LEVEL = "info"

# packages/frontend/mise.toml
[tools]
node = "18"            # ルートの node 20 を上書き
[env]
LOG_LEVEL = "debug"    # ルートの LOG_LEVEL を上書き
PORT = "3000"          # 新規追加

# タスク固有
[tasks.build]
tools = { node = "22" }  # さらに上書き
env = { DEBUG = "true" }
run = "npm run build"
```

## task_templates

ルートで再利用可能なテンプレートを定義:

```toml
# ルート mise.toml
[task_templates."python:build"]
run = "uv build"
tools = { python = "3.12", uv = "latest" }

[task_templates."python:test"]
run = "pytest"
tools = { python = "3.12" }
depends = ["build"]
```

サブディレクトリで extends:

```toml
# packages/api/mise.toml
[tasks.build]
extends = "python:build"

[tasks.test]
extends = "python:test"
run = "pytest --cov"  # run を上書き
```

extends 時のマージルール:
- **完全上書き**: `run`, `depends`, `depends_post`, `wait_for`, `sources`, `outputs`, `description`, `shell`, `timeout`
- **ディープマージ**: `tools`, `env` はテンプレートとタスクの値を統合（タスク側が優先）

公式ドキュメント: https://mise.jdx.dev/tasks/templates.html

## trust 伝播

ルートが trust されていれば、全子孫の config も自動的に trust される。

## タスク一覧

```bash
mise tasks          # 現在の config root 階層のタスク
mise tasks --all    # monorepo 全体のタスク
mise tasks '//packages/frontend:*'  # 特定プロジェクトのタスク
```

## monorepo 設定項目

| 設定 | デフォルト | 説明 |
|------|-----------|------|
| `task.monorepo_depth` | `5` | サブディレクトリ検索の深さ |
| `task.monorepo_exclude_dirs` | `[]` | 除外ディレクトリ（未設定時: node_modules, target, dist, build） |
| `task.monorepo_respect_gitignore` | `true` | .gitignore を尊重 |
