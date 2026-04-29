"""
robot_arm_build.py
==================
Fusion 360 MCP server で「関節付きロボットアーム」を構築する参考スクリプト。

目的:
- 動画内で Copilot CLI に与えるプロンプトと「同じ最終形」を再現するためのバックアップ。
- すべて MCP のツール呼び出し (cm 単位) と等価。Fusion 360 Python API でも実行可能。

前提:
- Fusion 360 を起動し、空のデザインを開いてあること。
- Fusion360MCP アドインが有効化されていること。

寸法 (cm):
    Base       : 円柱  r=6.0  h=2.0   z=0..2
    YawJoint   : 円柱  r=2.5  h=3.0   z=2..5  (ヨー回転軸: Z)
    UpperArm   : 直方体 3x3x12        中心 z=11  (z=5..17)
    ElbowPivot : 円柱  r=2.0  h=4.0   y=-2..2, z=17  (ピッチ回転軸: Y)
    Forearm    : 直方体 2.5x2.5x10    中心 z=22  (z=17..27)
    GripperL/R : 直方体 0.6x2x3       中心 z=28.5, x=±1.5
"""

import adsk.core
import adsk.fusion


def run(context):
    app = adsk.core.Application.get()
    ui = app.userInterface
    design = adsk.fusion.Design.cast(app.activeProduct)
    if not design:
        ui.messageBox("アクティブなデザインがありません。Fusion 360 で新規デザインを開いてください。")
        return

    root = design.rootComponent
    tbm = adsk.fusion.TemporaryBRepManager.get()

    def add_body(brep, name):
        b = root.bRepBodies.add(brep)
        b.name = name
        return b

    def cylinder(name, base_xyz, axis, radius, height):
        bx, by, bz = base_xyz
        ax, ay, az = axis
        start = adsk.core.Point3D.create(bx, by, bz)
        end = adsk.core.Point3D.create(bx + ax * height, by + ay * height, bz + az * height)
        brep = tbm.createCylinderOrCone(start, radius, end, radius)
        return add_body(brep, name)

    def box(name, center_xyz, size_xyz):
        cx, cy, cz = center_xyz
        sx, sy, sz = size_xyz
        ob = adsk.core.OrientedBoundingBox3D.create(
            adsk.core.Point3D.create(cx, cy, cz),
            adsk.core.Vector3D.create(1, 0, 0),
            adsk.core.Vector3D.create(0, 1, 0),
            sx, sy, sz,
        )
        brep = tbm.createBox(ob)
        return add_body(brep, name)

    cylinder("Base",       (0, 0, 0),   (0, 0, 1), 6.0, 2.0)
    cylinder("YawJoint",   (0, 0, 2),   (0, 0, 1), 2.5, 3.0)
    box     ("UpperArm",   (0, 0, 11),  (3.0, 3.0, 12.0))
    cylinder("ElbowPivot", (0, -2, 17), (0, 1, 0), 2.0, 4.0)
    box     ("Forearm",    (0, 0, 22),  (2.5, 2.5, 10.0))
    box     ("GripperL",   (-1.5, 0, 28.5), (0.6, 2.0, 3.0))
    box     ("GripperR",   ( 1.5, 0, 28.5), (0.6, 2.0, 3.0))
