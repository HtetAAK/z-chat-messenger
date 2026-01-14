import streamlit as st
import random
import smtplib
import json
import requests
import re
from email.message import EmailMessage

# --- CONFIG & SECRETS ---
API_ID = st.secrets["API_ID"]
API_HASH = st.secrets["API_HASH"]
BOT_TOKEN = st.secrets["BOT_TOKEN"]
CHANNEL_ID = st.secrets["CHANNEL_ID"]
GMAIL_USER = st.secrets["GMAIL_USER"]
GMAIL_PASS = st.secrets["GMAIL_PASS"]

# --- CSS STYLING (Inspired by your UI image) ---
st.markdown("""
<style>
    .stApp {
        background: radial-gradient(circle at top, #2D0B5A 0%, #0E1117 100%);
        color: white;
    }
    /* Glassmorphism Card */
    .glass-card {
        background: rgba(255, 255, 255, 0.05);
        backdrop-filter: blur(15px);
        border-radius: 25px;
        padding: 30px;
        border: 1px solid rgba(255, 255, 255, 0.1);
        margin-bottom: 20px;
    }
    /* Button Styling */
    .stButton>button {
        background: linear-gradient(90deg, #8A2BE2 0%, #D02BE2 100%);
        color: white; border-radius: 15px; height: 3.5em; 
        border: none; width: 100%; font-weight: bold;
        box-shadow: 0 4px 15px rgba(138, 43, 226, 0.3);
    }
    /* Input Box Styling */
    .stTextInput>div>div>input {
        background-color: rgba(255, 255, 255, 0.07) !important;
        color: white !important;
        border: 1px solid rgba(138, 43, 226, 0.5) !important;
        border-radius: 12px !important;
    }
    h1, h2, h3 { color: #E0AAFF !important; text-align: center; }
</style>
""", unsafe_allow_html=True)

# --- TELEGRAM DATABASE FUNCTIONS ---
def send_to_tg(text):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {"chat_id": CHANNEL_ID, "text": text}
    requests.post(url, data=payload)

def get_user_from_tg(username):
    # Telegram Bot API ကိုသုံးပြီး user data ရှာခြင်း
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/getUpdates"
    try:
        response = requests.get(url).json()
        if response.get("ok"):
            # နောက်ဆုံး message များမှ USER_DB ကို ရှာဖွေခြင်း
            for update in reversed(response.get("result", [])):
                msg = update.get("channel_post", {}).get("text", "")
                if msg.startswith("USER_DB:"):
                    data = json.loads(msg.split("USER_DB:")[1])
                    if data['username'] == username:
                        return data
    except: pass
    return None

# --- EMAIL FUNCTIONS ---
def send_otp(email):
    otp = str(random.randint(100000, 999999))
    msg = EmailMessage()
    msg.set_content(f"Nebula Chat အတွက် သင်၏ OTP ကုဒ်မှာ {otp} ဖြစ်ပါသည်။")
    msg['Subject'] = 'Nebula Verification'
    msg['From'] = GMAIL_USER
    msg['To'] = email
    with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
        smtp.login(GMAIL_USER, GMAIL_PASS)
        smtp.send_message(msg)
    return otp

# --- APP NAVIGATION ---
if "page" not in st.session_state: st.session_state.page = "welcome"

# 1. Welcome Screen
if st.session_state.page == "welcome":
    st.markdown("<br><br><h1>🌌 Nebula Chat</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align:center;'>အနာဂတ်ရဲ့ စကားပြောခန်းမှ ကြိုဆိုပါတယ်။</p>", unsafe_allow_html=True)
    st.write("")
    if st.button("စတင်အသုံးပြုမည်"):
        st.session_state.page = "auth_choice"
        st.rerun()

# 2. Auth Choice
elif st.session_state.page == "auth_choice":
    st.markdown("<div class='glass-card'>", unsafe_allow_html=True)
    st.subheader("Welcome Back")
    if st.button("Sign In (Login)"):
        st.session_state.page = "login"
        st.rerun()
    st.write("")
    if st.button("Sign Up (New Account)"):
        st.session_state.page = "signup"
        st.rerun()
    st.markdown("</div>", unsafe_allow_html=True)

# 3. Sign Up
elif st.session_state.page == "signup":
    st.markdown("<div class='glass-card'>", unsafe_allow_html=True)
    st.subheader("Create Account")
    email = st.text_input("Gmail Address")
    
    if "otp_sent" not in st.session_state:
        if st.button("Send OTP"):
            if "@gmail.com" in email:
                st.session_state.gen_otp = send_otp(email)
                st.session_state.otp_sent = True
                st.success("OTP ပို့လိုက်ပါပြီ!")
                st.rerun()
            else: st.error("Gmail အမှန် ထည့်ပေးပါ။")
    else:
        u_otp = st.text_input("Verify Code (OTP)")
        u_name = st.text_input("Username (@id)")
        d_name = st.text_input("Display Name")
        pw = st.text_input("Password", type="password")
        
        if st.button("Complete Sign Up"):
            if u_otp == st.session_state.gen_otp:
                user_data = {"username": u_name, "display_name": d_name, "password": pw}
                send_to_tg(f"USER_DB:{json.dumps(user_data)}")
                st.success("အကောင့်ဖွင့်ခြင်း အောင်မြင်ပါသည်!")
                st.session_state.page = "login"
                st.rerun()
            else: st.error("OTP ကုဒ် မှားနေပါသည်။")
    st.markdown("</div>", unsafe_allow_html=True)

# 4. Login
elif st.session_state.page == "login":
    st.markdown("<div class='glass-card'>", unsafe_allow_html=True)
    st.subheader("Login")
    l_user = st.text_input("Username")
    l_pass = st.text_input("Password", type="password")
    
    if st.button("Continue"):
        user = get_user_from_tg(l_user)
        if user and user['password'] == l_pass:
            st.session_state.user = user
            st.session_state.page = "main_chat"
            st.rerun()
        else: st.error("Username သို့မဟုတ် Password မှားယွင်းနေပါသည်။")
    st.markdown("</div>", unsafe_allow_html=True)

# 5. Main Chat UI
elif st.session_state.page == "main_chat":
    st.sidebar.title(f"Hi, {st.session_state.user['display_name']}")
    if st.sidebar.button("Logout"):
        st.session_state.page = "welcome"
        st.rerun()
    
    st.write("### 💬 Global Nebula Chat")
    st.info("စကားပြောခန်းကို မကြာမီ Update ပြုလုပ်ပေးပါမည်။")
