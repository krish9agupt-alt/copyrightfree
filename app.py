import streamlit as st
import tempfile
import time
from moviepy.editor import VideoFileClip

# Page Config
st.set_page_config(
    page_title="Mobile Video Auto-Editor",
    page_icon="🎬",
    layout="wide"
)

# Initialize Session State (New users get 10 FREE Coins)
if "user_coins" not in st.session_state:
    st.session_state.user_coins = 10  # 🎁 New user signup bonus = 10 Coins

# Custom CSS Styling
st.markdown("""
    <style>
    .coin-badge {
        background: linear-gradient(135deg, #FFD700 0%, #FFA500 100%);
        color: #000;
        padding: 10px 18px;
        border-radius: 20px;
        font-weight: bold;
        font-size: 1.1rem;
        display: inline-block;
        margin-bottom: 12px;
        width: 100%;
        text-align: center;
    }
    .stButton>button {
        width: 100%;
        background: linear-gradient(90deg, #FF4B4B 0%, #FF6B6B 100%);
        color: white;
        font-weight: bold;
        border-radius: 8px;
        padding: 10px;
    }
    </style>
""", unsafe_allow_html=True)

# Sidebar - Wallet & Recharge System
with st.sidebar:
    st.title("💰 Wallet Balance")
    st.markdown(f'<div class="coin-badge">🪙 Balance: {st.session_state.user_coins} Coins</div>', unsafe_allow_html=True)
    
    st.info("🎁 **Bonus:** New User 10 Free Coins!\n\n📌 **Rate:** ₹1 = 1 Coin\n🎬 **1 Video Edit = 10 Coins**")
    
    st.markdown("---")
    st.subheader("💳 UPI Recharge (Add Coins)")
    
    recharge_amount = st.number_input("Enter Amount in ₹ (Min ₹10)", min_value=10, value=10, step=10)
    
    # Updated UPI ID
    upi_id = "Masterki9g@ybl"
    st.markdown(f"**Pay ₹{recharge_amount} using GPay / PhonePe / Paytm to UPI ID:**")
    st.code(upi_id, language="text")
    
    utr_number = st.text_input("Enter UTR / Transaction ID")
    
    if st.button("✅ Confirm Payment & Add Coins"):
        if len(utr_number) >= 4:
            st.session_state.user_coins += recharge_amount
            st.success(f"🎉 Success! {recharge_amount} Coins added to your wallet.")
            st.rerun()
        else:
            st.warning("⚠️ Kripya valid Transaction ID / UTR number dalein!")

# Main App Interface
st.title("🎬 Mobile Video Auto-Editor")
st.write("अपनी वीडियो अपलोड करें (प्रति एडिट 10 कॉइंस कटेंगे)")

uploaded_file = st.file_uploader("वीडियो सेलेक्ट करें (.mp4, .mov)", type=["mp4", "mov"])

if uploaded_file is not None:
    st.video(uploaded_file)
    
    if st.button("🚀 Process & Edit Video (10 Coins)"):
        # Check Balance
        if st.session_state.user_coins < 10:
            st.error("❌ Balance Kam hai! 1 Video Edit ke liye 10 Coins chahiye. Side menu se UPI Recharge karein.")
        else:
            # Deduct 10 Coins
            st.session_state.user_coins -= 10
            
            # 1% to 100% Progress Animation
            progress_text = st.empty()
            progress_bar = st.progress(0)
            
            try:
                for percent_complete in range(100):
                    time.sleep(0.02)
                    progress_bar.progress(percent_complete + 1)
                    progress_text.markdown(f"🔄 **Video Editing Progress:** `{percent_complete + 1}%` completed...")
                
                # Video Processing Logic
                tfile = tempfile.NamedTemporaryFile(delete=False, suffix=".mp4")
                tfile.write(uploaded_file.read())
                
                clip = VideoFileClip(tfile.name)
                output_path = tempfile.NamedTemporaryFile(delete=False, suffix=".mp4").name
                clip.write_videofile(output_path, codec="libx264", audio_codec="aac", logger=None)
                
                progress_text.markdown("✅ **Editing 100% Complete!**")
                st.balloons()
                st.success(f"🎉 Video Successfully Edited! 10 Coins Deducted. Remaining Balance: {st.session_state.user_coins} Coins")
                
                with open(output_path, "rb") as file:
                    st.download_button(
                        label="📥 Download Edited Video",
                        data=file,
                        file_name="edited_video.mp4",
                        mime="video/mp4"
                    )
            except Exception as e:
                st.error(f"Error: {e}")
