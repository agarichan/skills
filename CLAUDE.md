# Skills リポジトリ

Claude Code 向け Agent Skills のソースリポジトリ。

## 構成

```
skills/<skill-name>/
  SKILL.md              # スキル本体（YAML frontmatter + 本文）
  references/           # スキルが参照するデータファイル
  scripts/              # ヘルパースクリプト
```

## スキルの更新フロー

1. `skills/<skill-name>/` 以下のファイルを編集
2. コミット & push
3. `npx skills add agarichan/skills --skill <skill-name> --yes` で再インストール

外部レジストリ等からデータを取得して `references/` を更新する場合も同じ手順。

## orbit-ui スキル

コンポーネント一覧 (`references/components.md`) はレジストリ `https://orbit-ui.pages.dev/r/registry.json` から生成。更新時は最新の registry.json を取得して差分を反映する。
