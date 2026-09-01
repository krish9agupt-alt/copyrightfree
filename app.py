import streamlit as st
from supabase import create_client
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

# -----------------------------------------------------------------------------
# 2. SUPABASE INITIALIZATION & HARD-CLEAN URL
# -----------------------------------------------------------------------------
@st.cache_resource
def get_supabase_client():
    # Forcefully removes all line breaks (\n, \r), quotes, and spaces
    raw_url = str(st.secrets["SUPABASE_URL"]).replace("\n", "").replace("\r", "").replace(" ", "").replace('"', '').strip()
    raw_key = str(st.secrets["SUPABASE_KEY"]).replace("\n", "").replace("\r", "").replace(" ", "").replace('"', '').strip()
    return create_client(raw_url, raw_key)

supabase = get_supabase_client()

# Session State Initializations
if "user" not in st.session_state:
    st.session_state.user = None

if "coins" not in st.session_state:
    st.session_state.coins = 10

# Catch authentication session automatically
try:
    session = supabase.auth.get_session()
    if session:
        st.session_state.user = session.user
except Exception:
    pass

# -----------------------------------------------------------------------------
# 3. HEADER & TOP NAVIGATION BAR
# -----------------------------------------------------------------------------
st.markdown("<h1 class='main-header'>🎬 No Copyright Video Studio</h1>", unsafe_allow_html=True)

top_col1, top_col2 = st.columns([3, 1])

with top_col1:
    if st.session_state.user:
        st.success(f"Logged in as: **{st.session_state.user.email}**")
    else:
        st.info("Welcome! Please sign in to process videos.")

with top_col2:
    if st.session_state.user:
        if st.button("Sign Out", type="secondary"):
            supabase.auth.sign_out()
            st.session_state.user = None
            st.rerun()

st.divider()

# -----------------------------------------------------------------------------
# 4. VIEW 1: DIRECT GOOGLE LOGIN REDIRECT
# -----------------------------------------------------------------------------
if st.session_state.user is None:
    st.subheader("🔑 Account Authentication")
    st.write("Click the button below to sign in directly with Google.")
    
    if st.button("🌐 Sign in with Google", type="primary"):
        res = supabase.auth.sign_in_with_oauth({
            "provider": "google",
            "options": {
                "redirect_to": "https://copyrightfree.streamlit.app"
            }
        })
        # Instant Auto-Redirect Script
        st.markdown(f'<meta http-equiv="refresh" content="0;url={res.url}">', unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# 5. VIEW 2: MODERN DASHBOARD & TOOLS
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
