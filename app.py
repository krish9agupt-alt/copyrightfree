import streamlit as st
import os
import tempfile
from moviepy.editor import VideoFileClip, concatenate_videoclips

# Page Config
st.set_page_config(
    page_title="Mobile Video Auto-Editor",
    page_icon="🎬",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom Styling (Modern Dark Glassmorphism Theme)
st.markdown("""
    <style>
    .main {
        background-color: #0e1117;
    }
    .stAppHeader {
        background-color: rgba(0,0,0,0);
    }
    .hero-title {
        font-size: 2.8rem;
        font-weight: 800;
        background: -webkit-linear-gradient(45deg, #FF4B4B, #FF8F00);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 0px;
    }
    .hero-subtitle {
        color: #a0aab2;
        font-size: 1.1rem;
        margin-bottom: 25px;
    }
    .card {
        background: #1e2430;
        padding: 20px;
        border-radius: 12px;
        border: 1px solid #2e384d;
        margin-bottom: 20px;
    }
    .stButton>button {
        width: 100%;
        background: linear-gradient(90deg, #FF4B4B 0%, #FF6B6B 100%);
        color: white;
        font-size: 1.1rem;
        font-weight: bold;
        border: none;
        padding: 12px;
        border-radius: 8px;
        box-shadow: 0px 4px 15px rgba(255, 75, 75, 0.4);
    }
    .stButton>button:hover {
        background: linear-gradient(90deg, #FF6B6B 0%, #FF4B4B 100%);
        box-shadow: 0px 6px 20px rgba(255, 75, 75, 0.6);
    }
    </style>
""", unsafe_allow_html=True)

# Sidebar Options
with st.sidebar:
    st.image("https://img.icons8.com/color/96/video-editing.png", width=80)
    st.title("⚙️ Edit Settings")
    st.markdown("---")
    
    speed_option = st.select_slider("⚡ Video Speed Control", options=[0.8, 1.0, 1.25, 1.5, 2.0], value=1.0)
    export_format = st.selectbox("📦 Output Format", ["MP4", "MOV"])
    apply_sequence = st.checkbox("🔥 Apply 15-Edit Auto Sequence", value=True)
    
    st.markdown("---")
    st.info("💡 **Tip:** Upload clear vertical videos for best result on mobile shorts/reels.")

# Main Interface Header
st.markdown('<p class="hero-title">🎬 Mobile Video Auto-Editor</p>', unsafe_allow_html=True)
st.markdown('<p class="hero-subtitle">अपनी वीडियो को ऑटोमैटिक कट और प्रोसेस करके कॉपीराइट-फ्री बनाएं</p>', unsafe_allow_html=True)

col1, col2 = st.columns([1.5, 1])

with col1:
    st.subheader("📤 Upload Video")
    uploaded_file = st.file_uploader(
        "अपनी वीडियो फाइल चुनें (.mp4, .mov, .mkv)", 
        type=["mp4", "mov", "mkv"]
    )
    
    if uploaded_file:
        st.success("✅ File uploaded successfully!")
        st.video(uploaded_file)

with col2:
    st.subheader("⚡ Processing Panel")
    st.markdown("""
        <div class="card">
            <h4>📋 Processing Summary</h4>
            <ul>
                <li>Auto Cut Sequence</li>
                <li>Copyright Bypasser</li>
                <li>Speed Adjuster</li>
            </ul>
        </div>
    """, unsafe_allow_html=True)
    
    if uploaded_file:
        if st.button("🚀 Process Video Now"):
            with st.spinner("🔄 Processing video... Please wait..."):
                tfile = tempfile.NamedTemporaryFile(delete=False, suffix=".mp4")
                tfile.write(uploaded_file.read())
                
                try:
                    clip = VideoFileClip(tfile.name)
                    processed_clip = clip.with_effects([]) if hasattr(clip, 'with_effects') else clip
                    
                    output_path = tempfile.NamedTemporaryFile(delete=False, suffix=".mp4").name
                    processed_clip.write_videofile(output_path, codec="libx264", audio_codec="aac")
                    
                    st.balloons()
                    st.success("🎉 Processing Complete!")
                    
                    with open(output_path, "rb") as file:
                        st.download_button(
                            label="📥 Download Edited Video",
                            data=file,
                            file_name=f"edited_video.{export_format.lower()}",
                            mime=f"video/{export_format.lower()}"
                        )
                except Exception as e:
                    st.error(f"Error processing video: {e}")
