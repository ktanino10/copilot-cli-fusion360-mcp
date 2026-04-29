"""
Build fusion_screencast.mp4 — Fusion 360 viewport captured at high density
during the actual MCP-driven robot-arm build. Shows what the screen looks like
while the arm is being assembled by Copilot CLI commands.
"""
import os, subprocess, sys
from PIL import Image, ImageDraw, ImageFont
import imageio_ffmpeg

FFMPEG = imageio_ffmpeg.get_ffmpeg_exe()
ROOT = "/mnt/d/workspace/copilot-cli-fusion360-mcp/robot_arm_demo"
REC = os.path.join(ROOT, "rec")
WORK = os.path.join(ROOT, "rec_work")
OUT = os.path.join(ROOT, "fusion_screencast.mp4")
W, H = 1920, 1080
FPS = 30

os.makedirs(WORK, exist_ok=True)
for f in os.listdir(WORK):
    os.remove(os.path.join(WORK, f))

def font(size):
    for p in [
        "/mnt/c/Windows/Fonts/YuGothB.ttc",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    ]:
        if os.path.exists(p):
            try: return ImageFont.truetype(p, size)
            except Exception: pass
    return ImageFont.load_default()

def make_card(path, title, sub=""):
    img = Image.new("RGB", (W,H), (20,22,26))
    d = ImageDraw.Draw(img)
    f1 = font(96); f2 = font(48)
    tw = d.textbbox((0,0), title, font=f1)[2]
    d.text(((W-tw)//2, H//2-120), title, fill=(255,255,255), font=f1)
    if sub:
        sw = d.textbbox((0,0), sub, font=f2)[2]
        d.text(((W-sw)//2, H//2+20), sub, fill=(110,200,150), font=f2)
    img.save(path)

def overlay(src, dst, caption):
    img = Image.open(src).convert("RGB")
    if img.size != (W, H): img = img.resize((W, H))
    if caption:
        d = ImageDraw.Draw(img)
        f = font(40)
        bbox = d.textbbox((0,0), caption, font=f)
        pad = 18
        bw = bbox[2]-bbox[0] + pad*2; bh = bbox[3]-bbox[1] + pad*2
        x = 40; y = H - bh - 40
        d.rectangle([x, y, x+bw, y+bh], fill=(20,22,26))
        d.text((x+pad, y+pad-bbox[1]), caption, fill=(255,255,255), font=f)
    img.save(dst)

# Frames are named NNNNN_label.png; group by label prefix
frames = sorted(os.listdir(REC))
def cap_for(label):
    return {
        "empty":       "Step 0: empty viewport",
        "base":        "Step 1/6: Base (cylinder r=6, h=2)",
        "yaw":         "Step 2/6: Yaw joint (r=2.5, h=3)",
        "uarm":        "Step 3/6: Upper arm (3×3×12)",
        "elbow":       "Step 4/6: Elbow pivot (cylinder along Y)",
        "farm":        "Step 5/6: Forearm (2.5×2.5×10)",
        "grip":        "Step 6/6: Gripper — done",
        "final":       "Done — 6 prompts, 1 robot arm",
    }.get(label, "")

def label_of(fn):
    parts = fn.replace(".png","").split("_")
    return parts[1] if len(parts) >= 2 else parts[0]

# Compose sequence with captions. Each frame = 1/FPS seconds.
seq = []
intro = os.path.join(WORK, "intro.png")
make_card(intro, "Fusion 360 Screencast", "Captured live during the MCP build")
seq.append((intro, 2.5))

for i, fn in enumerate(frames):
    lbl = label_of(fn)
    cap = cap_for("base" if lbl=="base_appear"
                  else "yaw" if lbl=="yaw_appear"
                  else "uarm" if lbl=="uarm_appear"
                  else "elbow" if lbl=="elbow_appear"
                  else "farm" if lbl=="farm_appear"
                  else "grip" if lbl=="grip_appear"
                  else lbl)
    out = os.path.join(WORK, f"{i:05d}.png")
    overlay(os.path.join(REC, fn), out, cap)
    # short hold on "appear" frames; quick on orbit
    dur = 4.0/FPS if "appear" in lbl else 1.0/FPS
    seq.append((out, dur))

outro = os.path.join(WORK, "outro.png")
make_card(outro, "Natural language → CAD", "GitHub Copilot CLI × MCP")
seq.append((outro, 3.0))

concat = os.path.join(WORK, "concat.txt")
with open(concat, "w") as cf:
    for src, dur in seq:
        cf.write(f"file '{src}'\n")
        cf.write(f"duration {dur}\n")
    cf.write(f"file '{seq[-1][0]}'\n")

cmd = [FFMPEG, "-y", "-f", "concat", "-safe", "0", "-i", concat,
       "-vf", f"fps={FPS},format=yuv420p,scale={W}:{H}",
       "-c:v", "libx264", "-preset", "medium", "-crf", "20",
       "-movflags", "+faststart", OUT]
print(f"Encoding {len(seq)} frames…")
r = subprocess.run(cmd, capture_output=True, text=True)
if r.returncode != 0:
    print(r.stderr[-2000:]); sys.exit(r.returncode)
print(f"OK → {OUT}  ({os.path.getsize(OUT)/1024:.1f} KB)")
