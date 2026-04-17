# Progressive Disclosure

一次情報: https://agentskills.io/specification#progressive-disclosure

スキルは context を効率的に使うため3層構造でロードする。

## 3層モデル

| 層 | 内容 | タイミング | 目安 |
|---|---|---|---|
| 1. Metadata | `name` / `description` | 起動時、**全スキル分** | ~100 tokens |
| 2. Instructions | `SKILL.md` 本文 | スキル活性化時 | **< 5000 tokens 推奨** |
| 3. Resources | `scripts/` `references/` `assets/` 配下 | 必要時に個別ロード | 任意 |

## サイズガイド

- **SKILL.md は 500 行以下推奨**
- 本文 5000 tokens を超えそうなら詳細を `references/` へ分離
- `description` は起動時に全スキル分ロードされる。検索ヒット性を左右する最重要フィールド

## ファイル参照

相対パスで SKILL.md から **1階層まで**:

```markdown
See [the reference guide](references/REFERENCE.md) for details.
Run the script: scripts/extract.py
```

深くネストした参照チェーンは避ける。

## 判断基準：インライン vs 別ファイル

| 状況 | 置き場所 |
|---|---|
| 原則・核心概念（短い） | `SKILL.md` インライン |
| 50行未満のコード例 | `SKILL.md` インライン |
| 100行超の詳細リファレンス | `references/` |
| 再利用可能な実行コード | `scripts/` |
| テンプレ・画像・データ | `assets/` |
