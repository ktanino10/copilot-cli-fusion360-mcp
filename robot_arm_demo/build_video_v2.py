"""
v2: Build demo_video_split_v2.mp4 with typewriter-style terminal animation.

Each prompt is "typed" character by character (terminal panel updates per frame),
then Fusion side switches to the new state, then a brief hold.
"""
import os, subprocess, sys
from PIL import Image, ImageDraw, ImageFont
import imageio_ffmpeg

FFMPEG = imageio_ffmpeg.get_ffmpeg_exe()
ROOT = "/mnt/d/workspace/copilot-cli-fusion360-mcp/robot_arm_demo"
FRAMES = os.path.join(ROOT, "frames")
WORK = os.path.join(ROOT, "frames_v2")
OUT_MP4 = os.path.join(ROOT, "demo_video_split_v2.mp4")
W, H = 1920, 1080
FPS = 30
LEFT_W = 1344
RIGHT_W = W - LEFT_W
TYPE_CPS = 28          # chars per second
HOLD_FRAMES = int(FPS * 1.0)  # 1s after each step

os.makedirs(WORK, exist_ok=True)
for f in os.listdir(WORK):
    os.remove(os.path.join(WORK, f))

def font(size, mono=False):
    paths_mono = [
        "/mnt/c/Windows/Fonts/consola.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf",
    ]
    paths_sans = [
        "/mnt/c/Windows/Fonts/YuGothB.ttc",
        "/mnt/c/Windows/Fonts/meiryob.ttc",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    ]
    for p in (paths_mono if mono else paths_sans):
        if os.path.exists(p):
            try: return ImageFont.truetype(p, size)
            except Exception: pass
    return ImageFont.load_default()

TERM_BG=(12,14,18); FG=(220,220,220); GREEN=(130,220,140)
USER=(200,220,255); ACK=(255,200,100); GRAY=(120,120,120); HEAD=(35,38,44)

F_MONO = font(20, mono=True)
LINE_H = 26
MAX_CHARS = 50  # rough wrap width for RIGHT_W=576 mono20

def wrap(text, room=MAX_CHARS):
    out=[]
    while len(text) > room:
        cut = text.rfind(' ', 0, room)
        if cut < 10: cut = room
        out.append(text[:cut]); text = text[cut:].lstrip()
    out.append(text)
    return out

def render_terminal(history, current_typing=None, cursor_visible=True):
    """history: list of (style,text) already-completed lines.
       current_typing: (style, partial_text) being typed right now (or None)."""
    img = Image.new("RGB", (RIGHT_W, H), TERM_BG)
    d = ImageDraw.Draw(img)
    d.rectangle([0,0,RIGHT_W,44], fill=HEAD)
    d.text((16,10), "● ● ●   copilot — ~/  ", fill=(180,180,180), font=F_MONO)

    lines_to_draw = []  # (color, text)
    for style, text in history:
        if style == "prompt":
            for i, c in enumerate(wrap(text, MAX_CHARS-2)):
                lines_to_draw.append((USER, ("❯ " if i==0 else "  ") + c))
        elif style == "assist":
            for c in wrap("✓ "+text, MAX_CHARS):
                lines_to_draw.append((ACK, c))
        elif style == "sys":
            for c in wrap(text, MAX_CHARS):
                lines_to_draw.append((GRAY, c))
        else:
            for c in wrap(text, MAX_CHARS):
                lines_to_draw.append((FG, c))
        lines_to_draw.append((FG, ""))  # spacer

    if current_typing is not None:
        style, txt = current_typing
        chunks = wrap(txt, MAX_CHARS-2)
        for i, c in enumerate(chunks):
            lines_to_draw.append((USER, ("❯ " if i==0 else "  ") + c))

    # tail to fit
    max_lines = (H - 60) // LINE_H
    if len(lines_to_draw) > max_lines:
        lines_to_draw = lines_to_draw[-max_lines:]

    y = 60
    for color, text in lines_to_draw:
        d.text((16, y), text, fill=color, font=F_MONO)
        y += LINE_H

    if current_typing is not None and cursor_visible:
        last = lines_to_draw[-1][1] if lines_to_draw else ""
        cx = 16 + len(last) * 11
        cy = y - LINE_H
        d.rectangle([cx, cy+2, cx+11, cy+22], fill=FG)
    return img

def compose(fusion_img, term_img, caption=None, faded_alpha=None, prev_fusion=None):
    out = Image.new("RGB", (W, H), (20, 22, 26))
    if prev_fusion is not None and faded_alpha is not None:
        # crossfade between prev and current fusion
        f1 = prev_fusion.resize((LEFT_W, H)) if prev_fusion.size != (LEFT_W, H) else prev_fusion
        f2 = fusion_img.resize((LEFT_W, H)) if fusion_img.size != (LEFT_W, H) else fusion_img
        blended = Image.blend(f1, f2, faded_alpha)
        out.paste(blended, (0, 0))
    else:
        f = fusion_img.resize((LEFT_W, H)) if fusion_img.size != (LEFT_W, H) else fusion_img
        out.paste(f, (0, 0))
    out.paste(term_img, (LEFT_W, 0))
    d = ImageDraw.Draw(out)
    d.line([(LEFT_W, 0), (LEFT_W, H)], fill=(50,55,65), width=2)
    if caption:
        cf = font(36)
        bbox = d.textbbox((0,0), caption, font=cf)
        pad=18; bw=bbox[2]-bbox[0]+pad*2; bh=bbox[3]-bbox[1]+pad*2
        x=30; y=H-bh-30
        d.rectangle([x,y,x+bw,y+bh], fill=(20,22,26))
        d.text((x+pad, y+pad-bbox[1]), caption, fill=(255,255,255), font=cf)
    return out

def make_card(path, title, subtitle=""):
    img = Image.new("RGB", (W,H), (20,22,26))
    d = ImageDraw.Draw(img)
    f1 = font(96); f2 = font(48)
    tw = d.textbbox((0,0), title, font=f1)[2]
    d.text(((W-tw)//2, H//2-120), title, fill=(255,255,255), font=f1)
    if subtitle:
        sw = d.textbbox((0,0), subtitle, font=f2)[2]
        d.text(((W-sw)//2, H//2+20), subtitle, fill=(110,200,150), font=f2)
    img.save(path)

# ---- Sequence ----
seq = []  # list of (image_path, duration_seconds)
frame_idx = [0]
def add_frame(img, dur=1.0/FPS):
    p = os.path.join(WORK, f"f_{frame_idx[0]:05d}.png")
    img.save(p)
    seq.append((p, dur))
    frame_idx[0] += 1

# Intro
intro = os.path.join(WORK, "intro.png")
make_card(intro, "Fusion 360 × Copilot CLI", "Build a robot arm — with words.")
seq.append((intro, 2.5))

# Initial Fusion empty + sys lines
fusion_imgs = {fn: Image.open(os.path.join(FRAMES, fn)).convert("RGB") for fn in sorted(os.listdir(FRAMES)) if fn.endswith(".png")}
empty_img = fusion_imgs["00_empty.png"]

history = [
    ("sys", "$ copilot"),
    ("sys", "Connected to fusion360 MCP server"),
    ("sys", "Active design: 無題 (empty)"),
    ("sys", ""),
]

steps = [
    ("01_base.png",     "Base ベース",        "土台を作って。半径6cm 高さ2cm の円柱。Baseと命名。",
     "create_cylinder r=6 h=2 → Base"),
    ("02_yaw.png",      "Yaw ヨー軸",         "Baseの上にヨー軸の円柱、半径2.5cm 高さ3cm。YawJoint。",
     "create_cylinder r=2.5 h=3 z=2 → YawJoint"),
    ("03_upperarm.png", "Upper Arm 上腕",    "上腕、3×3×12cmの直方体、中心(0,0,11)。UpperArm。",
     "create_box 3×3×12 → UpperArm"),
    ("04_elbow.png",    "Elbow 肘ピッチ軸",   "肘軸、Y方向に半径2cm 長さ4cmの円柱。ElbowPivot。",
     "create_cylinder axis=Y → ElbowPivot"),
    ("05_forearm.png",  "Forearm 前腕",       "前腕、2.5×2.5×10cmの直方体、中心(0,0,22)。",
     "create_box 2.5×2.5×10 → Forearm"),
    ("06_gripper.png",  "Gripper グリッパー",  "二本指のグリッパー。0.6×2×3cmを±1.5に2つ。",
     "create_box ×2 → GripperL, GripperR"),
]

prev_fusion = empty_img
for i, (fn, cap, prompt, ack) in enumerate(steps):
    new_fusion = fusion_imgs[fn]
    cur_fusion_for_typing = prev_fusion  # while typing, show old state

    # Typewriter animation
    chars_total = len(prompt)
    type_frames = max(int(chars_total / TYPE_CPS * FPS), 12)
    for k in range(type_frames):
        progress = (k+1) / type_frames
        n_chars = int(chars_total * progress)
        partial = prompt[:n_chars]
        cursor_visible = (k % 8) < 5
        term = render_terminal(history, current_typing=("prompt", partial), cursor_visible=cursor_visible)
        img = compose(cur_fusion_for_typing, term, caption=f"Step {i+1}: {cap}")
        add_frame(img)

    # Pause briefly with full prompt + cursor
    for k in range(int(FPS*0.4)):
        cursor_visible = (k % 8) < 5
        term = render_terminal(history, current_typing=("prompt", prompt), cursor_visible=cursor_visible)
        img = compose(cur_fusion_for_typing, term, caption=f"Step {i+1}: {cap}")
        add_frame(img)

    # Commit prompt to history & show response while crossfading fusion
    history.append(("prompt", prompt))
    cross_frames = int(FPS*0.5)
    for k in range(cross_frames):
        a = (k+1)/cross_frames
        # response appears halfway
        if k > cross_frames//2:
            disp_history = history + [("assist", ack)]
        else:
            disp_history = history
        term = render_terminal(disp_history)
        img = compose(new_fusion, term, caption=f"Step {i+1}: {cap}",
                      faded_alpha=a, prev_fusion=cur_fusion_for_typing)
        add_frame(img)
    history.append(("assist", ack))

    # Hold
    term = render_terminal(history)
    hold_img = compose(new_fusion, term, caption=f"Step {i+1}: {cap}")
    p = os.path.join(WORK, f"hold_{i:02d}.png"); hold_img.save(p)
    seq.append((p, 1.2))
    prev_fusion = new_fusion

# Final reveal: type one more prompt then orbit
final_prompt = "全部できた？360°で見せて。"
final_ack = "7 bodies created. Rotating view…"
chars_total = len(final_prompt)
type_frames = max(int(chars_total / TYPE_CPS * FPS), 12)
for k in range(type_frames):
    progress = (k+1)/type_frames
    partial = final_prompt[:int(chars_total*progress)]
    cv = (k%8)<5
    term = render_terminal(history, current_typing=("prompt", partial), cursor_visible=cv)
    img = compose(prev_fusion, term, caption="Reveal")
    add_frame(img)

history.append(("prompt", final_prompt))
history.append(("assist", final_ack))
term_done = render_terminal(history)

orbit_files = sorted(f for f in fusion_imgs if f.startswith("07_orbit_"))
for fn in orbit_files:
    img = compose(fusion_imgs[fn], term_done, caption="Done — 6 prompts, 1 robot arm")
    add_frame(img, dur=2.0/FPS)

# Export step
history.append(("prompt", "F3DとSTLでエクスポートして。"))
history.append(("assist", "Exported robot_arm.f3d, robot_arm_upperarm.stl"))
term_exp = render_terminal(history)
exp_img = compose(fusion_imgs[orbit_files[0]], term_exp, caption="Export")
p = os.path.join(WORK, "export.png"); exp_img.save(p); seq.append((p, 2.5))

# Outro
outro = os.path.join(WORK, "outro.png")
make_card(outro, "Natural language → CAD", "GitHub Copilot CLI × MCP")
seq.append((outro, 3.0))

# Concat
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
    "-c:v", "libx264", "-preset", "medium", "-crf", "22",
    "-movflags", "+faststart",
    OUT_MP4,
]
print(f"Running ffmpeg on {len(seq)} frames…")
r = subprocess.run(cmd, capture_output=True, text=True)
if r.returncode != 0:
    print(r.stderr[-2000:]); sys.exit(r.returncode)
print(f"OK → {OUT_MP4}  ({os.path.getsize(OUT_MP4)/1024:.1f} KB)")
