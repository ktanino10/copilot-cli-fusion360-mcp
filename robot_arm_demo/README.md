# Robot Arm Demo — Fusion 360 × Copilot CLI (MCP)

GitHub Copilot CLI から Fusion 360 MCP server を呼び出して、関節付きロボットアームを構築する技術デモ。

## 動画

### ⭐ `fusion_screencast.mp4` — Fusion画面の高密度キャプチャ
**13秒 / 1080p / 30fps**。MCP コマンドが Fusion 360 のビューポートを動かしている最中に、`Viewport.saveAsImageFile()` で連続キャプチャ (237枚)。各ステップでカメラがゆっくりオービットしながら、新しいパーツが現れる様子を映している。**「Copilot CLI で動かすとこんな感じになります」というイメージを掴むのに使ってください。**

### 補助動画
| ファイル | 内容 | 長さ |
|---|---|---|
| `demo_video.mp4` | Fusion静止画スライドショー | 24s |
| `demo_video_split.mp4` | Fusion + 静的ターミナル分割 | 28s |
| `demo_video_split_v2.mp4` | Fusion + タイプライター式ターミナル | 30s |

> いずれもライブ録画ではなく、Fusion ビューポートのスクショ + Pillow 描画パネルの合成です。

## 構築するロボットアーム

| 部位 | 形状 | 寸法 (cm) | 位置 |
|---|---|---|---|
| Base | 円柱 | r=6, h=2 | z=0..2 |
| YawJoint | 円柱 | r=2.5, h=3 | z=2..5 |
| UpperArm | 直方体 | 3×3×12 | 中心 z=11 |
| ElbowPivot | 円柱 | r=2, h=4 | y=-2..2, z=17 |
| Forearm | 直方体 | 2.5×2.5×10 | 中心 z=22 |
| GripperL/R | 直方体 | 0.6×2×3 | x=±1.5, z=28.5 |

## ファイル構成

| ファイル | 用途 |
|---|---|
| `fusion_screencast.mp4` | **メイン動画**: Fusion画面のキャプチャ |
| `rec/` | 上記動画の素材 237 PNG |
| `build_screencast.py` | スクリーンキャストの動画化スクリプト |
| `frames/` | スライドショー版の静止素材 31 PNG |
| `build_video*.py` | 合成動画の生成スクリプト |
| `robot_arm_build.py` | Fusion 360 Python API 用の参考スクリプト |
| `copilot_prompts.md` | Copilot CLI に渡すプロンプト例 |
| `fusion_artifacts/` | 検証エクスポート (F3D / STL) |

## 再現手順

1. Fusion 360 を起動 → 新規デザインを開く
2. Fusion360MCP アドインを起動
3. WSL ターミナルで `copilot` を起動
4. `copilot_prompts.md` の Step 1〜6 を順番に投げる
5. `python3 build_screencast.py` で動画を生成

## 注意
- アペアランス (`set_appearance`) はマテリアルライブラリ未ロード時にエラー
- STEP エクスポートはコンポーネント単位 (Body 単体不可)
- ジョイント (`add_joint`) はアセンブリ型ドキュメント必須
