import streamlit as st
import time, json, os, hashlib, gc, glob, threading
import numpy as np
import PIL.Image
from datetime import datetime, timedelta
import urllib.parse

# MoviePy Compatibility Fix
if not hasattr(PIL.Image, 'ANTIALIAS'):
    PIL.Image.ANTIALIAS = PIL.Image.Resampling.LANCZOS

try:
    from moviepy.editor import VideoFileClip, concatenate_videoclips
    import moviepy.video.fx.all as vfx
except ImportError:
    from moviepy import VideoFileClip, concatenate_videoclips
    import moviepy.video.fx as vfx

# Global Render Lock System (Single User At A Time Execution)
@st.cache_resource
def get_render_lock():
    return threading.Lock()

RENDER_LOCK = get_render_lock()

st.set_page_config(page_title="No Copyright Video Studio Pro", page_icon="🎬", layout="wide")

DB_FILE = "database.json"
TELEGRAM_SUPPORT_URL = "https://t.me/+Yhr7ZJWcqBwyNmFl"
UPI_ID_TEXT = "cinepoliis@ibl"
BG_IMAGE_URL = "https://i.postimg.cc/P5P1CkHY/no.png"
EXPORT_DIR = "exports"

def hash_text(text):
    return hashlib.sha256(text.encode()).hexdigest()

ADMIN_EMAIL_HASH = hash_text("krish9agupt@gmail.com")
ADMIN_PASSCODE_HASH = hash_text("Krish9A")
USER_PASSCODE = "123456"

# Automated Cleanup Function (Storage and Memory Optimization)
def auto_cleanup_storage_and_memory(temp_file_path=None, max_age_hours=24):
    if temp_file_path and os.path.exists(temp_file_path):
        try:
            os.remove(temp_file_path)
        except Exception:
            pass
            
    if os.path.exists(EXPORT_DIR):
        now_time = time.time()
        for file_path in glob.glob(os.path.join(EXPORT_DIR, "*")):
            if os.path.isfile(file_path):
                file_age_hours = (now_time - os.path.getmtime(file_path)) / 3600
                if file_age_hours > max_age_hours:
                    try:
                        os.remove(file_path)
                    except Exception:
                        pass
                        
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
    with open(DB_FILE, "w") as f:
        json.dump(data, f, indent=4)

if "logged_in" not in st.session_state: st.session_state.logged_in = False
if "user_email" not in st.session_state: st.session_state.user_email = ""
if "is_admin" not in st.session_state: st.session_state.is_admin = False

# Custom CSS Styling
st.markdown(f"""
    <style>
    #MainMenu, header, footer {{visibility: hidden;}}
    .stApp {{
        background-image: url("{BG_IMAGE_URL}");
        background-size: cover;
        background-position: center;
        background-attachment: fixed;
        color: #FFFFFF;
    }}
    .stApp > div {{
        background: rgba(11, 12, 16, 0.85);
        padding: 20px;
        border-radius: 10px;
    }}
    .main-header {{
        text-align: left; font-weight: 900; font-size: 2.2rem;
        background: linear-gradient(45deg, #FFD700, #FF69B4);
        -webkit-background-clip: text; -webkit-text-fill-color: transparent;
    }}
    .tg-support-btn {{
        float: right; background: linear-gradient(90deg, #0088cc, #00c6ff);
        color: white !important; padding: 8px 16px; border-radius: 20px;
        text-decoration: none; font-weight: bold;
    }}
    [data-testid="stMetricValue"] {{
        font-size: 1.1rem !important;
        font-weight: 600 !important;
    }}
    [data-testid="stMetricLabel"] {{
        font-size: 0.85rem !important;
    }}
    </style>
""", unsafe_allow_html=True)

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
    elif edit_num == 3: clip = clip.speedx(1.2) if hasattr(clip, 'speedx') else clip
    elif edit_num in [4, 13]: clip = clip.fx(vfx.colorx, 0.90) if hasattr(vfx, 'colorx') else clip
    elif edit_num in [5, 11, 15]: clip = clip.fx(vfx.colorx, 1.20) if hasattr(vfx, 'colorx') else clip
    elif edit_num == 6: clip = clip.fl_image(lambda img: img[:, ::-1])
    elif edit_num == 7: clip = clip.fx(vfx.colorx, 1.10) if hasattr(vfx, 'colorx') else clip
    elif edit_num == 9: clip = clip.speedx(1.15) if hasattr(clip, 'speedx') else clip
    elif edit_num == 10: clip = manual_zoom(clip, 1.05)
    elif edit_num == 12: clip = manual_zoom(clip, 1.12)
    elif edit_num == 14:
        clip = clip.fl_image(lambda img: img[:, ::-1])
        if hasattr(clip, 'speedx'): clip = clip.speedx(1.15)
    return clip

def process_single_video(input_path, output_path, target_height, bitrate, progress_bar, status_text_holder):
    start_time = time.time()
    
    status_text_holder.info("🎬 Video load ho raha hai... (Calculating ETA)")
    progress_bar.progress(5)
    
    video = VideoFileClip(input_path)
    cut_duration = video.duration / 15.0
    clips = []

    orig_w, orig_h = video.size
    aspect_ratio = orig_w / float(orig_h)

    for edit_idx in range(1, 16):
        subclip = video.subclip((edit_idx - 1) * cut_duration, edit_idx * cut_duration)
        clips.append(apply_custom_effects(subclip, edit_idx))

    final_clip = concatenate_videoclips(clips)

    if orig_h != target_height:
        new_w = int(target_height * aspect_ratio)
        if new_w % 2 != 0: new_w += 1
        final_clip = final_clip.resize(newsize=(new_w, target_height))

    estimated_total = max(20, int(video.duration * 1.5))

    for pct in range(10, 85, 5):
        elapsed = int(time.time() - start_time)
        rem_sec = max(1, estimated_total - elapsed)
        status_text_holder.warning(f"⚡ Processing Effects & Rescaling... | ⏳ Remaining Time: {rem_sec} sec left (Elapsed: {elapsed}s)")
        progress_bar.progress(pct)
        time.sleep(0.3)

    status_text_holder.warning("⚙️ Video Render ho raha hai... Finalizing file...")
    progress_bar.progress(85)
    
    # Low Memory Optimization Render Parameters
    final_clip.write_videofile(
        output_path, 
        codec="libx264", 
        audio_codec="aac", 
        bitrate=bitrate, 
        preset="ultrafast", 
        threads=1, 
        logger=None
    )
    
    try:
        video.close()
        final_clip.close()
        for c in clips: c.close()
    except Exception:
        pass

    total_elapsed = int(time.time() - start_time)
    progress_bar.progress(100)
    status_text_holder.success(f"✅ Video Render Completed in {total_elapsed} seconds!")

# Main Layout Header
col_title, col_support = st.columns([3, 1])
with col_title: st.markdown("<h1 class='main-header'>🎬 NO COPYRIGHT VIDEO STUDIO PRO</h1>", unsafe_allow_html=True)
with col_support: st.markdown(f'<a href="{TELEGRAM_SUPPORT_URL}" target="_blank" class="tg-support-btn">✈️ Telegram Support</a>', unsafe_allow_html=True)

st.divider()

if not st.session_state.logged_in:
    st.subheader("🔑 Sign In")
    with st.form("login_form"):
        email = st.text_input("Enter Email Address")
        passcode = st.text_input("Access Passcode", value=USER_PASSCODE, type="password")
        if st.form_submit_button("🚀 Enter Dashboard"):
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
            days = diff.days
            hours, remainder = divmod(diff.seconds, 3600)
            minutes, seconds = divmod(remainder, 60)
            timer_str = f"⏳ {days}d {hours}h {minutes}m left"
            expiry_display = f"{sub_info['plan']} ({timer_str})"
        else:
            expiry_display = "⚠️ Plan Expired!"

    col_m1, col_m2, col_logout = st.columns([2, 2, 1])
    with col_m1: st.metric("Available Coins", f"🪙 {user_coins}")
    with col_m2: st.metric("Plan Status", expiry_display)
    with col_logout:
        if st.button("🚪 Logout"):
            st.session_state.logged_in = False
            st.rerun()

    tab_list = ["📹 Studio Processor", "🪙 Buy Coins / Subscriptions", "💬 Chat with Admin", "📜 Download History"]
    if st.session_state.is_admin:
        tab_list.append("👑 Admin Panel")
    
    tabs = st.tabs(tab_list)

    # 1. STUDIO PROCESSOR
    with tabs[0]:
        uploaded_file = st.file_uploader("Upload Video File", type=["mp4", "mov", "mkv", "avi"])
        if uploaded_file:
            quality_option = st.radio("Select Export Quality:", ["720p HD (Free - 0 Coin)", "1080p Full HD (5 Coins)", "2K / 4K Ultra HD (10 Coins)"])
            
            res_config = {
                "720p HD (Free - 0 Coin)": (720, "4000k", 0),
                "1080p Full HD (5 Coins)": (1080, "12000k", 5),
                "2K / 4K Ultra HD (10 Coins)": (2160, "45000k", 10)
            }
            target_height, bitrate, required_coins = res_config[quality_option]

            if st.button("🚀 Render Video"):
                if user_coins < required_coins and not st.session_state.is_admin:
                    st.error(f"❌ Iss quality ke liye {required_coins} Coins chahiye. Aapke paas sirf {user_coins} Coins hain.")
                else:
                    if RENDER_LOCK.locked():
                        st.warning("⏳ Server busy hai! Aap Queue me hain. Estimated Waiting Time: ~1-2 Minutes.")

                    with RENDER_LOCK:
                        if not os.path.exists(EXPORT_DIR): os.makedirs(EXPORT_DIR)
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
                            db_data["history"][current_user].append({
                                "filename": uploaded_file.name, 
                                "path": out_path, 
                                "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                            })
                            save_db(db_data)

                            st.success("🎉 Video Render Ho Gaya Hai! Unique file aapki Download History me sync ho chuki hai.")
                            
                            with open(out_path, "rb") as f:
                                st.download_button("📥 Direct Download Video", f, file_name=f"edited_{uploaded_file.name}", mime="video/mp4", use_container_width=True)

                        except Exception as e:
                            st.error(f"Processing me error aaya: {e}")

                        finally:
                            auto_cleanup_storage_and_memory(temp_file_path=temp_in)

    # 2. BUY COINS & PLANS TAB
    with tabs[1]:
        st.subheader("🪙 Recharge Coins & Buy Plans")
        
        st.markdown("""
        ### 📌 **Our Pricing & Subscription Plans:**
        * 🪙 **Starter Pack:** ₹49 = **50 Coins**
        * 🚀 **Pro Pack:** ₹199 = **300 Coins**
        * 🗓️ **Weekly Plan:** ₹249 = **600 Coins** *(Validity: 7 Days)*
        * 📅 **Monthly Plan:** ₹399 = **999 Coins** *(Validity: 30 Days)*
        * 👑 **Monthly VIP:** ₹999 = **Unlimited Coins** *(Validity: 30 Days)*
        """)
        
        st.divider()
        st.subheader("💳 UPI Payment & QR Code")
        
        col_qr1, col_qr2 = st.columns([1, 2])
        with col_qr1:
            upi_qr_url = f"https://api.qrserver.com/v1/create-qr-code/?size=220x220&data={urllib.parse.quote(f'upi://pay?pa={UPI_ID_TEXT}&pn=CinepoliisStudio&cu=INR')}"
            st.image(upi_qr_url, caption="Scan QR to Pay via PhonePe / GPay / Paytm / UPI", width=200)
            
        with col_qr2:
            st.info("Niche diye gaye UPI ID par payment karein ya QR Code scan karein. Payment ke baad UTR Reference Number submit karein:")
            st.code(UPI_ID_TEXT, language="text")

        with st.form("buy_coins_form"):
            utr_no = st.text_input("Enter UTR / Transaction Reference No.")
            selected_plan = st.selectbox("Select Your Plan / Coins Pack", [
                "₹49 - 50 Coins",
                "₹199 - 300 Coins",
                "₹249 - 600 Coins (Weekly - 7 Days)",
                "₹399 - 999 Coins (Monthly - 30 Days)",
                "₹999 - VIP Unlimited Plan (30 Days)"
            ])
            if st.form_submit_button("📩 Submit Payment Request"):
                if utr_no.strip():
                    if "pending_requests" not in db_data: db_data["pending_requests"] = []
                    db_data["pending_requests"].append({
                        "email": current_user,
                        "utr": utr_no.strip(),
                        "plan": selected_plan,
                        "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    })
                    save_db(db_data)
                    st.success("✅ Payment Request Submitted! Admin verification ke baad coins aur plan duration add kar diya jayega.")
                else:
                    st.error("⚠️ UTR / Transaction ID bharna zaroori hai.")

    # 3. CHAT WITH ADMIN
    with tabs[2]:
        st.subheader("💬 Private Support Chat with Admin")
        with st.form("send_msg_form"):
            user_msg = st.text_area("Write Message:")
            if st.form_submit_button("📤 Send Message"):
                if user_msg.strip():
                    ticket = {
                        "id": int(time.time()),
                        "user": current_user,
                        "msg": user_msg.strip(),
                        "reply": "",
                        "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    }
                    if "support_tickets" not in db_data: db_data["support_tickets"] = []
                    db_data["support_tickets"].append(ticket)
                    save_db(db_data)
                    st.success("✅ Message bhej diya gaya hai!")
                    st.rerun()

        st.divider()
        st.write("🔒 **Your Private Chat History:**")
        all_tickets = db_data.get("support_tickets", [])
        my_tickets = [t for t in all_tickets if t.get("user") == current_user]
        
        if not my_tickets:
            st.info("Aapka koi purana message nahi hai.")
        else:
            for t in reversed(my_tickets):
                st.write(f"💬 **You ({t['date']}):** {t['msg']}")
                if t.get("reply"):
                    st.success(f"👑 **Admin Reply:** {t['reply']}")
                else:
                    st.warning("⏳ Admin reply ka wait karein...")
                st.divider()

    # 4. DOWNLOAD HISTORY
    with tabs[3]:
        st.subheader("📜 Your Edited Videos History")
        user_history = db_data.get("history", {}).get(current_user, [])
        if not user_history:
            st.write("Koi history nahi hai.")
        for item in reversed(user_history):
            st.write(f"📹 **{item['filename']}** | 🕒 {item['date']}")
            if os.path.exists(item['path']):
                with open(item['path'], "rb") as f:
                    st.download_button("📥 Download Again", f, file_name=f"edited_{item['filename']}", key=item['path'])
            else:
                st.caption("⚠️ File cleanup System ke karan storage se delete ho chuki hai.")
            st.divider()

    # 5. ADMIN PANEL
    if st.session_state.is_admin:
        with tabs[4]:
            st.subheader("👑 Admin Management Console")
            
            st.write("### 🪙 Pending Payment Verification Requests")
            pending_reqs = db_data.get("pending_requests", [])
            if not pending_reqs:
                st.info("Koi pending payment request nahi hai.")
            else:
                for idx, req in enumerate(pending_reqs):
                    st.write(f"👤 **{req['email']}** | Plan: **{req['plan']}** | UTR: `{req['utr']}` ({req['date']})")
                    c1, c2 = st.columns(2)
                    if c1.button("✅ Approve Request", key=f"app_{idx}"):
                        u_email = req['email']
                        plan_str = req['plan']
                        coins_to_add = 50
                        days_validity = 0

                        if "300" in plan_str: coins_to_add = 300
                        elif "600" in plan_str or "Weekly" in plan_str:
                            coins_to_add = 600
                            days_validity = 7
                        elif "999 Coins" in plan_str or "Monthly" in plan_str:
                            coins_to_add = 999
                            days_validity = 30
                        elif "VIP" in plan_str:
                            coins_to_add = 99999
                            days_validity = 30
                        
                        db_data["users"][u_email] = db_data["users"].get(u_email, 0) + coins_to_add
                        
                        if days_validity > 0:
                            exp_time = datetime.now() + timedelta(days=days_validity)
                            if "subscriptions" not in db_data: db_data["subscriptions"] = {}
                            db_data["subscriptions"][u_email] = {
                                "plan": plan_str,
                                "expiry": exp_time.strftime("%Y-%m-%d %H:%M:%S")
                            }

                        db_data["pending_requests"].pop(idx)
                        save_db(db_data)
                        st.success(f"Approved {plan_str} for {u_email}")
                        st.rerun()
                        
                    if c2.button("❌ Reject Request", key=f"rej_{idx}"):
                        db_data["pending_requests"].pop(idx)
                        save_db(db_data)
                        st.warning("Request Rejected")
                        st.rerun()
                    st.divider()

            st.write("### 💬 User Support Tickets")
            all_tickets = db_data.get("support_tickets", [])
            unreplied = [t for t in all_tickets if not t.get("reply")]
            
            if not unreplied:
                st.info("Koi naya message nahi hai.")
            else:
                for t in unreplied:
                    st.write(f"👤 **{t['user']}** ({t['date']}): {t['msg']}")
                    reply_text = st.text_input("Reply text:", key=f"reply_in_{t['id']}")
                    if st.button("Send Reply", key=f"btn_rep_{t['id']}"):
                        if reply_text.strip():
                            t["reply"] = reply_text.strip()
                            save_db(db_data)
                            st.success("Reply bhej diya gaya!")
                            st.rerun()
                    st.divider()
