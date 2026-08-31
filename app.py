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
st.write("Upload your video (10 coins will be deducted per edit)")

uploaded_file = st.file_uploader("Select a video (.mp4, .mov)", type=["mp4", "mov"])

if uploaded_file is not None:
    st.video(uploaded_file)
    
    if st.button("🚀 Process & Edit Video (10 Coins)"):
        if st.session_state.user_coins < 10:
            st.error("❌ Low Balance! You need 10 coins for 1 video edit. Please recharge using the QR code below.")
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

# 2. BOTTOM SECTION: Video Editing Plans Table (Updated A, B, C Plans)
st.subheader("📦 Video Editing Plans")

plans = [
    {"plan": "Plan A", "days": "Day 7", "price": 99, "coins": 70},
    {"plan": "Plan B", "days": "Day 14", "price": 179, "coins": 150},
    {"plan": "Plan C", "days": "Day 28", "price": 249, "coins": 300},
]

# Column Table Format Header
col_h1, col_h2, col_h3, col_h4 = st.columns([1, 1, 1, 1])
with col_h1:
    st.markdown("**Plan**")
with col_h2:
    st.markdown("**Days**")
with col_h3:
    st.markdown("**Price**")
with col_h4:
    st.markdown("**Coins**")

st.markdown("<hr style='margin:4px 0; border-top: 2px solid #ccc;'>", unsafe_allow_html=True)

# Table Rows
for p in plans:
    col1, col2, col3, col4 = st.columns([1, 1, 1, 1])
    with col1:
        st.write(f"📌 **{p['plan']}**")
    with col2:
        st.write(p['days'])
    with col3:
        st.write(f"₹{p['price']}")
    with col4:
        st.write(f"🪙 +{p['coins']}")
    st.markdown("<hr style='margin:2px 0;'>", unsafe_allow_html=True)

st.markdown("---")

# 3. QR Code & Manual Payment Section
col_qr, col_claim = st.columns([1, 1.5])

with col_qr:
    st.subheader("📲 Scan QR Code To Pay")
    qr_api_url = f"https://api.qrserver.com/v1/create-qr-code/?size=250x250&data=upi://pay?pa={upi_id}%26pn=Krishna%20Kumar"
    st.image(qr_api_url, caption="Scan using GPay / PhonePe / Paytm", width=220)
    st.write("**UPI ID:**")
    st.code(upi_id, language="text")

with col_claim:
    st.subheader("✅ Confirm Payment & Add Coins")
    selected_plan_idx = st.selectbox(
        "Choose Paid Plan",
        range(len(plans)),
        format_func=lambda i: f"{plans[i]['plan']} - {plans[i]['days']} (₹{plans[i]['price']} = {plans[i]['coins']} Coins)"
    )
    utr_number = st.text_input("Enter UTR / Transaction ID (12 Digits)")
    
    if st.button("Submit & Claim Coins"):
        if len(utr_number) >= 4:
            added_coins = plans[selected_plan_idx]["coins"]
            st.session_state.user_coins += added_coins
            st.balloons()
            st.success(f"🎉 Payment Verified! {added_coins} Coins added to your wallet. Current Balance: {st.session_state.user_coins} Coins")
        else:
            st.warning("⚠️ Please enter a valid UTR / Transaction ID!")
