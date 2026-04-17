# Task Arguments Reference

mise タスクの引数定義。`usage` フィールドを使う。

公式ドキュメント: https://mise.jdx.dev/tasks/task-arguments.html

## usage フィールド（推奨）

### 位置引数 (arg)

```toml
[tasks.deploy]
usage = '''
arg "<environment>" env="DEPLOY_ENV" help="Target environment" default="staging"
arg "<region>" env="AWS_REGION" help="AWS region" default="us-east-1"
'''
run = 'echo "Deploying to ${usage_environment?} in ${usage_region?}"'
```

| 構文 | 意味 |
|------|------|
| `arg "<name>"` | 必須引数 |
| `arg "[name]"` | オプション引数 |
| `arg "<name>" default="value"` | デフォルト値 |
| `arg "<name>" env="VAR_NAME"` | 環境変数からも受け取る |
| `arg "<name>" { choices "a" "b" "c" }` | 選択肢 |
| `arg "[files]" var=#true` | 可変長（0個以上） |
| `arg "<files>" var=#true` | 可変長（1個以上） |
| `arg "<files>" var=#true var_min=2` | 最小個数 |
| `arg "<files>" var=#true var_max=5` | 最大個数 |
| `arg "<file>"` | ファイル名補完 |
| `arg "<dir>"` | ディレクトリ補完 |
| `arg "<name>" hide=#true` | ヘルプに非表示 |
| `arg "<name>" long_help="..."` | 詳細ヘルプ |
| `arg "<name>" double_dash="required"` | `--` 必須 |
| `arg "<name>" double_dash="optional"` | `--` オプション |
| `arg "<name>" double_dash="automatic"` | 最初の引数後に自動 |

### フラグ (flag)

```toml
[tasks.build]
usage = '''
flag "-p --profile <profile>" env="BUILD_PROFILE" help="Build profile" default="dev"
flag "-v --verbose" help="Verbose output"
'''
run = 'cargo build --profile ${usage_profile?}'
```

| 構文 | 意味 |
|------|------|
| `flag "-f --force"` | ブール型 |
| `flag "-f"` | ショートのみ |
| `flag "--force"` | ロングのみ |
| `flag "-o --output <file>"` | 値を受け取る |
| `flag "--port <port>" default="8080"` | デフォルト値 |
| `flag "-v --verbose" count=#true` | カウント（`-vvv` → 3） |
| `flag "--color" negate="--no-color"` | 否定フラグ |
| `flag "--verbose" global=#true` | サブコマンド全体で有効 |
| `flag "--debug" hide=#true` | ヘルプに非表示 |
| `flag "--color <when>" { choices "auto" "always" "never" }` | 選択肢 |

### 補完 (complete)

```toml
[tasks.plugin]
usage = '''
complete "plugin" run="mise plugins ls"
complete "plugin" run="cmd" descriptions=#true
'''
```

## File task ヘッダー

スクリプト形式のタスクでは `#MISE` / `#USAGE` コメントを使う:

```bash
#!/usr/bin/env bash
#MISE description "Deploy application"
#USAGE arg "<environment>" env="DEPLOY_ENV" help="Target environment"
#USAGE flag "--dry-run" help="Preview mode"

ENVIRONMENT="${usage_environment?}"
DRY_RUN="${usage_dry_run:-false}"
```

## 引数アクセス方法

`run` 内では環境変数を使う。Tera は `depends` の引数フォワーディング等シェルを通さない場面で使う。

**環境変数**（`run` 内で使用）: `usage_` プレフィックス + スネークケース
- `arg "<environment>"` → `$usage_environment`
- `flag "--dry-run"` → `$usage_dry_run`（ハイフン → アンダースコア）

**Tera テンプレート**（`depends` の `args` 等で使用）: `{{ usage.name }}`
- 例: `depends = [{ task = "build", args = ["{{usage.app}}"] }]`
- `run` 内で使うと flag 未指定時にエラーになるため非推奨

### 変数展開パターン

| パターン | 動作 |
|----------|------|
| `${var?}` | 未設定ならエラー |
| `${var:?}` | 未設定/空ならエラー |
| `${var:-default}` | 未設定ならデフォルト |
| `${var:=default}` | 未設定ならデフォルトをセットして使用 |
| `${var:+value}` | 設定済みなら value を使用 |

## 優先順位

CLI引数 > 環境変数（`env="VAR"`） > デフォルト値

