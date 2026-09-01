import streamlit as st
from supabase import create_client
import time

# -----------------------------------------------------------------------------
# 1. PAGE CONFIG & SUPABASE SETUP
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="No Copyright Video Editor", 
    page_icon="🎬", 
    layout="wide"
)

@st.cache_resource
def get_supabase_client():
    raw_url = str(st.secrets["SUPABASE_URL"]).strip()
    raw_key = str(st.secrets["SUPABASE_KEY"]).strip()
    return create_client(raw_url, raw_key)

supabase = get_supabase_client()

# Session state initializations
if "user" not in st.session_state:
    st.session_state.user = None

if "coins" not in st.session_state:
    st.session_state.coins = 10

# -----------------------------------------------------------------------------
# 2. APP TITLE & HEADER
# -----------------------------------------------------------------------------
st.title("🎬 No Copyright Video Studio")

# -----------------------------------------------------------------------------
# 3. SIDEBAR NAVIGATION & AUTHENTICATION
# -----------------------------------------------------------------------------
st.sidebar.header("🔐 Auth & Profile")

if st.session_state.user is None:
    # NON-LOGGED IN SIDEBAR
    st.sidebar.info("ऐप की सुविधाओं का उपयोग करने के लिए लॉगिन करें।")
    
    st.subheader("🔑 Sign In Required")
    st.write("Google खाते से साइन इन करने के लिए नीचे दिए गए बटन पर क्लिक करें:")
    
    if st.button("🌐 Sign in with Google", type="primary"):
        res = supabase.auth.sign_in_with_oauth({
            "provider": "google",
            "options": {
                "redirect_to": "https://copyrightfree.streamlit.app"
            }
        })
        st.success("लॉगिन पूरा करने के लिए नीचे दिए गए लिंक पर टैप करें:")
        st.markdown(f"[👉 **Click here to complete Google Login**]({res.url})")

else:
    # LOGGED IN SIDEBAR
    user_email = st.session_state.user.email
    st.sidebar.success(f"Logged in:\n**{user_email}**")
    st.sidebar.metric(label="🪙 Available Coins", value=st.session_state.coins)
    
    if st.sidebar.button("Logout", type="secondary"):
        supabase.auth.sign_out()
        st.session_state.user = None
        st.rerun()

# -----------------------------------------------------------------------------
# 4. MAIN DASHBOARD & WORKING APP (ONLY AFTER LOGIN)
# -----------------------------------------------------------------------------
if st.session_state.user is not None:
    st.divider()
    
    # Overview Metrics
    col1, col2, col3 = st.columns(3)
    col1.metric("Account Status", "Active Pro")
    col2.metric("Coins Left", st.session_state.coins)
    col3.metric("Processed Videos", "0")

    st.divider()

    # Video Editor Section
    st.header("📤 Upload & Process Video")
    
    uploaded_file = st.file_uploader(
        "अपनी वीडियो फ़ाइल चुनें (MP4, MOV)", 
        type=["mp4", "mov", "avi"]
    )

    if uploaded_file is not None:
        st.subheader("📹 Video Preview")
        st.video(uploaded_file)
        
        st.divider()
        st.subheader("⚙️ Processing Options")
        
        col_opt1, col_opt2 = st.columns(2)
        with col_opt1:
            remove_audio = st.checkbox("Remove Audio Track", value=True)
            add_watermark = st.checkbox("Apply Copyright Protection Shield", value=True)
        
        with col_opt2:
            flip_video = st.checkbox("Mirror/Flip Video")
            speed = st.slider("Speed adjustment", 0.5, 2.0, 1.0)

        # Action Button
        if st.button("🚀 Process Video (Cost: 2 Coins)", type="primary"):
            if st.session_state.coins >= 2:
                # Deduct coins
                st.session_state.coins -= 2
                
                # Progress simulation
                progress_bar = st.progress(0)
                status_text = st.empty()

                for i in range(1, 101):
                    time.sleep(0.03)
                    progress_bar.progress(i)
                    status_text.text(f"Processing Video... {i}%")
                
                status_text.empty()
                st.success("✅ वीडियो सफलतापूर्वक प्रोसेस हो गई है!")
                
                # Download Button Simulation
                st.download_button(
                    label="📥 Download Output Video",
                    data=uploaded_file.getvalue(),
                    file_name="processed_video.mp4",
                    mime="video/mp4"
                )
            else:
                st.error("❌ पर्याप्त सिक्के (Coins) नहीं हैं! कृपया कॉइन्स रीचार्ज करें।")

else:
    st.divider()
    st.info("💡 लॉगिन करने के बाद आपको वीडियो एडिटिंग डैशबोर्ड और प्रोसेसिंग टूल्स दिखाई देंगे।")
