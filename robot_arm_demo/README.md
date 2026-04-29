# Fusion 360 × GitHub Copilot CLI 技術デモ動画

GitHub Copilot CLI から **Fusion 360 MCP server** を呼び出し、
自然言語だけで関節付きロボットアームを構築する様子を見せる **約 4 分の YouTube 向け技術デモ**。

## 含まれるもの

| ファイル | 用途 |
|---|---|
| `script_ja.md` | 日本語ナレーション台本（タイムコード付き） |
| `subtitles_en.srt` | 英語字幕 (SRT) |
| `shot_list.md` | OBS 録画手順・編集ガイド |
| `copilot_prompts.md` | 動画中にコピペで打ち込む Copilot CLI プロンプト一覧 |
| `robot_arm_build.py` | Fusion 360 MCP / Python API 用のバックアップ構築スクリプト |
| `thumbnail_concept.md` | サムネイル案 |
| `fusion_artifacts/` | 事前検証で生成済の F3D / STL |

## 撮影〜公開までの流れ

1. **準備**
   - Fusion 360 を起動し、`ファイル > 新規デザイン` で空のアセンブリ系ドキュメントを開く
   - Fusion360MCP アドインを起動
   - WSL ターミナルで `copilot` を実行できるようにしておく
   - OBS シーン `RobotArmDemo` を `shot_list.md` のレイアウトで構成
2. **リハーサル**
   - `copilot_prompts.md` の Step 1〜8 を一度通しで流し、Fusion 側の生成結果を確認
   - 失敗した場合は MCP に「全部消してやり直して」と指示すれば `delete_all` が呼ばれる
3. **本番録画** — `shot_list.md` のシーン分割で個別ファイル化
4. **編集** — 5 ファイルを連結 + タイトル + 字幕 (`subtitles_en.srt`) + BGM
5. **書き出し** — `fusion_copilot_demo.mp4` (1080p/30fps)
6. **公開** — タイトル例: 「Fusion 360 を会話だけで動かす：GitHub Copilot CLI × MCP」

## 仕様（ロボットアーム）

| 部位 | 形状 | 寸法 (cm) | 位置 (cm) |
|---|---|---|---|
| Base | 円柱 | r=6, h=2 | z=0..2 |
| YawJoint | 円柱 | r=2.5, h=3 | z=2..5 (軸:Z) |
| UpperArm | 直方体 | 3×3×12 | 中心 z=11 |
| ElbowPivot | 円柱 | r=2, h=4 | y=-2..2, z=17 (軸:Y) |
| Forearm | 直方体 | 2.5×2.5×10 | 中心 z=22 |
| GripperL/R | 直方体 | 0.6×2×3 | x=±1.5, z=28.5 |

## 検証済みエクスポート
- `fusion_artifacts/robot_arm.f3d` — フルデザイン
- `fusion_artifacts/robot_arm_upperarm.stl` — 1 ボディ例

## 動画について（重要）
本リポジトリ同梱の `demo_video*.mp4` は **ライブ画面録画ではなく合成動画** です。
- **左側 (Fusion 360)**: 本物のビューポートを `Viewport.saveAsImageFile()` で1枚ずつ静止キャプチャしたもの
- **右側 (ターミナル)**: Pillow で描画したシミュレートパネル（`build_video_v2.py` の `render_terminal()`）

| 動画 | 構成 | 長さ |
|---|---|---|
| `demo_video.mp4` | Fusionのみ (スライドショー) | 24s |
| `demo_video_split.mp4` | Fusion + 静的ターミナル分割 | 28s |
| **`demo_video_split_v2.mp4`** | **Fusion + タイプライター式アニメ ターミナル** | **30s** |

本物のリアルタイム画面録画にしたい場合は `shot_list.md` の OBS 手順に従って手動で録画してください。

## 注意
- アペアランス (色付け) の MCP API はマテリアルライブラリ未ロード時にエラー (`'NoneType' object has no attribute 'appearances'`) になる。動画ではマテリアルパネルを開いて事前にロードしておくか、色付けは編集時に Fusion 上で手動指定する。
- STEP エクスポートはコンポーネント単位 (Body 単体不可)。アセンブリ化してから `export_step` を呼ぶと成功する。
- ジョイント追加 (`add_joint`) はアセンブリ型ドキュメントが必須。Step 7 の前に新規デザインで開き直すこと。

## クレジット
- ロゴや BGM は YouTube Audio Library など商用利用可能なものに限定する。
