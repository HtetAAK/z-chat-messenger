import streamlit as st
import random
import smtplib
import re
import json
import asyncio
from telethon import TelegramClient
from email.message import EmailMessage

# --- CONFIG & SECRETS (Streamlit Cloud ရဲ့ Secrets ထဲမှာ ထည့်ရမယ့် အချက်အလက်များ) ---
API_ID = st.secrets["API_ID"]
API_HASH = st.secrets["API_HASH"]
BOT_TOKEN = st.secrets["BOT_TOKEN"]
CHANNEL_ID = int(st.secrets["CHANNEL_ID"])
GMAIL_USER = st.secrets["GMAIL_USER"]
GMAIL_PASS = st.secrets["GMAIL_PASS"]

client = TelegramClient('bot_session', API_ID, API_HASH)

# --- CSS STYLING ---
st.markdown("""
<style>
    .stApp { background-color: #0E1117; color: white; }
    .stButton>button {
        background: linear-gradient(90deg, #8A2BE2 0%, #4B0082 100%);
        color: white; border-radius: 12px; height: 3em; border: none; width: 100%;
    }
</style>
""", unsafe_allow_html=True)

# --- FUNCTIONS ---
def send_otp(target_email):
    otp = str(random.randint(100000, 999999))
    msg = EmailMessage()
    msg.set_content(f"သင်၏ Nebula Chat Verify Code မှာ {otp} ဖြစ်ပါသည်။")
    msg['Subject'] = 'Nebula Chat Verification'
    msg['From'] = GMAIL_USER
    msg['To'] = target_email
    with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
        smtp.login(GMAIL_USER, GMAIL_PASS)
        smtp.send_message(msg)
    return otp

async def save_user_to_tg(user_data):
    await client.start(bot_token=BOT_TOKEN)
    await client.send_message(CHANNEL_ID, f"USER_DB:{json.dumps(user_data)}")

async def check_user_exists(username):
    await client.start(bot_token=BOT_TOKEN)
    async for msg in client.iter_messages(CHANNEL_ID):
        if msg.text and msg.text.startswith("USER_DB:"):
            data = json.loads(msg.text.split("USER_DB:")[1])
            if data['username'] == username: return data
    return None

# --- APP FLOW ---
if "page" not in st.session_state: st.session_state.page = "welcome"

if st.session_state.page == "welcome":
    st.markdown("<h1 style='text-align: center;'>🌌 Nebula Chat</h1>", unsafe_allow_html=True)
    st.write("---")
    st.write("### မင်္ဂလာပါ! Nebula မှ ကြိုဆိုပါသည်။")
    if st.button("စတင်အသုံးပြုမည်"):
        st.session_state.page = "auth_choice"
        st.rerun()

elif st.session_state.page == "auth_choice":
    if st.button("Sign In (Login)"): 
        st.session_state.page = "login"
        st.rerun()
    if st.button("Sign Up (New Account)"): 
        st.session_state.page = "signup"
        st.rerun()

elif st.session_state.page == "signup":
    st.subheader("📝 Register")
    email = st.text_input("Gmail Address")
    if "otp_sent" not in st.session_state:
        if st.button("OTP ပို့မည်"):
            st.session_state.generated_otp = send_otp(email)
            st.session_state.otp_sent = True
            st.rerun()
    else:
        u_otp = st.text_input("OTP ရိုက်ပါ")
        u_name = st.text_input("User Name")
        d_name = st.text_input("Display Name")
        pw = st.text_input("Password", type="password")
        if st.button("Confirm Register"):
            if u_otp == st.session_state.generated_otp:
                user_data = {"username": u_name, "display_name": d_name, "password": pw}
                asyncio.run(save_user_to_tg(user_data))
                st.session_state.page = "login"
                st.rerun()

elif st.session_state.page == "login":
    st.subheader("🔐 Login")
    l_user = st.text_input("Username")
    l_pass = st.text_input("Password", type="password")
    if st.button("Login"):
        user = asyncio.run(check_user_exists(l_user))
        if user and user['password'] == l_pass:
            st.session_state.user = user
            st.session_state.page = "chat_main"
            st.rerun()
        else: st.error("မှားယွင်းနေပါသည်။")

elif st.session_state.page == "chat_main":
    st.sidebar.write(f"Logged in as: {st.session_state.user['display_name']}")
    st.write("### Chat စနစ်သို့ ရောက်ရှိသွားပါပြီ။")
    if st.sidebar.button("Logout"):
        st.session_state.page = "welcome"
        st.rerun()
