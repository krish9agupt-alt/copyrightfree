import streamlit as st
import time, json, os, hashlib, gc, glob, threading
import numpy as np
import PIL.Image
from datetime import datetime
import urllib.parse
import urllib.request
import re

# MoviePy Compatibility Patch
if not hasattr(PIL.Image, 'ANTIALIAS'):
    PIL.Image.ANTIALIAS = PIL.Image.Resampling.LANCZOS

try:
    from moviepy.editor import VideoFileClip, concatenate_videoclips
    import moviepy.video.fx.all as vfx
except ImportError:
    st.error("MoviePy import error! Please check requirements.txt")

# Global Render Lock System
@st.cache_resource
def get_render_lock():
    return threading.Lock()

RENDER_LOCK = get_render_lock()

st.set_page_config(page_title="CR Removes - AI Copyright Remover", page_icon="✨", layout="wide")

DB_FILE = "database.json"
TELEGRAM_SUPPORT_URL = "https://t.me/+Yhr7ZJWcqBwyNmFl"
UPI_ID_TEXT = "cinepoliis@ibl"
EXPORT_DIR = "exports"

os.makedirs(EXPORT_DIR, exist_ok=True)

def hash_text(text):
    return hashlib.sha256(text.encode()).hexdigest()

ADMIN_EMAIL_HASH = hash_text("krish9agupt@gmail.com")
ADMIN_PASSCODE_HASH = hash_text("Krish9A")
USER_PASSCODE = "123456"

# Storage Cleanup System
def auto_cleanup_storage_and_memory(temp_file_path=None, max_age_hours=24):
    if temp_file_path and os.path.exists(temp_file_path):
        try: os.remove(temp_file_path)
        except Exception: pass
            
    if os.path.exists(EXPORT_DIR):
        now_time = time.time()
        for file_path in glob.glob(os.path.join(EXPORT_DIR, "*")):
            if os.path.isfile(file_path):
                file_age_hours = (now_time - os.path.getmtime(file_path)) / 3600
                if file_age_hours > max_age_hours:
                    try: os.remove(file_path)
                    except Exception: pass
    gc.collect()

def load_db():
    if not os.path.exists(DB_FILE):
        default_db = {"users": {}, "subscriptions": {}, "pending_requests": [], "support_tickets": [], "history": {}}
        with open(DB_FILE, "w") as f: json.dump(default_db, f, indent=4)
        return default_db
    try:
        with open(DB_FILE, "r") as f: 
            db = json.load(f)
            if "subscriptions" not in db: db["subscriptions"] = {}
            return db
    except Exception:
        return {"users": {}, "subscriptions": {}, "pending_requests": [], "support_tickets": [], "history": {}}

def save_db(data):
    with open(DB_FILE, "w") as f: json.dump(data, f, indent=4)

if "logged_in" not in st.session_state: st.session_state.logged_in = False
if "user_email" not in st.session_state: st.session_state.user_email = ""
if "is_admin" not in st.session_state: st.session_state.is_admin = False

# -------------------------------------------------------------
# 🎨 CUSTOM SAAS DARK MODE CSS (CR REMOVES THEME MATCH)
# -------------------------------------------------------------
st.markdown("""
    <style>
    /* Dark Theme Core Setup */
    #MainMenu, header, footer {visibility: hidden;}
    
    .stApp {
        background-color: #0b0f17 !important;
        color: #e6edf3 !important;
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
    }
    
    /* Global Typography Fixes */
    p, span, label, div, li {
        color: #919eab !important;
        text-shadow: none !important;
    }
    
    h1, h2, h3, h4, h5, h6 {
        color: #ffffff !important;
        font-weight: 700 !important;
        text-shadow: none !important;
    }

    /* Top Navigation Bar Simulation */
    .nav-container {
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding: 10px 0px 20px 0px;
        border-bottom: 1px solid #1e293b;
        margin-bottom: 25px;
    }
    
    .brand-logo {
        font-size: 1.5rem;
        font-weight: 800;
        color: #ffffff !important;
        display: flex;
        align-items: center;
        gap: 8px;
    }
    
    .brand-logo span {
        color: #2fd1c5 !important;
    }

    /* SaaS Badges & Cards */
    .pill-badge {
        background: rgba(47, 209, 197, 0.1);
        border: 1px solid rgba(47, 209, 197, 0.3);
        color: #2fd1c5 !important;
        padding: 6px 16px;
        border-radius: 20px;
        font-size: 0.85rem;
        font-weight: 600;
        display: inline-block;
        margin-bottom: 15px;
    }

    .saas-card {
        background-color: #121824;
        border: 1px solid #1e293b;
        border-radius: 16px;
        padding: 24px;
        margin-bottom: 20px;
    }

    /* Primary Accent Cyan Buttons */
    .stButton > button, div[data-testid="stDownloadButton"] > button {
        background-color: #2fd1c5 !important;
        color: #0b0f17 !important;
        font-weight: 700 !important;
        border-radius: 10px !important;
        border: none !important;
        padding: 10px 24px !important;
        transition: all 0.2s ease-in-out;
        width: 100%;
    }
    
    .stButton > button:hover, div[data-testid="stDownloadButton"] > button:hover {
        background-color: #26b3a9 !important;
        color: #0b0f17 !important;
        box-shadow: 0 4px 12px rgba(47, 209, 197, 0.3);
    }

    /* Inputs, Radio Buttons & Selectboxes */
    div[data-baseweb="input"] > div, div[data-baseweb="select"] > div {
        background-color: #161f2e !important;
        border: 1px solid #283548 !important;
        color: #ffffff !important;
        border-radius: 10px !important;
    }

    div[data-testid="stRadio"] div[role="radiogroup"] > label {
        background-color: #121824 !important;
        border: 1px solid #1e293b !important;
        border-radius: 10px !important;
        padding: 12px 18px !important;
        margin-bottom: 8px !important;
        color: #e6edf3 !important;
        width: 100% !important;
    }
    
    div[data-testid="stRadio"] div[role="radiogroup"] > label:hover {
        border-color: #2fd1c5 !important;
    }

    /* Telegram Header Button */
    .tg-support-btn {
        background-color: #2fd1c5;
        color: #0b0f17 !important;
        padding: 8px 18px;
        border-radius: 8px;
        text-decoration: none;
        font-weight: 700;
        font-size: 0.9rem;
        transition: opacity 0.2s;
    }
    .tg-support-btn:hover {
        opacity: 0.9;
    }
    
    /* Metrics Customization */
    div[data-testid="stMetricValue"] {
        color: #2fd1c5 !important;
        font-weight: 800 !important;
    }
    </style>
""", unsafe_allow_html=True)

# -------------------------------------------------------------
# 🛡️ ADVANCED ANTI-COPYRIGHT ENGINE
# -------------------------------------------------------------
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

def apply_anti_copyright_effects(clip, edit_num=1):
    if edit_num % 5 == 0:
        clip = manual_zoom(clip, 1.08)
        clip = clip.fx(vfx.colorx, 1.05)
    elif edit_num % 4 == 0:
        clip = clip.speedx(1.04)
        clip = clip.fx(vfx.colorx, 0.96)
    elif edit_num % 3 == 0:
        clip = manual_zoom(clip, 1.05)
        clip = clip.fl_image(lambda img: img[:, ::-1])
    elif edit_num % 2 == 0:
        clip = clip.speedx(1.03)
        clip = manual_zoom(clip, 1.06)
    else:
        clip = manual_zoom(clip, 1.07)
        clip = clip.fx(vfx.colorx, 1.03)
    return clip

def process_single_video(input_path, output_path, target_height, bitrate, progress_bar, status_text_holder):
    start_time = time.time()
    status_text_holder.info("🎬 Loading & Analyzing video stream...")
    progress_bar.progress(5)
    
    video = VideoFileClip(input_path)
    cut_duration = video.duration / 15.0
    clips = []

    orig_w, orig_h = video.size
    aspect_ratio = orig_w / float(orig_h)

    for edit_idx in range(1, 16):
        subclip = video.subclip((edit_idx - 1) * cut_duration, edit_idx * cut_duration)
        clips.append(apply_anti_copyright_effects(subclip, edit_idx))

    final_clip = concatenate_videoclips(clips)

    if orig_h != target_height:
        new_w = int(target_height * aspect_ratio)
        if new_w % 2 != 0: new_w += 1
        final_clip = final_clip.resize(newsize=(new_w, target_height))

    for pct in range(10, 85, 15):
        progress_bar.progress(pct)
        time.sleep(0.2)

    status_text_holder.warning("⚙️ Injecting AI Anti-Copyright Algorithm & Rendering...")
    progress_bar.progress(85)
    
    final_clip.write_videofile(
        output_path, codec="libx264", audio_codec="aac", bitrate=bitrate, preset="ultrafast", threads=1, logger=None
    )
    
    try:
        video.close()
        final_clip.close()
        for c in clips: c.close()
    except Exception: pass

    total_elapsed = int(time.time() - start_time)
    progress_bar.progress(100)
    status_text_holder.success(f"✅ AI Content Optimization Complete ({total_elapsed} sec)!")

# -------------------------------------------------------------
#  NAVBAR HEADER
# -------------------------------------------------------------
st.markdown(f"""
    <div class="nav-container">
        <div class="brand-logo">✨ CR <span>Removes</span></div>
        <div>
            <a href="{TELEGRAM_SUPPORT_URL}" target="_blank" class="tg-support-btn">Support Community</a>
        </div>
    </div>
""", unsafe_allow_html=True)

# -------------------------------------------------------------
# LOGIN & DASHBOARD VIEW
# -------------------------------------------------------------
if not st.session_state.logged_in:
    st.markdown("""
        <div style="text-align: center; margin: 30px 0;">
            <div class="pill-badge">✨ AI CR Removes. Studio finish.</div>
            <h1 style="font-size: 2.8rem; margin-bottom: 10px;">Remove Copyright Claims from Your YouTube Videos Instantly</h1>
            <p style="font-size: 1.1rem; max-width: 650px; margin: 0 auto 30px auto;">
                Copyright Remover - Professional AI deep-clean technology. Upload your video below to simulate advanced content optimization.
            </p>
        </div>
    """, unsafe_allow_html=True)
    
    col_center, _ = st.columns([1, 0.01])
    with col_center:
        st.subheader("Sign in to your Dashboard")
        with st.form("login_form"):
            email = st.text_input("Email Address", placeholder="name@domain.com")
            passcode = st.text_input("Access Passcode", value=USER_PASSCODE, type="password")
            if st.form_submit_button("Sign In →"):
                clean_email = email.lower().strip()
                if hash_text(clean_email) == ADMIN_EMAIL_HASH and hash_text(passcode) == ADMIN_PASSCODE_HASH:
                    st.session_state.logged_in = True
                    st.session_state.user_email = clean_email
                    st.session_state.is_admin = True
                    st.rerun()
                elif clean_email and (passcode == USER_PASSCODE or hash_text(passcode) == ADMIN_PASSCODE_HASH):
                    db = load_db()
                    if clean_email not in db["users"]: db["users"][clean_email] = 10; save_db(db)
                    st.session_state.logged_in = True
                    st.session_state.user_email = clean_email
                    st.session_state.is_admin = False
                    st.rerun()

else:
    current_user = st.session_state.user_email
    db_data = load_db()
    user_coins = db_data["users"].get(current_user, 10) if not st.session_state.is_admin else 99999
    
    sub_info = db_data.get("subscriptions", {}).get(current_user, None)
    expiry_display = "No Active Plan"
    if sub_info:
        exp_date = datetime.strptime(sub_info["expiry"], "%Y-%m-%d %H:%M:%S")
        now = datetime.now()
        if now < exp_date:
            diff = exp_date - now
            expiry_display = f"{sub_info['plan']} (⏳ {diff.days}d {diff.seconds//3600}h left)"
        else: expiry_display = "⚠️ Plan Expired!"

    col_m1, col_m2, col_logout = st.columns([2, 2, 1])
    with col_m1: st.metric("Available Balance", f"🪙 {user_coins} Credits")
    with col_m2: st.metric("Plan Status", expiry_display)
    with col_logout:
        if st.button("Sign Out"):
            st.session_state.logged_in = False
            st.rerun()

    st.divider()

    menu_options = ["📹 Studio Processor", "📁 Output Library Manager", "🧹 Library Cleaner", "🪙 Prepaid Packs / Pricing", "💬 Direct Admin Support"]
    if st.session_state.is_admin: menu_options.append("👑 Admin Panel")
    
    selected_menu = st.radio("Navigation Menu:", menu_options)
    st.divider()

    # 1. STUDIO PROCESSOR
    if selected_menu == "📹 Studio Processor":
        st.markdown('<div class="pill-badge">Upload & Process</div>', unsafe_allow_html=True)
        st.subheader("Upload securely")
        st.write("Drag and drop your video file below into private processing storage.")
        
        uploaded_file = st.file_uploader("Select Video File", type=["mp4", "mov", "mkv", "avi"])
        
        if uploaded_file:
            process_mode = st.radio("Select Processing Mode:", [
                "1. Full Anti-Copyright Video Processor (Single File)", 
                "2. Anti-Copyright Clipping & Trimming Mode (Multiple Parts)"
            ])
            
            # MODE 1
            if process_mode == "1. Full Anti-Copyright Video Processor (Single File)":
                quality_option = st.radio("Select Export Quality:", ["720p HD (Free - 0 Coin)", "1080p Full HD (5 Coins)", "2K / 4K Ultra HD (10 Coins)"])
                res_config = {"720p HD (Free - 0 Coin)": (720, "4000k", 0), "1080p Full HD (5 Coins)": (1080, "12000k", 5), "2K / 4K Ultra HD (10 Coins)": (2160, "45000k", 10)}
                target_height, bitrate, required_coins = res_config[quality_option]

                if st.button("🚀 Process Video Now"):
                    if user_coins < required_coins and not st.session_state.is_admin:
                        st.error(f"❌ Iss quality ke liye {required_coins} Coins chahiye.")
                    else:
                        with RENDER_LOCK:
                            p_bar = st.progress(0)
                            status_text_holder = st.empty()
                            temp_in = f"temp_in_{int(time.time())}.mp4"
                            out_path = f"{EXPORT_DIR}/{int(time.time())}_{uploaded_file.name}"
                            
                            try:
                                with open(temp_in, "wb") as f: f.write(uploaded_file.read())
                                process_single_video(temp_in, out_path, target_height, bitrate, p_bar, status_text_holder)
                                
                                if not st.session_state.is_admin and required_coins > 0:
                                    db_data["users"][current_user] = user_coins - required_coins
                                
                                if current_user not in db_data["history"]: db_data["history"][current_user] = []
                                db_data["history"][current_user].append({"filename": uploaded_file.name, "path": out_path, "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S")})
                                save_db(db_data)

                                st.success("🎉 Processing complete!")
                                with open(out_path, "rb") as f:
                                    st.download_button("📥 Download Optimized Video", f, file_name=f"edited_{uploaded_file.name}", mime="video/mp4")
                            except Exception as e: st.error(f"Error: {e}")
                            finally: auto_cleanup_storage_and_memory(temp_file_path=temp_in)

            # MODE 2
            elif process_mode == "2. Anti-Copyright Clipping & Trimming Mode (Multiple Parts)":
                clip_mode = st.radio("Clipping Mode:", ["Auto-Interval", "Custom Timestamps"])
                
                if clip_mode == "Auto-Interval":
                    interval_sec = st.number_input("Interval duration (Seconds):", min_value=5, max_value=600, value=10)
                else:
                    timestamps_input = st.text_input("Timestamps (seconds: e.g. 0-10, 15-30):", value="0-10, 15-30")

                if st.button("✂️ Generate Optimized Clips"):
                    with RENDER_LOCK:
                        temp_in = f"temp_in_{int(time.time())}.mp4"
                        try:
                            with open(temp_in, "wb") as f: f.write(uploaded_file.read())
                            
                            with st.spinner("⏳ Cutting & applying Anti-Copyright bypass layers..."):
                                video = VideoFileClip(temp_in)
                                generated_clips = []

                                if clip_mode == "Auto-Interval":
                                    total_dur = video.duration
                                    curr = 0
                                    count = 1
                                    while curr < total_dur:
                                        end = min(curr + interval_sec, total_dur)
                                        subclip = video.subclip(curr, end)
                                        edited_subclip = apply_anti_copyright_effects(subclip, count)
                                        
                                        out_clip_path = f"{EXPORT_DIR}/clip_{count}_{int(time.time())}.mp4"
                                        edited_subclip.write_videofile(out_clip_path, codec="libx264", audio_codec="aac", preset="ultrafast", logger=None)
                                        generated_clips.append((f"Clip_{count}.mp4", out_clip_path))
                                        curr += interval_sec
                                        count += 1
                                else:
                                    ranges = [r.strip().split("-") for r in timestamps_input.split(",") if "-" in r]
                                    for idx, r in enumerate(ranges):
                                        start, end = float(r[0]), float(r[1])
                                        subclip = video.subclip(start, min(end, video.duration))
                                        edited_subclip = apply_anti_copyright_effects(subclip, idx + 1)
                                        
                                        out_clip_path = f"{EXPORT_DIR}/custom_clip_{idx+1}_{int(time.time())}.mp4"
                                        edited_subclip.write_videofile(out_clip_path, codec="libx264", audio_codec="aac", preset="ultrafast", logger=None)
                                        generated_clips.append((f"Custom_Clip_{idx+1}.mp4", out_clip_path))

                                video.close()

                                st.success(f"🎉 Generated {len(generated_clips)} optimized clips!")
                                for name, path in generated_clips:
                                    with open(path, "rb") as f:
                                        st.download_button(f"📥 Download {name}", f, file_name=name, key=path)

                        except Exception as e:
                            st.error(f"❌ Error: {e}")
                        finally:
                            auto_cleanup_storage_and_memory(temp_file_path=temp_in)

    # 2. OUTPUT LIBRARY MANAGER
    elif selected_menu == "📁 Output Library Manager":
        st.subheader("📁 Output Library Manager")
        if st.button("🔄 Refresh Library"): st.rerun()
            
        all_exports = glob.glob(os.path.join(EXPORT_DIR, "*"))
        if not all_exports:
            st.info("No processed files available in your library yet.")
        else:
            for filepath in all_exports:
                if os.path.isfile(filepath):
                    fname = os.path.basename(filepath)
                    fsize = round(os.path.getsize(filepath) / (1024 * 1024), 2)
                    c1, c2, c3 = st.columns([3, 2, 2])
                    with c1: st.write(f"📄 **{fname}**")
                    with c2: st.write(f"📦 Size: `{fsize} MB`")
                    with c3:
                        with open(filepath, "rb") as f:
                            st.download_button("📥 Download", f, file_name=fname, key=f"lib_dl_{fname}")
                    st.divider()

    # 3. LIBRARY CLEANER
    elif selected_menu == "🧹 Library Cleaner":
        st.subheader("🧹 System Storage & Library Cleaner")
        if st.button("🚨 Purge Entire Library Cache"):
            deleted_count = 0
            if os.path.exists(EXPORT_DIR):
                for file_path in glob.glob(os.path.join(EXPORT_DIR, "*")):
                    if os.path.isfile(file_path):
                        try: os.remove(file_path); deleted_count += 1
                        except Exception: pass
            gc.collect()
            st.success(f"✅ Library Cleaned! Total {deleted_count} files removed.")
            st.rerun()

    # 4. PREPAID PACKS / PRICING
    elif selected_menu == "🪙 Prepaid Packs / Pricing":
        st.subheader("Prepaid video packs")
        st.write("Every plan is a prepaid pack. Choose your required package to continue uninterrupted processing.")
        st.info(f"💳 Direct UPI Deposit ID: **{UPI_ID_TEXT}**")
        
        with st.form("buy_coins_form"):
            utr_no = st.text_input("UTR Reference Number (Post Payment)")
            selected_plan = st.selectbox("Select Plan", [
                "Basic - ₹149 (16 Videos / 28 Days)",
                "Standard - ₹249 (35 Videos / 28 Days)",
                "Pro - ₹399 (999 Credits / Monthly)",
                "VIP Unlimited - ₹999 (Yearly Unlimited)"
            ])
            if st.form_submit_button("Choose Plan / Submit Request"):
                if utr_no.strip():
                    if "pending_requests" not in db_data: db_data["pending_requests"] = []
                    db_data["pending_requests"].append({"email": current_user, "utr": utr_no.strip(), "plan": selected_plan, "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S")})
                    save_db(db_data)
                    st.success("✅ Payment Request Submitted! Your account will be updated shortly.")

    # 5. CHAT WITH ADMIN
    elif selected_menu == "💬 Direct Admin Support":
        st.subheader("💬 Private Support Desk")
        with st.form("send_msg_form"):
            user_msg = st.text_area("How can we help you?")
            if st.form_submit_button("📤 Submit Ticket"):
                if user_msg.strip():
                    ticket = {"id": int(time.time()), "user": current_user, "msg": user_msg.strip(), "reply": "", "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
                    if "support_tickets" not in db_data: db_data["support_tickets"] = []
                    db_data["support_tickets"].append(ticket)
                    save_db(db_data)
                    st.success("Ticket sent successfully!")
                    st.rerun()

    # 6. ADMIN PANEL
    elif selected_menu == "👑 Admin Panel" and st.session_state.is_admin:
        st.subheader("👑 Admin Management Console")
        pending_reqs = db_data.get("pending_requests", [])
        if not pending_reqs:
            st.write("No pending requests.")
        for idx, req in enumerate(pending_reqs):
            st.write(f"👤 **{req['email']}** | Plan: **{req['plan']}** | UTR: `{req['utr']}`")
            if st.button("✅ Approve Access", key=f"app_{idx}"):
                db_data["users"][req['email']] = db_data["users"].get(req['email'], 0) + 500
                db_data["pending_requests"].pop(idx)
                save_db(db_data)
                st.rerun()
