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
# Connection အမှားမတက်အောင် try-except နဲ့ စစ်ပါမယ်
try:
    conn = st.connection("gsheets", type=GSheetsConnection)
except Exception as e:
    st.error("Database ချိတ်ဆက်မှု Error တက်နေပါသည်။ Secrets ထဲက Format ကို ပြန်စစ်ပါ။")
    st.stop()

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

# --- APP NAVIGATION ---
if "page" not in st.session_state: st.session_state.page = "welcome"

# 1. Welcome
if st.session_state.page == "welcome":
    st.markdown("<h1 style='text-align:center;'>🌌 Nebula Messenger</h1>", unsafe_allow_html=True)
    if st.button("စတင်အသုံးပြုမည်", use_container_width=True):
        st.session_state.page = "auth_choice"
        st.rerun()

# 2. Auth Choice
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

# 3. Sign Up
elif st.session_state.page == "signup":
    st.subheader("📝 Sign Up")
    email = st.text_input("Gmail")
    
    if "otp_sent" not in st.session_state:
        if st.button("Send OTP"):
            if "@gmail.com" in email:
                with st.spinner("OTP ပို့နေသည်..."):
                    res = send_otp(email)
                    if res:
                        st.session_state.gen_otp, st.session_state.otp_sent = res, True
                        st.success("OTP ပို့ပြီးပါပြီ။ Gmail ကိုစစ်ပါ။")
                        st.rerun()
            else: st.error("Gmail အမှန်ရိုက်ပါ။")
    else:
        u_otp = st.text_input("Enter OTP")
        u_id = st.text_input("Username")
        d_name = st.text_input("Display Name")
        pw = st.text_input("Password", type="password")
        
        if st.button("Register Account"):
            if u_otp == st.session_state.gen_otp:
                try:
                    df = conn.read()
                    new_user = pd.DataFrame([{"email": email, "username": u_id, "display_name": d_name, "password": pw}])
                    updated_df = pd.concat([df, new_user], ignore_index=True)
                    conn.update(data=updated_df)
                    st.success("အောင်မြင်ပါပြီ။ Login ဝင်ပါ။")
                    time.sleep(2)
                    st.session_state.page = "login"
                    del st.session_state.otp_sent
                    st.rerun()
                except Exception as e:
                    st.error(f"Database Error: {e}")
            else: st.error("OTP မှားနေပါသည်။")

# 4. Login
elif st.session_state.page == "login":
    st.subheader("🔐 Login")
    l_user = st.text_input("Username")
    l_pass = st.text_input("Password", type="password")
    
    if st.button("Login"):
        data = conn.read()
        user_row = data[data['username'] == l_user]
        if not user_row.empty and str(user_row.iloc[0]['password']) == l_pass:
            st.session_state.user = user_row.iloc[0].to_dict()
            st.session_state.page = "chat_room"
            st.rerun()
        else: st.error("မှားယွင်းနေပါသည်။")

# 5. Global Chat Room (Basic Messaging Added)
elif st.session_state.page == "chat_room":
    st.title("💬 Global Chat")
    st.sidebar.write(f"Logged in as: {st.session_state.user['display_name']}")
    if st.sidebar.button("Logout"):
        st.session_state.page = "welcome"
        st.rerun()

    # Chat messages များကို ယာယီပြသခြင်း (နောက်ပိုင်းတွင် DB ထဲသိမ်းပါမည်)
    st.info("Messaging system is now active.")
    chat_input = st.chat_input("စာရိုက်ပါ...")
    if chat_input:
        st.chat_message("user").write(f"**{st.session_state.user['display_name']}:** {chat_input}")
