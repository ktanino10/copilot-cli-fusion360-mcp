"""Extract Octocat polygon (outer + holes) from GitHub-Mark logo."""
import cv2, numpy as np, json
from pathlib import Path

SRC = "/home/ktanino/copilot-cli-minecraft-experiment/images/GitHub-Mark-ea2971cee799.png"
OUT = Path("/mnt/d/workspace/octocat_wheel_cap_v3/src")

img = cv2.imread(SRC, cv2.IMREAD_UNCHANGED)
# convert palette/RGBA to gray; the cat is black (0) on white (255) with transparent bg
if img.ndim == 3 and img.shape[2] == 4:
    # composite onto white
    bgr = img[:, :, :3].astype(float)
    a = (img[:, :, 3:4].astype(float)) / 255.0
    bgr = bgr * a + 255.0 * (1 - a)
    img = bgr.astype(np.uint8)
gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY) if img.ndim == 3 else img

# binary: 1 where cat (black), 0 background (white)
_, bw = cv2.threshold(gray, 128, 255, cv2.THRESH_BINARY_INV)
H, W = bw.shape
print("image:", W, "x", H, " black px:", int(bw.sum() / 255))

# RETR_CCOMP: 2-level (outer + holes)
contours, hierarchy = cv2.findContours(bw, cv2.RETR_CCOMP, cv2.CHAIN_APPROX_NONE)
hierarchy = hierarchy[0]
print("contour count:", len(contours))

# group: outer contours + their holes
shapes = []  # list of (outer_pts, [hole_pts...])
for i, h in enumerate(hierarchy):
    nxt, prv, child, parent = h
    if parent == -1:  # outer
        outer = contours[i].reshape(-1, 2)
        holes = []
        c = child
        while c != -1:
            holes.append(contours[c].reshape(-1, 2))
            c = hierarchy[c][0]
        shapes.append((outer, holes))

# pick largest outer by area
shapes.sort(key=lambda s: cv2.contourArea(s[0].reshape(-1, 1, 2)), reverse=True)
outer, holes = shapes[0]
print("outer pts:", len(outer), "holes:", len(holes), [len(h) for h in holes])

# normalize to model coordinates (cm)
# We want the cat to fit in radius 2.4cm (so cap radius 2.7cm has 0.3cm rim)
# bounding circle of outer
(cx, cy), r_px = cv2.minEnclosingCircle(outer.astype(np.float32))
TARGET_R_CM = 2.4
scale = TARGET_R_CM / r_px

def to_cm(pts):
    p = pts.astype(np.float64)
    p[:, 0] = (p[:, 0] - cx) * scale
    # flip Y because image Y goes down
    p[:, 1] = -(p[:, 1] - cy) * scale
    return p

outer_cm = to_cm(outer)
holes_cm = [to_cm(h) for h in holes]

# Simplify lightly (sub-pixel level) to keep file sizes reasonable
# epsilon ~ 0.005 cm = 50 microns, well under print resolution
def simplify(pts, eps_cm=0.003):
    arr = pts.reshape(-1, 1, 2).astype(np.float32)
    out = cv2.approxPolyDP(arr, eps_cm, True)
    return out.reshape(-1, 2)

outer_s = simplify(outer_cm)
holes_s = [simplify(h) for h in holes_cm]
print("after simplify outer:", len(outer_s), "holes:", [len(h) for h in holes_s])

data = {
    "outer": outer_s.tolist(),
    "holes": [h.tolist() for h in holes_s],
    "scale_cm_per_px": scale,
    "target_radius_cm": TARGET_R_CM,
    "src_image_size": [W, H],
}
out_file = OUT / "octocat_polygon.json"
out_file.write_text(json.dumps(data))
print("wrote", out_file, out_file.stat().st_size, "bytes")
