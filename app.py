import streamlit as st
import time

# -----------------------------------------------------------------------------
# 1. PAGE CONFIGURATION
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="No Copyright Video Studio", 
    page_icon="🎬", 
    layout="centered"
)

# Custom CSS for Modern Clean Look
st.markdown("""
    <style>
    [data-testid="stSidebar"] {
        display: none;
    }
    .main-header {
        text-align: center;
        margin-bottom: 2rem;
    }
    .stButton>button {
        width: 100%;
        border-radius: 8px;
        height: 3em;
    }
    </style>
""", unsafe_allow_html=True)

# Session State Initializations
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

if "user_email" not in st.session_state:
    st.session_state.user_email = ""

if "coins" not in st.session_state:
    st.session_state.coins = 10

# -----------------------------------------------------------------------------
# 2. HEADER
# -----------------------------------------------------------------------------
st.markdown("<h1 class='main-header'>🎬 No Copyright Video Studio</h1>", unsafe_allow_html=True)

top_col1, top_col2 = st.columns([3, 1])

with top_col1:
    if st.session_state.logged_in:
        st.success(f"Logged in as: **{st.session_state.user_email}**")
    else:
        st.info("Welcome! Enter your details to access the studio.")

with top_col2:
    if st.session_state.logged_in:
        if st.button("Sign Out", type="secondary"):
            st.session_state.logged_in = False
            st.session_state.user_email = ""
            st.rerun()

st.divider()

# -----------------------------------------------------------------------------
# 3. DEVICE LOGIN FORM
# -----------------------------------------------------------------------------
if not st.session_state.logged_in:
    st.subheader("🔑 Access Studio Dashboard")
    
    with st.form("login_form"):
        email = st.text_input("Email Address", placeholder="user@example.com")
        passcode = st.text_input("Access Passcode", type="password", placeholder="Enter passcode (123456)")
        submit_button = st.form_submit_button("🚀 Enter Dashboard", type="primary")

        if submit_button:
            if email and passcode == "123456":
                st.session_state.logged_in = True
                st.session_state.user_email = email
                st.success("Login Successful! Loading dashboard...")
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
    # Key Stats Dashboard Cards
    metric_col1, metric_col2, metric_col3 = st.columns(3)
    metric_col1.metric("Available Coins", f"🪙 {st.session_state.coins}")
    metric_col2.metric("Account Status", "PRO Active")
    metric_col3.metric("Videos Processed", "0")

    st.divider()

    # Video Editor Section
    st.header("📤 Upload & Modify Video")
    
    uploaded_file = st.file_uploader(
        "Choose a video file (MP4, MOV, AVI)", 
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
        if st.button("🚀 Start Processing Video (Cost: 2 Coins)", type="primary"):
            if st.session_state.coins >= 2:
                st.session_state.coins -= 2
                
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
                st.error("❌ Insufficient Coins! Please recharge your balance to continue.")
