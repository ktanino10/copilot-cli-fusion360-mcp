"""Render Octocat cap with pyrender (EGL headless OpenGL)."""
import os
os.environ["PYOPENGL_PLATFORM"] = "egl"
import numpy as np, trimesh, pyrender
from pathlib import Path
from PIL import Image

ROOT = Path("/mnt/d/workspace/octocat_wheel_cap_v3")
black = trimesh.load(ROOT / "stl/cap_black.stl")
white = trimesh.load(ROOT / "stl/cap_white_octocat.stl")

# Materials
mat_black = pyrender.MetallicRoughnessMaterial(
    baseColorFactor=(0.97, 0.97, 0.97, 1.0),
    metallicFactor=0.0, roughnessFactor=0.50)
mat_white = pyrender.MetallicRoughnessMaterial(
    baseColorFactor=(0.07, 0.07, 0.09, 1.0),
    metallicFactor=0.0, roughnessFactor=0.55)

pm_black = pyrender.Mesh.from_trimesh(black, material=mat_black, smooth=False)
pm_white = pyrender.Mesh.from_trimesh(white, material=mat_white, smooth=False)

W, H = 900, 900
renderer = pyrender.OffscreenRenderer(viewport_width=W, viewport_height=H)

def look_at(eye, target=(0,0,0), up=(0,0,1)):
    eye = np.array(eye, dtype=float)
    target = np.array(target, dtype=float)
    up = np.array(up, dtype=float)
    f = target - eye; f /= np.linalg.norm(f)
    s = np.cross(f, up); s /= (np.linalg.norm(s) + 1e-9)
    u = np.cross(s, f)
    M = np.eye(4)
    M[:3, 0] = s
    M[:3, 1] = u
    M[:3, 2] = -f
    M[:3, 3] = eye
    return M

def render(eye, out_path, ortho=False, scale=4.0, bg=(1.0, 1.0, 1.0, 1.0),
           light_dirs=None):
    scene = pyrender.Scene(bg_color=list(bg),
                            ambient_light=[0.45, 0.45, 0.45])
    scene.add(pm_black); scene.add(pm_white)

    # determine up
    eye_arr = np.array(eye, dtype=float)
    up = (0, 0, 1)
    if abs(eye_arr[0]) < 1e-6 and abs(eye_arr[1]) < 1e-6:
        up = (0, 1, 0)  # looking straight down
    cam_pose = look_at(eye, (0, 0, 0), up)
    if ortho:
        cam = pyrender.OrthographicCamera(xmag=scale, ymag=scale)
    else:
        cam = pyrender.PerspectiveCamera(yfov=np.pi / 6.5, aspectRatio=1.0)
    scene.add(cam, pose=cam_pose)

    # 3 directional lights for nice illumination
    light = pyrender.DirectionalLight(color=np.ones(3), intensity=3.5)
    dirs = light_dirs or [(0.4, -0.6, 1.0), (-0.7, 0.3, 0.6), (0.0, 0.0, 1.0)]
    for direction in dirs:
        d = np.array(direction, dtype=float)
        d /= np.linalg.norm(d)
        # camera at -d * 5 looking at origin
        scene.add(light, pose=look_at(-d * 5, (0, 0, 0), (0, 0, 1) if abs(d[2]) < 0.99 else (0, 1, 0)))

    color, _ = renderer.render(scene)
    Image.fromarray(color).save(out_path)
    print("rendered", out_path)

R = ROOT / "renders"
GRAY = (0.78, 0.80, 0.83, 1.0)
# Top (orthographic, looking down -Z from above)
render((0, 0, 8), R / "octocat_cap_top.png", ortho=True, scale=3.0)
# Bottom-tilt to show snap-fit ring (camera below, lights from below)
render((4, -4, -5), R / "octocat_cap_bottom.png", ortho=False, bg=GRAY,
       light_dirs=[(0.4, -0.6, -1.0), (-0.7, 0.3, -0.6), (0.0, 0.0, -1.0)])
# Side (looking from +Y)
render((0, 10, 0.5), R / "octocat_cap_side.png", ortho=True, scale=3.0, bg=GRAY)
# Isometric
render((6, -6, 5), R / "octocat_cap_isometric.png", ortho=False)

# Rotation GIF (24 frames)
print("rendering rotation GIF...")
frames = []
n = 36
radius = 9.0; height = 4.0
for i in range(n):
    theta = i * (2 * np.pi / n)
    eye = (radius * np.cos(theta), radius * np.sin(theta), height)
    fp = R / f"_rot_{i:02d}.png"
    render(eye, fp, ortho=False)
    frames.append(Image.open(fp).convert("RGB").resize((600, 600), Image.LANCZOS))

gif = R / "octocat_cap_rotation.gif"
frames[0].save(gif, save_all=True, append_images=frames[1:],
               duration=80, loop=0, optimize=True)
print("GIF:", gif, gif.stat().st_size, "bytes")
for i in range(n):
    (R / f"_rot_{i:02d}.png").unlink(missing_ok=True)
