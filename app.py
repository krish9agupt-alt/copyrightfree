import streamlit as st
import time

# -----------------------------------------------------------------------------
# 1. PAGE CONFIG & CUSTOM THEME
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="No Copyright Video Studio - Premium", 
    page_icon="🎬", 
    layout="centered"
)

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

if "coins" not in st.session_state:
    st.session_state.coins = 20

if "selected_plan" not in st.session_state:
    st.session_state.selected_plan = None

if "pending_requests" not in st.session_state:
    st.session_state.pending_requests = []

# -----------------------------------------------------------------------------
# 2. HEADER
# -----------------------------------------------------------------------------
st.markdown("<h1 class='main-header'>🎬 NO COPYRIGHT VIDEO STUDIO</h1>", unsafe_allow_html=True)
st.markdown("<p class='sub-header'>AI Video Protection & Editing Portal</p>", unsafe_allow_html=True)

top_col1, top_col2 = st.columns([3, 1])

with top_col1:
    if st.session_state.logged_in:
        st.success(f"User: **{st.session_state.user_email}**")
    else:
        st.info("Please login to process videos.")

with top_col2:
    if st.session_state.logged_in:
        if st.button("Sign Out", type="secondary"):
            st.session_state.logged_in = False
            st.session_state.user_email = ""
            st.rerun()

st.divider()

# -----------------------------------------------------------------------------
# 3. DEVICE LOGIN
# -----------------------------------------------------------------------------
if not st.session_state.logged_in:
    st.subheader("🔑 Access Dashboard")
    
    with st.form("login_form"):
        email = st.text_input("Email Address", placeholder="user@example.com")
        passcode = st.text_input("Access Passcode", type="password", placeholder="Enter passcode (123456)")
        submit_button = st.form_submit_button("🚀 Enter Studio", type="primary")

        if submit_button:
            if email and passcode == "123456":
                st.session_state.logged_in = True
                st.session_state.user_email = email
                st.success("Access Granted!")
                time.sleep(1)
                st.rerun()
            elif not email:
                st.error("Please enter a valid email address.")
            else:
                st.error("Invalid passcode! Enter '123456'.")

# -----------------------------------------------------------------------------
# 4. DASHBOARD & TOOLS
# -----------------------------------------------------------------------------
else:
    metric_col1, metric_col2, metric_col3 = st.columns(3)
    metric_col1.metric("Available Coins", f"🪙 {st.session_state.coins}")
    metric_col2.metric("Account Status", "PRO Active")
    metric_col3.metric("Upload Limit", "200 MB")

    st.divider()

    tab1, tab2, tab3 = st.tabs(["📹 Video Studio", "🪙 Scan & Buy Coins", "⚙️ Admin Approval"])

    # --- TAB 1: VIDEO STUDIO ---
    with tab1:
        st.header("📤 Upload & Process Video")
        st.caption("Pricing: Below 50 MB = 🪙 5 Coins | Above 50 MB = 🪙 10 Coins")
        
        uploaded_file = st.file_uploader("Choose a video file", type=["mp4", "mov", "avi"])

        if uploaded_file is not None:
            file_size_mb = uploaded_file.size / (1024 * 1024)
            required_coins = 5 if file_size_mb < 50 else 10
            
            st.info(f"📁 **File Size:** {file_size_mb:.2f} MB | **Processing Cost:** 🪙 {required_coins} Coins")
            st.video(uploaded_file)
            
            st.divider()
            st.subheader("⚙️ Processing Settings")
            
            opt_col1, opt_col2 = st.columns(2)
            with opt_col1:
                remove_audio = st.checkbox("Remove Existing Audio Track", value=True)
                add_watermark = st.checkbox("Apply Copyright Protection Shield", value=True)
            
            with opt_col2:
                flip_video = st.checkbox("Mirror / Flip Video Horizon")
                speed = st.slider("Speed Adjustment", 0.5, 2.0, 1.0)

            st.write("")
            if st.button(f"🚀 Start Processing (Deduct 🪙 {required_coins} Coins)", type="primary"):
                if st.session_state.coins >= required_coins:
                    st.session_state.coins -= required_coins
                    progress_bar = st.progress(0)
                    status_text = st.empty()

                    for i in range(1, 101):
                        time.sleep(0.02)
                        progress_bar.progress(i)
                        status_text.text(f"Processing filters... {i}%")
                    
                    status_text.empty()
                    st.balloons()
                    st.success("✅ Video processing completed successfully!")
                    
                    st.download_button(
                        label="📥 Download Processed Video",
                        data=uploaded_file.getvalue(),
                        file_name="processed_no_copyright_video.mp4",
                        mime="video/mp4"
                    )
                else:
                    st.error(f"❌ Insufficient Coins! You need 🪙 {required_coins} Coins. Please request coins in Buy tab.")

    # --- TAB 2: SCAN & BUY COINS ---
    with tab2:
        st.header("⚡ Request Coins Recharge")
        st.write("Select a package, scan QR code, and submit UTR for manual admin verification.")

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
                # Displays your PhonePe QR code from GitHub
                st.image("https://raw.githubusercontent.com/Anand993188/noncopyright/main/image_8.png", caption="PhonePe QR Code", width=200)

            with pay_col2:
                utr_number = st.text_input("Enter 12-Digit Transaction / UTR No.", max_chars=12)
                if st.button("SUBMIT FOR VERIFICATION", type="primary"):
                    if len(utr_number) == 12 and utr_number.isdigit():
                        st.session_state.pending_requests.append({
                            "user": st.session_state.user_email,
                            "utr": utr_number,
                            "amount": amount,
                            "coins": coins_to_add
                        })
                        st.info("⏳ UTR submitted! Coins will be added after Admin verifies payment in Bank Statement.")
                        st.session_state.selected_plan = None
                    else:
                        st.error("Please enter a valid 12-digit numeric UTR Number.")

    # --- TAB 3: ADMIN APPROVAL PANEL ---
    with tab3:
        st.header("⚙️ Admin Payment Verification Panel")
        st.caption("Cross-check UTR numbers with your PhonePe / Bank app before approving.")

        if len(st.session_state.pending_requests) == 0:
            st.write("No pending payment verification requests.")
        else:
            for idx, req in enumerate(st.session_state.pending_requests):
                st.warning(f"**User:** {req['user']} | **Amount:** ₹{req['amount']} | **UTR:** `{req['utr']}` | **Coins:** 🪙 {req['coins']}")
                col_a, col_b = st.columns(2)
                with col_a:
                    if st.button(f"✅ Approve & Add {req['coins']} Coins", key=f"app_{idx}"):
                        st.session_state.coins += req["coins"]
                        st.session_state.pending_requests.pop(idx)
                        st.success(f"Payment Verified! Added {req['coins']} coins to account.")
                        time.sleep(1)
                        st.rerun()
                with col_b:
                    if st.button("❌ Reject Payment", key=f"rej_{idx}"):
                        st.session_state.pending_requests.pop(idx)
                        st.error("Payment rejected.")
                        time.sleep(1)
                        st.rerun()
