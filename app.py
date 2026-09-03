import streamlit as st
import time, json, os, hashlib
import numpy as np
import PIL.Image
from datetime import datetime

# MoviePy Compatibility Fix
if not hasattr(PIL.Image, 'ANTIALIAS'):
    PIL.Image.ANTIALIAS = PIL.Image.Resampling.LANCZOS

try:
    from moviepy.editor import VideoFileClip, concatenate_videoclips
    import moviepy.video.fx.all as vfx
except ImportError:
    from moviepy import VideoFileClip, concatenate_videoclips
    import moviepy.video.fx as vfx

# Page Configuration
st.set_page_config(page_title="No Copyright Video Studio Pro", page_icon="🎬", layout="wide")

DB_FILE = "database.json"
TELEGRAM_SUPPORT_URL = "https://t.me/your_telegram_username"
UPI_QR_IMAGE_PATH = "upi_qr.png"
UPI_ID_TEXT = "yourupi@upi"

def hash_text(text):
    return hashlib.sha256(text.encode()).hexdigest()

ADMIN_EMAIL_HASH = hash_text("krish9agupt@gmail.com")
ADMIN_PASSCODE_HASH = hash_text("Krish9A")
USER_PASSCODE = "123456"

# Database Operations
def load_db():
    if not os.path.exists(DB_FILE):
        default_db = {"users": {}, "pending_requests": [], "support_tickets": [], "history": {}}
        with open(DB_FILE, "w") as f: json.dump(default_db, f, indent=4)
        return default_db
    try:
        with open(DB_FILE, "r") as f: return json.load(f)
    except Exception:
        return {"users": {}, "pending_requests": [], "support_tickets": [], "history": {}}

def save_db(data):
    with open(DB_FILE, "w") as f:
        json.dump(data, f, indent=4)

if "logged_in" not in st.session_state: st.session_state.logged_in = False
if "user_email" not in st.session_state: st.session_state.user_email = ""
if "is_admin" not in st.session_state: st.session_state.is_admin = False

# Custom CSS Styling
st.markdown("""
    <style>
    #MainMenu, header, footer {visibility: hidden;}
    .stApp { background-color: #0b0c10; color: #FFFFFF; }
    .main-header {
        text-align: left; font-weight: 900; font-size: 2.2rem;
        background: linear-gradient(45deg, #FFD700, #FF69B4);
        -webkit-background-clip: text; -webkit-text-fill-color: transparent;
    }
    .tg-support-btn {
        float: right; background: linear-gradient(90deg, #0088cc, #00c6ff);
        color: white !important; padding: 8px 16px; border-radius: 20px;
        text-decoration: none; font-weight: bold;
    }
    </style>
""", unsafe_allow_html=True)

# Custom Manual Zoom Helper
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

# 15 Unique Cut Effects Logic
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

# Core Processing Function
def process_single_video(input_path, output_path, target_height, bitrate, progress_bar):
    progress_bar.progress(10, text="🎬 Video load ho raha hai...")
    video = VideoFileClip(input_path)
    cut_duration = video.duration / 15.0
    clips = []

    for edit_idx in range(1, 16):
        pct = 10 + int((edit_idx / 15.0) * 60)
        progress_bar.progress(pct, text=f"⚡ Sequence Effect #{edit_idx}/15 apply ho raha hai...")
        subclip = video.subclip((edit_idx - 1) * cut_duration, edit_idx * cut_duration)
        clips.append(apply_custom_effects(subclip, edit_idx))

    final_clip = concatenate_videoclips(clips)

    if video.size[1] != target_height:
        progress_bar.progress(75, text="📐 Resizing Output...")
        new_w = int(target_height * (video.size[0] / float(video.size[1])))
        if new_w % 2 != 0: new_w += 1
        final_clip = final_clip.resize(newsize=(new_w, target_height))

    progress_bar.progress(85, text="⚙️ Video Render ho raha hai...")
    final_clip.write_videofile(output_path, codec="libx264", audio_codec="aac", bitrate=bitrate, preset="ultrafast", threads=4, logger=None)
    progress_bar.progress(100, text="✅ Video Complete!")

# App UI Header
col_title, col_support = st.columns([3, 1])
with col_title: st.markdown("<h1 class='main-header'>🎬 NO COPYRIGHT VIDEO STUDIO PRO</h1>", unsafe_allow_html=True)
with col_support: st.markdown(f'<a href="{TELEGRAM_SUPPORT_URL}" target="_blank" class="tg-support-btn">✈️ Telegram Support</a>', unsafe_allow_html=True)

st.divider()

# Authentication System
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
    
    col_metric, col_logout = st.columns([3, 1])
    with col_metric: st.metric("Available Coins", f"🪙 {user_coins}")
    with col_logout:
        if st.button("🚪 Logout"):
            st.session_state.logged_in = False
            st.rerun()

    # Dynamic Tabs Allocation
    tab_list = ["📹 Studio Processor", "🪙 Buy Coins (Scan QR)", "💬 Chat with Admin", "📜 Download History"]
    if st.session_state.is_admin:
        tab_list.append("👑 Admin Panel")
    
    tabs = st.tabs(tab_list)

    # 1. STUDIO PROCESSOR TAB
    with tabs[0]:
        uploaded_file = st.file_uploader("Upload Video File", type=["mp4", "mov", "mkv", "avi"])
        if uploaded_file:
            quality_option = st.radio("Select Quality:", ["720p HD", "1080p Full HD", "4K Ultra HD"])
            res_map = {"720p HD": (720, "4000k"), "1080p Full HD": (1080, "12000k"), "4K Ultra HD": (2160, "45000k")}
            target_height, bitrate = res_map[quality_option]

            if st.button("🚀 Render Video"):
                if user_coins <= 0 and not st.session_state.is_admin:
                    st.error("❌ Coins khatam ho gaye hain! Kripya extra coins buy karein.")
                else:
                    if not os.path.exists("exports"): os.makedirs("exports")
                    p_bar = st.progress(0, text="Starting...")
                    temp_in = "temp_input.mp4"
                    out_path = f"exports/{int(time.time())}_{uploaded_file.name}"
                    with open(temp_in, "wb") as f: f.write(uploaded_file.read())
                    
                    process_single_video(temp_in, out_path, target_height, bitrate, p_bar)
                    
                    if not st.session_state.is_admin:
                        db_data["users"][current_user] = user_coins - 1
                    
                    if current_user not in db_data["history"]: db_data["history"][current_user] = []
                    db_data["history"][current_user].append({"filename": uploaded_file.name, "path": out_path, "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S")})
                    save_db(db_data)

                    st.success("🎉 Video Render Ho Gaya Hai!")
                    
                    # Direct Download Only (No Player Overhead)
                    with open(out_path, "rb") as f:
                        st.download_button("📥 Direct Download Video", f, file_name=f"edited_{uploaded_file.name}", mime="video/mp4", use_container_width=True)

    # 2. BUY COINS TAB
    with tabs[1]:
        st.subheader("🪙 Buy Extra Coins (Scan UPI QR)")
        col_qr, col_info = st.columns([1, 2])
        with col_qr:
            if os.path.exists(UPI_QR_IMAGE_PATH):
                st.image(UPI_QR_IMAGE_PATH, caption="Scan QR Code to Pay", width=220)
            else:
                st.info("📌 **UPI Payment Details:**")
                st.code(UPI_ID_TEXT, language="text")
        with col_info:
            st.markdown("**Coin Rate Plans:**\n* 🪙 50 Coins = ₹100\n* 🪙 120 Coins = ₹200\n* 🪙 300 Coins = ₹500")
            st.divider()
            with st.form("buy_coins_form"):
                utr_no = st.text_input("Enter UTR / Transaction Ref No.")
                requested_coins = st.number_input("Select Coins Amount", min_value=10, step=10, value=50)
                if st.form_submit_button("📩 Submit Payment Request"):
                    if utr_no.strip():
                        if "pending_requests" not in db_data: db_data["pending_requests"] = []
                        db_data["pending_requests"].append({
                            "email": current_user,
                            "utr": utr_no.strip(),
                            "coins": int(requested_coins),
                            "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        })
                        save_db(db_data)
                        st.success("✅ Payment Request Submit ho gayi hai! Admin verify karke coins add kar dega.")
                    else:
                        st.error("⚠️ UTR Number enter karna zaroori hai.")

    # 3. CHAT WITH ADMIN TAB
    with tabs[2]:
        st.subheader("💬 Support & Direct Chat with Admin")
        st.write("Apni query ya issue niche likhein. Admin panel se aapko reply mil jayega.")
        
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
        st.write("📜 **Your Messages & Responses:**")
        all_tickets = db_data.get("support_tickets", [])
        my_tickets = [t for t in all_tickets if t.get("user") == current_user]
        
        if not my_tickets:
            st.info("Aapka koi message nahi hai.")
        else:
            for t in reversed(my_tickets):
                st.write(f"💬 **You ({t['date']}):** {t['msg']}")
                if t.get("reply"):
                    st.success(f"👑 **Admin Reply:** {t['reply']}")
                else:
                    st.warning("⏳ Admin reply ka wait karein...")
                st.divider()

    # 4. DOWNLOAD HISTORY TAB
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
            st.divider()

    # 5. ADMIN MANAGEMENT PANEL
    if st.session_state.is_admin:
        with tabs[4]:
            st.subheader("👑 Admin Management Console")
            
            # Pending Recharge Requests
            st.write("### 🪙 Pending Coin Recharge Requests")
            pending_reqs = db_data.get("pending_requests", [])
            if not pending_reqs:
                st.info("Koi pending payment request nahi hai.")
            else:
                for idx, req in enumerate(pending_reqs):
                    st.write(f"👤 **{req['email']}** | Coins: **{req['coins']}** | UTR: `{req['utr']}` ({req['date']})")
                    col_app, col_rej = st.columns(2)
                    if col_app.button("✅ Approve", key=f"app_{idx}"):
                        db_data["users"][req['email']] = db_data["users"].get(req['email'], 0) + req['coins']
                        db_data["pending_requests"].pop(idx)
                        save_db(db_data)
                        st.success(f"Approved {req['coins']} coins for {req['email']}")
                        st.rerun()
                    if col_rej.button("❌ Reject", key=f"rej_{idx}"):
                        db_data["pending_requests"].pop(idx)
                        save_db(db_data)
                        st.warning("Request rejected!")
                        st.rerun()
                    st.divider()

            # Chat Tickets Support
            st.write("### 💬 User Support Tickets")
            all_tickets = db_data.get("support_tickets", [])
            unreplied = [t for t in all_tickets if not t.get("reply")]
            
            if not unreplied:
                st.info("Koi naya message nahi hai.")
            else:
                for t in unreplied:
                    st.write(f"👤 **{t['user']}** ({t['date']}): {t['msg']}")
                    reply_text = st.text_input("Write Reply:", key=f"reply_in_{t['id']}")
                    if st.button("Send Reply", key=f"btn_rep_{t['id']}"):
                        if reply_text.strip():
                            t["reply"] = reply_text.strip()
                            save_db(db_data)
                            st.success("Reply bhej diya gaya!")
                            st.rerun()
                    st.divider()
