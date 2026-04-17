# SKILL.md Specification

一次情報: https://agentskills.io/specification

## Frontmatter 全フィールド

| Field | Required | Constraints |
|---|---|---|
| `name` | Yes | 1–64字、小文字 a-z + 数字 + `-` のみ、先頭末尾 `-` 不可、`--` 連続不可、**親ディレクトリ名と一致** |
| `description` | Yes | 1–1024字、「何をするか」＋「いつ使うか」両方、検索用キーワードを含める |
| `license` | No | ライセンス名 or バンドル済ファイル参照 |
| `compatibility` | No | 最大500字、環境要件（対象製品・パッケージ・ネット可否等） |
| `metadata` | No | 任意 key-value マップ（キー名は衝突回避のため一意に） |
| `allowed-tools` | No | 事前承認ツールの空白区切り文字列（experimental） |

最小例:
```yaml
---
name: pdf-processing
description: Extract PDF text, fill forms, merge files. Use when handling PDFs.
---
```

拡張例:
```yaml
---
name: pdf-processing
description: Extract PDF text, fill forms, merge files. Use when handling PDFs.
license: Apache-2.0
metadata:
  author: example-org
  version: "1.0"
---
```

## name の規則

- 小文字 `a-z` + 数字 + `-` のみ（1–64字）
- 先頭末尾のハイフン禁止
- `--` 連続禁止
- **ディレクトリ名と一致必須**

OK: `pdf-processing`, `data-analysis`, `code-review`
NG: `PDF-Processing`（大文字）, `-pdf`（先頭）, `pdf--processing`（連続）

## description の書き方

「何をするか」＋「いつ使うか」両方。検索キーワードを含める。

- Good: `Extracts text and tables from PDF files, fills PDF forms, and merges multiple PDFs. Use when working with PDF documents or when the user mentions PDFs, forms, or document extraction.`
- Poor: `Helps with PDFs.`

## compatibility の使い所

環境要件がある場合のみ記述（多くのスキルは不要）:

- `Designed for Claude Code (or similar products)`
- `Requires git, docker, jq, and access to the internet`
- `Requires Python 3.14+ and uv`

## allowed-tools（experimental）

事前承認ツールの空白区切り。サポートは実装依存:
```yaml
allowed-tools: Bash(git:*) Bash(jq:*) Read
```

**書式・挙動は実装ごとに異なる**（Claude Code は YAML list もサポート／「制限ではなく事前承認」扱い、Codex は別ファイル `agents/openai.yaml` の `dependencies.tools` で管理、など）。各エージェントの詳細は [agentskills.io](https://agentskills.io) のエコシステム一覧から各 `instructionsUrl` を参照。

## 本文（Markdown body）

フォーマット制約なし。活性化時に全文ロードされる。推奨セクション:

- Step-by-step instructions
- Examples of inputs and outputs
- Common edge cases

## サブディレクトリ規約

| ディレクトリ | 用途 |
|---|---|
| `scripts/` | 実行可能コード（Python/Bash/JS等、実装依存） |
| `references/` | 詳細ドキュメント（`REFERENCE.md`等） |
| `assets/` | テンプレ・画像・データファイル |

## Validation

```bash
skills-ref validate ./my-skill
```
https://github.com/agentskills/agentskills/tree/main/skills-ref
