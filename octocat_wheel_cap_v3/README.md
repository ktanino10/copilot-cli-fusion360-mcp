# Octocat Wheel Cap (high-fidelity v3)

GitHub Octocat 入りホイールキャップ。FS90R タイヤホイール（φ54mm）にスナップフィットで装着可能。

## なぜこの実装に切り替えたか

最初は Fusion 360 MCP の `draw_spline` で 27 → 40 → 10,000 点と精度を上げていったが、
**Fusion 360 のスプラインは点数が増えると後続のフィーチャー操作（押し出し等）が極端に遅くなり、
10,000 点ではフリーズして応答不能になった**ため、Python 側で直接ジオメトリを構築する方針に転換。

## アプローチ

| ステージ | ツール | 結果 |
|----------|--------|------|
| 1. 輪郭抽出 | OpenCV (`findContours` + `approxPolyDP`) | 1,072 点（30µm 精度） |
| 2. 2D ポリゴン処理 | `shapely`（外周−ねじ穴差分など） | 穴付きポリゴン |
| 3. 押し出し | `trimesh.creation.extrude_polygon` | 水密 STL |
| 4. レンダリング | `pyrender` (EGL ヘッドレス OpenGL) | 4 視点 + 36F GIF |

## 寸法

| パラメータ | 値 | 備考 |
|-----------|----|----|
| キャップ外径 | φ54mm | FS90R ホイールと同径 |
| キャップ厚さ | 1.2mm | |
| Octocat 浮き出し高さ | 0.3mm | |
| スナップリング内径 | φ52mm | 1mm 差で締まり嵌め |
| リップ径 | φ54mm | 0.5mm 高さで抜け止め |
| M2 ねじ穴 | φ2.0mm × 3 | 中央 + ±7mm（FS90R ハブと同配置） |

## ファイル

- `src/extract_octocat.py` — GitHub Mark PNG → 高精度ポリゴン JSON
- `src/build_mesh.py` — JSON → STL（黒キャップ・白 Octocat・統合）
- `src/render_pr.py` — STL → PNG/GIF（pyrender）
- `stl/cap_black.stl` — キャップ本体（白プラスチック想定）
- `stl/cap_white_octocat.stl` — 浮き出し Octocat（黒プラスチック想定）
- `stl/cap_combined.stl` — 単色プリント用に統合した STL

## 再生成

```bash
pip install opencv-python shapely trimesh manifold3d mapbox-earcut pyrender pillow numpy
python3 src/extract_octocat.py
python3 src/build_mesh.py
PYOPENGL_PLATFORM=egl python3 src/render_pr.py
```
