"""Build Octocat wheel cap as STL meshes using trimesh."""
import json, numpy as np, trimesh
from shapely.geometry import Polygon, Point
from shapely.ops import unary_union
from pathlib import Path

ROOT = Path("/mnt/d/workspace/octocat_wheel_cap_v3")
poly = json.loads((ROOT / "src/octocat_polygon.json").read_text())

# --- Parameters (cm) ---
CAP_R       = 2.7      # 54 mm diameter
CAP_T       = 0.12     # 1.2 mm thickness
EMBOSS_T    = 0.03     # 0.3 mm white emboss height
RING_IR     = 2.55     # snap-fit ring inner radius (52 mm bore w/ 1mm wall... actually 51mm)
RING_OR     = 2.65     # snap-fit ring outer radius
RING_H      = 0.20     # 2 mm ring height
LIP_OR      = 2.70     # 0.5 mm outward lip at ring tip
LIP_H       = 0.05     # 0.5 mm lip height
SCREW_R     = 0.10     # M2 hole radius (φ2.0 mm)
SCREW_POS   = [(0.0, 0.0), (0.7, 0.0), (-0.7, 0.0)]  # match FS90R hub

# --- Shapely polygons ---
oct_poly = Polygon(poly["outer"])
if not oct_poly.is_valid:
    oct_poly = oct_poly.buffer(0)
print("octocat area cm^2:", oct_poly.area, "valid:", oct_poly.is_valid)

cap_disk = Point(0, 0).buffer(CAP_R, resolution=256)
ring_outer = Point(0, 0).buffer(RING_OR, resolution=256)
ring_inner = Point(0, 0).buffer(RING_IR, resolution=256)
ring_ring  = ring_outer.difference(ring_inner)
lip_outer  = Point(0, 0).buffer(LIP_OR, resolution=256)
lip_ring   = lip_outer.difference(ring_inner)

screw_holes = unary_union([Point(x, y).buffer(SCREW_R, resolution=64) for x, y in SCREW_POS])

# Cap with screw holes
cap_with_holes = cap_disk.difference(screw_holes)
ring_with_holes = ring_ring  # ring doesn't intersect center holes (RING_IR=2.55, screws at <=0.7+0.1)
# Actually screws at (±0.7, 0) far from ring. OK.

# Octocat silhouette minus screw holes (so embossed Octocat doesn't fill screws)
octocat_top = oct_poly.difference(screw_holes)

# --- Extrude with trimesh ---
def shp_to_mesh(shp, height, z_base=0.0):
    if shp.geom_type == "Polygon":
        polys = [shp]
    else:
        polys = list(shp.geoms)
    meshes = []
    for p in polys:
        m = trimesh.creation.extrude_polygon(p, height)
        m.apply_translation([0, 0, z_base])
        meshes.append(m)
    return trimesh.util.concatenate(meshes)

cap_mesh   = shp_to_mesh(cap_with_holes, CAP_T, z_base=0.0)
ring_mesh  = shp_to_mesh(ring_with_holes, RING_H, z_base=-RING_H)
lip_mesh   = shp_to_mesh(lip_ring, LIP_H, z_base=-RING_H - LIP_H)
black_mesh = trimesh.util.concatenate([cap_mesh, ring_mesh, lip_mesh])
white_mesh = shp_to_mesh(octocat_top, EMBOSS_T, z_base=CAP_T)

print("black faces:", len(black_mesh.faces), "white faces:", len(white_mesh.faces))
print("black watertight:", black_mesh.is_watertight, "vol:", black_mesh.volume)
print("white watertight:", white_mesh.is_watertight, "vol:", white_mesh.volume)

# Export
stl_dir = ROOT / "stl"
black_mesh.export(stl_dir / "cap_black.stl")
white_mesh.export(stl_dir / "cap_white_octocat.stl")

# Combined for preview
combined = trimesh.util.concatenate([black_mesh, white_mesh])
combined.export(stl_dir / "cap_combined.stl")
print("Exported STLs to", stl_dir)
