import streamlit as st
import time
import json
import os
import hashlib
import numpy as np

# Safe Imports for MoviePy (Supports both v1.x and v2.x)
try:
    from moviepy.editor import VideoFileClip, concatenate_videoclips
    import moviepy.video.fx.all as vfx
except ImportError:
    from moviepy import VideoFileClip, concatenate_videoclips
    import moviepy.video.fx as vfx

# -----------------------------------------------------------------------------
# 1. PAGE CONFIG & CUSTOM THEME
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="No Copyright Video Studio - Dynamic Sequences", 
    page_icon="🎬", 
    layout="centered"
)

# Encryption Helper Function (SHA-256)
def hash_text(text):
    return hashlib.sha256(text.encode()).hexdigest()

# Admin Credentials (Encrypted)
ADMIN_EMAIL_HASH = hash_text("krish9agupt@gmail.com")
ADMIN_PASSCODE_HASH = hash_text("Krish9A")

USER_PASSCODE = "123456"
UPI_ID = "cinepoliis@ibl"
DB_FILE = "database.json"

# Permanent Database Setup
def load_db():
    if not os.path.exists(DB_FILE):
        default_db = {"users": {}, "pending_requests": [], "support_tickets": []}
        with open(DB_FILE, "w") as f:
            json.dump(default_db, f)
        return default_db
    try:
        with open(DB_FILE, "r") as f:
            data = json.load(f)
            if "support_tickets" not in data:
                data["support_tickets"] = []
            return data
    except:
        return {"users": {}, "pending_requests": [], "support_tickets": []}

def save_db(db):
    with open(DB_FILE, "w") as f:
        json.dump(db, f, indent=4)

db = load_db()

st.markdown("""
    <style>
    .stApp {
        background-color: #0B0C10;
        color: #FFFFFF;
    }
    [data-testid="stSidebar"] {
        display: none;
    }
    .main-header {
        text-align: center;
        font-weight: 900;
        background: linear-gradient(45deg, #FFD700, #FF69B4);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 0.2rem;
    }
    .sub-header {
        text-align: center;
        color: #E0E0E0;
        font-size: 0.95rem;
        margin-bottom: 2rem;
    }
    .plan-card {
        background: #121212;
        border: 2px solid #FFD700;
        border-radius: 15px;
        padding: 1.2rem;
        text-align: center;
        margin-bottom: 1rem;
        box-shadow: 0px 4px 15px rgba(255, 215, 0, 0.15);
    }
    .plan-card h3 {
        color: #FF69B4 !important;
        margin-bottom: 0.5rem;
    }
    .plan-card h2 {
        color: #FFD700 !important;
    }
    .plan-card p {
        color: #FFFFFF !important;
        font-weight: bold;
    }
    .stButton>button {
        width: 100%;
        border-radius: 10px;
        height: 3em;
        background: linear-gradient(90deg, #FFD700, #FF69B4);
        color: #000000;
        font-weight: bold;
        border: none;
    }
    .stButton>button:hover {
        opacity: 0.9;
        color: #FFFFFF;
    }
    </style>
""", unsafe_allow_html=True)

# Session States
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

if "user_email" not in st.session_state:
    st.session_state.user_email = ""

if "is_admin" not in st.session_state:
    st.session_state.is_admin = False

if "selected_plan" not in st.session_state:
    st.session_state.selected_plan = None

# -----------------------------------------------------------------------------
# MOVIEPY VIDEO & AUDIO TRANSFORMATION FUNCTIONS
# -----------------------------------------------------------------------------
def manual_zoom(clip, zoom_factor):
    def zoom_frame(image):
        h, w, c = image.shape
        crop_h, crop_w = int(h / zoom_factor), int(w / zoom_factor)
        top = (h - crop_h) // 2
        left = (w - crop_w) // 2
        cropped = image[top:top+crop_h, left:left+crop_w]
        row_indices = (np.linspace(0, crop_h - 1, h)).astype(int)
        col_indices = (np.linspace(0, crop_w - 1, w)).astype(int)
        return cropped[row_indices[:, None], col_indices]
    return clip.fl_image(zoom_frame)

def apply_custom_effects(clip, edit_num):
    # Visual Effects
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

    # Audio Delay Sync Pattern Logic
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

# -----------------------------------------------------------------------------
# 2. HEADER
# -----------------------------------------------------------------------------
st.markdown("<h1 class='main-header'>🎬 NO COPYRIGHT VIDEO STUDIO</h1>", unsafe_allow_html=True)
st.markdown("<p class='sub-header'>AI Dynamic 15-Edit Sequence Engine</p>", unsafe_allow_html=True)

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
# 3. DEVICE LOGIN
# -----------------------------------------------------------------------------
if not st.session_state.logged_in:
    st.subheader("🔑 Access Dashboard")
    st.info(f"💡 Default User Passcode: **{USER_PASSCODE}**")
    
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
                time.sleep(1)
                st.rerun()
            elif clean_email and passcode == USER_PASSCODE:
                if clean_email not in db["users"]:
                    db["users"][clean_email] = 20
                    save_db(db)
                
                st.session_state.logged_in = True
                st.session_state.user_email = clean_email
                st.session_state.is_admin = False
                st.success("Access Granted!")
                time.sleep(1)
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
    user_coins = db["users"].get(current_user, 20)

    metric_col1, metric_col2, metric_col3 = st.columns(3)
    metric_col1.metric("Available Coins", f"🪙 {user_coins}")
    metric_col2.metric("Account Status", "PRO Active")
    metric_col3.metric("Upload Limit", "200 MB")

    st.divider()

    if st.session_state.is_admin:
        tab1, tab2, tab3, tab4 = st.tabs(["📹 Sequence Studio", "🪙 Scan & Buy Coins", "💬 Help & Support", "⚙️ Admin Control"])
    else:
        tab1, tab2, tab3 = st.tabs(["📹 Sequence Studio", "🪙 Scan & Buy Coins", "💬 Help & Support"])

    with tab1:
        st.header("📤 Auto-Looping 15-Edit Sequence Processor")
        st.caption("Pricing: Below 50 MB = 🪙 5 Coins | Above 50 MB = 🪙 10 Coins")
        
        uploaded_file = st.file_uploader("Choose video file", type=["mp4", "mov", "mkv", "avi"])

        if uploaded_file is not None:
            file_size_mb = uploaded_file.size / (1024 * 1024)
            required_coins = 5 if file_size_mb < 50 else 10
            
            upload_bar = st.progress(0, text="📤 वीडियो फाइल अपलोड हो रही है...")
            input_path = "temp_input.mp4"
            output_path = "output_edited.mp4"
            
            bytes_data = uploaded_file.read()
            with open(input_path, "wb") as f:
                f.write(bytes_data)
            
            upload_bar.progress(100, text="✅ अपलोड पूर्ण हुआ!")

            st.info(f"📁 **File Size:** {file_size_mb:.2f} MB | **Processing Cost:** 🪙 {required_coins} Coins")
            st.video(uploaded_file)
            
            st.divider()
            st.subheader("⏱️ Video Length & Looping Parameters")
            
            total_duration_sec = st.number_input("Total Video Length (in seconds)", min_value=10, max_value=3600, value=60, step=10)
            
            loops_required = (total_duration_sec // 30) + (1 if total_duration_sec % 30 != 0 else 0)
            total_edits = (loops_required * 15)
            
            st.success(f"🔁 Video will undergo **{loops_required} Sequence Loop(s)** across **{total_edits} total edits** ({total_duration_sec} Seconds total processing).")

            st.write("")
            if st.button(f"🚀 Apply 15-Edit Dynamic Loops (Deduct 🪙 {required_coins} Coins)", type="primary"):
                if user_coins >= required_coins:
                    db["users"][current_user] -= required_coins
                    save_db(db)
                    
                    process_bar = st.progress(0, text="🎬 MoviePy 15-Sequence FX और Audio Delay अप्लाई हो रहा है...")
                    status_box = st.empty()

                    try:
                        video = VideoFileClip(input_path)
                        actual_vid_duration = video.duration
                        target_duration = float(total_duration_sec)
                        
                        pattern_duration = 30.0
                        clips = []
                        current_time = 0.0

                        total_expected_cuts = total_edits
                        completed_cuts = 0

                        while current_time < target_duration:
                            for edit_idx in range(1, 16):
                                start = (edit_idx - 1) * 2.0
                                end = edit_idx * 2.0
                                
                                seg_start = (current_time + start) % actual_vid_duration
                                seg_end = seg_start + (end - start)
                                
                                if seg_end > actual_vid_duration:
                                    subclip = video.subclip(seg_start, actual_vid_duration)
                                else:
                                    subclip = video.subclip(seg_start, seg_end)

                                edited_subclip = apply_custom_effects(subclip, edit_idx)
                                clips.append(edited_subclip)

                                completed_cuts += 1
                                prog_percentage = min(int((completed_cuts / total_expected_cuts) * 90), 90)
                                process_bar.progress(prog_percentage, text=f"⚡ एडिट स्टेप {completed_cuts}/{total_expected_cuts} प्रोसेस हो रहा है...")

                            current_time += pattern_duration

                        status_box.info("⚙️ फाइनल वीडियो और ऑडियो ट्रैक को रेंडर किया जा रहा है...")
                        final_clip = concatenate_videoclips(clips)
                        final_clip.write_videofile(output_path, codec="libx264", audio_codec="aac", logger=None)
                        
                        process_bar.progress(100, text="✅ वीडियो एडिटिंग पूर्ण हुई!")
                        status_box.empty()
                        st.balloons()

                        st.divider()
                        st.subheader("📥 तैयार वीडियो डाउनलोड करें")
                        download_bar = st.progress(0, text="💾 फाइल तैयार की जा रही है...")
                        
                        with open(output_path, "rb") as file:
                            download_bar.progress(100, text="✅ फाइल डाउनलोड के लिए उपलब्ध है!")
                            st.download_button(
                                label=f"📥 Download Processed Video ({total_duration_sec}s)",
                                data=file,
                                file_name=f"sequence_edited_{total_duration_sec}s.mp4",
                                mime="video/mp4",
                                type="primary"
                            )

                    except Exception as e:
                        st.error(f"❌ वीडियो प्रोसेसिंग एरर: {str(e)}")
                else:
                    st.error(f"❌ Insufficient Coins! You need 🪙 {required_coins} Coins.")

    # --- TAB 2: SCAN & BUY COINS ---
    with tab2:
        st.header("⚡ Request Coins Recharge")
        st.write("Select a package, scan QR code, and submit UTR for admin verification.")

        plan_col1, plan_col2 = st.columns(2)
        plan_col3, plan_col4 = st.columns(2)

        with plan_col1:
            st.markdown("<div class='plan-card'><h3>Starter</h3><h2>₹49</h2><p>🪙 50 Coins</p></div>", unsafe_allow_html=True)
            if st.button("Buy ₹49 Plan", key="p1"):
                st.session_state.selected_plan = ("Starter", 49, 50)

        with plan_col2:
            st.markdown("<div class='plan-card'><h3>Popular</h3><h2>₹99</h2><p>🪙 110 Coins</p></div>", unsafe_allow_html=True)
            if st.button("Buy ₹99 Plan", key="p2"):
                st.session_state.selected_plan = ("Popular", 99, 110)

        with plan_col3:
            st.markdown("<div class='plan-card'><h3>Value</h3><h2>₹199</h2><p>🪙 221 Coins</p></div>", unsafe_allow_html=True)
            if st.button("Buy ₹199 Plan", key="p3"):
                st.session_state.selected_plan = ("Value", 199, 221)

        with plan_col4:
            st.markdown("<div class='plan-card'><h3>Mega Pro</h3><h2>₹399</h2><p>🪙 500 Coins</p></div>", unsafe_allow_html=True)
            if st.button("Buy ₹399 Plan", key="p4"):
                st.session_state.selected_plan = ("Mega Pro", 399, 500)

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
                        db["pending_requests"].append({
                            "user": current_user,
                            "utr": utr_number,
                            "amount": amount,
                            "coins": coins_to_add
                        })
                        save_db(db)
                        st.info("⏳ UTR submitted! Coins will be added after Admin verifies payment.")
                        st.session_state.selected_plan = None
                    else:
                        st.error("Please enter a valid 12-digit numeric UTR Number.")

    # --- TAB 3: HELP & SUPPORT ---
    with tab3:
        st.header("💬 Help & Support")
        with st.form("support_form"):
            user_msg = st.text_area("Your Message / Query", placeholder="Describe your problem or question here...")
            sub_ticket = st.form_submit_button("📩 Send Message")
            if sub_ticket and user_msg:
                db["support_tickets"].append({
                    "user": current_user,
                    "message": user_msg,
                    "reply": "No reply yet from Admin.",
                    "status": "Pending"
                })
                save_db(db)
                st.success("Message sent to Admin successfully!")

        st.divider()
        st.subheader("📋 Your Past Tickets")
        my_tickets = [t for t in db["support_tickets"] if t["user"] == current_user]
        
        if not my_tickets:
            st.write("No previous support messages.")
        else:
            for t in reversed(my_tickets):
                st.markdown(f"**Query:** {t['message']}")
                st.markdown(f"**Admin Reply:** {t['reply']}")
                st.caption(f"Status: `{t['status']}`")
                st.divider()

    # --- TAB 4: ADMIN CONTROL PANEL ---
    if st.session_state.is_admin:
        with tab4:
            st.header("⚙️ Admin Dashboard & Control")
            
            st.subheader("💳 Pending Payment Approvals")
            pending_list = db.get("pending_requests", [])

            if len(pending_list) == 0:
                st.write("No pending payment requests.")
            else:
                for idx, req in enumerate(list(pending_list)):
                    st.warning(f"**User:** {req['user']} | **Amount:** ₹{req['amount']} | **UTR:** `{req['utr']}` | **Coins:** 🪙 {req['coins']}")
                    col_a, col_b = st.columns(2)
                    with col_a:
                        if st.button(f"✅ Approve ({req['coins']} Coins)", key=f"app_{idx}"):
                            req_user = req["user"]
                            db["users"][req_user] = db["users"].get(req_user, 0) + req["coins"]
                            db["pending_requests"].pop(idx)
                            save_db(db)
                            st.success(f"Approved coins for {req_user}")
                            time.sleep(1)
                            st.rerun()
                    with col_b:
                        if st.button("❌ Reject", key=f"rej_{idx}"):
                            db["pending_requests"].pop(idx)
                            save_db(db)
                            st.error("Rejected.")
                            time.sleep(1)
                            st.rerun()

            st.divider()

            st.subheader("💬 User Support Requests")
            tickets = db.get("support_tickets", [])
            
            if len(tickets) == 0:
                st.write("No support tickets found.")
            else:
                for idx, t in enumerate(list(tickets)):
                    st.info(f"**From:** {t['user']} | **Query:** {t['message']}")
                    reply_text = st.text_input("Reply to User", value="" if t["reply"] == "No reply yet from Admin." else t["reply"], key=f"rep_{idx}")
                    if st.button("Reply & Mark Resolved", key=f"btn_rep_{idx}"):
                        db["support_tickets"][idx]["reply"] = reply_text
                        db["support_tickets"][idx]["status"] = "Resolved"
                        save_db(db)
                        st.success("Reply sent successfully!")
                        time.sleep(1)
                        st.rerun()
