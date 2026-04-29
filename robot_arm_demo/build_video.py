"""
Build demo_video.mp4 from screenshots in frames/ using ffmpeg.
Sequence:
  - title card (3s)
  - each build step held for 2.5s (00..06)
  - orbit frames at 15 fps for a smooth turntable
  - outro card (3s)
Total ~ 30 seconds (a "shorter" tech-demo cut).
"""
import os, subprocess, sys
from PIL import Image, ImageDraw, ImageFont

import imageio_ffmpeg
FFMPEG = imageio_ffmpeg.get_ffmpeg_exe()

ROOT = "/mnt/d/workspace/fusion_copilot_demo_video"
FRAMES = os.path.join(ROOT, "frames")
WORK   = os.path.join(ROOT, "frames_seq")
OUT_MP4 = os.path.join(ROOT, "demo_video.mp4")
W, H = 1920, 1080
FPS = 30

os.makedirs(WORK, exist_ok=True)
for f in os.listdir(WORK):
    os.remove(os.path.join(WORK, f))

def font(size):
    for p in [
        "/mnt/c/Windows/Fonts/YuGothB.ttc",
        "/mnt/c/Windows/Fonts/meiryob.ttc",
        "/mnt/c/Windows/Fonts/arialbd.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    ]:
        if os.path.exists(p):
            try: return ImageFont.truetype(p, size)
            except Exception: pass
    return ImageFont.load_default()

def make_card(path, title, subtitle=""):
    img = Image.new("RGB", (W, H), (20, 22, 26))
    d = ImageDraw.Draw(img)
    f1 = font(96); f2 = font(48)
    tw = d.textbbox((0,0), title, font=f1)[2]
    d.text(((W-tw)//2, H//2-120), title, fill=(255,255,255), font=f1)
    if subtitle:
        sw = d.textbbox((0,0), subtitle, font=f2)[2]
        d.text(((W-sw)//2, H//2+20), subtitle, fill=(110,200,150), font=f2)
    img.save(path)

def overlay(src, dst, caption):
    img = Image.open(src).convert("RGB")
    if img.size != (W, H):
        img = img.resize((W, H))
    d = ImageDraw.Draw(img)
    f = font(48)
    bbox = d.textbbox((0,0), caption, font=f)
    pad = 24
    box_w = bbox[2]-bbox[0] + pad*2
    box_h = bbox[3]-bbox[1] + pad*2
    x = 60; y = H - box_h - 60
    d.rectangle([x, y, x+box_w, y+box_h], fill=(20,22,26,200))
    d.text((x+pad, y+pad-bbox[1]), caption, fill=(255,255,255), font=f)
    img.save(dst)

# ---- Build sequence as a list of (source_path, hold_seconds) ----
seq = []

intro = os.path.join(WORK, "intro.png")
make_card(intro, "Fusion 360 × Copilot CLI", "Build a robot arm — with words.")
seq.append((intro, 3.0))

steps = [
    ("01_base.png",      "Step 1: Base — cylinder r=6cm h=2cm"),
    ("02_yaw.png",       "Step 2: Yaw joint — cylinder r=2.5cm h=3cm"),
    ("03_upperarm.png",  "Step 3: Upper arm — box 3×3×12cm"),
    ("04_elbow.png",     "Step 4: Elbow pivot — cylinder along Y"),
    ("05_forearm.png",   "Step 5: Forearm — box 2.5×2.5×10cm"),
    ("06_gripper.png",   "Step 6: Gripper — two fingers"),
]
for i, (fn, cap) in enumerate(steps):
    out = os.path.join(WORK, f"step_{i:02d}.png")
    overlay(os.path.join(FRAMES, fn), out, cap)
    seq.append((out, 2.5))

orbit_card = os.path.join(WORK, "orbit_card.png")
make_card(orbit_card, "完成", "Done in 6 prompts.")
seq.append((orbit_card, 1.5))

orbit_files = sorted(f for f in os.listdir(FRAMES) if f.startswith("07_orbit_"))
for fn in orbit_files:
    out = os.path.join(WORK, f"orb_{fn}")
    img = Image.open(os.path.join(FRAMES, fn)).convert("RGB")
    if img.size != (W, H): img = img.resize((W, H))
    img.save(out)
    seq.append((out, 1.0/FPS * 2))  # 2-frame hold each → ~24*2/30 = 1.6s total

outro = os.path.join(WORK, "outro.png")
make_card(outro, "Natural language → CAD", "GitHub Copilot CLI × MCP")
seq.append((outro, 3.0))

# Build concat list
concat_path = os.path.join(WORK, "concat.txt")
with open(concat_path, "w") as cf:
    for src, dur in seq:
        cf.write(f"file '{src}'\n")
        cf.write(f"duration {dur}\n")
    cf.write(f"file '{seq[-1][0]}'\n")  # last file repeated per ffmpeg concat spec

cmd = [
    FFMPEG, "-y",
    "-f", "concat", "-safe", "0",
    "-i", concat_path,
    "-vf", f"fps={FPS},format=yuv420p,scale={W}:{H}",
    "-c:v", "libx264", "-preset", "medium", "-crf", "20",
    "-movflags", "+faststart",
    OUT_MP4,
]
print("Running ffmpeg...")
r = subprocess.run(cmd, capture_output=True, text=True)
if r.returncode != 0:
    print("FFMPEG STDERR (tail):"); print(r.stderr[-2000:])
    sys.exit(r.returncode)
print(f"OK → {OUT_MP4}  ({os.path.getsize(OUT_MP4)/1024:.1f} KB)")
