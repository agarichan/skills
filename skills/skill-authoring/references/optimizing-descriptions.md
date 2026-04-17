# description の最適化（紙面レビュー版）

一次情報: https://agentskills.io/skill-creation/optimizing-descriptions

> 公式には `claude -p` で trigger rate を実測する eval ループが紹介されているが、コストが重い（~300 回の LLM 呼び出し）。本書は **実測せず紙面レビューで完結する範囲** に絞る。完全自動化したい場合は公式スキル `skill-creator` を参照。

スキルは起動時に `name` と `description` だけがロードされ、エージェントはそれで「このスキルを使うか」を判断する。description の質がトリガの全てを担う。

**重要な nuance**: 単純な1ステップ依頼（"read this PDF"）は、description が完璧でもトリガしないことが多い。エージェントが基本ツールで処理できるため。トリガが効くのは **専門知識・独特のワークフロー・特殊フォーマット** が絡むタスク。

## 効果的な description の 4 原則

1. **命令形で書く**: 「Use this skill when ...」の形。エージェントは行動判断中なので「いつ行動するか」を伝える
2. **ユーザーの意図に焦点**: 内部実装ではなく、ユーザーが達成したいことを書く
3. **やや押し付けがましく**: 適用コンテキストを明示列挙する。ユーザーがドメインを明示しない場合もカバー（例: "even if they don't explicitly mention 'CSV' or 'analysis'"）
4. **簡潔に**: 数文〜短い段落。[1024字のハード上限](https://agentskills.io/specification#description-field)

## Before/After 例

```yaml
# Before
description: Process CSV files.

# After
description: >
  Analyze CSV and tabular data files — compute summary statistics,
  add derived columns, generate charts, and clean messy data. Use this
  skill when the user has a CSV, TSV, or Excel file and wants to
  explore, transform, or visualize the data, even if they don't
  explicitly mention "CSV" or "analysis."
```

改善後は **「何をするか」が具体的**（summary stats / derived columns / charts / cleaning）で、**「いつ使うか」が広範**（CSV/TSV/Excel、キーワード無くても）。

## クエリ設計（思考実験用）

実測はしないが、**脳内でクエリを並べ、現 description がどこまでカバーするか目視する**。should-trigger と should-not-trigger を各 5–10 件程度で十分。

### Should-trigger queries（拾いたい）

以下の軸でバリエーションを作る:

- **Phrasing**: フォーマル／カジュアル／タイポや略語
- **Explicitness**: ドメイン名を明示するもの／しないもの
- **Detail**: 短い依頼／ファイルパス・列名・背景付きの長文
- **Complexity**: 単ステップ／多ステップの一部にスキル対象タスクが埋もれているケース

最も価値があるのは「スキルが役立つが、クエリだけ見ると繋がりが明白でない」もの。明白なら誰でもトリガするため description の工夫が効かない。

### Should-not-trigger queries（除外したい）

価値が高いのは **Near-miss**（キーワード共有するが別タスク）。

CSV 分析スキルの場合:

- ❌ 弱い例: `"Write a fibonacci function"`（キーワード重複なし、テストにならない）
- ✅ 強い例:
  - `"I need to update the formulas in my Excel budget spreadsheet"`（`spreadsheet`/`data` は共有、だが Excel 編集タスク）
  - `"csv を読んで postgres に upload する python を書いて"`（CSV 関連だが ETL タスク）

### リアリズムのコツ

- ファイルパス: `~/Downloads/report_final_v2.xlsx`
- 個人背景: `"my manager asked me to..."`
- 具体情報（列名、会社名、数値）
- カジュアル語・略語・タイポ

## 紙面レビュー手順

1. 現 description を **4 原則** でチェック（○/△/✗ を付ける）
2. should-trigger / should-not-trigger を各 5–10 件 **脳内列挙**
3. 現 description がどこまで拾えるか／誤発火しそうかを **表で目視**
4. 落ちる should-trigger / 誤発火しそうな should-not-trigger を特定
5. **revise**:
   - should-trigger が落ちる → 狭すぎる。スコープ拡大・適用コンテキスト追記
   - should-not-trigger で誤発火 → 広すぎる。境界を明記、隣接能力との差別化
   - **失敗クエリのキーワードそのものを足さない**（overfitting）。カテゴリ・概念レベルで対処
   - 詰まったら構造を根本から変える（incremental tweak ではなく re-framing）
6. 1024字以内を確認して適用
