import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
import random
import smtplib
import ssl
import time
from email.message import EmailMessage

# --- PAGE SETUP ---
st.set_page_config(page_title="Nebula Messenger", page_icon="🌌", layout="centered")

# --- DATABASE CONNECTION ---
conn = st.connection("gsheets", type=GSheetsConnection)

# --- CSS STYLING (Glassmorphism) ---
st.markdown("""
<style>
    .stApp { background: radial-gradient(circle at top, #1a0b2e, #09090b); color: white; }
    .glass-card {
        background: rgba(255, 255, 255, 0.05); backdrop-filter: blur(15px);
        border-radius: 15px; padding: 20px; border: 1px solid rgba(255, 255, 255, 0.1);
        margin-bottom: 10px;
    }
    .chat-bubble {
        padding: 10px 15px; border-radius: 15px; margin-bottom: 10px;
        background: rgba(138, 43, 226, 0.2); border: 0.5px solid rgba(138, 43, 226, 0.3);
    }
</style>
""", unsafe_allow_html=True)

# --- HELPER FUNCTIONS ---
def send_otp(target_email):
    otp = str(random.randint(100000, 999999))
    sender = st.secrets["GMAIL_USER"].strip()
    pw = st.secrets["GMAIL_PASS"].strip().replace(" ", "")
    msg = EmailMessage()
    msg.set_content(f"Nebula Chat OTP: {otp}")
    msg['Subject'] = 'Nebula Verification'
    msg['From'] = sender
    msg['To'] = target_email
    context = ssl.create_default_context()
    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465, context=context) as server:
            server.login(sender, pw)
            server.send_message(msg)
            return otp
    except: return None

# --- APP NAVIGATION ---
if "page" not in st.session_state: st.session_state.page = "welcome"

# 1. Welcome Screen
if st.session_state.page == "welcome":
    st.markdown("<h1 style='text-align:center;'>🌌 Nebula Messenger</h1>", unsafe_allow_html=True)
    if st.button("Get Started", use_container_width=True):
        st.session_state.page = "auth_choice"
        st.rerun()

# 2. Auth Choice
elif st.session_state.page == "auth_choice":
    st.markdown("<div class='glass-card'>", unsafe_allow_html=True)
    if st.button("Sign In (Login)", use_container_width=True):
        st.session_state.page = "login"
        st.rerun()
    st.write("")
    if st.button("Sign Up (New Account)", use_container_width=True):
        st.session_state.page = "signup"
        st.rerun()
    st.markdown("</div>", unsafe_allow_html=True)

# 3. Sign Up
elif st.session_state.page == "signup":
    st.subheader("Create New Account")
    email = st.text_input("Gmail Address")
    if "otp_sent" not in st.session_state:
        if st.button("Send OTP"):
            res = send_otp(email)
            if res:
                st.session_state.gen_otp, st.session_state.otp_sent = res, True
                st.success("OTP Sent!")
                st.rerun()
    else:
        u_otp = st.text_input("OTP Code")
        u_id = st.text_input("Username (@id)")
        d_name = st.text_input("Display Name")
        pw = st.text_input("Password", type="password")
        if st.button("Register"):
            if u_otp == st.session_state.gen_otp:
                # User DB အား Sheet ထဲထည့်ခြင်း
                df = conn.read(worksheet="Sheet1")
                new_user = pd.DataFrame([{"email": email, "username": u_id, "display_name": d_name, "password": pw}])
                updated_df = pd.concat([df, new_user], ignore_index=True)
                conn.update(worksheet="Sheet1", data=updated_df)
                st.success("Account Created! Please Login.")
                st.session_state.page = "login"
                st.rerun()

# 4. Login
elif st.session_state.page == "login":
    st.subheader("Sign In")
    l_user = st.text_input("Username")
    l_pass = st.text_input("Password", type="password")
    if st.button("Login"):
        data = conn.read(worksheet="Sheet1")
        user_row = data[data['username'] == l_user]
        if not user_row.empty and str(user_row.iloc[0]['password']) == l_pass:
            st.session_state.user = user_row.iloc[0].to_dict()
            st.session_state.page = "chat"
            st.rerun()
        else: st.error("Wrong credentials")

# 5. Chat Room
elif st.session_state.page == "chat":
    st.sidebar.title(f"Hi, {st.session_state.user['display_name']}")
    if st.sidebar.button("Logout"):
        st.session_state.page = "welcome"
        st.rerun()

    st.title("💬 Global Nebula Chat")
    
    # Message များကို Sheet 2 (သို့မဟုတ်) Sheet တစ်ခုတည်းမှာ သိမ်းနိုင်သည်
    # ဤနေရာတွင် ရိုးရှင်းစေရန် Chat System ကို ထည့်သွင်းထားသည်
    msg_input = st.chat_input("စာရိုက်ရန်...")
    if msg_input:
        # ဤနေရာတွင် Message ကို Database ထဲလှမ်းသိမ်းရမည်
        st.write(f"**You:** {msg_input}")
        st.toast("Message sent!")
