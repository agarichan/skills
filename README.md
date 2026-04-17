# skills リポジトリ

このディレクトリは、`npx skills` で配布できる Agent Skills リポジトリ構成になっています。

## 現在の構成

```text
skills/
  mise-config/
    SKILL.md
    references/
  codex-cli-runtime/
    SKILL.md
    .claude-plugin/plugin.json
    scripts/
    prompts/
    schemas/
  codex-result-handling/
    SKILL.md
  codex-task-delegate/
    SKILL.md
    scripts/
  gpt-5-4-prompting/
    SKILL.md
    references/
```

- `mise-config`: 既存の実用スキル
- `codex-cli-runtime`: Codex companion 呼び出し契約の日本語移植（内部向け、`mjs` ランタイム同梱）
- `codex-result-handling`: Codex 出力整形ルールの日本語移植（内部向け）
- `codex-task-delegate`: 指示ファイルまたは直接テキストを `codex_wrapper.py` 経由で Codex へ委譲する実行スキル
- `gpt-5-4-prompting`: Codex/GPT-5.4 向けプロンプト設計ガイドの日本語移植（内部向け）

## 配布手順

1. このディレクトリを Git で管理し、GitHub（または対応する Git ホスト）へ push します。
2. 別環境でリポジトリ全体をインストールします。

```bash
npx skills add <owner>/<repo>
```

3. 特定のスキルだけ入れたい場合は `--skill` を使います。

```bash
npx skills add <owner>/<repo> --skill mise-config
```

4. リポジトリ内の配布対象スキルを一覧表示するには `--list` を使います。

```bash
npx skills add <owner>/<repo> --list
```

## Codex薄いラッパー

`skills/codex-task-delegate/scripts/codex_wrapper.py` は、`codex exec` の薄いラッパーです。  
目的は次の2つだけです。

- ローカル状態管理（`.codex-wrapper/state.json`）
- 出力のJSON整形（CC側で扱いやすい固定フォーマット）

主なコマンド（`skills/codex-task-delegate` に移動して実行）:

```bash
cd skills/codex-task-delegate

# 新規タスク委譲
./scripts/codex_wrapper.py delegate --cwd "<workspace>" --check-in-seconds 180 "<task>"

# 途中経過から再接続（最大180秒待つ）
./scripts/codex_wrapper.py reconnect --thread-id <thread_id> --wait-seconds 180

# 問題があればキャンセル
./scripts/codex_wrapper.py cancel --thread-id <thread_id>

# 同一スレッドにフィードバック
./scripts/codex_wrapper.py feedback --thread-id <thread_id> "案2で実装して、影響範囲のテストも実行して"

# 最新スレッドの状態確認
./scripts/codex_wrapper.py status

# 最新スレッドの最終メッセージだけ表示
./scripts/codex_wrapper.py result --raw
```

補足:

- `feedback` は内部的に `codex exec resume <thread_id>` を使います。
- `--check-in-seconds` は進行中の安全確認ポイントです。意図どおりなら `reconnect`、意図とズレたら `cancel` で止めます。
- `--check-in-seconds 0` は安全確認ポイントを無効化します（意図ズレ検知が効かない）。
- `feedback/status/result` は `--thread-id` で対象を指定できます（必要なら `--cwd` も併用可）。
- `--model`, `--sandbox`, `--profile` など一部オプションはそのまま `codex exec` に渡します。

## 自作スキルの追加方法

`skills/<skill-name>/` 配下に新しいフォルダを作成し、最低でも次を用意してください。

- `SKILL.md`（YAML frontmatter に `name` と `description` を含める）
- 必要に応じて `agents/openai.yaml`
- 必要に応じて `scripts/`、`references/`、`assets/`

既存の `skills/mise-config` を参考にして、同階層へ新しいスキルを追加してください。
