---
name: orbit-ui
description: >
  Add Orbit UI components to a React project via shadcn-compatible registry.
  Use when the user asks to add UI components, build interfaces, or set up
  a design system using Orbit. Also use when the user asks about Orbit component
  APIs, props, or usage patterns. Triggers include: "orbit", "add button/input/tabs",
  "use the registry", "npx shadcn add", building UI with the Orbit component catalog,
  or asking how to use Orbit components.
allowed-tools: Bash(npx:*) Bash(pnpm:*) Bash(npm:*) Read
---

# Orbit UI

Orbit は `https://orbit-ui.pages.dev` でホストされている shadcn 互換コンポーネントレジストリ。

## 前提条件

プロジェクトに shadcn が初期化済みであること（`npx shadcn@latest init`）。
shadcn には Tailwind CSS と tsconfig.json の `@/*` import alias が必要 — 未設定なら先にセットアップする。

`registry:hook` アイテム（`use-scroll-lock` 等）を使うコンポーネントがあるため、
`components.json` に `aliases.hooks` が設定されている必要がある:

```jsonc
{
  "aliases": {
    "components": "@/components",
    "ui": "@/components/ui",
    "hooks": "@/hooks"   // ← 必須
  }
}
```

hook を依存に持つコンポーネント（modal, command-palette, code-viewer, data-table, file-browser）を
`npx shadcn add` すると hook も自動インストールされる。

## コンポーネントのインストール

```bash
npx shadcn@latest add "https://orbit-ui.pages.dev/r/<component>.json"
```

依存関係（`tokens`・`use-scroll-lock` 等）はフルURL の `registryDependencies` により自動解決される。
複数コンポーネントを 1 コマンドでまとめてインストール可能。

## トークンのセットアップ

コンポーネントインストール後、アプリのルートでトークン CSS をインポートする:

```tsx
import "@/components/ui/tokens.css"
```

`<html>` に `data-theme="dark"` または `data-theme="light"` を追加してテーマを切り替える。
tokens.css は shadcn の `--background`/`--foreground` を Orbit の値に自動ブリッジするため、body の手動上書きは不要。

## ワークフロー

1. shadcn が初期化済みか確認（`components.json` の存在チェック）
2. `components.json` に `aliases.hooks` があるか確認 — なければ追加
3. レジストリ URL でコンポーネントをインストール（tokens・hook は自動解決）
4. アプリルートで `tokens.css` をインポートし、`<html>` に `data-theme` を設定
5. 検証: `npx vite build`（またはフレームワーク相当）でエラーがないことを確認

## 利用可能なコンポーネント

全コンポーネントの一覧・説明・依存関係は [references/components.md](references/components.md) を参照。
最新の一覧は `https://orbit-ui.pages.dev/r/registry.json` から取得可能。

## 主要パターン

- コンポーネントは `tokens.css` の CSS カスタムプロパティを使用（Tailwind は shadcn CLI にのみ必要で、コンポーネントのスタイリングには不要）
- コンポーネントはプロジェクトにコピーされる（node_modules ではない）— 自由に編集可能
- コンポーネント間 import はレジストリ JSON 内で `@/registry/orbit-ui/<pkg>/<sub>` 形式で宣言されており、shadcn CLI がインストール時に利用者の aliases に応じてパスを自動解決する
- `Icon` は name prop でインライン SVG を切り替える。アイコン一覧はカタログを参照
- `modal` は flat 構造（`modal.tsx` + `modal.css`）。backdrop + container だけ提供し中身は自由
- `overlay` は flat prefix 構造（`overlay.tsx`, `overlay-dialog.tsx`, `overlay-toast.tsx`, `overlay.css`）。Dialog と Toast を提供
- `code-viewer` は flat prefix 構造（`code-viewer.tsx`, `code-viewer-shiki.ts`, `code-viewer-diff-utils.ts`, `code-viewer.css`）
- `app-shell` は `registry:block` — Sidebar + Topbar + MainContent の完全レイアウト

## カタログ

ライブプレビュー付きの全コンポーネント一覧: https://orbit-ui.pages.dev
