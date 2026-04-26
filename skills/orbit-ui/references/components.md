# Orbit UI コンポーネント一覧

| 名前 | 種別 | 説明 | 依存 | npm |
|------|------|------|------|-----|
| `tokens` | registry:style | CSS変数一式 (color/spacing/radius/motion/status)。dark/light は `data-theme` 属性で切替 | — | — |
| `icon` | registry:ui | ストロークアイコンセット (84種)。`name` prop で切替、`stroke=currentColor` で親色継承 | — | — |
| `button` | registry:ui | primary/secondary/ghost/danger variant、sm/md/lg サイズ、iconOnly 対応 | tokens | — |
| `input` | registry:ui | Input, Textarea, InputGroup。tokens ベースの focus ring 付き | tokens, icon | — |
| `badge` | registry:ui | ステータス表示。default/success/warn/danger/info/accent variant、dot/pill オプション | tokens | — |
| `card` | registry:ui | Card (title + action + body) と MetricCard (値 + unit + delta) | tokens | — |
| `tabs` | registry:ui | 下線式タブ切替 (controlled)。count chip 付き対応 | tokens | — |
| `toggle` | registry:ui | Checkbox / Radio / Switch / SegmentedSwitch の 4 種 | tokens | — |
| `select` | registry:ui | Select (単一) と Combobox (複数 + フィルタ)。キーボード操作対応 | tokens, icon | — |
| `tooltip` | registry:ui | ホバー吹き出し。portal + 矢印付き自動位置決め | tokens | — |
| `overlay` | registry:ui | Dialog (backdrop blur + pop-in) と Toast (右下スタック、自動消滅) | tokens, icon, button | — |
| `spinner` | registry:ui | Spinner (円形) / Pulse (ドット) / Progress (バー) のローディング 3 種 | tokens | — |
| `kbd` | registry:ui | キーボードキー badge。mono フォント + 下側ダブルボーダー | tokens | — |
| `truncate` | registry:ui | 1 行省略 (…) + ホバー全文 tooltip + C キーコピー | tokens, tooltip, kbd | — |
| `page-header` | registry:ui | ページ上部 title + meta + actions。sticky 対応 | tokens | — |
| `meta-item` | registry:ui | アイコン + ラベル + 値の横並び表示 | tokens, icon | — |
| `breadcrumb` | registry:ui | パンくずナビ。renderLink で SPA ルーター対応、maxItems 自動折りたたみ | tokens, icon | — |
| `empty-state` | registry:ui | アイコン + タイトル + 説明 + アクション。sm/md サイズ | tokens, icon | — |
| `confirm` | registry:ui | 確認ダイアログ。default/danger トーン、async onConfirm 自動 disable | tokens, button, overlay | — |
| `button-group` | registry:ui | 複数 Button を枠共有でグルーピング。horizontal/vertical | tokens, button | — |
| `theme-toggle` | registry:ui | dark/light 切替ボタン。localStorage 永続化 | tokens, button, icon | — |
| `compact-number` | registry:ui | 数値を SI 接頭辞 (k/M/B) で短縮表示。hover で完全値 tooltip | tokens, tooltip, kbd | — |
| `compact-bytes` | registry:ui | バイト数を human-readable 表示 (SI/IEC)。hover で正確値 tooltip | tokens, tooltip, kbd | — |
| `time-display` | registry:ui | RelativeTime / AbsoluteTime / LiveElapsed / DurationDisplay の 4 種 | tokens, tooltip, kbd | — |
| `md` | registry:ui | Markdown 風リッチタイポグラフィ (H1-H4, P, Link, List, Blockquote, Code 等) | tokens | — |
| `command-palette` | registry:ui | Cmd+K 式コマンドパレット。fuzzy 検索、キーボードナビ、グループ表示 | tokens, icon | — |
| `code-viewer` | registry:ui | 構文ハイライト + Diff ビュワー (Shiki ベース、unified/split) | tokens, icon, truncate | shiki, diff |
| `log-viewer` | registry:ui | 構造化ログ表示。フィルタ / 自動追従 / 色分け / 仮想化 | tokens, icon, input, toggle, time-display | @tanstack/react-virtual |
| `data-table` | registry:ui | 列定義ベーステーブル。仮想化 / ソート / 行選択 / sticky / expand | tokens, icon, tooltip, compact-number, toggle | @tanstack/react-virtual |
| `file-browser` | registry:ui | ツリーペイン + コンテンツペイン。リサイズ / 自動展開 / レスポンシブ | tokens, icon, spinner | — |
| `app-shell` | registry:block | Sidebar + Topbar + mobile drawer の完全アプリ外枠 | tokens, button, icon | — |

## インストール

```bash
npx shadcn@latest add "https://orbit-ui.pages.dev/r/<component>.json"
```

依存関係（`tokens` 含む）は自動解決される。複数コンポーネントを 1 コマンドで指定可能。
