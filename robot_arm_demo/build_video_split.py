"""
Build demo_video_split.mp4: left = Fusion screenshot, right = simulated terminal.
"""
import os, subprocess, sys
from PIL import Image, ImageDraw, ImageFont
import imageio_ffmpeg

FFMPEG = imageio_ffmpeg.get_ffmpeg_exe()
ROOT = "/mnt/d/workspace/fusion_copilot_demo_video"
FRAMES = os.path.join(ROOT, "frames")
WORK = os.path.join(ROOT, "frames_split")
OUT_MP4 = os.path.join(ROOT, "demo_video_split.mp4")
W, H = 1920, 1080
FPS = 30
LEFT_W = 1344  # 70%
RIGHT_W = W - LEFT_W  # 576

os.makedirs(WORK, exist_ok=True)
for f in os.listdir(WORK):
    os.remove(os.path.join(WORK, f))

def font(size, mono=False):
    paths_mono = [
        "/mnt/c/Windows/Fonts/consolab.ttf",
        "/mnt/c/Windows/Fonts/consola.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf",
    ]
    paths_sans = [
        "/mnt/c/Windows/Fonts/YuGothB.ttc",
        "/mnt/c/Windows/Fonts/meiryob.ttc",
        "/mnt/c/Windows/Fonts/arialbd.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    ]
    for p in (paths_mono if mono else paths_sans):
        if os.path.exists(p):
            try: return ImageFont.truetype(p, size)
            except Exception: pass
    return ImageFont.load_default()

# ------------ Terminal panel rendering ------------
TERM_BG = (12, 14, 18)
TERM_FG = (220, 220, 220)
PROMPT_FG = (130, 220, 140)   # green
USER_FG = (200, 220, 255)
ASSIST_FG = (255, 200, 100)   # orange
HEADER_BG = (35, 38, 44)

def render_terminal(lines, cursor=False):
    """lines: list of (style, text) where style in {'prompt','user','assist','sys'}"""
    img = Image.new("RGB", (RIGHT_W, H), TERM_BG)
    d = ImageDraw.Draw(img)
    # title bar
    d.rectangle([0, 0, RIGHT_W, 44], fill=HEADER_BG)
    fbar = font(20, mono=True)
    d.text((16, 10), "● ● ●   copilot — ~/  ", fill=(180,180,180), font=fbar)

    f = font(20, mono=True)
    line_h = 26
    x0 = 16
    y = 60
    max_chars = (RIGHT_W - 32) // 11   # ~width per mono char at size 20

    def wrap(text, indent=0):
        out = []
        room = max_chars - indent
        if room < 10: room = 10
        while len(text) > room:
            cut = text.rfind(' ', 0, room)
            if cut < 10: cut = room
            out.append(text[:cut])
            text = text[cut:].lstrip()
        out.append(text)
        return out

    for style, text in lines:
        if style == "prompt":
            d.text((x0, y), "❯ ", fill=PROMPT_FG, font=f)
            chunks = wrap(text, indent=2)
            for i, c in enumerate(chunks):
                d.text((x0 + (22 if i==0 else 22), y), c, fill=USER_FG, font=f)
                y += line_h
        elif style == "assist":
            for c in wrap("✓ " + text, indent=0):
                d.text((x0, y), c, fill=ASSIST_FG, font=f)
                y += line_h
        elif style == "sys":
            for c in wrap(text, indent=0):
                d.text((x0, y), c, fill=(120,120,120), font=f)
                y += line_h
        else:
            for c in wrap(text, indent=0):
                d.text((x0, y), c, fill=TERM_FG, font=f)
                y += line_h
        y += 4
        if y > H - 40: break

    if cursor:
        d.rectangle([x0, y, x0+12, y+22], fill=TERM_FG)
    return img

# ------------ Compose split frame ------------
def compose(fusion_path, terminal_img, caption=None):
    out = Image.new("RGB", (W, H), (20, 22, 26))
    if fusion_path and os.path.exists(fusion_path):
        f_img = Image.open(fusion_path).convert("RGB").resize((LEFT_W, H))
        out.paste(f_img, (0, 0))
    out.paste(terminal_img, (LEFT_W, 0))
    # divider line
    d = ImageDraw.Draw(out)
    d.line([(LEFT_W, 0), (LEFT_W, H)], fill=(50, 55, 65), width=2)
    if caption:
        cf = font(36)
        bbox = d.textbbox((0,0), caption, font=cf)
        pad = 18
        bw = bbox[2]-bbox[0] + pad*2
        bh = bbox[3]-bbox[1] + pad*2
        x = 30; y = H - bh - 30
        d.rectangle([x, y, x+bw, y+bh], fill=(20,22,26))
        d.text((x+pad, y+pad-bbox[1]), caption, fill=(255,255,255), font=cf)
    return out

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

# ------------ Sequence ------------
seq = []  # list of (path, duration_sec)

intro = os.path.join(WORK, "intro.png")
make_card(intro, "Fusion 360 × Copilot CLI", "Build a robot arm — with words.")
seq.append((intro, 3.0))

# Build cumulative terminal history for each step
history = [
    ("sys", "Connected to fusion360 MCP server"),
    ("sys", "Active design: 無題 (empty)"),
]

steps = [
    ("01_base.png",     "Base ベース",
     "土台を作って。半径6cm 高さ2cm の円柱。名前はBase。",
     "create_cylinder r=6 h=2 → Base"),
    ("02_yaw.png",      "Yaw ヨー軸",
     "Baseの上にヨー軸の円柱、半径2.5cm 高さ3cm。名前はYawJoint。",
     "create_cylinder r=2.5 h=3 z=2 → YawJoint"),
    ("03_upperarm.png", "Upper Arm 上腕",
     "上腕、3×3×12cmの直方体、中心(0,0,11)。名前はUpperArm。",
     "create_box 3×3×12 → UpperArm"),
    ("04_elbow.png",    "Elbow 肘ピッチ軸",
     "肘の回転軸、Y方向に 半径2cm 長さ4cm の円柱。",
     "create_cylinder axis=Y → ElbowPivot"),
    ("05_forearm.png",  "Forearm 前腕",
     "前腕、2.5×2.5×10cmの直方体、中心(0,0,22)。",
     "create_box 2.5×2.5×10 → Forearm"),
    ("06_gripper.png",  "Gripper グリッパー",
     "グリッパー、二本指。0.6×2×3cmを±1.5に2つ。",
     "create_box ×2 → GripperL, GripperR"),
]

for i, (fn, cap, prompt_jp, ack) in enumerate(steps):
    history.append(("prompt", prompt_jp))
    history.append(("assist", ack))
    term = render_terminal(history[-12:])  # show last lines
    img = compose(os.path.join(FRAMES, fn), term, caption=f"Step {i+1}: {cap}")
    p = os.path.join(WORK, f"step_{i:02d}.png")
    img.save(p)
    seq.append((p, 3.0))

# Reveal: orbit with persistent terminal showing "completed" state
history.append(("prompt", "全部できた？最終形を見せて。"))
history.append(("assist", "7 bodies created. Rotating view…"))
term_done = render_terminal(history[-14:])

orbit_files = sorted(f for f in os.listdir(FRAMES) if f.startswith("07_orbit_"))
for j, fn in enumerate(orbit_files):
    img = compose(os.path.join(FRAMES, fn), term_done, caption="Done — 6 prompts, 1 robot arm")
    p = os.path.join(WORK, f"orb_{j:02d}.png")
    img.save(p)
    seq.append((p, 2.0/FPS))  # ~2 frames each → smooth-ish turntable

# Export step
history.append(("prompt", "F3DとSTLでエクスポートして。"))
history.append(("assist", "Exported robot_arm.f3d, robot_arm_upperarm.stl"))
term_export = render_terminal(history[-14:])
last_orbit = os.path.join(FRAMES, orbit_files[0])
exp_img = compose(last_orbit, term_export, caption="Export")
exp_p = os.path.join(WORK, "export.png")
exp_img.save(exp_p)
seq.append((exp_p, 3.0))

outro = os.path.join(WORK, "outro.png")
make_card(outro, "Natural language → CAD", "GitHub Copilot CLI × MCP")
seq.append((outro, 3.0))

# ------------ ffmpeg concat ------------
concat = os.path.join(WORK, "concat.txt")
with open(concat, "w") as cf:
    for src, dur in seq:
        cf.write(f"file '{src}'\n")
        cf.write(f"duration {dur}\n")
    cf.write(f"file '{seq[-1][0]}'\n")

cmd = [
    FFMPEG, "-y",
    "-f", "concat", "-safe", "0", "-i", concat,
    "-vf", f"fps={FPS},format=yuv420p,scale={W}:{H}",
    "-c:v", "libx264", "-preset", "medium", "-crf", "20",
    "-movflags", "+faststart",
    OUT_MP4,
]
print("Running ffmpeg…")
r = subprocess.run(cmd, capture_output=True, text=True)
if r.returncode != 0:
    print(r.stderr[-2000:]); sys.exit(r.returncode)
print(f"OK → {OUT_MP4}  ({os.path.getsize(OUT_MP4)/1024:.1f} KB)")
