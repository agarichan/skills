# Tera Templates Reference

mise.toml 内で使える Tera テンプレートの関数・フィルター・変数。`[env]` の初期化や `dir` の指定等で活用する。

公式ドキュメント: https://mise.jdx.dev/templates.html

## 変数

| 変数 | 型 | 説明 |
|------|------|------|
| `env` | HashMap | 現在の環境変数 |
| `config_root` | PathBuf | mise.toml があるディレクトリ |
| `cwd` | PathBuf | カレントディレクトリ |
| `mise_bin` | String | mise 実行ファイルのパス |
| `mise_pid` | String | mise プロセスの PID |
| `mise_env` | Vec | `MISE_ENV` / `-E` / `--env` の値 |
| `xdg_cache_home` | PathBuf | XDG キャッシュディレクトリ |
| `xdg_config_home` | PathBuf | XDG 設定ディレクトリ |
| `xdg_data_home` | PathBuf | XDG データディレクトリ |
| `tools` | HashMap | インストール済みツール情報 |

タスク内のみ: `usage` (パース済み引数/フラグ)

## 関数

### よく使うもの

```toml
[env]
# コマンド出力を取得
GIT_SHA = "{{ exec(command='git rev-parse --short HEAD') }}"

# キャッシュ付き（重い処理向け）
DEPS = "{{ exec(command='expensive-cmd', cache_key='deps', cache_duration='1d') }}"

# 環境変数をデフォルト付きで取得
NODE_VER = "{{ get_env(name='NODE_VERSION', default='20') }}"

# ファイル内容を読む
VERSION = "{{ read_file(path='VERSION') | trim }}"
```

### システム情報

```toml
[env]
ARCH = "{{ arch() }}"           # x64, arm64
OS = "{{ os() }}"               # linux, macos, windows
OS_FAMILY = "{{ os_family() }}" # unix, windows
CPUS = "{{ num_cpus() }}"
```

### その他

| 関数 | 説明 |
|------|------|
| `range(end, start=0, step_by=1)` | 整数配列を生成 |
| `now(timestamp=false, utc=false)` | 現在時刻 |
| `choice(n, alphabet)` | ランダム文字列生成 |
| `throw(message)` | エラーを投げる |

## フィルター

### パス操作

```toml
[env]
PROJECT_NAME = "{{ cwd | basename }}"
PARENT_DIR = "{{ config_root | dirname }}"
CONFIG_FILE = "{{ [config_root, 'config.json'] | join_path }}"
```

| フィルター | 説明 |
|-----------|------|
| `basename` | ファイル名を抽出 |
| `dirname` | ディレクトリパスを返す |
| `extname` | 拡張子を返す |
| `file_stem` | 拡張子なしのファイル名 |
| `file_size` | ファイルサイズ（バイト） |
| `last_modified` | 最終更新時刻 |
| `join_path` | パス配列を結合 |
| `absolute` | 絶対パスに変換 |
| `canonicalize` | 正規化（存在しないとエラー） |

### 文字列操作

| フィルター | 説明 |
|-----------|------|
| `trim` / `trim_start` / `trim_end` | 空白除去 |
| `lower` / `upper` | 大文字小文字変換 |
| `replace(from, to)` | 置換 |
| `split(pat)` | 分割 → 配列 |
| `quote` | クォート |
| `urlencode` | URL エンコード |
| `kebabcase` / `snakecase` / `shoutysnakecase` | ケース変換 |
| `lowercamelcase` / `uppercamelcase` | キャメルケース変換 |

### 配列

| フィルター | 説明 |
|-----------|------|
| `first` / `last` | 先頭/末尾要素 |
| `join(sep)` | 結合 |
| `length` | 長さ |
| `reverse` | 逆順 |
| `concat(with)` | 配列に追加 |

### ハッシュ

```toml
[env]
HASH = '{{ "input" | hash }}'                    # SHA256（デフォルト）
SHORT = '{{ "input" | hash(len=8) }}'             # 先頭8文字
FILE_HASH = '{{ "path/to/file" | hash_file }}'    # BLAKE3
```

### その他

| フィルター | 説明 |
|-----------|------|
| `default(value)` | 未定義/空なら value を返す |
| `date(format)` | 日時フォーマット |
| `filesizeformat` | 人間可読なファイルサイズ |
| `abs` | 絶対値 |

## テスト

条件分岐で使用:

```toml
[env]
# ファイル存在チェック
_.LOCAL_ENV = '{% if ".env.local" is exists %}{{ read_file(path=".env.local") }}{% endif %}'
```

| テスト | 説明 |
|--------|------|
| `is file` | ファイルか |
| `is dir` | ディレクトリか |
| `is exists` | 存在するか |
| `is defined` | 変数が定義済みか |
| `is string` / `is number` | 型チェック |
| `is starting_with(pat)` | 前方一致 |
| `is ending_with(pat)` | 後方一致 |
| `is containing(pat)` | 含むか |
| `is matching(pat)` | 正規表現マッチ |
