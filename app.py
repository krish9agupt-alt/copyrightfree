import streamlit as st
import time
import json
import os
import hashlib
import numpy as np
import PIL.Image
from datetime import datetime

# -----------------------------------------------------------------------------
# MoviePy / PIL Antialias Compatibility Fix
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
# App Setup & Configuration
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="No Copyright Video Studio", 
    page_icon="🎬", 
    layout="wide",
    initial_sidebar_state="expanded"
)

DB_FILE = "database.json"

def hash_text(text):
    return hashlib.sha256(text.encode()).hexdigest()

ADMIN_EMAIL_HASH = hash_text("krish9agupt@gmail.com")
ADMIN_PASSCODE_HASH = hash_text("Krish9A")
USER_PASSCODE = "123456"
UPI_ID = "cinepoliis@ibl"

# -----------------------------------------------------------------------------
# Safe Database Operations
# -----------------------------------------------------------------------------
def load_db():
    if not os.path.exists(DB_FILE):
        default_db = {
            "users": {},
            "pending_requests": [],
            "support_tickets": [],
            "history": {}
        }
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

def save_db(data):
    with open(DB_FILE, "w") as f:
        json.dump(data, f, indent=4)
        f.flush()
        os.fsync(f.fileno())

# -----------------------------------------------------------------------------
# Theme & State Management
# -----------------------------------------------------------------------------
if "theme" not in st.session_state:
    st.session_state.theme = "dark"

if "logged_in" not in st.session_state: 
    st.session_state.logged_in = False
    
if "user_email" not in st.session_state: 
    st.session_state.user_email = ""
    
if "is_admin" not in st.session_state: 
    st.session_state.is_admin = False
    
if "selected_plan" not in st.session_state: 
    st.session_state.selected_plan = None

# Custom CSS with Wallpaper & Hidden Top Icons
WALLPAPER_URL = "https://i.ibb.co/3ykXgY8/doodle-bg.jpg"

st.markdown(f"""
    <style>
    /* Hide Streamlit Header, Toolbar, Footer & 3 Top Icons */
    #MainMenu {{visibility: hidden;}}
    header {{visibility: hidden;}}
    footer {{visibility: hidden;}}
    [data-testid="stHeader"] {{display: none !important;}}
    [data-testid="stToolbar"] {{display: none !important;}}
    .stAppToolbar {{display: none !important;}}

    /* Full Background Wallpaper with Dark Overlay for Text Visibility */
    .stApp {{ 
        background: linear-gradient(rgba(11, 12, 16, 0.82), rgba(11, 12, 16, 0.82)), 
                    url('https://img.freepik.com/free-vector/hand-drawn-no-copyright-doodles_23-2150385966.jpg');
        background-size: cover;
        background-position: center;
        background-attachment: fixed;
        color: #FFFFFF;
    }}
    
    [data-testid="stSidebar"] {{ 
        background-color: rgba(31, 40, 51, 0.95); 
    }}
    
    /* Make Input Text Labels Bright White & Bold */
    label, div[data-aria-hidden="true"], .stWidgetLabel p {{
        color: #FFFFFF !important;
        font-weight: 700 !important;
        font-size: 1.05rem !important;
    }}
    
    .main-header {{
        text-align: center; font-weight: 900; font-size: 2.5rem;
        background: linear-gradient(45deg, #FFD700, #FF69B4);
        -webkit-background-clip: text; -webkit-text-fill-color: transparent;
        margin-bottom: 20px;
        text-shadow: 2px 2px 8px rgba(0,0,0,0.8);
    }}
    
    .plan-card {{
        background: rgba(18, 18, 18, 0.9); border: 2px solid #FFD700; border-radius: 15px;
        padding: 1.5rem; text-align: center; margin-bottom: 1rem;
        box-shadow: 0 4px 15px rgba(0,0,0,0.5);
    }}
    
    .stButton>button {{
        width: 100%; border-radius: 10px; height: 3em;
        background: linear-gradient(90deg, #FFD700, #FF69B4); 
        color: #000; font-weight: bold; border: none;
    }}
    </style>
""", unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# Video Editing Processing Functions
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

    if watermark_file is not None:
        progress_bar.progress(72, text="🖼️ Adding Custom Logo Overlay...")
        wm_path = "temp_wm.png"
        with open(wm_path, "wb") as f: f.write(watermark_file.read())
        pos_map = {"Top-Left": ("left", "top"), "Top-Right": ("right", "top"), "Bottom-Left": ("left", "bottom"), "Bottom-Right": ("right", "bottom")}
        logo = (ImageClip(wm_path).set_duration(final_clip.duration).resize(height=int(final_clip.h * 0.12)).set_pos(pos_map.get(watermark_pos, ("right", "bottom"))))
        final_clip = CompositeVideoClip([final_clip, logo])

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
# SIDEBAR CONTROLS (Theme Toggle & User Profile)
# -----------------------------------------------------------------------------
with st.sidebar:
    st.title("⚙️ Studio Settings")
    
    st.subheader("🎨 Appearance Mode")
    theme_choice = st.radio("Select Theme:", ["🌙 Dark Mode", "☀️ Light Mode"], index=0 if st.session_state.theme == "dark" else 1)
    new_theme = "dark" if "Dark" in theme_choice else "light"
    if new_theme != st.session_state.theme:
        st.session_state.theme = new_theme
        st.rerun()

    st.divider()

    if st.session_state.logged_in:
        st.subheader("👤 Account Info")
        st.write(f"**Email:** `{st.session_state.user_email}`")
        if st.session_state.is_admin:
            st.markdown("👑 **Role:** `Administrator`")
        else:
            st.markdown("⭐ **Role:** `Pro User`")
        
        st.divider()
        if st.button("🚪 Log Out"):
            st.session_state.logged_in = False
            st.session_state.user_email = ""
            st.session_state.is_admin = False
            st.rerun()

# -----------------------------------------------------------------------------
# DASHBOARD UI
# -----------------------------------------------------------------------------
st.markdown("<h1 class='main-header'>🎬 NO COPYRIGHT VIDEO STUDIO PRO</h1>", unsafe_allow_html=True)

if not st.session_state.logged_in:
    st.subheader("🔑 Sign In to Studio Account")
    with st.form("login_form"):
        email = st.text_input("Enter Email Address")
        passcode = st.text_input("Access Passcode", value=USER_PASSCODE, type="password")
        submit_btn = st.form_submit_button("🚀 Enter Studio Dashboard")
        
        if submit_btn:
            clean_email = email.lower().strip()
            if hash_text(clean_email) == ADMIN_EMAIL_HASH and hash_text(passcode) == ADMIN_PASSCODE_HASH:
                st.session_state.logged_in = True
                st.session_state.user_email = clean_email
                st.session_state.is_admin = True
                st.rerun()
            elif clean_email and (passcode == USER_PASSCODE or hash_text(passcode) == ADMIN_PASSCODE_HASH):
                db = load_db()
                if clean_email not in db["users"]:
                    db["users"][clean_email] = 10
                    save_db(db)
                st.session_state.logged_in = True
                st.session_state.user_email = clean_email
                st.session_state.is_admin = False
                st.rerun()
            else:
                st.error("❌ Please enter a valid Email Address!")

else:
    current_user = st.session_state.user_email
    db_data = load_db()
    
    if not st.session_state.is_admin:
        if current_user not in db_data["users"]:
            db_data["users"][current_user] = 10
            save_db(db_data)
        user_coins = db_data["users"][current_user]
    else:
        user_coins = 99999

    m1, m2, m3 = st.columns(3)
    m1.metric("Available Coins", f"🪙 {user_coins}")
    m2.metric("Account Plan", "PRO Unlocked")
    m3.metric("Upload Limit", "200 MB")

    st.divider()

    tabs_list = ["📹 Dynamic Sequence Studio", "📜 Download History", "🪙 Scan & Recharge Coins", "💬 Help & Support"]
    if st.session_state.is_admin:
        tabs_list.append("⚙️ Admin Control Panel")
    
    tabs = st.tabs(tabs_list)

    # TAB 1: SEQUENCE VIDEO STUDIO
    with tabs[0]:
        st.header("📤 15-Edit Sequence Video Processor")
        proc_mode = st.radio("Choose Mode:", ["Single Video Processing", "Bulk Batch Processing (2-3 Videos)"])
        
        uploaded_files = []
        if proc_mode == "Single Video Processing":
            file = st.file_uploader("Upload Target Video", type=["mp4", "mov", "mkv", "avi"], key="single_up")
            if file: uploaded_files.append(file)
        else:
            files = st.file_uploader("Upload Batch Videos (Max 3)", type=["mp4", "mov", "mkv", "avi"], accept_multiple_files=True, key="bulk_up")
            if files: uploaded_files = files[:3]

        if uploaded_files:
            st.divider()
            st.subheader("⚙️ Quality & Watermark Customization")
            quality_option = st.radio("Select Export Quality:", ["720p HD (Free)", "1080p Full HD (3 Coins)", "2K Ultra HD (5 Coins)", "4K Ultra HD (10 Coins)"])
            res_map = {
                "720p HD (Free)": (720, 0, "4000k"),
                "1080p Full HD (3 Coins)": (1080, 3, "12000k"),
                "2K Ultra HD (5 Coins)": (1440, 5, "24000k"),
                "4K Ultra HD (10 Coins)": (2160, 10, "45000k")
            }
            target_height, quality_coins, bitrate = res_map[quality_option]

            total_required_coins = 0
            for file in uploaded_files:
                base = 5 if (file.size / (1024 * 1024)) < 50 else 10
                total_required_coins += (base + quality_coins)

            st.info(f"🪙 **Total Deductible Coins:** `{total_required_coins} Coins`")

            col_wm1, col_wm2 = st.columns(2)
            with col_wm1:
                wm_file = st.file_uploader("Upload Logo Watermark (Optional)", type=["png", "jpg"])
            with col_wm2:
                wm_pos = st.selectbox("Logo Position", ["Bottom-Right", "Bottom-Left", "Top-Right", "Top-Left"]) if wm_file else "Bottom-Right"
            
            st.subheader("🎵 Audio Setup")
            col_au1, col_au2 = st.columns(2)
            with col_au1:
                mute_audio = st.checkbox("Mute Original Sound Entirely")
            with col_au2:
                bg_music_file = st.file_uploader("Overlay Non-Copyright Music (Vol 2.0)", type=["mp3", "wav"])

            if st.button(f"🚀 Render Video & Deduct {total_required_coins} Coins", type="primary"):
                fresh_db = load_db()
                bal = fresh_db["users"].get(current_user, 0) if not st.session_state.is_admin else 999999

                if bal >= total_required_coins:
                    if not st.session_state.is_admin:
                        fresh_db["users"][current_user] -= total_required_coins
                        save_db(fresh_db)
                        st.toast(f"🪙 {total_required_coins} Coins Deducted!", icon="💸")

                    if not os.path.exists("exports"): os.makedirs("exports")

                    for idx, up_file in enumerate(uploaded_files):
                        st.subheader(f"🎬 Processing File #{idx+1}: {up_file.name}")
                        p_bar = st.progress(0, text="Initializing Engine...")
                        
                        temp_in = f"temp_{idx}.mp4"
                        out_path = f"exports/{int(time.time())}_{idx}_{up_file.name}"
                        with open(temp_in, "wb") as f: f.write(up_file.read())

                        try:
                            process_single_video(temp_in, out_path, target_height, bitrate, wm_file, wm_pos, mute_audio, bg_music_file, p_bar)
                            
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
                    st.success("🎉 All videos rendered successfully!")
                    time.sleep(1)
                    st.rerun()
                else:
                    st.error(f"❌ Insufficient Balance! You need {total_required_coins} Coins.")

    # TAB 2: DOWNLOAD HISTORY
    with tabs[1]:
        st.header("📜 Exported Videos History")
        user_history = db_data.get("history", {}).get(current_user, [])
        if not user_history:
            st.info("No video processing history found.")
        else:
            for item in reversed(user_history):
                c1, c2 = st.columns([3, 1])
                with c1:
                    st.write(f"📹 **File:** `{item['filename']}`")
                    st.caption(f"🗓️ {item['date']} | Resolution: {item['quality']} | Deducted: {item['coins']} Coins")
                with c2:
                    if os.path.exists(item['path']):
                        with open(item['path'], "rb") as f:
                            st.download_button(f"📥 Download ({item['quality']})", f, file_name=f"edited_{item['filename']}", key=item['path'])
                    else:
                        st.warning("File expired")
                st.divider()

    # TAB 3: SCAN & BUY COINS
    with tabs[2]:
        st.header("🪙 Buy Coins via UPI QR Code")
        plans = [("Starter Pack", 49, 50), ("Popular Pack", 99, 110), ("Value Pack", 199, 221), ("Mega Pro Pack", 399, 500)]
        cols = st.columns(2)
        for idx, (pname, amt, c_val) in enumerate(plans):
            with cols[idx % 2]:
                st.markdown(f"""
                <div class='plan-card'>
                    <h3>{pname}</h3>
                    <h2 style='color:#FFD700;'>₹{amt}</h2>
                    <p style='font-size:1.2rem;'>🪙 <b>{c_val} Coins</b></p>
                </div>
                """, unsafe_allow_html=True)
                if st.button(f"Select ₹{amt} Plan", key=f"plan_{idx}"):
                    st.session_state.selected_plan = (pname, amt, c_val)

        if st.session_state.selected_plan:
            pname, amt, c_val = st.session_state.selected_plan
            st.divider()
            st.subheader(f"📲 Scan & Pay ₹{amt} for {c_val} Coins")
            qr_url = f"https://api.qrserver.com/v1/create-qr-code/?size=200x200&data=upi://pay?pa={UPI_ID}%26am={amt}"
            st.image(qr_url, width=200, caption=f"Pay ₹{amt} to UPI ID: {UPI_ID}")
            
            utr = st.text_input("Enter 12-Digit Transaction UTR No.", max_chars=12)
            if st.button("Submit Payment for Verification"):
                if len(utr) == 12 and utr.isdigit():
                    db_u = load_db()
                    db_u["pending_requests"].append({"user": current_user, "utr": utr, "amount": amt, "coins": c_val})
                    save_db(db_u)
                    st.success("✅ Payment Details Submitted! Admin will verify soon.")
                    st.session_state.selected_plan = None
                else:
                    st.error("❌ Invalid UTR Number! Must be 12 digits.")

    # TAB 4: HELP & SUPPORT
    with tabs[3]:
        st.header("💬 Help & Support Helpdesk")
        with st.form("sup_form", clear_on_submit=True):
            msg = st.text_area("Describe your issue or question:")
            if st.form_submit_button("Send Support Ticket"):
                if msg.strip():
                    db_s = load_db()
                    db_s["support_tickets"].append({"user": current_user, "message": msg.strip(), "reply": "", "status": "Pending"})
                    save_db(db_s)
                    st.success("Ticket submitted successfully!")

        st.divider()
        st.subheader("📋 Your Queries")
        tickets = [t for t in db_data.get("support_tickets", []) if t.get("user") == current_user]
        if not tickets:
            st.info("No queries asked yet.")
        else:
            for t in reversed(tickets):
                st.write(f"**You:** {t['message']}")
                if t.get("reply"): 
                    st.success(f"**Admin Reply:** {t['reply']}")
                else: 
                    st.warning("Status: Pending Admin Reply...")
                st.divider()

    # TAB 5: ADMIN CONTROL PANEL
    if st.session_state.is_admin and len(tabs) > 4:
        with tabs[4]:
            st.header("⚙️ Admin Dashboard Control")
            db_a = load_db()
            
            st.subheader("💳 Pending Coin Requests")
            pending = db_a.get("pending_requests", [])
            if not pending:
                st.info("No pending payment approvals.")
            else:
                for idx, req in enumerate(list(pending)):
                    st.write(f"**User:** `{req['user']}` | **Amount:** ₹{req['amount']} | **UTR:** `{req['utr']}`")
                    col_ap, col_rj = st.columns(2)
                    with col_ap:
                        if st.button(f"✅ Approve {req['coins']} Coins", key=f"ap_{idx}"):
                            db_a["users"][req['user']] = db_a["users"].get(req['user'], 0) + req['coins']
                            db_a["pending_requests"].pop(idx)
                            save_db(db_a)
                            st.success(f"Approved {req['coins']} coins!")
                            st.rerun()
                    with col_rj:
                        if st.button(f"❌ Reject", key=f"rj_{idx}"):
                            db_a["pending_requests"].pop(idx)
                            save_db(db_a)
                            st.rerun()
                    st.divider()
