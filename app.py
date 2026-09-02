import streamlit as st
import time
import json
import os
import hashlib
import numpy as np
import PIL.Image
from datetime import datetime

# -----------------------------------------------------------------------------
# CRITICAL FIX FOR MOVIEPY / PIL ANTIALIAS DEPRECATION
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
# 1. PAGE CONFIG & THEME STATE
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="No Copyright Video Studio - Dynamic Sequences", 
    page_icon="🎬", 
    layout="centered"
)

if "theme" not in st.session_state:
    st.session_state.theme = "dark"

def hash_text(text):
    return hashlib.sha256(text.encode()).hexdigest()

ADMIN_EMAIL_HASH = hash_text("krish9agupt@gmail.com")
ADMIN_PASSCODE_HASH = hash_text("Krish9A")

USER_PASSCODE = "123456"
UPI_ID = "cinepoliis@ibl"
DB_FILE = "database.json"

def load_db():
    if not os.path.exists(DB_FILE):
        default_db = {"users": {}, "pending_requests": [], "support_tickets": [], "history": {}}
        with open(DB_FILE, "w") as f:
            json.dump(default_db, f, indent=4)
        return default_db
    try:
        with open(DB_FILE, "r") as f:
            data = json.load(f)
            if "history" not in data:
                data["history"] = {}
            return data
    except Exception:
        return {"users": {}, "pending_requests": [], "support_tickets": [], "history": {}}

def save_db(data):
    with open(DB_FILE, "w") as f:
        json.dump(data, f, indent=4)

bg_color = "#0B0C10" if st.session_state.theme == "dark" else "#FFFFFF"
text_color = "#FFFFFF" if st.session_state.theme == "dark" else "#000000"
card_bg = "#121212" if st.session_state.theme == "dark" else "#F0F2F5"

st.markdown(f"""
    <style>
    #MainMenu {{visibility: hidden;}}
    header {{visibility: hidden;}}
    footer {{visibility: hidden;}}
    [data-testid="stHeader"] {{display: none;}}
    
    .stApp {{
        background-color: {bg_color};
        color: {text_color};
    }}
    [data-testid="stSidebar"] {{
        display: none;
    }}
    .main-header {{
        text-align: center;
        font-weight: 900;
        background: linear-gradient(45deg, #FFD700, #FF69B4);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 0.2rem;
    }}
    .sub-header {{
        text-align: center;
        color: {text_color};
        opacity: 0.8;
        font-size: 0.95rem;
        margin-bottom: 1.5rem;
    }}
    .plan-card {{
        background: {card_bg};
        border: 2px solid #FFD700;
        border-radius: 15px;
        padding: 1.2rem;
        text-align: center;
        margin-bottom: 1rem;
        box-shadow: 0px 4px 15px rgba(255, 215, 0, 0.15);
    }}
    .plan-card h3 {{
        color: #FF69B4 !important;
        margin-bottom: 0.5rem;
    }}
    .plan-card h2 {{
        color: #FFD700 !important;
    }}
    .plan-card p {{
        color: {text_color} !important;
        font-weight: bold;
    }}
    .stButton>button {{
        width: 100%;
        border-radius: 10px;
        height: 3em;
        background: linear-gradient(90deg, #FFD700, #FF69B4);
        color: #000000;
        font-weight: bold;
        border: none;
    }}
    .stButton>button:hover {{
        opacity: 0.9;
        color: #FFFFFF;
    }}
    </style>
""", unsafe_allow_html=True)

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "user_email" not in st.session_state:
    st.session_state.user_email = ""
if "is_admin" not in st.session_state:
    st.session_state.is_admin = False
if "selected_plan" not in st.session_state:
    st.session_state.selected_plan = None

# -----------------------------------------------------------------------------
# MOVIEPY TRANSFORMATION LOGIC
# -----------------------------------------------------------------------------
def manual_zoom(clip, zoom_factor):
    def zoom_frame(image):
        h, w, c = image.shape
        crop_h, crop_w = int(h / zoom_factor), int(w / zoom_factor)
        top = (h - crop_h) // 2
        left = (w - crop_w) // 2
        cropped = image[top:top+crop_h, left:left+crop_w]
        resizer = PIL.Image.Resampling.LANCZOS if hasattr(PIL.Image, 'Resampling') else PIL.Image.BICUBIC
        img_pil = PIL.Image.fromarray(cropped)
        resized_pil = img_pil.resize((w, h), resizer)
        return np.array(resized_pil)
    return clip.fl_image(zoom_frame)

def apply_custom_effects(clip, edit_num):
    if edit_num in [2, 8]:
        clip = manual_zoom(clip, 1.10)
    elif edit_num == 3:
        clip = clip.speedx(1.3) if hasattr(clip, 'speedx') else clip
    elif edit_num in [4, 13]:
        clip = clip.fx(vfx.colorx, 0.85) if hasattr(vfx, 'colorx') else clip
    elif edit_num in [5, 11, 15]:
        clip = clip.fx(vfx.colorx, 1.30) if hasattr(vfx, 'colorx') else clip
    elif edit_num == 6:
        clip = clip.fl_image(lambda img: img[:, ::-1])
    elif edit_num == 7:
        clip = clip.fx(vfx.colorx, 1.15) if hasattr(vfx, 'colorx') else clip
    elif edit_num == 9:
        clip = clip.speedx(1.2) if hasattr(clip, 'speedx') else clip
    elif edit_num == 10:
        clip = manual_zoom(clip, 1.05)
    elif edit_num == 12:
        clip = manual_zoom(clip, 1.15)
    elif edit_num == 14:
        clip = clip.fl_image(lambda img: img[:, ::-1])
        if hasattr(clip, 'speedx'):
            clip = clip.speedx(1.25)

    delay_factors = {
        1: 1.000, 2: 0.973, 3: 0.946, 4: 0.919, 5: 0.892, 6: 0.865, 
        7: 1.000, 8: 0.973, 9: 0.946, 10: 0.919, 11: 0.892, 12: 0.865,
        13: 1.000, 14: 0.973, 15: 0.946                            
    }
    speed_factor = delay_factors.get(edit_num, 1.0)
    if clip.audio is not None and speed_factor != 1.0:
        audio = clip.audio.fl_time(lambda t: t * speed_factor)
        clip.audio = audio.set_duration(clip.duration)

    return clip

def process_single_video(input_path, output_path, target_height, bitrate, watermark_file, watermark_pos, mute_audio, bg_music_file):
    video = VideoFileClip(input_path)
    actual_vid_duration = video.duration
    orig_w, orig_h = video.size
    
    clips = []
    cut_duration = actual_vid_duration / 15.0

    for edit_idx in range(1, 16):
        seg_start = (edit_idx - 1) * cut_duration
        seg_end = edit_idx * cut_duration
        subclip = video.subclip(seg_start, seg_end)
        edited_subclip = apply_custom_effects(subclip, edit_idx)
        clips.append(edited_subclip)

    final_clip = concatenate_videoclips(clips)

    if orig_h != target_height:
        aspect_ratio = orig_w / float(orig_h)
        new_w = int(target_height * aspect_ratio)
        if new_w % 2 != 0:
            new_w += 1
        final_clip = final_clip.resize(newsize=(new_w, target_height))

    # Watermark Processing
    if watermark_file is not None:
        wm_path = "temp_wm.png"
        with open(wm_path, "wb") as f:
            f.write(watermark_file.read())
        
        pos_map = {
            "Top-Left": ("left", "top"),
            "Top-Right": ("right", "top"),
            "Bottom-Left": ("left", "bottom"),
            "Bottom-Right": ("right", "bottom")
        }
        logo = (ImageClip(wm_path)
                .set_duration(final_clip.duration)
                .resize(height=int(final_clip.h * 0.12))
                .set_pos(pos_map.get(watermark_pos, ("right", "bottom"))))
        final_clip = CompositeVideoClip([final_clip, logo])

    # Audio Customization
    if mute_audio:
        final_clip = final_clip.without_audio()
    elif bg_music_file is not None:
        music_path = "temp_music.mp3"
        with open(music_path, "wb") as f:
            f.write(bg_music_file.read())
        
        bg_audio = AudioFileClip(music_path)
        bg_audio = bg_audio.volumex(2.0)  # Volume set to 2.0
        
        if bg_audio.duration < final_clip.duration:
            bg_audio = afx.audio_loop(bg_audio, duration=final_clip.duration)
        else:
            bg_audio = bg_audio.subclip(0, final_clip.duration)
            
        if final_clip.audio is not None:
            combined_audio = CompositeAudioClip([final_clip.audio, bg_audio])
            final_clip.audio = combined_audio
        else:
            final_clip.audio = bg_audio

    final_clip.write_videofile(
        output_path, 
        codec="libx264", 
        audio_codec="aac", 
        bitrate=bitrate,
        preset="medium",
        threads=4,
        logger=None
    )

# -----------------------------------------------------------------------------
# 2. HEADER & THEME TOGGLE
# -----------------------------------------------------------------------------
top_hdr1, top_hdr2 = st.columns([4, 1])

with top_hdr1:
    st.markdown("<h1 class='main-header'>🎬 NO COPYRIGHT VIDEO STUDIO</h1>", unsafe_allow_html=True)
    st.markdown("<p class='sub-header'>AI Dynamic 15-Edit Sequence Engine</p>", unsafe_allow_html=True)

with top_hdr2:
    theme_btn_label = "☀️ Light" if st.session_state.theme == "dark" else "🌙 Dark"
    if st.button(theme_btn_label, key="theme_toggle"):
        st.session_state.theme = "light" if st.session_state.theme == "dark" else "dark"
        st.rerun()

top_col1, top_col2 = st.columns([3, 1])

with top_col1:
    if st.session_state.logged_in:
        role = "ADMIN" if st.session_state.is_admin else "USER"
        st.success(f"[{role}] Logged in as: **{st.session_state.user_email}**")
    else:
        st.info("Please login to process videos.")

with top_col2:
    if st.session_state.logged_in:
        if st.button("Sign Out", type="secondary"):
            st.session_state.logged_in = False
            st.session_state.user_email = ""
            st.session_state.is_admin = False
            st.rerun()

st.divider()

# -----------------------------------------------------------------------------
# 3. LOGIN & REGISTRATION
# -----------------------------------------------------------------------------
if not st.session_state.logged_in:
    st.subheader("🔑 Access Dashboard")
    st.info(f"💡 Default Passcode: **{USER_PASSCODE}**")
    
    with st.form("login_form"):
        email = st.text_input("Email Address", placeholder="user@example.com")
        passcode = st.text_input("Access Passcode", type="password", placeholder="Enter passcode")
        submit_button = st.form_submit_button("🚀 Enter Studio", type="primary")

        if submit_button:
            clean_email = email.lower().strip()
            if hash_text(clean_email) == ADMIN_EMAIL_HASH and hash_text(passcode) == ADMIN_PASSCODE_HASH:
                st.session_state.logged_in = True
                st.session_state.user_email = clean_email
                st.session_state.is_admin = True
                st.success("Welcome Admin! Accessing Dashboard...")
                time.sleep(0.5)
                st.rerun()
            elif clean_email and passcode == USER_PASSCODE:
                db_data = load_db()
                if clean_email not in db_data["users"]:
                    db_data["users"][clean_email] = 10
                    save_db(db_data)
                
                st.session_state.logged_in = True
                st.session_state.user_email = clean_email
                st.session_state.is_admin = False
                st.success("Access Granted!")
                time.sleep(0.5)
                st.rerun()
            elif hash_text(clean_email) == ADMIN_EMAIL_HASH and hash_text(passcode) != ADMIN_PASSCODE_HASH:
                st.error("Incorrect Admin Passcode!")
            elif not clean_email:
                st.error("Please enter a valid email address.")
            else:
                st.error("Invalid passcode! Use '123456'.")

# -----------------------------------------------------------------------------
# 4. DASHBOARD & TOOLS
# -----------------------------------------------------------------------------
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

    metric_col1, metric_col2, metric_col3 = st.columns(3)
    metric_col1.metric("Available Coins", f"🪙 {user_coins}")
    metric_col2.metric("Account Status", "PRO Active")
    metric_col3.metric("Upload Limit", "200 MB")

    st.divider()

    tabs_list = ["📹 Sequence Studio", "📜 Download History", "🪙 Scan & Buy Coins", "💬 Help & Support"]
    if st.session_state.is_admin:
        tabs_list.append("⚙️ Admin Control")
        
    tabs = st.tabs(tabs_list)
    
    tab_studio = tabs[0]
    tab_history = tabs[1]
    tab_recharge = tabs[2]
    tab_support = tabs[3]
    tab_admin = tabs[4] if st.session_state.is_admin else None

    # --- TAB 1: STUDIO (SINGLE & BULK PROCESSING) ---
    with tab_studio:
        st.header("📤 15-Edit Sequence Video Processor")
        
        proc_mode = st.radio("Choose Processing Mode:", ["Single Video Edit", "Bulk / Batch Editing (2-3 Videos)"])
        
        uploaded_files = []
        if proc_mode == "Single Video Edit":
            file = st.file_uploader("Choose video file", type=["mp4", "mov", "mkv", "avi"], key="single_up")
            if file: uploaded_files.append(file)
        else:
            files = st.file_uploader("Choose up to 3 videos for Bulk Edit", type=["mp4", "mov", "mkv", "avi"], accept_multiple_files=True, key="bulk_up")
            if files: uploaded_files = files[:3]

        if uploaded_files:
            st.divider()
            st.subheader("⚙️ Output Quality Settings")
            quality_option = st.radio(
                "Choose Export Quality:",
                options=["720p (Free)", "1080p Full HD (3 Coins)", "2K Ultra HD (5 Coins)", "4K Ultra HD (10 Coins)"],
                index=0
            )

            resolution_costs = {
                "720p (Free)": (720, 0, "4000k"),
                "1080p Full HD (3 Coins)": (1080, 3, "12000k"),
                "2K Ultra HD (5 Coins)": (1440, 5, "24000k"),
                "4K Ultra HD (10 Coins)": (2160, 10, "45000k")
            }
            target_height, quality_coins, bitrate = resolution_costs[quality_option]

            # Calculate Coins
            total_required_coins = 0
            for file in uploaded_files:
                f_size_mb = file.size / (1024 * 1024)
                base = 5 if f_size_mb < 50 else 10
                total_required_coins += (base + quality_coins)

            st.info(f"🪙 **Total Required Coins for {len(uploaded_files)} Video(s):** **{total_required_coins} Coins**")

            # --- ADVANCED OPTIONS ---
            st.divider()
            st.subheader("🎨 Customization & Branding (Optional)")
            
            exp_wm = st.expander("🖼️ Add Watermark / Logo Overlay")
            with exp_wm:
                wm_file = st.file_uploader("Upload PNG/JPG Logo", type=["png", "jpg", "jpeg"], key="wm_file")
                wm_pos = st.selectbox("Logo Position", ["Bottom-Right", "Bottom-Left", "Top-Right", "Top-Left"])

            exp_audio = st.expander("🎵 Audio Replacement & Background Music")
            with exp_audio:
                mute_audio = st.checkbox("Mute Original Video Sound")
                bg_music_file = st.file_uploader("Add Non-Copyright Music (Volume set to 2.0)", type=["mp3", "wav"], key="music_file")

            if st.button(f"🚀 Process {len(uploaded_files)} Video(s) ({total_required_coins} Coins)", type="primary"):
                fresh_db = load_db()
                current_balance = fresh_db["users"].get(current_user, 0)

                if current_balance >= total_required_coins:
                    fresh_db["users"][current_user] -= total_required_coins
                    save_db(fresh_db)
                    
                    if not os.path.exists("exports"):
                        os.makedirs("exports")

                    for idx, up_file in enumerate(uploaded_files):
                        st.subheader(f"Processing Video {idx+1}/{len(uploaded_files)}: {up_file.name}")
                        p_bar = st.progress(0, text="Initializing Engine...")
                        
                        temp_in = f"temp_in_{idx}.mp4"
                        out_filename = f"exports/{int(time.time())}_{idx}_{up_file.name}"
                        
                        with open(temp_in, "wb") as f:
                            f.write(up_file.read())

                        p_bar.progress(30, text="Applying 15-Edit Dynamic Sequence...")
                        
                        try:
                            process_single_video(
                                temp_in, out_filename, target_height, bitrate,
                                wm_file, wm_pos, mute_audio, bg_music_file
                            )
                            p_bar.progress(100, text="Complete!")
                            
                            # Save to History Database
                            fresh_db = load_db()
                            if current_user not in fresh_db["history"]:
                                fresh_db["history"][current_user] = []
                            
                            fresh_db["history"][current_user].append({
                                "filename": up_file.name,
                                "path": out_filename,
                                "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                                "quality": quality_option.split()[0],
                                "coins": (5 if (up_file.size / (1024*1024)) < 50 else 10) + quality_coins
                            })
                            save_db(fresh_db)
                            
                        except Exception as e:
                            st.error(f"Error processing {up_file.name}: {str(e)}")

                    st.balloons()
                    st.success("🎉 All videos processed successfully! Check 'Download History' tab.")
                else:
                    st.error(f"❌ Insufficient Coins! You need 🪙 {total_required_coins} Coins.")

    # --- TAB 2: DOWNLOAD HISTORY ---
    with tab_history:
        st.header("📜 Download & Processed Video History")
        user_history = db_data.get("history", {}).get(current_user, [])

        if not user_history:
            st.info("No processed video history found.")
        else:
            for item in reversed(user_history):
                st.write(f"📹 **File:** `{item['filename']}`")
                st.caption(f"🗓️ Date: {item['date']} | ✨ Quality: {item['quality']} | 🪙 Cost: {item['coins']} Coins")
                
                if os.path.exists(item['path']):
                    with open(item['path'], "rb") as f:
                        st.download_button(
                            label=f"📥 Download Video ({item['quality']})",
                            data=f,
                            file_name=f"processed_{item['filename']}",
                            mime="video/mp4",
                            key=f"hist_btn_{item['path']}"
                        )
                else:
                    st.warning("⚠️ File no longer available on server.")
                st.divider()

    # --- TAB 3: RECHARGE ---
    with tab_recharge:
        st.header("⚡ Request Coins Recharge")
        st.write("Select a package, scan QR code, and submit UTR for admin verification.")

        plan_col1, plan_col2 = st.columns(2)
        plan_col3, plan_col4 = st.columns(2)

        with plan_col1:
            st.markdown("<div class='plan-card'><h3>Starter</h3><h2>₹49</h2><p>🪙 50 Coins</p></div>", unsafe_allow_html=True)
            if st.button("Buy ₹49 Plan", key="p1"): st.session_state.selected_plan = ("Starter", 49, 50)

        with plan_col2:
            st.markdown("<div class='plan-card'><h3>Popular</h3><h2>₹99</h2><p>🪙 110 Coins</p></div>", unsafe_allow_html=True)
            if st.button("Buy ₹99 Plan", key="p2"): st.session_state.selected_plan = ("Popular", 99, 110)

        with plan_col3:
            st.markdown("<div class='plan-card'><h3>Value</h3><h2>₹199</h2><p>🪙 221 Coins</p></div>", unsafe_allow_html=True)
            if st.button("Buy ₹199 Plan", key="p3"): st.session_state.selected_plan = ("Value", 199, 221)

        with plan_col4:
            st.markdown("<div class='plan-card'><h3>Mega Pro</h3><h2>₹399</h2><p>🪙 500 Coins</p></div>", unsafe_allow_html=True)
            if st.button("Buy ₹399 Plan", key="p4"): st.session_state.selected_plan = ("Mega Pro", 399, 500)

        st.divider()

        if st.session_state.selected_plan:
            plan_name, amount, coins_to_add = st.session_state.selected_plan
            st.subheader(f"📲 Scan QR & Submit UTR for ₹{amount} ({coins_to_add} Coins)")
            pay_col1, pay_col2 = st.columns([1, 1])

            with pay_col1:
                qr_api_url = f"https://api.qrserver.com/v1/create-qr-code/?size=220x220&data=upi://pay?pa={UPI_ID}%26pn=VideoStudio%26am={amount}%26cu=INR"
                st.image(qr_api_url, caption=f"UPI: {UPI_ID}", width=200)

            with pay_col2:
                utr_number = st.text_input("Enter 12-Digit Transaction / UTR No.", max_chars=12)
                if st.button("SUBMIT FOR VERIFICATION", type="primary"):
                    if len(utr_number) == 12 and utr_number.isdigit():
                        current_db = load_db()
                        current_db["pending_requests"].append({
                            "user": current_user, "utr": utr_number, "amount": amount, "coins": coins_to_add
                        })
                        save_db(current_db)
                        st.session_state.selected_plan = None
                        st.success("⏳ UTR Submitted Successfully!")
                        time.sleep(1)
                        st.rerun()
                    else:
                        st.error("Please enter a valid 12-digit numeric UTR Number.")

    # --- TAB 4: SUPPORT CHAT ---
    with tab_support:
        st.header("💬 Help & Support")
        with st.form("support_form", clear_on_submit=True):
            user_msg = st.text_area("Your Message / Query", placeholder="Describe your problem or question here...")
            sub_ticket = st.form_submit_button("📩 Send Message")
            if sub_ticket and user_msg.strip():
                current_db = load_db()
                ticket_id = f"TICK_{int(time.time()*1000)}"
                current_db["support_tickets"].append({
                    "ticket_id": ticket_id, "user": current_user, "message": user_msg.strip(), "reply": "", "status": "Pending"
                })
                save_db(current_db)
                st.success("Message sent to Admin!")
                time.sleep(0.5)
                st.rerun()

        st.divider()
        st.subheader("📋 Your Private Chats")
        current_db = load_db()
        user_tickets = [t for t in current_db.get("support_tickets", []) if t.get("user") == current_user]
        
        if not user_tickets:
            st.info("No previous messages.")
        else:
            for t in reversed(user_tickets):
                st.write(f"**You:** {t['message']}")
                if t.get("reply"): st.success(f"**Admin Reply:** {t['reply']}")
                else: st.warning("⏳ Waiting for Admin reply...")
                st.caption(f"Status: `{t.get('status', 'Pending')}`")
                st.divider()

    # --- TAB 5: ADMIN PANEL ---
    if st.session_state.is_admin and tab_admin:
        with tab_admin:
            st.header("⚙️ Admin Dashboard & Control")
            admin_db = load_db()
            
            st.subheader("💳 Pending Payment Approvals")
            pending_requests = admin_db.get("pending_requests", [])

            if not pending_requests:
                st.info("No pending payment approvals.")
            else:
                for idx, req in enumerate(list(pending_requests)):
                    st.warning(f"👤 **User:** `{req['user']}` | 💰 **Amount:** ₹{req['amount']} | 🔢 **UTR:** `{req['utr']}` | 🪙 **Coins:** {req['coins']}")
                    col1, col2 = st.columns(2)
                    with col1:
                        if st.button(f"✅ Approve ({req['coins']} Coins)", key=f"app_btn_{idx}"):
                            db_to_update = load_db()
                            target_user = req["user"]
                            db_to_update["users"][target_user] = db_to_update["users"].get(target_user, 0) + req["coins"]
                            db_to_update["pending_requests"].pop(idx)
                            save_db(db_to_update)
                            st.success(f"Approved {req['coins']} coins for {target_user}!")
                            time.sleep(0.5)
                            st.rerun()

                    with col2:
                        if st.button("❌ Reject Request", key=f"rej_btn_{idx}"):
                            db_to_update = load_db()
                            db_to_update["pending_requests"].pop(idx)
                            save_db(db_to_update)
                            st.error("Request rejected.")
                            time.sleep(0.5)
                            st.rerun()
                    st.divider()
