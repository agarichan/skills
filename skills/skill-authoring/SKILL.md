---
name: skill-authoring
description: >
  Use when creating, editing, reviewing, naming, or restructuring an
  Agent Skill (SKILL.md / スキル) — even if the user doesn't say
  "Agent Skills" but is working in a skill directory, designing
  skill metadata, or asking to fix/improve a skill that didn't
  trigger or behaved unexpectedly. Provides the official specification, progressive
  disclosure model, and description-optimization methodology.
---

# Agent Skills 公式仕様リファレンス

Agent Skills は Anthropic 発のオープン標準。エージェントにスキル（手順・知識・リソースのフォルダ）を与えるフォーマット。Claude Code / Cursor / Gemini CLI / OpenCode 等が対応。

## 一次情報

- 仕様: https://agentskills.io/specification
- 概要: https://agentskills.io/what-are-skills
- 公式サンプル: https://github.com/anthropics/skills
- エコシステム: https://agentskills.io

## 最小構成

```
skill-name/
├── SKILL.md      # 必須。メタデータ + 手順
├── scripts/      # 任意。実行可能コード
├── references/   # 任意。追加ドキュメント
└── assets/       # 任意。テンプレ・画像・データ等
```

## 詳細

- Frontmatter 全フィールド、命名規則、本文、validation → [references/specification.md](references/specification.md)
- Progressive disclosure の3層モデル、サイズ目安、ファイル参照規則 → [references/progressive-disclosure.md](references/progressive-disclosure.md)
- description の最適化（4原則、クエリ設計による紙面レビュー） → [references/optimizing-descriptions.md](references/optimizing-descriptions.md)
- ベストプラクティス（coherent unit、命令の強弱、gotchas、validation loop、plan-validate-execute 等） → [references/best-practices.md](references/best-practices.md)

## オリジナル追加ルール（公式仕様より厳しい独自制約）

スキルを新規作成・編集する際、公式仕様に加えて以下を守る:

- **`SKILL.md` は 100 行以内**
- **`references/` 配下は 1 ファイルあたり 500 行以内**

いずれも超過しそうな場合は、さらなる分割（`references/` への切り出し、複数ファイル化）を検討する。
