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
# Sheet link ကို တိုက်ရိုက်သတ်မှတ်ပေးခြင်းဖြင့် Error ကို လျှော့ချပါမယ်
SHEET_URL = "https://docs.google.com/spreadsheets/d/1aQvBwZ-ucJNlGNFiuS5ep60mvD5ezWzqOM2g0ZOH6S0/edit?usp=sharing"

conn = st.connection("gsheets", type=GSheetsConnection)

# --- CSS STYLING ---
st.markdown("""
<style>
    .stApp { background: radial-gradient(circle at top, #1a0b2e, #09090b); color: white; }
    .glass-card {
        background: rgba(255, 255, 255, 0.05); backdrop-filter: blur(15px);
        border-radius: 20px; padding: 30px; border: 1px solid rgba(255, 255, 255, 0.1);
    }
</style>
""", unsafe_allow_html=True)

# --- OTP FUNCTION ---
def send_otp(target_email):
    otp = str(random.randint(100000, 999999))
    try:
        sender = st.secrets["GMAIL_USER"].strip()
        pw = st.secrets["GMAIL_PASS"].strip().replace(" ", "")
        msg = EmailMessage()
        msg.set_content(f"Nebula Chat OTP Code: {otp}")
        msg['Subject'] = 'Account Verification'
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

# --- APP FLOW ---
if "page" not in st.session_state: st.session_state.page = "welcome"

if st.session_state.page == "welcome":
    st.markdown("<h1 style='text-align:center;'>🌌 Nebula Messenger</h1>", unsafe_allow_html=True)
    if st.button("စတင်အသုံးပြုမည်", use_container_width=True):
        st.session_state.page = "auth_choice"
        st.rerun()

elif st.session_state.page == "auth_choice":
    st.markdown("<div class='glass-card'>", unsafe_allow_html=True)
    if st.button("Sign In (Login)", use_container_width=True):
        st.session_state.page = "login"
        st.rerun()
    st.write("")
    if st.button("Sign Up (အကောင့်ဖွင့်ရန်)", use_container_width=True):
        st.session_state.page = "signup"
        st.rerun()
    st.markdown("</div>", unsafe_allow_html=True)

elif st.session_state.page == "signup":
    st.subheader("📝 Sign Up")
    email = st.text_input("Gmail")
    
    if "otp_sent" not in st.session_state:
        if st.button("Send OTP"):
            if "@gmail.com" in email:
                res = send_otp(email)
                if res:
                    st.session_state.gen_otp, st.session_state.otp_sent = res, True
                    st.success("OTP ပို့ပြီးပါပြီ။")
                    st.rerun()
    else:
        u_otp = st.text_input("Enter OTP")
        u_id = st.text_input("Username")
        d_name = st.text_input("Display Name")
        pw = st.text_input("Password", type="password")
        
        if st.button("Register Account"):
            if u_otp == st.session_state.gen_otp:
                try:
                    # Database ဖတ်ခြင်း
                    df = conn.read(spreadsheet=SHEET_URL)
                    
                    # Data အသစ်ထည့်ခြင်း
                    new_row = pd.DataFrame([{"email": email, "username": u_id, "display_name": d_name, "password": pw}])
                    updated_df = pd.concat([df, new_row], ignore_index=True)
                    
                    # Database အား Update လုပ်ခြင်း
                    conn.update(spreadsheet=SHEET_URL, data=updated_df)
                    
                    st.success("အောင်မြင်ပါပြီ။ Login ဝင်ပါ။")
                    time.sleep(2)
                    st.session_state.page = "login"
                    del st.session_state.otp_sent
                    st.rerun()
                except Exception as e:
                    st.error(f"Database Error: {e}")
            else: st.error("OTP မှားနေပါသည်။")

elif st.session_state.page == "login":
    st.subheader("🔐 Login")
    l_user = st.text_input("Username")
    l_pass = st.text_input("Password", type="password")
    
    if st.button("Login"):
        data = conn.read(spreadsheet=SHEET_URL)
        # username column ရှိမရှိ စစ်ဆေးခြင်း
        if 'username' in data.columns:
            user_row = data[data['username'] == l_user]
            if not user_row.empty and str(user_row.iloc[0]['password']) == l_pass:
                st.session_state.user = user_row.iloc[0].to_dict()
                st.session_state.page = "chat"
                st.rerun()
            else: st.error("မှားယွင်းနေပါသည်။")
        else: st.error("Database Error: Column headers are missing in Google Sheet.")

elif st.session_state.page == "chat":
    st.title("💬 Global Chat")
    st.sidebar.write(f"Logged in as: {st.session_state.user['display_name']}")
    if st.sidebar.button("Logout"):
        st.session_state.page = "welcome"
        st.rerun()
    st.chat_input("စာရိုက်ပါ...")
