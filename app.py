import streamlit as st
import time
import json
import os
import hashlib
import numpy as np
import PIL.Image
from datetime import datetime

# -----------------------------------------------------------------------------
# MoviePy / PIL Antialias Fix
# -----------------------------------------------------------------------------
if not hasattr(PIL.Image, 'ANTIALIAS'):
    PIL.Image.ANTIALIAS = PIL.Image.Resampling.LANCZOS

try:
    from moviepy.editor import VideoFileClip, concatenate_videoclips, ImageClip, CompositeVideoClip, AudioFileClip, CompositeAudioClip
    import moviepy.video.fx.all as vfx
    import moviepy.audio.fx.all as afx
except ImportError:
    from moviepy import VideoFileClip, concatenate_videoclips, ImageClip, CompositeVideoClip, AudioFileClip, CompositeAudioClip
    import moviepy.video.fx as vfx
    import moviepy.audio.fx as afx

# -----------------------------------------------------------------------------
# Setup & Database Configuration
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="No Copyright Video Studio", 
    page_icon="🎬", 
    layout="centered"
)

DB_FILE = "database.json"

def hash_text(text):
    return hashlib.sha256(text.encode()).hexdigest()

ADMIN_EMAIL_HASH = hash_text("krish9agupt@gmail.com")
ADMIN_PASSCODE_HASH = hash_text("Krish9A")
USER_PASSCODE = "123456"
UPI_ID = "cinepoliis@ibl"

def load_db():
    if not os.path.exists(DB_FILE):
        default_db = {"users": {}, "pending_requests": [], "support_tickets": [], "history": {}}
        with open(DB_FILE, "w") as f:
            json.dump(default_db, f, indent=4)
        return default_db
    try:
        with open(DB_FILE, "r") as f:
            data = json.load(f)
            if "history" not in data: data["history"] = {}
            if "users" not in data: data["users"] = {}
            if "pending_requests" not in data: data["pending_requests"] = []
            if "support_tickets" not in data: data["support_tickets"] = []
            return data
    except Exception:
        return {"users": {}, "pending_requests": [], "support_tickets": [], "history": {}}

# Safe JSON Save Mechanism (Force Flush & OS Sync)
def save_db(data):
    with open(DB_FILE, "w") as f:
        json.dump(data, f, indent=4)
        f.flush()
        os.fsync(f.fileno())

if "theme" not in st.session_state:
    st.session_state.theme = "dark"

bg_color = "#0B0C10" if st.session_state.theme == "dark" else "#FFFFFF"
text_color = "#FFFFFF" if st.session_state.theme == "dark" else "#000000"
card_bg = "#121212" if st.session_state.theme == "dark" else "#F0F2F5"

st.markdown(f"""
    <style>
    #MainMenu {{visibility: hidden;}}
    header {{visibility: hidden;}}
    footer {{visibility: hidden;}}
    [data-testid="stHeader"] {{display: none;}}
    .stApp {{ background-color: {bg_color}; color: {text_color}; }}
    [data-testid="stSidebar"] {{ display: none; }}
    .main-header {{
        text-align: center; font-weight: 900;
        background: linear-gradient(45deg, #FFD700, #FF69B4);
        -webkit-background-clip: text; -webkit-text-fill-color: transparent;
    }}
    .plan-card {{
        background: {card_bg}; border: 2px solid #FFD700; border-radius: 15px;
        padding: 1rem; text-align: center; margin-bottom: 1rem;
    }}
    .stButton>button {{
        width: 100%; border-radius: 10px; height: 3em;
        background: linear-gradient(90deg, #FFD700, #FF69B4); color: #000; font-weight: bold; border: none;
    }}
    </style>
""", unsafe_allow_html=True)

if "logged_in" not in st.session_state: st.session_state.logged_in = False
if "user_email" not in st.session_state: st.session_state.user_email = ""
if "is_admin" not in st.session_state: st.session_state.is_admin = False
if "selected_plan" not in st.session_state: st.session_state.selected_plan = None

# -----------------------------------------------------------------------------
# Video Engine Logic
# -----------------------------------------------------------------------------
def manual_zoom(clip, zoom_factor):
    def zoom_frame(image):
        h, w, c = image.shape
        crop_h, crop_w = int(h / zoom_factor), int(w / zoom_factor)
        top, left = (h - crop_h) // 2, (w - crop_w) // 2
        cropped = image[top:top+crop_h, left:left+crop_w]
        resizer = PIL.Image.Resampling.LANCZOS if hasattr(PIL.Image, 'Resampling') else PIL.Image.BICUBIC
        img_pil = PIL.Image.fromarray(cropped)
        return np.array(img_pil.resize((w, h), resizer))
    return clip.fl_image(zoom_frame)

def apply_custom_effects(clip, edit_num):
    if edit_num in [2, 8]: clip = manual_zoom(clip, 1.10)
    elif edit_num == 3: clip = clip.speedx(1.3) if hasattr(clip, 'speedx') else clip
    elif edit_num in [4, 13]: clip = clip.fx(vfx.colorx, 0.85) if hasattr(vfx, 'colorx') else clip
    elif edit_num in [5, 11, 15]: clip = clip.fx(vfx.colorx, 1.30) if hasattr(vfx, 'colorx') else clip
    elif edit_num == 6: clip = clip.fl_image(lambda img: img[:, ::-1])
    elif edit_num == 7: clip = clip.fx(vfx.colorx, 1.15) if hasattr(vfx, 'colorx') else clip
    elif edit_num == 9: clip = clip.speedx(1.2) if hasattr(clip, 'speedx') else clip
    elif edit_num == 10: clip = manual_zoom(clip, 1.05)
    elif edit_num == 12: clip = manual_zoom(clip, 1.15)
    elif edit_num == 14:
        clip = clip.fl_image(lambda img: img[:, ::-1])
        if hasattr(clip, 'speedx'): clip = clip.speedx(1.25)

    speed_factor = {1: 1.0, 2: 0.97, 3: 0.94, 4: 0.91, 5: 0.89}.get(edit_num, 1.0)
    if clip.audio is not None and speed_factor != 1.0:
        audio = clip.audio.fl_time(lambda t: t * speed_factor)
        clip.audio = audio.set_duration(clip.duration)

    return clip

def process_single_video(input_path, output_path, target_height, bitrate, watermark_file, watermark_pos, mute_audio, bg_music_file, progress_bar):
    progress_bar.progress(10, text="🎬 Loading video file...")
    video = VideoFileClip(input_path)
    actual_vid_duration = video.duration
    orig_w, orig_h = video.size
    
    clips = []
    cut_duration = actual_vid_duration / 15.0

    for edit_idx in range(1, 16):
        pct = 10 + int((edit_idx / 15.0) * 50)
        progress_bar.progress(pct, text=f"⚡ Applying Sequence Effect #{edit_idx}/15...")
        seg_start = (edit_idx - 1) * cut_duration
        seg_end = edit_idx * cut_duration
        subclip = video.subclip(seg_start, seg_end)
        clips.append(apply_custom_effects(subclip, edit_idx))

    final_clip = concatenate_videoclips(clips)

    if orig_h != target_height:
        progress_bar.progress(65, text="📐 Resizing Video Dimensions...")
        aspect_ratio = orig_w / float(orig_h)
        new_w = int(target_height * aspect_ratio)
        if new_w % 2 != 0: new_w += 1
        final_clip = final_clip.resize(newsize=(new_w, target_height))

    # Watermark Processing
    if watermark_file is not None:
        progress_bar.progress(72, text="🖼️ Adding Custom Logo Overlay...")
        wm_path = "temp_wm.png"
        with open(wm_path, "wb") as f: f.write(watermark_file.read())
        pos_map = {"Top-Left": ("left", "top"), "Top-Right": ("right", "top"), "Bottom-Left": ("left", "bottom"), "Bottom-Right": ("right", "bottom")}
        logo = (ImageClip(wm_path).set_duration(final_clip.duration).resize(height=int(final_clip.h * 0.12)).set_pos(pos_map.get(watermark_pos, ("right", "bottom"))))
        final_clip = CompositeVideoClip([final_clip, logo])

    # Audio Customization
    if mute_audio:
        progress_bar.progress(80, text="🔇 Muting Original Audio...")
        final_clip = final_clip.without_audio()
    elif bg_music_file is not None:
        progress_bar.progress(80, text="🎵 Mixing Non-Copyright Music (Vol 2.0)...")
        music_path = "temp_music.mp3"
        with open(music_path, "wb") as f: f.write(bg_music_file.read())
        bg_audio = AudioFileClip(music_path).volumex(2.0)
        bg_audio = afx.audio_loop(bg_audio, duration=final_clip.duration) if bg_audio.duration < final_clip.duration else bg_audio.subclip(0, final_clip.duration)
        final_clip.audio = CompositeAudioClip([final_clip.audio, bg_audio]) if final_clip.audio is not None else bg_audio

    progress_bar.progress(88, text="⚙️ Rendering & Encoding Final Output...")
    final_clip.write_videofile(output_path, codec="libx264", audio_codec="aac", bitrate=bitrate, preset="ultrafast", threads=4, logger=None)
    progress_bar.progress(100, text="✅ Video Processing Complete!")

# -----------------------------------------------------------------------------
# Dashboard UI
# -----------------------------------------------------------------------------
st.markdown("<h1 class='main-header'>🎬 NO COPYRIGHT VIDEO STUDIO</h1>", unsafe_allow_html=True)

if not st.session_state.logged_in:
    st.subheader("🔑 Access Dashboard")
    with st.form("login_form"):
        email = st.text_input("Email Address")
        passcode = st.text_input("Access Passcode", type="password")
        if st.form_submit_button("🚀 Enter Studio"):
            clean_email = email.lower().strip()
            if hash_text(clean_email) == ADMIN_EMAIL_HASH and hash_text(passcode) == ADMIN_PASSCODE_HASH:
                st.session_state.logged_in, st.session_state.user_email, st.session_state.is_admin = True, clean_email, True
                st.rerun()
            elif clean_email and passcode == USER_PASSCODE:
                db = load_db()
                # Strict Persistence Check: केवल बिलकुल नए यूजर को 10 कॉइन मिलेंगे
                if clean_email not in db["users"]:
                    db["users"][clean_email] = 10
                    save_db(db)
                st.session_state.logged_in, st.session_state.user_email, st.session_state.is_admin = True, clean_email, False
                st.rerun()
            else: st.error("Invalid Credentials!")

else:
    current_user = st.session_state.user_email
    db_data = load_db()
    
    # Strict Balance Load: डेटाबेस में जो balance दर्ज है वही दिखाया जाएगा
    if not st.session_state.is_admin:
        if current_user not in db_data["users"]:
            db_data["users"][current_user] = 10
            save_db(db_data)
        user_coins = db_data["users"][current_user]
    else:
        user_coins = 99999

    m1, m2, m3 = st.columns(3)
    m1.metric("Available Coins", f"🪙 {user_coins}")
    m2.metric("Account Status", "PRO Active")
    m3.metric("Upload Limit", "200 MB")

    if st.button("Sign Out"):
        st.session_state.logged_in = False
        st.rerun()

    st.divider()

    # Dynamic Tabs Order Requested
    tabs_list = ["📹 Sequence Studio", "📜 Download History", "🪙 Scan & Buy Coins", "💬 Help & Support"]
    if st.session_state.is_admin: tabs_list.append("⚙️ Admin Control")
    
    tabs = st.tabs(tabs_list)

    # 1. SEQUENCE STUDIO
    with tabs[0]:
        st.header("📤 15-Edit Sequence Video Processor")
        proc_mode = st.radio("Choose Processing Mode:", ["Single Video Edit", "Bulk / Batch Editing (2-3 Videos)"])
        
        uploaded_files = []
        if proc_mode == "Single Video Edit":
            file = st.file_uploader("Choose video file", type=["mp4", "mov", "mkv", "avi"], key="s_up")
            if file: uploaded_files.append(file)
        else:
            files = st.file_uploader("Choose up to 3 videos", type=["mp4", "mov", "mkv", "avi"], accept_multiple_files=True, key="b_up")
            if files: uploaded_files = files[:3]

        if uploaded_files:
            quality_option = st.radio("Choose Export Quality:", ["720p (Free)", "1080p Full HD (3 Coins)", "2K Ultra HD (5 Coins)", "4K Ultra HD (10 Coins)"])
            res_map = {"720p (Free)": (720, 0, "4000k"), "1080p Full HD (3 Coins)": (1080, 3, "12000k"), "2K Ultra HD (5 Coins)": (1440, 5, "24000k"), "4K Ultra HD (10 Coins)": (2160, 10, "45000k")}
            target_height, quality_coins, bitrate = res_map[quality_option]

            # Calculate total coins needed
            total_required_coins = 0
            for file in uploaded_files:
                base = 5 if (file.size / (1024 * 1024)) < 50 else 10
                total_required_coins += (base + quality_coins)

            st.info(f"🪙 **Total Required Coins:** `{total_required_coins} Coins`")

            # Branding/Audio Options
            wm_file = st.file_uploader("Upload Logo Overlay (Optional)", type=["png", "jpg"])
            wm_pos = st.selectbox("Logo Position", ["Bottom-Right", "Bottom-Left", "Top-Right", "Top-Left"]) if wm_file else "Bottom-Right"
            mute_audio = st.checkbox("Mute Original Video Sound")
            bg_music_file = st.file_uploader("Background Music (Vol 2.0)", type=["mp3", "wav"])

            if st.button(f"🚀 Start Processing & Deduct {total_required_coins} Coins", type="primary"):
                fresh_db = load_db()
                bal = fresh_db["users"].get(current_user, 0) if not st.session_state.is_admin else 999999

                if bal >= total_required_coins:
                    # COIN DEDUCTION (Safe Forced JSON Save)
                    if not st.session_state.is_admin:
                        fresh_db["users"][current_user] -= total_required_coins
                        save_db(fresh_db)
                        st.toast(f"🪙 {total_required_coins} Coins Deducted Successfully!", icon="💸")

                    if not os.path.exists("exports"): os.makedirs("exports")

                    for idx, up_file in enumerate(uploaded_files):
                        st.subheader(f"🎬 Processing Video {idx+1}/{len(uploaded_files)}: {up_file.name}")
                        p_bar = st.progress(0, text="Initializing Engine...")
                        
                        temp_in = f"temp_{idx}.mp4"
                        out_path = f"exports/{int(time.time())}_{idx}_{up_file.name}"
                        with open(temp_in, "wb") as f: f.write(up_file.read())

                        try:
                            # REALTIME PROGRESS BAR DRIVEN FUNCTION
                            process_single_video(temp_in, out_path, target_height, bitrate, wm_file, wm_pos, mute_audio, bg_music_file, p_bar)
                            
                            # Add to History DB & Safe Save
                            db_hist = load_db()
                            if current_user not in db_hist["history"]: db_hist["history"][current_user] = []
                            db_hist["history"][current_user].append({
                                "filename": up_file.name,
                                "path": out_path,
                                "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                                "quality": quality_option.split()[0],
                                "coins": (5 if (up_file.size / (1024*1024)) < 50 else 10) + quality_coins
                            })
                            save_db(db_hist)
                            
                        except Exception as e:
                            st.error(f"Error processing {up_file.name}: {str(e)}")

                    st.balloons()
                    st.success("🎉 All videos processed successfully!")
                    time.sleep(1)
                    st.rerun()
                else:
                    st.error(f"❌ Insufficient Balance! You need {total_required_coins} Coins.")

    # 2. DOWNLOAD HISTORY
    with tabs[1]:
        st.header("📜 Download History")
        user_history = db_data.get("history", {}).get(current_user, [])
        if not user_history:
            st.info("No videos edited yet.")
        else:
            for item in reversed(user_history):
                st.write(f"📹 **File:** `{item['filename']}`")
                st.caption(f"🗓️ {item['date']} | Quality: {item['quality']} | Deducted: {item['coins']} Coins")
                if os.path.exists(item['path']):
                    with open(item['path'], "rb") as f:
                        st.download_button(f"📥 Download ({item['quality']})", f, file_name=f"edited_{item['filename']}", key=item['path'])
                else: st.warning("File expired on server.")
                st.divider()

    # 3. SCAN & BUY COINS
    with tabs[2]:
        st.header("🪙 Scan & Buy Coins")
        plans = [("Starter", 49, 50), ("Popular", 99, 110), ("Value", 199, 221), ("Mega Pro", 399, 500)]
        cols = st.columns(2)
        for idx, (pname, amt, c_val) in enumerate(plans):
            with cols[idx % 2]:
                st.markdown(f"<div class='plan-card'><h3>{pname}</h3><h2>₹{amt}</h2><p>🪙 {c_val} Coins</p></div>", unsafe_allow_html=True)
                if st.button(f"Buy ₹{amt}", key=f"plan_{idx}"):
                    st.session_state.selected_plan = (pname, amt, c_val)

        if st.session_state.selected_plan:
            pname, amt, c_val = st.session_state.selected_plan
            st.divider()
            st.subheader(f"📲 Pay ₹{amt} via UPI")
            st.image(f"https://api.qrserver.com/v1/create-qr-code/?size=200x200&data=upi://pay?pa={UPI_ID}%26am={amt}", width=180)
            utr = st.text_input("Enter 12-Digit UTR No.", max_chars=12)
            if st.button("Submit UTR"):
                if len(utr) == 12 and utr.isdigit():
                    db_u = load_db()
                    db_u["pending_requests"].append({"user": current_user, "utr": utr, "amount": amt, "coins": c_val})
                    save_db(db_u)
                    st.success("Submitted for Admin Approval!")
                    st.session_state.selected_plan = None
                else: st.error("Enter valid 12-digit numeric UTR")

    # 4. HELP & SUPPORT
    with tabs[3]:
        st.header("💬 Help & Support")
        with st.form("sup_f", clear_on_submit=True):
            msg = st.text_area("Write your query:")
            if st.form_submit_button("Send Ticket"):
                if msg.strip():
                    db_s = load_db()
                    db_s["support_tickets"].append({"user": current_user, "message": msg.strip(), "reply": "", "status": "Pending"})
                    save_db(db_s)
                    st.success("Ticket Sent!")

        st.divider()
        tickets = [t for t in db_data.get("support_tickets", []) if t.get("user") == current_user]
        for t in reversed(tickets):
            st.write(f"**You:** {t['message']}")
            if t.get("reply"): st.success(f"**Admin:** {t['reply']}")
            else: st.warning("Waiting for reply...")
            st.divider()

    # 5. ADMIN CONTROL (IF ADMIN)
    if st.session_state.is_admin and len(tabs) > 4:
        with tabs[4]:
            st.header("⚙️ Admin Panel")
            db_a = load_db()
            for idx, req in enumerate(list(db_a.get("pending_requests", []))):
                st.write(f"User: `{req['user']}` | Amt: ₹{req['amount']} | UTR: `{req['utr']}`")
                if st.button(f"Approve {req['coins']} Coins", key=f"ap_{idx}"):
                    db_a["users"][req['user']] = db_a["users"].get(req['user'], 0) + req['coins']
                    db_a["pending_requests"].pop(idx)
                    save_db(db_a)
                    st.rerun()
