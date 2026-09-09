import streamlit as st
import time, json, os, hashlib, gc, glob, threading
import numpy as np
import PIL.Image
from datetime import datetime

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

# Auto Cleanup
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
            "qr_url": "https://i.postimg.cc/P5P1CkHY/no.png"
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

# Styling
st.markdown("""
    <style>
    #MainMenu, header, footer {visibility: hidden;}
    .stApp { background-color: #0b0f17 !important; color: #e6edf3 !important; }
    p, span, label, div, li { color: #919eab !important; }
    h1, h2, h3, h4, h5, h6 { color: #ffffff !important; font-weight: 700 !important; }
    .nav-container { display: flex; justify-content: space-between; align-items: center; padding: 10px 0px 20px 0px; border-bottom: 1px solid #1e293b; margin-bottom: 25px; }
    .brand-logo { font-size: 1.5rem; font-weight: 800; color: #ffffff !important; }
    .brand-logo span { color: #2fd1c5 !important; }
    .pill-badge { background: rgba(47, 209, 197, 0.1); border: 1px solid rgba(47, 209, 197, 0.3); color: #2fd1c5 !important; padding: 6px 16px; border-radius: 20px; font-size: 0.85rem; font-weight: 600; display: inline-block; margin-bottom: 15px; }
    .stButton > button, div[data-testid="stDownloadButton"] > button { background-color: #2fd1c5 !important; color: #0b0f17 !important; font-weight: 700 !important; border-radius: 10px !important; border: none !important; width: 100%; }
    .stButton > button:hover { background-color: #26b3a9 !important; }
    div[data-baseweb="input"] > div, div[data-baseweb="select"] > div { background-color: #161f2e !important; border: 1px solid #283548 !important; color: #ffffff !important; border-radius: 10px !important; }
    div[data-testid="stRadio"] div[role="radiogroup"] > label { background-color: #121824 !important; border: 1px solid #1e293b !important; border-radius: 10px !important; padding: 12px 18px !important; margin-bottom: 8px !important; width: 100% !important; }
    .tg-support-btn { background-color: #2fd1c5; color: #0b0f17 !important; padding: 8px 18px; border-radius: 8px; text-decoration: none; font-weight: 700; }
    div[data-testid="stMetricValue"] { color: #2fd1c5 !important; font-weight: 800 !important; }
    .task-card { background: #121824; border: 1px solid #1e293b; padding: 15px; border-radius: 10px; margin-bottom: 15px; }
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
    status_text_holder.info("🎬 Video load ho rahi hai...")
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

    status_text_holder.warning("⚙️ Processing & Anti-Copyright Engine running...")
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
    status_text_holder.success("✅ Complete!")

# Header
st.markdown(f"""
    <div class="nav-container">
        <div class="brand-logo">✨ CR <span>Removes</span></div>
        <div><a href="{TELEGRAM_SUPPORT_URL}" target="_blank" class="tg-support-btn">Support Community</a></div>
    </div>
""", unsafe_allow_html=True)

# Authentication
if not st.session_state.logged_in:
    st.markdown("""
        <div style="text-align: center; margin: 30px 0;">
            <div class="pill-badge">✨ AI CR Removes</div>
            <h1>Remove Copyright Claims Instantly</h1>
        </div>
    """, unsafe_allow_html=True)
    
    with st.form("login_form"):
        email = st.text_input("Email Address")
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
    with col_m2: st.metric("Account", "Admin" if st.session_state.is_admin else "Standard User")
    with col_logout:
        if st.button("Sign Out"):
            st.session_state.logged_in = False
            st.rerun()

    st.divider()

    menu_options = [
        "📹 Studio Processor", 
        "🎁 Free Credits Tasks", 
        "🪙 Buy Coins / QR Pay", 
        "📁 Output Library", 
        "🧹 Library Cleaner", 
        "💬 Chat Support"
    ]
    if st.session_state.is_admin: menu_options.append("👑 Admin Panel")
    
    selected_menu = st.radio("Navigation Menu:", menu_options)
    st.divider()

    # 1. STUDIO PROCESSOR (NEW COIN DEDUCTION LOGIC)
    if selected_menu == "📹 Studio Processor":
        st.subheader("📹 Anti-Copyright Video Studio")
        uploaded_file = st.file_uploader("Upload Video File", type=["mp4", "mov", "mkv", "avi"])
        
        if uploaded_file:
            file_size_mb = uploaded_file.size / (1024 * 1024)
            size_charge = 10 if file_size_mb <= 50 else 20
            
            st.info(f"📦 File Size: **{file_size_mb:.2f} MB** | Base Editing Charge: **{size_charge} Coins**")
            
            process_mode = st.radio("Processing Mode:", ["1. Single Full Video", "2. Anti-Copyright Clipping Mode"])
            
            if process_mode == "1. Single Full Video":
                quality_option = st.radio("Export Resolution:", ["480p (Free - 0 Coins)", "720p (5 Coins)", "1080p (10 Coins)"])
                res_map = {"480p (Free - 0 Coins)": (480, "2000k", 0), "720p (5 Coins)": (720, "4000k", 5), "1080p (10 Coins)": (1080, "8000k", 10)}
                target_height, bitrate, res_charge = res_map[quality_option]
                
                total_cost = size_charge + res_charge
                st.warning(f"🪙 Total Required: **{total_cost} Coins** (Base Editing: {size_charge} + Resolution: {res_charge})")

                if st.button("🚀 Process & Render Video"):
                    if user_coins < total_cost and not st.session_state.is_admin:
                        st.error(f"❌ Coins kam hain! Is process ke liye {total_cost} Coins chahiye.")
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
                                    st.download_button("📥 Download Video", f, file_name=f"edited_{uploaded_file.name}")
                            except Exception as e: st.error(f"Error: {e}")
                            finally: auto_cleanup_storage_and_memory(temp_file_path=temp_in)

            elif process_mode == "2. Anti-Copyright Clipping Mode":
                interval_sec = st.number_input("Clip Interval (Seconds):", min_value=5, max_value=600, value=15)
                total_cost = size_charge
                st.warning(f"🪙 Required: **{total_cost} Coins**")
                
                if st.button("✂️ Generate Clips"):
                    if user_coins < total_cost and not st.session_state.is_admin:
                        st.error("❌ Coins kam hain!")
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
                                        st.download_button(f"📥 Download Clip {count}", f, file_name=f"Clip_{count}.mp4", key=out_clip_path)
                                    curr += interval_sec
                                    count += 1
                                video.close()
                                if not st.session_state.is_admin:
                                    db_data["users"][current_user] -= total_cost
                                    save_db(db_data)
                            except Exception as e: st.error(f"Error: {e}")
                            finally: auto_cleanup_storage_and_memory(temp_file_path=temp_in)

    # 2. FREE CREDITS TASKS MENU
    elif selected_menu == "🎁 Free Credits Tasks":
        st.subheader("🎁 Get Free Video Credits")
        st.write("Neeche diye gaye simple tasks complete karke 10-10 Free Credits claim karein!")
        
        user_claims = db_data.get("claimed_tasks", {}).get(current_user, [])
        links = db_data.get("admin_links", {})

        # Task 1: YouTube
        st.markdown('<div class="task-card">', unsafe_allow_html=True)
        st.markdown("### 🔴 Subscribe YouTube Channel (+10 Credits)")
        st.markdown(f"[👉 Click Here to Subscribe Channel]({links.get('yt_url', '#')})")
        if "youtube" in user_claims:
            st.success("✅ Already Claimed!")
        else:
            if st.button("Claim 10 Credits (YouTube)", key="yt_claim"):
                db_data["users"][current_user] = db_data["users"].get(current_user, 0) + 10
                if "claimed_tasks" not in db_data: db_data["claimed_tasks"] = {}
                if current_user not in db_data["claimed_tasks"]: db_data["claimed_tasks"][current_user] = []
                db_data["claimed_tasks"][current_user].append("youtube")
                save_db(db_data)
                st.success("🎉 +10 Credits Added!")
                st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

        # Task 2: Instagram
        st.markdown('<div class="task-card">', unsafe_allow_html=True)
        st.markdown("### 📸 Follow on Instagram (+10 Credits)")
        st.markdown(f"[👉 Click Here to Follow Instagram]({links.get('insta_url', '#')})")
        if "instagram" in user_claims:
            st.success("✅ Already Claimed!")
        else:
            if st.button("Claim 10 Credits (Instagram)", key="insta_claim"):
                db_data["users"][current_user] = db_data["users"].get(current_user, 0) + 10
                if "claimed_tasks" not in db_data: db_data["claimed_tasks"] = {}
                if current_user not in db_data["claimed_tasks"]: db_data["claimed_tasks"][current_user] = []
                db_data["claimed_tasks"][current_user].append("instagram")
                save_db(db_data)
                st.success("🎉 +10 Credits Added!")
                st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

        # Task 3: Watch Video
        st.markdown('<div class="task-card">', unsafe_allow_html=True)
        st.markdown("### ▶️ Watch Video (+10 Credits)")
        st.markdown(f"[👉 Click Here to Watch Video]({links.get('video_url', '#')})")
        if "watch_video" in user_claims:
            st.success("✅ Already Claimed!")
        else:
            if st.button("Claim 10 Credits (Video)", key="vid_claim"):
                db_data["users"][current_user] = db_data["users"].get(current_user, 0) + 10
                if "claimed_tasks" not in db_data: db_data["claimed_tasks"] = {}
                if current_user not in db_data["claimed_tasks"]: db_data["claimed_tasks"][current_user] = []
                db_data["claimed_tasks"][current_user].append("watch_video")
                save_db(db_data)
                st.success("🎉 +10 Credits Added!")
                st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

    # 3. BUY COINS & QR PAY
    elif selected_menu == "🪙 Buy Coins / QR Pay":
        st.subheader("🪙 Recharge & Prepaid Plans")
        links = db_data.get("admin_links", {})
        
        c1, c2 = st.columns([1, 1])
        with c1:
            st.image(links.get("qr_url", "https://i.postimg.cc/P5P1CkHY/no.png"), caption="Scan QR Code to Pay", width=260)
            st.info(f"💳 Direct UPI ID: `{UPI_ID_TEXT}`")
        
        with c2:
            with st.form("buy_coins_form"):
                utr_no = st.text_input("Enter Transaction / UTR No.")
                selected_plan = st.selectbox("Select Coin Pack", ["₹49 - 50 Coins", "₹149 - 200 Coins", "₹249 - 400 Coins", "₹399 - 800 Coins"])
                if st.form_submit_button("📩 Submit Payment Proof"):
                    if utr_no.strip():
                        if "pending_requests" not in db_data: db_data["pending_requests"] = []
                        db_data["pending_requests"].append({"email": current_user, "utr": utr_no.strip(), "plan": selected_plan, "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S")})
                        save_db(db_data)
                        st.success("✅ Payment Details Sent for Admin Approval!")

    # 4. OUTPUT LIBRARY
    elif selected_menu == "📁 Output Library":
        st.subheader("📁 Output Video Library")
        all_exports = glob.glob(os.path.join(EXPORT_DIR, "*"))
        if not all_exports:
            st.info("Library khali hai.")
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
                            st.download_button("📥 Download", f, file_name=fname, key=f"dl_{fname}")
                    st.divider()

    # 5. CLEANER
    elif selected_menu == "🧹 Library Cleaner":
        st.subheader("🧹 Clear Memory Cache")
        if st.button("🚨 Clear Storage Cache"):
            for f in glob.glob(os.path.join(EXPORT_DIR, "*")):
                try: os.remove(f)
                except Exception: pass
            gc.collect()
            st.success("✅ Cache Cleaned!")

    # 6. CHAT SUPPORT (WITH REPLY VIEW)
    elif selected_menu == "💬 Chat Support":
        st.subheader("💬 Private Help & Support")
        
        tickets = db_data.get("support_tickets", [])
        my_tickets = [t for t in tickets if t.get("user") == current_user]
        
        if my_tickets:
            st.markdown("### 📩 Your Previous Messages & Admin Replies:")
            for t in my_tickets:
                st.info(f"**You ({t['date']}):** {t['msg']}")
                if t.get("reply"):
                    st.success(f"**👑 Admin Reply:** {t['reply']}")
                else:
                    st.warning("⏳ Admin reply is pending...")
                st.divider()

        with st.form("send_msg_form"):
            user_msg = st.text_area("Write Message for Admin:")
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
                    st.success("Message Sent!")
                    st.rerun()

    # 7. ADMIN PANEL (FULL CONTROLS)
    elif selected_menu == "👑 Admin Panel" and st.session_state.is_admin:
        st.subheader("👑 Master Admin Controls")
        
        tab1, tab2, tab3 = st.tabs(["🔗 Manage Links & QR", "📩 Reply to Messages", "🪙 Pending Payments"])
        
        # LINK & QR MANAGEMENT
        with tab1:
            st.markdown("### Update Task Links & QR Image")
            curr_links = db_data.get("admin_links", {})
            with st.form("links_form"):
                yt = st.text_input("YouTube Channel Link", value=curr_links.get("yt_url", ""))
                insta = st.text_input("Instagram Profile Link", value=curr_links.get("insta_url", ""))
                vid = st.text_input("Watch Video Link", value=curr_links.get("video_url", ""))
                qr = st.text_input("Payment QR Image Direct URL", value=curr_links.get("qr_url", ""))
                
                if st.form_submit_button("💾 Save All Links"):
                    db_data["admin_links"] = {"yt_url": yt, "insta_url": insta, "video_url": vid, "qr_url": qr}
                    save_db(db_data)
                    st.success("✅ All Links & QR Updated!")

        # MESSAGE REPLIES
        with tab2:
            st.markdown("### Reply to User Messages")
            tickets = db_data.get("support_tickets", [])
            if not tickets:
                st.write("No support tickets.")
            for idx, t in enumerate(tickets):
                st.write(f"👤 **{t['user']}** ({t['date']}): {t['msg']}")
                if t.get("reply"):
                    st.write(f" Reply Sent: *{t['reply']}*")
                
                reply_input = st.text_input(f"Write Reply for ticket #{t['id']}", key=f"rep_{t['id']}")
                if st.button("Send Reply", key=f"btn_rep_{t['id']}"):
                    if reply_input.strip():
                        db_data["support_tickets"][idx]["reply"] = reply_input.strip()
                        save_db(db_data)
                        st.success("Reply Sent!")
                        st.rerun()
                st.divider()

        # PAYMENTS
        with tab3:
            st.markdown("### Pending Payment Approvals")
            pending_reqs = db_data.get("pending_requests", [])
            for idx, req in enumerate(pending_reqs):
                st.write(f"👤 **{req['email']}** | Pack: **{req['plan']}** | UTR: `{req['utr']}`")
                add_c = st.number_input("Coins to Add:", min_value=1, value=100, key=f"c_{idx}")
                if st.button("✅ Approve Payment", key=f"app_{idx}"):
                    db_data["users"][req['email']] = db_data["users"].get(req['email'], 0) + add_c
                    db_data["pending_requests"].pop(idx)
                    save_db(db_data)
                    st.success("Payment Approved & Coins Added!")
                    st.rerun()
                st.divider()
