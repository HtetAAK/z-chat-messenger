import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
import random
import smtplib
import ssl
import time
from email.message import EmailMessage

# --- PAGE CONFIG ---
st.set_page_config(page_title="Nebula Messenger", page_icon="🌌", layout="centered")

# --- DATABASE CONNECTION ---
# Secrets ထဲက [connections.gsheets] ကို အလိုအလျောက် သုံးပါလိမ့်မယ်
conn = st.connection("gsheets", type=GSheetsConnection)

# --- CSS STYLING (Glassmorphism) ---
st.markdown("""
<style>
    .stApp { background: radial-gradient(circle at top, #1a0b2e, #09090b); color: white; }
    .glass-card {
        background: rgba(255, 255, 255, 0.05); backdrop-filter: blur(15px);
        border-radius: 20px; padding: 30px; border: 1px solid rgba(255, 255, 255, 0.1);
        box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.37);
    }
    .stButton>button {
        background: linear-gradient(90deg, #8A2BE2 0%, #D02BE2 100%);
        color: white; border-radius: 12px; border: none; width: 100%; height: 3.5em; font-weight: bold;
    }
    input { color: white !important; }
</style>
""", unsafe_allow_html=True)

# --- EMAIL FUNCTION ---
def send_otp(target_email):
    otp = str(random.randint(100000, 999999))
    try:
        sender = st.secrets["GMAIL_USER"].strip()
        # Password ထဲက space တွေကို ဖယ်ထုတ်ပါမယ်
        pw = st.secrets["GMAIL_PASS"].strip().replace(" ", "")
        
        msg = EmailMessage()
        msg.set_content(f"Nebula Chat OTP Code: {otp}")
        msg['Subject'] = 'Nebula Account Verification'
        msg['From'] = sender
        msg['To'] = target_email
        
        context = ssl.create_default_context()
        with smtplib.SMTP_SSL("smtp.gmail.com", 465, context=context) as server:
            server.login(sender, pw)
            server.send_message(msg)
            return otp
    except Exception as e:
        st.error(f"Gmail Error: {str(e)}")
        return None

# --- APP NAVIGATION ---
if "page" not in st.session_state: st.session_state.page = "welcome"

# 1. Welcome Screen
if st.session_state.page == "welcome":
    st.markdown("<br><h1 style='text-align:center;'>🌌 Nebula Messenger</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align:center;'>Secure Messaging with Google Cloud DB</p>", unsafe_allow_html=True)
    st.write("---")
    if st.button("Get Started"):
        st.session_state.page = "auth_choice"
        st.rerun()

# 2. Auth Choice
elif st.session_state.page == "auth_choice":
    st.markdown("<div class='glass-card'>", unsafe_allow_html=True)
    st.subheader("Login or Create Account")
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
    st.subheader("📝 Sign Up")
    email = st.text_input("Gmail Address")
    
    if "otp_sent" not in st.session_state:
        if st.button("Send OTP"):
            if "@gmail.com" in email:
                with st.spinner("OTP ပို့နေသည်..."):
                    res = send_otp(email)
                    if res:
                        st.session_state.gen_otp = res
                        st.session_state.otp_sent = True
                        st.success("OTP ပို့ပြီးပါပြီ။ Gmail ကို စစ်ဆေးပါ။")
                        time.sleep(1)
                        st.rerun()
            else: st.error("မှန်ကန်သော Gmail လိပ်စာ ရိုက်ထည့်ပါ။")
    else:
        u_otp = st.text_input("Enter 6-digit OTP")
        u_id = st.text_input("Username (@id)")
        d_name = st.text_input("Display Name")
        pw = st.text_input("Password", type="password")
        
        if st.button("Register Account"):
            if u_otp == st.session_state.gen_otp:
                try:
                    with st.spinner("Database ထဲ သိမ်းဆည်းနေသည်..."):
                        # Google Sheet ထဲက data အဟောင်းဖတ်မယ်
                        df = conn.read()
                        
                        # User အသစ် data row ဆောက်မယ်
                        new_user = pd.DataFrame([{
                            "email": email, 
                            "username": u_id, 
                            "display_name": d_name, 
                            "password": pw
                        }])
                        
                        # Data အဟောင်းနဲ့ အသစ်ပေါင်းပြီး Sheet ထဲ ပြန်တင်မယ်
                        updated_df = pd.concat([df, new_user], ignore_index=True)
                        conn.update(data=updated_df)
                        
                        st.success("Registration Success! Please Login.")
                        time.sleep(2)
                        st.session_state.page = "login"
                        # Reset signup status
                        if "otp_sent" in st.session_state: del st.session_state.otp_sent
                        st.rerun()
                except Exception as e:
                    st.error(f"Database Error: {e}")
            else:
                st.error("OTP ကုဒ် မှားယွင်းနေပါသည်။")
    st.markdown("</div>", unsafe_allow_html=True)

# 4. Login
elif st.session_state.page == "login":
    st.markdown("<div class='glass-card'>", unsafe_allow_html=True)
    st.subheader("🔐 Login")
    l_user = st.text_input("Username")
    l_pass = st.text_input("Password", type="password")
    
    if st.button("Login"):
        with st.spinner("ခဏစောင့်ပါ..."):
            data = conn.read()
            user_row = data[data['username'] == l_user]
            if not user_row.empty and str(user_row.iloc[0]['password']) == l_pass:
                st.session_state.user = user_row.iloc[0].to_dict()
                st.session_state.page = "main_chat"
                st.rerun()
            else:
                st.error("Username သို့မဟုတ် Password မှားယွင်းနေပါသည်။")
    
    if st.button("Back"):
        st.session_state.page = "auth_choice"
        st.rerun()
    st.markdown("</div>", unsafe_allow_html=True)

# 5. Main Chat (Placeholder)
elif st.session_state.page == "main_chat":
    st.sidebar.title(f"Hi, {st.session_state.user['display_name']}!")
    if st.sidebar.button("Logout"):
        del st.session_state.user
        st.session_state.page = "welcome"
        st.rerun()
    
    st.title("💬 Nebula Chat Room")
    st.info("Chat စနစ်အား နောက်တစ်ဆင့်တွင် အပြည့်အဝ ထည့်သွင်းပေးပါမည်။")
    st.write(f"Logged in as: {st.session_state.user['username']}")
