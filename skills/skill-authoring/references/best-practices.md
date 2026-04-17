# ベストプラクティス

一次情報: https://agentskills.io/skill-creation/best-practices

スキルを「当たり前のことを書いた薄いドキュメント」にしないための指針。エージェントが **知らないこと** だけを、**適切な粒度** で、**壊れやすさに応じた強制力** で書く。

## 実体験から起こす

LLM 任せで "generic best practices" から起こしたスキルは陳腐化する。以下を元にすると質が段違い:

- **実タスク由来**: エージェントと一緒に実タスクをこなし、成功手順・入れた修正・入出力形式・与えた文脈を **パターンとして抽出**
- **既存 artifacts 合成**: runbook / スタイルガイド / issue tracker / git history / 障害報告から合成。**プロジェクト固有の** schema・失敗モード・復旧手順を拾える
- **実行フィードバック**: 最初のドラフトを実タスクで試し、false positive / 漏れ / 不要部分を見て **execute → revise** を 1 回でも回す

> Tip: 実行トレースも読む。エージェントが無駄なステップを踏むなら、指示が曖昧／今タスクに不適用なのに読んでいる／デフォルトが示されていない、のいずれか。

## Context の使い方

### エージェントが知らないことだけ書く

PDF とは何か、HTTP とは何か、は書かない。**プロジェクト固有の規約・ドメイン手順・非自明なエッジケース・使うべきツール** だけ書く。

```markdown
<!-- 冗長: エージェントは PDF を知っている -->
PDF (Portable Document Format) は...。text 抽出にはライブラリが必要で...

<!-- 良い: 知らない部分に直行 -->
Use pdfplumber for text extraction. For scanned docs, fall back to pdf2image + pytesseract.
```

各内容に対して「この指示がないとエージェントは誤るか？」と自問。答えが No なら削る。

### Coherent unit で設計

関数の責務と同じ。狭すぎると複数スキルが同時にロードされて衝突、広すぎると発動精度が落ちる。**DB クエリ + 結果整形** は coherent、**DB クエリ + DB 管理** は広すぎ。

### 過剰詳細を避ける

全エッジケースを網羅すると、エージェントは今タスクに関係ない指示に引っ張られる。**簡潔な手順 + 動く例** が exhaustive doc より機能する。

## 命令の強弱を調整

### 壊れやすさに specificity を合わせる

| 状況 | 書き方 |
|---|---|
| 複数正解あり + 耐性あり | 柔軟に。**"why" を説明** して判断させる |
| 脆弱・順序が重要・一貫性必須 | **prescriptive**（"Run exactly this sequence"、"Do not modify"） |

同じスキル内でもパートごとに強弱を切り替える。

### メニューではなくデフォルトを

「A/B/C/D どれでも OK」ではなく **1 つのデフォルト + エスケープハッチ**:

```markdown
<!-- 悪い -->
You can use pypdf, pdfplumber, PyMuPDF, or pdf2image...

<!-- 良い -->
Use pdfplumber for text extraction. For scanned PDFs, use pdf2image + pytesseract instead.
```

### 手順 > 宣言（how-to > what-to-produce）

特定回答を書くのではなく、**このクラスの問題の approach** を教える:

```markdown
<!-- 悪い: 今回しか使えない -->
Join `orders` to `customers` on `customer_id`, filter region='EMEA'...

<!-- 良い: 再利用可能 -->
1. schema.yaml から関連テーブルを特定
2. `_id` 外部キー規約で join
3. ユーザー要求に応じた WHERE
4. 数値列を集約、markdown table で返す
```

## パターン集

### Gotchas セクション

**環境固有の非自明事実**。多くのスキルで最高価値の部分。一般論（"handle errors"）ではなく具体的:

```markdown
## Gotchas

- `users` テーブルはソフト削除。`WHERE deleted_at IS NULL` 必須
- user ID は DB で `user_id`、auth サービスで `uid`、billing API で `accountId`。全部同じ値
- `/health` は web server が生きてれば 200（DB 切断時も）。full check は `/ready`
```

エージェントが間違った時、その修正を **SKILL.md の gotchas に追記** するのが最も効く改善方法。

### 出力フォーマットのテンプレート

散文で「こう書け」と説明するより、**構造テンプレート** を示す方がパターンマッチが効く。短いものはインライン、長いものは `assets/` へ配置。

### チェックリスト

多段ワークフローで step 飛ばしを防ぐ:

```markdown
Progress:
- [ ] Step 1: 解析（`scripts/analyze.py`）
- [ ] Step 2: マッピング作成
- [ ] Step 3: 検証（`scripts/validate.py`）
- [ ] Step 4: 実行
- [ ] Step 5: 出力検証
```

### Validation loop

**作業 → バリデータ実行 → 失敗なら修正 → 再実行** を明示:

```markdown
1. 編集
2. `python scripts/validate.py` 実行
3. 失敗なら: エラー確認 → 修正 → 再実行
4. pass するまで進めない
```

バリデータはスクリプトでも「チェックリスト照合」でもよい。

### Plan-validate-execute

**バッチ処理・破壊的操作** で効く。中間成果物を作り、source of truth と突合してから実行:

```markdown
1. フィールド抽出: `analyze_form.py input.pdf` → form_fields.json
2. `field_values.json` を作成
3. 検証: `validate_fields.py` で form_fields.json と突合
4. 失敗なら修正して再検証
5. OK なら実行
```

エラーメッセージに「利用可能なフィールドの候補」を含めると、エージェントの自己修正が回る。

### 再利用可能スクリプトを `scripts/` に bundle

複数テストケースのトレースで **同じロジックを毎回エージェントが再発明** しているなら、スクリプトに切り出して bundle する。テスト済みのコードを 1 回書く方が、毎回 LLM に生成させるより安定・安価。
