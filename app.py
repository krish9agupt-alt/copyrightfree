import streamlit as st
import time, json, os, hashlib, gc, glob, threading
import numpy as np
import PIL.Image
from datetime import datetime
import urllib.parse

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

st.set_page_config(page_title="CR-copyright free", page_icon="✨", layout="wide")

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

# Auto Cleanup System
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
    default_db = {
        "users": {},
        "subscriptions": {},
        "pending_requests": [],
        "support_tickets": [],
        "history": {},
        "claimed_tasks": {},
        "admin_links": {
            "yt_url": "https://youtube.com",
            "insta_url": "https://instagram.com",
            "video_url": "https://youtube.com",
            "upi_id": "cinepoliis@ibl"
        }
    }
    if not os.path.exists(DB_FILE):
        with open(DB_FILE, "w") as f: json.dump(default_db, f, indent=4)
        return default_db
    try:
        with open(DB_FILE, "r") as f: 
            db = json.load(f)
            for k, v in default_db.items():
                if k not in db: db[k] = v
            return db
    except Exception:
        return default_db

def save_db(data):
    with open(DB_FILE, "w") as f: json.dump(data, f, indent=4)

if "logged_in" not in st.session_state: st.session_state.logged_in = False
if "user_email" not in st.session_state: st.session_state.user_email = ""
if "is_admin" not in st.session_state: st.session_state.is_admin = False

# Dynamic QR Code Generator URL Function
def generate_upi_qr(upi_id, amount, name="CR Copyright Free"):
    pay_url = f"upi://pay?pa={upi_id}&pn={urllib.parse.quote(name)}&am={amount}&cu=INR"
    qr_api_url = f"https://api.qrserver.com/v1/create-qr-code/?size=250x250&data={urllib.parse.quote(pay_url)}"
    return qr_api_url

# Enhanced UI Styling (Reduced Top Padding, Compact Telegram Button & Custom Buttons)
st.markdown("""
    <style>
    #MainMenu, header, footer {visibility: hidden;}
    .stApp { background-color: #0b0f17 !important; color: #e6edf3 !important; }
    
    /* Reduce top space */
    .block-container {
        padding-top: 1rem !important;
        padding-bottom: 1rem !important;
    }
    
    p, span, label, div, li { color: #919eab !important; }
    h1, h2, h3, h4, h5, h6 { color: #ffffff !important; font-weight: 700 !important; }
    
    .nav-container { 
        display: flex; 
        justify-content: space-between; 
        align-items: center; 
        padding: 5px 0px 10px 0px; 
        border-bottom: 1px solid #1e293b; 
        margin-bottom: 15px; 
    }
    
    .brand-logo { font-size: 1.3rem; font-weight: 800; color: #ffffff !important; letter-spacing: -0.5px; white-space: nowrap; }
    .brand-logo span { color: #2fd1c5 !important; }
    
    .pill-badge { background: rgba(47, 209, 197, 0.1); border: 1px solid rgba(47, 209, 197, 0.3); color: #2fd1c5 !important; padding: 4px 12px; border-radius: 20px; font-size: 0.8rem; font-weight: 600; display: inline-block; margin-bottom: 10px; }
    
    .stButton > button, div[data-testid="stDownloadButton"] > button { background-color: #2fd1c5 !important; color: #0b0f17 !important; font-weight: 700 !important; border-radius: 10px !important; border: none !important; width: 100%; height: 44px; transition: all 0.3s ease; }
    .stButton > button:hover { background-color: #26b3a9 !important; transform: translateY(-2px); box-shadow: 0 4px 15px rgba(47, 209, 197, 0.3); }
    
    div[data-baseweb="input"] > div, div[data-baseweb="select"] > div { background-color: #161f2e !important; border: 1px solid #283548 !important; color: #ffffff !important; border-radius: 10px !important; }
    
    div[data-testid="stRadio"] div[role="radiogroup"] { gap: 8px; }
    div[data-testid="stRadio"] div[role="radiogroup"] > label { background-color: #121824 !important; border: 1px solid #1e293b !important; border-radius: 10px !important; padding: 10px 14px !important; color: #ffffff !important; transition: border-color 0.2s; width: 100% !important; }
    div[data-testid="stRadio"] div[role="radiogroup"] > label:hover { border-color: #2fd1c5 !important; }
    
    /* Compact Telegram Support Button */
    .tg-support-btn { 
        background: linear-gradient(90deg, #0088cc, #00c6ff); 
        color: #ffffff !important; 
        padding: 6px 12px; 
        border-radius: 8px; 
        text-decoration: none; 
        font-weight: 600; 
        font-size: 0.82rem;
        display: inline-flex; 
        align-items: center; 
        gap: 5px; 
        box-shadow: 0 2px 8px rgba(0, 136, 204, 0.3); 
        white-space: nowrap;
    }
    .tg-support-btn:hover { opacity: 0.95; color: #ffffff !important; }

    /* Custom Task Action Buttons */
    .yt-sub-btn {
        background-color: #FF0000 !important;
        color: #ffffff !important;
        padding: 10px 20px;
        border-radius: 20px;
        text-decoration: none;
        font-weight: 700;
        display: inline-block;
        box-shadow: 0 4px 12px rgba(255, 0, 0, 0.3);
        margin-bottom: 12px;
    }
    .yt-sub-btn:hover { background-color: #cc0000 !important; color: #ffffff !important; }

    .insta-follow-btn {
        background: linear-gradient(45deg, #f09433, #e6683c, #dc2743, #cc2366, #bc1888) !important;
        color: #ffffff !important;
        padding: 10px 20px;
        border-radius: 20px;
        text-decoration: none;
        font-weight: 700;
        display: inline-block;
        box-shadow: 0 4px 12px rgba(220, 39, 67, 0.3);
        margin-bottom: 12px;
    }
    .insta-follow-btn:hover { opacity: 0.9; color: #ffffff !important; }

    .watch-vid-btn {
        background: linear-gradient(90deg, #1f1f1f, #ff0000) !important;
        color: #ffffff !important;
        padding: 10px 20px;
        border-radius: 20px;
        text-decoration: none;
        font-weight: 700;
        display: inline-block;
        box-shadow: 0 4px 12px rgba(255, 0, 0, 0.2);
        margin-bottom: 12px;
    }
    .watch-vid-btn:hover { opacity: 0.9; color: #ffffff !important; }
    
    div[data-testid="stMetricValue"] { color: #2fd1c5 !important; font-weight: 800 !important; font-size: 1.8rem !important; }
    .task-card { background: #121824; border: 1px solid #1e293b; padding: 15px; border-radius: 12px; margin-bottom: 15px; box-shadow: 0 4px 20px rgba(0,0,0,0.2); }
    </style>
""", unsafe_allow_html=True)

# Video Processing Engine
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
    status_text_holder.info("🎬 Video Stream Analyze & Load ho raha hai...")
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

    status_text_holder.warning("⚙️ AI Anti-Copyright Filters Inject Ho Rahe Hain...")
    progress_bar.progress(85)
    
    final_clip.write_videofile(
        output_path, codec="libx264", audio_codec="aac", bitrate=bitrate, preset="ultrafast", threads=1, logger=None
    )
    
    try:
        video.close()
        final_clip.close()
        for c in clips: c.close()
    except Exception: pass

    progress_bar.progress(100)
    status_text_holder.success("✅ Anti-Copyright Video Processing Completed!")

# Compact Header Layout
st.markdown(f"""
    <div class="nav-container">
        <div class="brand-logo">✨ CR-<span>copyright free</span></div>
        <div>
            <a href="{TELEGRAM_SUPPORT_URL}" target="_blank" class="tg-support-btn">
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21.198 2.433a2.242 2.242 0 0 0-1.022.215l-8.609 3.33c-2.068.8-4.133 1.598-6.2 2.397c-2.067.8-3.23 1.25-3.23 2.122c0 .538.356.914 1.135 1.18c.884.303 2.052.656 3.067.962c.31.093.618.183.91.272l11.455-7.182c.15-.094.3-.12.42-.08c.12.04.18.15.13.31c-.02.08-.08.18-.17.26l-9.336 8.42c-.08.08-.13.18-.14.29l-.36 3.73c-.05.51.27.98.76 1.12c.49.14 1.01-.06 1.25-.49l2.12-3.79l4.58 3.38c.67.5 1.58.38 2.09-.27c.21-.27.32-.61.32-.96l1.62-12.82c.08-.62-.17-1.24-.66-1.61c-.34-.26-.76-.38-1.18-.32z"/></svg>
                Telegram Support
            </a>
        </div>
    </div>
""", unsafe_allow_html=True)

# Authentication & Dashboard Router
if not st.session_state.logged_in:
    st.markdown("""
        <div style="text-align: center; margin: 15px 0;">
            <div class="pill-badge">✨ CR-copyright free Studio</div>
            <h1 style="font-size: 2rem; margin-bottom: 8px;">Remove Copyright Claims from Videos Instantly</h1>
            <p style="font-size: 0.9rem;">100% Automatic AI Bypass Engine for YouTube Shorts, Reels & Videos</p>
        </div>
    """, unsafe_allow_html=True)
    
    with st.form("login_form"):
        email = st.text_input("Enter Email Address")
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
    
    col_m1, col_m2, col_logout = st.columns([2, 2, 1])
    with col_m1: st.metric("Available Balance", f"🪙 {user_coins} Credits")
    with col_m2: st.metric("User Status", "👑 Admin Account" if st.session_state.is_admin else "Active Member")
    with col_logout:
        if st.button("Sign Out"):
            st.session_state.logged_in = False
            st.rerun()

    st.divider()

    menu_options = [
        "📹 Studio Processor", 
        "🎁 Free Credits Tasks", 
        "🪙 Recharge & Dynamic QR Pay", 
        "📁 Output Library Manager", 
        "🧹 Storage Cleaner", 
        "💬 Chat Support Desk"
    ]
    if st.session_state.is_admin: menu_options.append("👑 Admin Panel")
    
    selected_menu = st.radio("📌 Navigation Menu:", menu_options)
    st.divider()

    # 1. STUDIO PROCESSOR
    if selected_menu == "📹 Studio Processor":
        st.subheader("📹 Anti-Copyright Video Processing Studio")
        uploaded_file = st.file_uploader("Upload Video File (MP4, MOV, MKV, AVI)", type=["mp4", "mov", "mkv", "avi"])
        
        if uploaded_file:
            file_size_mb = uploaded_file.size / (1024 * 1024)
            size_charge = 10 if file_size_mb <= 50 else 20
            
            st.info(f"📦 File Size: **{file_size_mb:.2f} MB** | Base Editing Charge: **{size_charge} Coins**")
            
            process_mode = st.radio("Processing Mode:", ["1. Full Anti-Copyright Single Video", "2. Anti-Copyright Clipping Mode"])
            
            if process_mode == "1. Full Anti-Copyright Single Video":
                quality_option = st.radio("Export Quality & Resolution:", ["480p (Free - 0 Coins)", "720p (5 Coins)", "1080p (10 Coins)"])
                res_map = {"480p (Free - 0 Coins)": (480, "2000k", 0), "720p (5 Coins)": (720, "4000k", 5), "1080p (10 Coins)": (1080, "8000k", 10)}
                target_height, bitrate, res_charge = res_map[quality_option]
                
                total_cost = size_charge + res_charge
                st.warning(f"🪙 Total Deductible: **{total_cost} Coins** (Video Base Charge: {size_charge} + Resolution: {res_charge})")

                if st.button("🚀 Render Anti-Copyright Video"):
                    if user_coins < total_cost and not st.session_state.is_admin:
                        st.error(f"❌ Coins Kam Hain! Aapko {total_cost} Coins Chahiye.")
                    else:
                        with RENDER_LOCK:
                            p_bar = st.progress(0)
                            status_holder = st.empty()
                            temp_in = f"temp_in_{int(time.time())}.mp4"
                            out_path = f"{EXPORT_DIR}/{int(time.time())}_{uploaded_file.name}"
                            try:
                                with open(temp_in, "wb") as f: f.write(uploaded_file.read())
                                process_single_video(temp_in, out_path, target_height, bitrate, p_bar, status_holder)
                                
                                if not st.session_state.is_admin:
                                    db_data["users"][current_user] -= total_cost
                                    save_db(db_data)
                                
                                with open(out_path, "rb") as f:
                                    st.download_button("📥 Download Clean Video", f, file_name=f"CR_free_{uploaded_file.name}")
                            except Exception as e: st.error(f"Error aaya: {e}")
                            finally: auto_cleanup_storage_and_memory(temp_file_path=temp_in)

            elif process_mode == "2. Anti-Copyright Clipping Mode":
                interval_sec = st.number_input("Clip Length Interval (Seconds):", min_value=5, max_value=600, value=15)
                total_cost = size_charge
                st.warning(f"🪙 Required Coins: **{total_cost} Coins**")
                
                if st.button("✂️ Generate Cut Clips"):
                    if user_coins < total_cost and not st.session_state.is_admin:
                        st.error("❌ Balance kam hai!")
                    else:
                        with RENDER_LOCK:
                            temp_in = f"temp_in_{int(time.time())}.mp4"
                            try:
                                with open(temp_in, "wb") as f: f.write(uploaded_file.read())
                                video = VideoFileClip(temp_in)
                                curr, count = 0, 1
                                while curr < video.duration:
                                    end = min(curr + interval_sec, video.duration)
                                    subclip = apply_anti_copyright_effects(video.subclip(curr, end), count)
                                    out_clip_path = f"{EXPORT_DIR}/clip_{count}_{int(time.time())}.mp4"
                                    subclip.write_videofile(out_clip_path, codec="libx264", audio_codec="aac", preset="ultrafast", logger=None)
                                    with open(out_clip_path, "rb") as f:
                                        st.download_button(f"📥 Download Part {count}", f, file_name=f"CR_Clip_{count}.mp4", key=out_clip_path)
                                    curr += interval_sec
                                    count += 1
                                video.close()
                                if not st.session_state.is_admin:
                                    db_data["users"][current_user] -= total_cost
                                    save_db(db_data)
                            except Exception as e: st.error(f"Error aaya: {e}")
                            finally: auto_cleanup_storage_and_memory(temp_file_path=temp_in)

    # 2. FREE CREDITS TASKS
    elif selected_menu == "🎁 Free Credits Tasks":
        st.subheader("🎁 Get Free Video Credits")
        st.write("Complete tasks below to earn 10 Free Credits per action!")
        
        db_data = load_db()
        user_claims = db_data.get("claimed_tasks", {}).get(current_user, [])
        links = db_data.get("admin_links", {})

        # Task 1: YouTube
        st.markdown('<div class="task-card">', unsafe_allow_html=True)
        st.markdown("### 🔴 Subscribe YouTube Channel (+10 Credits)")
        st.markdown(f'<a href="{links.get("yt_url", "#")}" target="_blank" class="yt-sub-btn">🔴 Subscribe Now</a>', unsafe_allow_html=True)
        
        if "youtube" in user_claims:
            st.success("✅ Already Claimed!")
        else:
            if st.button("Claim 10 Credits (YouTube)", key="yt_claim"):
                db_data["users"][current_user] = db_data["users"].get(current_user, 0) + 10
                if "claimed_tasks" not in db_data: db_data["claimed_tasks"] = {}
                if current_user not in db_data["claimed_tasks"]: db_data["claimed_tasks"][current_user] = []
                db_data["claimed_tasks"][current_user].append("youtube")
                save_db(db_data)
                st.success("🎉 +10 Credits Added Successfully!")
                st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

        # Task 2: Instagram
        st.markdown('<div class="task-card">', unsafe_allow_html=True)
        st.markdown("### 📸 Follow on Instagram (+10 Credits)")
        st.markdown(f'<a href="{links.get("insta_url", "#")}" target="_blank" class="insta-follow-btn">📸 Follow Now</a>', unsafe_allow_html=True)
        
        if "instagram" in user_claims:
            st.success("✅ Already Claimed!")
        else:
            if st.button("Claim 10 Credits (Instagram)", key="insta_claim"):
                db_data["users"][current_user] = db_data["users"].get(current_user, 0) + 10
                if "claimed_tasks" not in db_data: db_data["claimed_tasks"] = {}
                if current_user not in db_data["claimed_tasks"]: db_data["claimed_tasks"][current_user] = []
                db_data["claimed_tasks"][current_user].append("instagram")
                save_db(db_data)
                st.success("🎉 +10 Credits Added Successfully!")
                st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

        # Task 3: Watch Video
        st.markdown('<div class="task-card">', unsafe_allow_html=True)
        st.markdown("### ▶️ Watch Video for 180+ Seconds (+10 Credits)")
        st.markdown(f'<a href="{links.get("video_url", "#")}" target="_blank" class="watch-vid-btn">▶️ Watch Video</a>', unsafe_allow_html=True)
        
        if "watch_video" in user_claims:
            st.success("✅ Already Claimed!")
        else:
            if "vid_timer" not in st.session_state: st.session_state.vid_timer = 0
            
            c_timer, c_btn = st.columns([2, 1])
            with c_timer:
                if st.button("⏱️ Start 180s Watch Verification Timer"):
                    st.session_state.vid_timer = time.time()
                    st.info("⌛ Timer started! Watch video link and return after 180 seconds.")
            
            with c_btn:
                if st.button("Claim 10 Credits (Video Watch)", key="vid_claim"):
                    elapsed = time.time() - st.session_state.vid_timer
                    if st.session_state.vid_timer > 0 and elapsed >= 180:
                        db_data["users"][current_user] = db_data["users"].get(current_user, 0) + 10
                        if "claimed_tasks" not in db_data: db_data["claimed_tasks"] = {}
                        if current_user not in db_data["claimed_tasks"]: db_data["claimed_tasks"][current_user] = []
                        db_data["claimed_tasks"][current_user].append("watch_video")
                        save_db(db_data)
                        st.success("🎉 +10 Credits Added Successfully!")
                        st.rerun()
                    else:
                        remaining = int(180 - elapsed) if st.session_state.vid_timer > 0 else 180
                        st.error(f"⚠️ Watch video minimum 180 seconds! ({remaining}s remaining)")
        st.markdown('</div>', unsafe_allow_html=True)

    # 3. RECHARGE & DYNAMIC QR PAY (Rule: 1 INR = 2 Coins)
    elif selected_menu == "🪙 Recharge & Dynamic QR Pay":
        st.subheader("🪙 Account Recharge via Dynamic UPI QR")
        links = db_data.get("admin_links", {})
        active_upi = links.get("upi_id", UPI_ID_TEXT)
        
        col_pay1, col_pay2 = st.columns([1, 1])
        
        with col_pay1:
            st.markdown("### 1. Payment QR Code")
            enter_amount = st.number_input("Enter Amount to Recharge (₹):", min_value=5, max_value=5000, value=50)
            calculated_coins = enter_amount * 2
            
            st.success(f"🎉 Rule (1 INR = 2 Coins): You will get **{calculated_coins} Coins**")
            
            dynamic_qr = generate_upi_qr(active_upi, enter_amount)
            st.image(dynamic_qr, caption=f"Scan & Pay ₹{enter_amount} to {active_upi}", width=220)
            st.info(f"💳 Direct UPI ID: `{active_upi}`")

        with col_pay2:
            st.markdown("### 2. Submit Transaction Proof")
            with st.form("buy_coins_form"):
                utr_no = st.text_input("Enter UTR / Transaction Ref No.")
                plan_label = f"Recharge ₹{enter_amount} ({calculated_coins} Coins)"
                if st.form_submit_button("📩 Submit UTR for Admin Approval"):
                    if utr_no.strip():
                        if "pending_requests" not in db_data: db_data["pending_requests"] = []
                        db_data["pending_requests"].append({
                            "email": current_user, 
                            "utr": utr_no.strip(), 
                            "plan": plan_label, 
                            "amount": enter_amount, 
                            "coins": calculated_coins,
                            "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        })
                        save_db(db_data)
                        st.success("✅ Payment Details Submitted! Admin will approve coins shortly.")

    # 4. OUTPUT LIBRARY
    elif selected_menu == "📁 Output Library Manager":
        st.subheader("📁 Output Video Library Manager")
        all_exports = glob.glob(os.path.join(EXPORT_DIR, "*"))
        if not all_exports:
            st.info("No processed exports available.")
        else:
            for filepath in all_exports:
                if os.path.isfile(filepath):
                    fname = os.path.basename(filepath)
                    fsize = round(os.path.getsize(filepath) / (1024 * 1024), 2)
                    c1, c2, c3 = st.columns([3, 2, 2])
                    with c1: st.write(f"📄 **{fname}**")
                    with c2: st.write(f"📦 `{fsize} MB`")
                    with c3:
                        with open(filepath, "rb") as f:
                            st.download_button("📥 Download File", f, file_name=fname, key=f"dl_{fname}")
                    st.divider()

    # 5. STORAGE CLEANER
    elif selected_menu == "🧹 Storage Cleaner":
        st.subheader("🧹 System Storage & Library Cleaner")
        if st.button("🚨 Purge Storage Cache"):
            for f in glob.glob(os.path.join(EXPORT_DIR, "*")):
                try: os.remove(f)
                except Exception: pass
            gc.collect()
            st.success("✅ Storage Successfully Purged!")

    # 6. CHAT SUPPORT
    elif selected_menu == "💬 Chat Support Desk":
        st.subheader("💬 Private Support Desk")
        
        tickets = db_data.get("support_tickets", [])
        my_tickets = [t for t in tickets if t.get("user") == current_user]
        
        if my_tickets:
            st.markdown("### 📩 Support History & Replies:")
            for t in my_tickets:
                st.info(f"**You ({t['date']}):** {t['msg']}")
                if t.get("reply"):
                    st.success(f"**👑 Admin Reply:** {t['reply']}")
                else:
                    st.warning("⏳ Admin reply pending...")
                st.divider()

        with st.form("send_msg_form"):
            user_msg = st.text_area("Write Message for Support Admin:")
            if st.form_submit_button("📤 Send Message"):
                if user_msg.strip():
                    new_ticket = {
                        "id": int(time.time()),
                        "user": current_user,
                        "msg": user_msg.strip(),
                        "reply": "",
                        "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    }
                    db_data["support_tickets"].append(new_ticket)
                    save_db(db_data)
                    st.success("Message Submitted!")
                    st.rerun()

    # 7. ADMIN PANEL
    elif selected_menu == "👑 Admin Panel" and st.session_state.is_admin:
        st.subheader("👑 Master Admin Console")
        
        tab1, tab2, tab3 = st.tabs(["🔗 Dynamic Link Settings", "💬 Message Desk", "🪙 Payment Approvals"])
        
        # TAB 1: LINKS MANAGEMENT (FIXED persistent save)
        with tab1:
            st.markdown("### Update Task Links & System UPI")
            curr_db = load_db()
            curr_links = curr_db.get("admin_links", {})
            
            with st.form("links_form"):
                yt = st.text_input("YouTube Channel Subscribe Link", value=curr_links.get("yt_url", ""))
                insta = st.text_input("Instagram Follow Profile Link", value=curr_links.get("insta_url", ""))
                vid = st.text_input("Watch Video Link (180s requirement)", value=curr_links.get("video_url", ""))
                upi = st.text_input("Default Payment UPI ID", value=curr_links.get("upi_id", UPI_ID_TEXT))
                
                if st.form_submit_button("💾 Save All Settings"):
                    curr_db["admin_links"] = {
                        "yt_url": yt.strip(), 
                        "insta_url": insta.strip(), 
                        "video_url": vid.strip(), 
                        "upi_id": upi.strip()
                    }
                    save_db(curr_db)
                    st.success("✅ All Links & System UPI Updated Successfully!")
                    st.rerun()

        # TAB 2: SUPPORT DESK REPLIES
        with tab2:
            st.markdown("### User Messages & Instant Replies")
            tickets = db_data.get("support_tickets", [])
            if not tickets:
                st.write("No active support tickets.")
            for idx, t in enumerate(tickets):
                st.write(f"👤 **{t['user']}** ({t['date']}): {t['msg']}")
                if t.get("reply"):
                    st.write(f"Current Reply: *{t['reply']}*")
                
                reply_input = st.text_input(f"Write Reply for #{t['id']}", key=f"rep_{t['id']}")
                if st.button("Send Reply", key=f"btn_rep_{t['id']}"):
                    if reply_input.strip():
                        db_data["support_tickets"][idx]["reply"] = reply_input.strip()
                        save_db(db_data)
                        st.success("Reply Sent!")
                        st.rerun()
                st.divider()

        # TAB 3: PAYMENT APPROVALS
        with tab3:
            st.markdown("### Approve Payment Requests")
            pending_reqs = db_data.get("pending_requests", [])
            if not pending_reqs:
                st.write("No pending requests.")
            for idx, req in enumerate(pending_reqs):
                default_grant = req.get("coins", req.get("amount", 10) * 2)
                st.write(f"👤 **{req['email']}** | Plan: **{req['plan']}** | UTR: `{req['utr']}`")
                add_c = st.number_input("Credits to Grant:", min_value=1, value=default_grant, key=f"c_{idx}")
                if st.button("✅ Approve Payment", key=f"app_{idx}"):
                    db_data["users"][req['email']] = db_data["users"].get(req['email'], 0) + add_c
                    db_data["pending_requests"].pop(idx)
                    save_db(db_data)
                    st.success("Payment Approved & Credits Granted!")
                    st.rerun()
                st.divider()
