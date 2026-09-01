import streamlit as st
import time

# -----------------------------------------------------------------------------
# 1. PAGE CONFIGURATION & DARK PREMIUM STYLING
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="No Copyright Video Studio - Premium", 
    page_icon="🎬", 
    layout="centered"
)

# Custom CSS for Premium Black/Dark Theme
st.markdown("""
    <style>
    /* Dark Theme Background */
    .stApp {
        background-color: #0E1117;
        color: #FFFFFF;
    }
    /* Hide Streamlit default sidebar completely */
    [data-testid="stSidebar"] {
        display: none;
    }
    .main-header {
        text-align: center;
        font-weight: 800;
        color: #00E676;
        margin-bottom: 0.5rem;
    }
    .sub-header {
        text-align: center;
        color: #888888;
        font-size: 0.95rem;
        margin-bottom: 2rem;
    }
    /* Premium Cards */
    .plan-card {
        background: #1A1D24;
        border: 1px solid #2B2F3A;
        border-radius: 12px;
        padding: 1.5rem;
        text-align: center;
        margin-bottom: 1rem;
    }
    .stButton>button {
        width: 100%;
        border-radius: 8px;
        height: 3em;
        background-color: #00E676;
        color: #000000;
        font-weight: bold;
        border: none;
    }
    .stButton>button:hover {
        background-color: #00B359;
        color: #FFFFFF;
    }
    </style>
""", unsafe_allow_html=True)

# Session State Initializations
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

if "user_email" not in st.session_state:
    st.session_state.user_email = ""

if "balance" not in st.session_state:
    st.session_state.balance = 10  # ₹10 Initial Balance

if "selected_plan" not in st.session_state:
    st.session_state.selected_plan = None

# -----------------------------------------------------------------------------
# 2. HEADER & NAVIGATION
# -----------------------------------------------------------------------------
st.markdown("<h1 class='main-header'>🎬 NO COPYRIGHT VIDEO STUDIO</h1>", unsafe_allow_html=True)
st.markdown("<p class='sub-header'>AI-Powered Video Protection & Editing Dashboard</p>", unsafe_allow_html=True)

top_col1, top_col2 = st.columns([3, 1])

with top_col1:
    if st.session_state.logged_in:
        st.success(f"Logged in as: **{st.session_state.user_email}**")
    else:
        st.info("Welcome! Sign in to access your studio.")

with top_col2:
    if st.session_state.logged_in:
        if st.button("Sign Out", type="secondary"):
            st.session_state.logged_in = False
            st.session_state.user_email = ""
            st.rerun()

st.divider()

# -----------------------------------------------------------------------------
# 3. VIEW 1: DEVICE LOGIN
# -----------------------------------------------------------------------------
if not st.session_state.logged_in:
    st.subheader("🔑 Premium Access Login")
    
    with st.form("login_form"):
        email = st.text_input("Email Address", placeholder="user@example.com")
        passcode = st.text_input("Access Passcode", type="password", placeholder="Enter passcode (123456)")
        submit_button = st.form_submit_button("🚀 Enter Studio Dashboard", type="primary")

        if submit_button:
            if email and passcode == "123456":
                st.session_state.logged_in = True
                st.session_state.user_email = email
                st.success("Access Granted! Opening Dashboard...")
                time.sleep(1)
                st.rerun()
            elif not email:
                st.error("Please enter a valid email address.")
            else:
                st.error("Invalid passcode! Enter '123456'.")

# -----------------------------------------------------------------------------
# 4. VIEW 2: PREMIUM DASHBOARD & TOOLS
# -----------------------------------------------------------------------------
else:
    # Key Stats Dashboard Cards
    metric_col1, metric_col2, metric_col3 = st.columns(3)
    metric_col1.metric("Available Balance", f"₹ {st.session_state.balance}")
    metric_col2.metric("Account Status", "PRO Active")
    metric_col3.metric("Upload Limit", "200 MB")

    st.divider()

    # Create Tabs for Video Processing and Subscription Recharge
    tab1, tab2 = st.tabs(["📹 Video Studio", "💳 Recharge Balance / Subscription"])

    # --- TAB 1: VIDEO PROCESSING ---
    with tab1:
        st.header("📤 Upload & Process Video")
        st.caption("Supports MP4, MOV, AVI up to 200 MB")
        
        uploaded_file = st.file_uploader(
            "Choose a video file", 
            type=["mp4", "mov", "avi"]
        )

        if uploaded_file is not None:
            st.subheader("📹 Video Preview")
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
            if st.button("🚀 Start Processing (Cost: ₹2)", type="primary"):
                if st.session_state.balance >= 2:
                    st.session_state.balance -= 2
                    
                    progress_bar = st.progress(0)
                    status_text = st.empty()

                    for i in range(1, 101):
                        time.sleep(0.02)
                        progress_bar.progress(i)
                        status_text.text(f"Applying protection filters... {i}%")
                    
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
                    st.error("❌ Insufficient Balance! Please go to the 'Recharge Balance' tab to top up.")

    # --- TAB 2: SUBSCRIPTION & SCAN & PAY ---
    with tab2:
        st.header("⚡ Choose a Recharge Plan")
        st.write("Select a plan and scan the QR code to top up your balance.")

        plan_col1, plan_col2, plan_col3 = st.columns(3)

        with plan_col1:
            st.markdown("<div class='plan-card'><h3>Basic</h3><h2>₹199</h2><p>Balance: ₹199</p></div>", unsafe_allow_html=True)
            if st.button("Select Basic", key="p1"):
                st.session_state.selected_plan = ("Basic", 199, 199)

        with plan_col2:
            st.markdown("<div class='plan-card'><h3>Pro</h3><h2>₹499</h2><p>Balance: ₹500</p></div>", unsafe_allow_html=True)
            if st.button("Select Pro", key="p2"):
                st.session_state.selected_plan = ("Pro", 499, 500)

        with plan_col3:
            st.markdown("<div class='plan-card'><h3>Unlimited</h3><h2>₹999</h2><p>Balance: ₹1100</p></div>", unsafe_allow_html=True)
            if st.button("Select Unlimited", key="p3"):
                st.session_state.selected_plan = ("Unlimited", 999, 1100)

        st.divider()

        # Payment QR Code & Verification Section
        if st.session_state.selected_plan:
            plan_name, amount, balance_to_add = st.session_state.selected_plan
            st.subheader(f"📲 Complete Payment for {plan_name} Plan (₹{amount})")
            
            pay_col1, pay_col2 = st.columns([1, 1])

            with pay_col1:
                st.image(
                    f"https://api.qrserver.com/v1/create-qr-code/?size=200x200&data=upi://pay?pa=yourupiid@upi&pn=Studio&am={amount}",
                    caption="Scan with GPay, PhonePe, or Paytm"
                )

            with pay_col2:
                utr_number = st.text_input("Enter 12-Digit Transaction / UTR Number")
                if st.button("VERIFY & ADD BALANCE", type="primary"):
                    if len(utr_number) >= 8:
                        st.session_state.balance += balance_to_add
                        st.success(f"🎉 Payment Verified! ₹{balance_to_add} added to your account.")
                        st.session_state.selected_plan = None
                        time.sleep(1.5)
                        st.rerun()
                    else:
                        st.error("Please enter a valid Transaction/UTR Number.")
