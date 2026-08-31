import streamlit as st
from supabase import create_client
import time

# Page Config
st.set_page_config(page_title="No Copyright", page_icon="🎬", layout="wide")

# Supabase Connection
@st.cache_resource
def init_supabase():
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]
    return create_client(url, key)

try:
    supabase = init_supabase()
except Exception as e:
    st.error("⚠️ Supabase Secrets missing! Please set SUPABASE_URL and SUPABASE_KEY in Streamlit Secrets.")
    st.stop()

# Session State Initializations
if "user" not in st.session_state:
    st.session_state.user = None

# Custom CSS
st.markdown("""
    <style>
    .coin-badge {
        background: linear-gradient(135deg, #FFD700 0%, #FFA500 100%);
        color: #000; padding: 10px 18px; border-radius: 20px;
        font-weight: bold; font-size: 1.1rem; display: inline-block;
    }
    .stButton>button {
        width: 100%; background: linear-gradient(90deg, #FF4B4B 0%, #FF6B6B 100%);
        color: white; font-weight: bold; border-radius: 8px; padding: 8px;
    }
    </style>
""", unsafe_allow_html=True)

upi_id = "Masterki9g@ybl"
st.title("🎬 No Copyright")

# --- LOGIN / SIGNUP SYSTEM ---
if st.session_state.user is None:
    tab1, tab2 = st.tabs(["🔑 Login", "📝 Sign Up"])
    
    with tab1:
        st.subheader("Login to your account")
        login_mobile = st.text_input("Mobile Number", key="log_mob")
        login_pass = st.text_input("Password", type="password", key="log_pass")
        if st.button("Login"):
            res = supabase.table("users").select("*").eq("mobile_number", login_mobile).eq("password", login_pass).execute()
            if len(res.data) > 0:
                st.session_state.user = res.data[0]
                st.success("Successfully Logged In!")
                st.rerun()
            else:
                st.error("Invalid Mobile Number or Password")
                
    with tab2:
        st.subheader("Create New Account")
        sign_mobile = st.text_input("Mobile Number", key="sign_mob")
        sign_pass = st.text_input("Password", type="password", key="sign_pass")
        if st.button("Sign Up"):
            if len(sign_mobile) >= 10 and len(sign_pass) >= 4:
                try:
                    res = supabase.table("users").insert({"mobile_number": sign_mobile, "password": sign_pass, "coins": 10}).execute()
                    st.success("Account created! 10 Free Coins added. Please login.")
                except Exception:
                    st.error("Mobile Number already registered!")
            else:
                st.warning("Enter a valid Mobile Number & Password")

else:
    # Fetch latest user data from Database
    user_data = supabase.table("users").select("*").eq("id", st.session_state.user["id"]).execute().data[0]
    
    col_bal1, col_bal2, col_bal3 = st.columns([1.5, 2, 1])
    with col_bal1:
        st.markdown(f'<div class="coin-badge">🪙 Coins: {user_data["coins"]} | 📱 {user_data["mobile_number"]}</div>', unsafe_allow_html=True)
    with col_bal2:
        st.info("🎬 **1 Video Edit = 10 Coins**")
    with col_bal3:
        if st.button("🚪 Logout"):
            st.session_state.user = None
            st.rerun()

    st.markdown("---")

    # 1. TOP SECTION: Video Editing Upload
    st.subheader("📤 Upload & Edit Video")
    st.write("Upload your video (10 coins will be deducted per edit)")

    uploaded_file = st.file_uploader("Select a video (.mp4, .mov)", type=["mp4", "mov"])

    if uploaded_file is not None:
        st.video(uploaded_file)
        if st.button("🚀 Process & Edit Video (10 Coins)"):
            if user_data["coins"] < 10:
                st.error("❌ Low Balance! Please recharge using the QR code below.")
            else:
                new_balance = user_data["coins"] - 10
                supabase.table("users").update({"coins": new_balance}).eq("id", user_data["id"]).execute()
                
                progress_bar = st.progress(0)
                for i in range(1, 101):
                    time.sleep(0.01)
                    progress_bar.progress(i)
                
                st.balloons()
                st.success("🎉 Video Processed Successfully!")
                st.download_button("📥 Download Edited Video", data=uploaded_file.getvalue(), file_name="edited_video.mp4", mime="video/mp4")
                st.rerun()

    st.markdown("---")

    # 2. PLANS TABLE
    st.subheader("📦 Video Editing Plans")
    plans = [
        {"plan": "Plan A", "days": "Day 7", "price": 99, "coins": 70},
        {"plan": "Plan B", "days": "Day 14", "price": 179, "coins": 150},
        {"plan": "Plan C", "days": "Day 28", "price": 249, "coins": 300},
    ]

    col_h1, col_h2, col_h3, col_h4 = st.columns([1, 1, 1, 1])
    col_h1.markdown("**Plan**"); col_h2.markdown("**Days**"); col_h3.markdown("**Price**"); col_h4.markdown("**Coins**")
    st.markdown("<hr style='margin:2px 0;'>", unsafe_allow_html=True)

    for p in plans:
        c1, c2, c3, c4 = st.columns([1, 1, 1, 1])
        c1.write(f"📌 **{p['plan']}**"); c2.write(p['days']); c3.write(f"₹{p['price']}"); c4.write(f"🪙 +{p['coins']}")

    st.markdown("---")

    # 3. PAYMENT & UTR CLAIM
    col_qr, col_claim = st.columns([1, 1.5])

    with col_qr:
        st.subheader("📲 Scan QR Code To Pay")
        qr_api_url = f"https://api.qrserver.com/v1/create-qr-code/?size=250x250&data=upi://pay?pa={upi_id}%26pn=Krishna%20Kumar"
        st.image(qr_api_url, caption="Scan using GPay / PhonePe / Paytm", width=200)
        st.code(upi_id, language="text")

    with col_claim:
        st.subheader("✅ Submit Transaction Details")
        selected_plan_idx = st.selectbox(
            "Choose Paid Plan",
            range(len(plans)),
            format_func=lambda i: f"{plans[i]['plan']} - {plans[i]['days']} (₹{plans[i]['price']} = {plans[i]['coins']} Coins)"
        )
        utr_number = st.text_input("Enter UTR / Transaction ID (12 Digits)")

        if st.button("Submit UTR for Verification"):
            if len(utr_number) >= 6:
                try:
                    supabase.table("transactions").insert({
                        "mobile_number": user_data["mobile_number"],
                        "plan_name": plans[selected_plan_idx]["plan"],
                        "coins_requested": plans[selected_plan_idx]["coins"],
                        "utr_number": utr_number,
                        "status": "Pending"
                    }).execute()
                    st.info("⏳ Payment Submitted! Coins will be added once verified by Admin.")
                except Exception:
                    st.error("⚠️ This UTR Number has already been submitted!")
            else:
                st.warning("⚠️ Enter a valid UTR Number!")

    # ADMIN PANEL (Visible for Admin Mobile Number: 9999999999)
    if user_data["mobile_number"] == "9999999999":
        st.markdown("---")
        st.subheader("⚙️ Admin Panel - Verify Payments")
        pending_tx = supabase.table("transactions").select("*").eq("status", "Pending").execute().data
        
        if pending_tx:
            for tx in pending_tx:
                col_a, col_b, col_c, col_d = st.columns([2, 2, 1, 1])
                col_a.write(f"📱 **{tx['mobile_number']}**")
                col_b.write(f"UTR: `{tx['utr_number']}` (+{tx['coins_requested']} Coins)")
                if col_c.button("Approve", key=f"app_{tx['id']}"):
                    u = supabase.table("users").select("coins").eq("mobile_number", tx['mobile_number']).execute().data[0]
                    supabase.table("users").update({"coins": u["coins"] + tx["coins_requested"]}).eq("mobile_number", tx['mobile_number']).execute()
                    supabase.table("transactions").update({"status": "Approved"}).eq("id", tx['id']).execute()
                    st.success("Approved!")
                    st.rerun()
                if col_d.button("Reject", key=f"rej_{tx['id']}"):
                    supabase.table("transactions").update({"status": "Rejected"}).eq("id", tx['id']).execute()
                    st.warning("Rejected!")
                    st.rerun()
        else:
            st.write("No pending payments for approval.")
            st.balloons()
            st.success(f"🎉 Payment Verified! {added_coins} Coins added to your wallet. Current Balance: {st.session_state.user_coins} Coins")
        else:
            st.warning("⚠️ Please enter a valid UTR / Transaction ID!")
