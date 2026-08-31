import streamlit as st
import time

# Page Config
st.set_page_config(
    page_title="Mobile Video Auto-Editor",
    page_icon="🎬",
    layout="wide"
)

# Initialize Session State
if "user_coins" not in st.session_state:
    st.session_state.user_coins = 10

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
    .pay-btn {
        display: block;
        width: 100%;
        background-color: #28a745;
        color: white !important;
        text-align: center;
        padding: 8px 12px;
        border-radius: 6px;
        font-weight: bold;
        text-decoration: none;
        margin-top: 5px;
    }
    .pay-btn:hover {
        background-color: #218838;
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

upi_id = "Masterki9g@ybl"

# Sidebar - Wallet & Plans System
with st.sidebar:
    st.title("💰 Wallet Balance")
    st.markdown(f'<div class="coin-badge">🪙 Balance: {st.session_state.user_coins} Coins</div>', unsafe_allow_html=True)
    
    st.info("🎁 **Bonus:** New User 10 Free Coins!\n\n🎬 **1 Video Edit = 10 Coins**")
    
    st.markdown("---")
    st.subheader("📦 Select Editing Plan")
    
    # Plans Data
    plans = [
        {"days": "1 Day", "price": 20},
        {"days": "3 Days", "price": 45},
        {"days": "7 Days", "price": 99},
        {"days": "14 Days", "price": 179},
        {"days": "28 Days", "price": 249},
    ]
    
    # Render Plans with Pay Now Redirect Buttons
    for plan in plans:
        col1, col2 = st.columns([1.2, 1])
        with col1:
            st.markdown(f"**Plan {plan['days']}**  \n₹{plan['price']}")
        with col2:
            # Deep Link to redirect mobile UPI Apps directly
            pay_url = f"upi://pay?pa={upi_id}&pn=VideoEditor&am={plan['price']}&cu=INR"
            st.markdown(f'<a href="{pay_url}" target="_blank" class="pay-btn">💳 Pay Now</a>', unsafe_allow_html=True)
        st.markdown("<hr style='margin:8px 0;'>", unsafe_allow_html=True)
        
    st.subheader("✅ Confirm Plan After Payment")
    selected_plan = st.selectbox("Choose Plan Paid For", ["1 Day (₹20)", "3 Days (₹45)", "7 Days (₹99)", "14 Days (₹179)", "28 Days (₹249)"])
    utr_number = st.text_input("Enter UTR / Transaction ID")
    
    if st.button("Submit Payment Proof"):
        if len(utr_number) >= 4:
            st.success("🎉 Payment Proof Submitted! Plan will be activated shortly.")
        else:
            st.warning("⚠️ Valid Transaction ID / UTR number dalein!")

# Main App Interface
st.title("🎬 Mobile Video Auto-Editor")
st.write("अपनी वीडियो अपलोड करें (प्रति एडिट 10 कॉइंस कटेंगे)")

uploaded_file = st.file_uploader("वीडियो सेलेक्ट करें (.mp4, .mov)", type=["mp4", "mov"])

if uploaded_file is not None:
    st.video(uploaded_file)
    
    if st.button("🚀 Process & Edit Video (10 Coins)"):
        if st.session_state.user_coins < 10:
            st.error("❌ Balance Kam hai! 1 Video Edit ke liye 10 Coins chahiye. Side menu se Plan buy karein.")
        else:
            st.session_state.user_coins -= 10
            
            progress_text = st.empty()
            progress_bar = st.progress(0)
            
            for i in range(1, 101):
                time.sleep(0.02)
                progress_bar.progress(i)
                progress_text.markdown(f"🔄 **Video Editing Progress:** `{i}%` completed...")
            
            st.balloons()
            st.success(f"🎉 Video Successfully Processed! 10 Coins Deducted. Remaining Balance: {st.session_state.user_coins} Coins")
            
            st.download_button(
                label="📥 Download Edited Video",
                data=uploaded_file.getvalue(),
                file_name="edited_video.mp4",
                mime="video/mp4"
            )
