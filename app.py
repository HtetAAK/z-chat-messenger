import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
import random
import smtplib
import ssl
from email.message import EmailMessage

# --- PAGE CONFIG ---
st.set_page_config(page_title="Nebula Chat", page_icon="🌌")

# --- DATABASE CONNECTION ---
conn = st.connection("gsheets", type=GSheetsConnection)

# --- CSS STYLING ---
st.markdown("""
<style>
    .stApp { background: radial-gradient(circle at top, #2D0B5A 0%, #0E1117 100%); color: white; }
    .glass-card {
        background: rgba(255, 255, 255, 0.05); backdrop-filter: blur(15px);
        border-radius: 20px; padding: 25px; border: 1px solid rgba(255, 255, 255, 0.1);
    }
    .stButton>button {
        background: linear-gradient(90deg, #8A2BE2 0%, #D02BE2 100%);
        color: white; border-radius: 12px; height: 3em; font-weight: bold; width: 100%;
    }
</style>
""", unsafe_allow_html=True)

# --- EMAIL FUNCTION (FIXED) ---
def send_otp(target_email):
    otp = str(random.randint(100000, 999999))
    sender_email = st.secrets["GMAIL_USER"].strip()
    # space များကို ဖယ်ရှားခြင်း
    app_password = st.secrets["GMAIL_PASS"].strip().replace(" ", "")
    
    msg = EmailMessage()
    msg.set_content(f"Nebula Chat OTP Code: {otp}")
    msg['Subject'] = 'Nebula Verification'
    msg['From'] = sender_email
    msg['To'] = target_email
    
    context = ssl.create_default_context()
    
    try:
        # SSL Port 465 ကို သုံးပြီး တိုက်ရိုက်ချိတ်ဆက်ခြင်း
        with smtplib.SMTP_SSL("smtp.gmail.com", 465, context=context) as server:
            server.login(sender_email, app_password)
            server.send_message(msg)
            return otp
    except Exception as e:
        st.error(f"Gmail Error: {e}")
        return None

# --- APP FLOW ---
if "page" not in st.session_state: st.session_state.page = "welcome"

# 1. Welcome
if st.session_state.page == "welcome":
    st.markdown("<h1 style='text-align:center;'>🌌 Nebula Chat</h1>", unsafe_allow_html=True)
    if st.button("စတင်အသုံးပြုမည်"):
        st.session_state.page = "auth_choice"
        st.rerun()

# 2. Auth Choice
elif st.session_state.page == "auth_choice":
    st.markdown("<div class='glass-card'>", unsafe_allow_html=True)
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
    st.subheader("📝 Sign Up")
    email = st.text_input("Gmail Address")
    
    if "otp_sent" not in st.session_state:
        if st.button("Send OTP Code"):
            if "@gmail.com" in email:
                with st.spinner("OTP ပို့နေသည်..."):
                    res = send_otp(email)
                    if res:
                        st.session_state.gen_otp = res
                        st.session_state.otp_sent = True
                        st.success("OTP ပို့ပြီးပါပြီ။")
                        st.rerun()
            else: st.error("Gmail အမှန် ထည့်ပေးပါ။")
    else:
        u_otp = st.text_input("OTP Code")
        u_name = st.text_input("Username")
        d_name = st.text_input("Display Name")
        pw = st.text_input("Password", type="password")
        
        if st.button("Register Account"):
            if u_otp == st.session_state.gen_otp:
                try:
                    new_user = pd.DataFrame([{"email": email, "username": u_name, "display_name": d_name, "password": pw}])
                    existing_data = conn.read()
                    updated_data = pd.concat([existing_data, new_user], ignore_index=True)
                    conn.update(data=updated_data)
                    st.success("Registration Success!")
                    st.session_state.page = "login"
                    del st.session_state.otp_sent
                    st.rerun()
                except Exception as e:
                    st.error(f"Sheet Error: {e}")
            else: st.error("OTP ကုဒ် မှားနေပါသည်။")

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
            st.session_state.page = "main_chat"
            st.rerun()
        else: st.error("အချက်အလက် မှားနေပါသည်။")

# 5. Main Chat Placeholder
elif st.session_state.page == "main_chat":
    st.sidebar.write(f"Logged in as: {st.session_state.user['display_name']}")
    if st.sidebar.button("Logout"):
        st.session_state.page = "welcome"
        st.rerun()
    st.write("### 💬 Nebula Global Chat Room")
    st.info("Chat စနစ်အား နောက်တစ်ဆင့်တွင် ထည့်သွင်းပေးပါမည်။")
