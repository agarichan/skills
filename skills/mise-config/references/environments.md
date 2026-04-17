# Environment Variables Reference

mise.toml の `[env]` セクションで環境変数を管理する。

公式ドキュメント: https://mise.jdx.dev/environments/

## 基本構文

```toml
[env]
NODE_ENV = "production"
PORT = 3000
DEBUG = true
REMOVED_VAR = false  # 環境変数を削除
```

## 特殊ディレクティブ（`_` プレフィックス）

### _.file — 外部ファイルの読み込み

```toml
[env]
_.file = ".env"
_.file = [".env", ".env.local"]
_.file = { path = ".secrets.env", redact = true }
_.file = { path = ".env", tools = true }  # ツール初期化後に評価
```

dotenv, JSON, YAML に対応。

### _.path — PATH への追加

```toml
[env]
_.path = "./bin"
_.path = ["~/.local/share/bin", "tools/bin"]
_.path = { path = ["{{env.GEM_HOME}}/bin"], tools = true }
```

`config_root` からの相対パスで解決。

### _.source — シェルスクリプトの読み込み

```toml
[env]
_.source = "./script.sh"
_.source = { path = "setup.sh", redact = true }
```

`source ./script.sh` として実行し、export された変数を取得。

### 複数ディレクティブ

同じキーを複数回使うには `[[env]]` 構文:

```toml
[[env]]
_.source = "./script_1.sh"
[[env]]
_.source = "./script_2.sh"
```

## Tera テンプレート

```toml
[env]
LD_LIBRARY_PATH = "/some/path:{{env.LD_LIBRARY_PATH}}"
PROJECT_ROOT = "{{config_root}}"
VERSION = "{{ exec(command='git describe --tags') }}"
NAME = "{{ cwd | basename }}"
```

詳細は [templates.md](templates.md) を参照。

## tools = true（遅延評価）

ツール初期化後に評価。ツールが提供する環境変数にアクセスできる:

```toml
[env]
MY_VAR = { value = "{{env.PATH}}", tools = true }
NODE_VER = { value = "{{ tools.node.version }}", tools = true }
```

## redact（機密情報のマスク）

```toml
[env]
SECRET = { value = "my_secret", redact = true }
_.file = { path = ".secrets.env", redact = true }

# glob パターンでまとめてマスク
redactions = ["SECRET_*", "*_TOKEN", "PASSWORD"]
```

## required（必須変数）

```toml
[env]
DATABASE_URL = { required = true }
API_KEY = { required = "https://example.com/api-keys から取得" }
```

通常コマンドではエラー、シェル activate 時は警告のみ。

## シェル展開

```toml
[settings]
env_shell_expand = true

[env]
LD_LIBRARY_PATH = "$MY_PROJ_LIB:$LD_LIBRARY_PATH"
FALLBACK = "${MISSING_VAR:-default_value}"
```

`$VAR`, `${VAR}`, `${VAR:-default}`, `${VAR:-}` に対応。

## タスク内の env

```toml
[tasks.test]
env = { NODE_ENV = "test", _.file = ".env.test" }
run = "npm test"
```

タスクの `env` はそのタスク専用。依存タスクには渡されない。
