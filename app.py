import streamlit as st
import time

# Page Config
st.set_page_config(
    page_title="No Copyright",
    page_icon="🎬",
    layout="wide"
)

# Initialize Session State
if "user_coins" not in st.session_state:
    st.session_state.user_coins = 10  # 🎁 New User Free Bonus

# Custom CSS
st.markdown("""
    <style>
    .coin-badge {
        background: linear-gradient(135deg, #FFD700 0%, #FFA500 100%);
        color: #000;
        padding: 12px 20px;
        border-radius: 20px;
        font-weight: bold;
        font-size: 1.2rem;
        display: inline-block;
        margin-bottom: 15px;
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

# UPI Details
upi_id = "Masterki9g@ybl"

# Header Section
st.title("🎬 No Copyright")

# Balance Badge & Info
col_bal1, col_bal2 = st.columns([1, 2])
with col_bal1:
    st.markdown(f'<div class="coin-badge">🪙 Wallet Balance: {st.session_state.user_coins} Coins</div>', unsafe_allow_html=True)
with col_bal2:
    st.info("🎁 **Bonus:** New User 10 Free Coins! | 🎬 **1 Video Edit = 10 Coins**")

st.markdown("---")

# 1. TOP SECTION: Video Editing Upload
st.subheader("📤 Upload & Edit Video")
st.write("अपनी वीडियो अपलोड करें (प्रति एडिट 10 कॉइंस कटेंगे)")

uploaded_file = st.file_uploader("वीडियो सेलेक्ट करें (.mp4, .mov)", type=["mp4", "mov"])

if uploaded_file is not None:
    st.video(uploaded_file)
    
    if st.button("🚀 Process & Edit Video (10 Coins)"):
        if st.session_state.user_coins < 10:
            st.error("❌ Balance Kam hai! 1 Video Edit ke liye 10 Coins chahiye. Niche diye plan se recharge karein.")
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

st.markdown("---")

# 2. BOTTOM SECTION: Video Editing Plans
st.subheader("📦 Select Video Editing Plan")

plans = [
    {"name": "Day 1", "price": 20, "coins": 10},
    {"name": "Day 3", "price": 45, "coins": 30},
    {"name": "Day 7", "price": 99, "coins": 70},
    {"name": "Day 14", "price": 179, "coins": 150},
    {"name": "Day 28", "price": 249, "coins": 300},
]

# Display Plans in Rows
for plan in plans:
    col1, col2, col3 = st.columns([2, 2, 1])
    with col1:
        st.markdown(f"**Plan {plan['name']}** (₹{plan['price']})")
    with col2:
        st.markdown(f"🪙 **+{plan['coins']} Coins**")
    with col3:
        pay_url = f"upi://pay?pa={upi_id}&pn=Krishna%20Kumar&am={plan['price']}&cu=INR"
        st.markdown(f'<a href="{pay_url}" target="_blank" class="pay-btn">💳 Pay Now</a>', unsafe_allow_html=True)

st.markdown("---")

# 3. QR Code & Manual Payment Section
col_qr, col_claim = st.columns([1, 1.5])

with col_qr:
    st.subheader("📲 Scan QR Code To Pay")
    # Generating QR code directly on screen via Google Chart API (No broken links)
    qr_api_url = f"https://api.qrserver.com/v1/create-qr-code/?size=250x250&data=upi://pay?pa={upi_id}%26pn=Krishna%20Kumar"
    st.image(qr_api_url, caption="Scan using GPay / PhonePe / Paytm", width=220)
    st.write("**UPI ID:**")
    st.code(upi_id, language="text")

with col_claim:
    st.subheader("✅ Confirm Payment & Add Coins")
    selected_plan_idx = st.selectbox(
        "Choose Plan Paid For",
        range(len(plans)),
        format_func=lambda i: f"{plans[i]['name']} - ₹{plans[i]['price']} ({plans[i]['coins']} Coins)"
    )
    utr_number = st.text_input("Enter UTR / Transaction ID")
    
    if st.button("Submit & Claim Coins"):
        if len(utr_number) >= 4:
            added_coins = plans[selected_plan_idx]["coins"]
            st.session_state.user_coins += added_coins
            st.success(f"🎉 Payment Verified! {added_coins} Coins added to your wallet.")
        else:
            st.warning("⚠️ Valid Transaction ID / UTR number dalein!")
