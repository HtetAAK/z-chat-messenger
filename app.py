import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
import random
import smtplib
from email.message import EmailMessage

# --- PAGE SETUP ---
st.set_page_config(page_title="Nebula Chat", page_icon="🌌")

# --- DATABASE CONNECTION ---
conn = st.connection("gsheets", type=GSheetsConnection)

# --- CSS DESIGN ---
st.markdown("""
<style>
    .stApp { background: radial-gradient(circle at top, #2D0B5A 0%, #0E1117 100%); color: white; }
    .glass-card {
        background: rgba(255, 255, 255, 0.05); backdrop-filter: blur(15px);
        border-radius: 20px; padding: 30px; border: 1px solid rgba(255, 255, 255, 0.1);
    }
    .stButton>button {
        background: linear-gradient(90deg, #8A2BE2 0%, #D02BE2 100%);
        color: white; border-radius: 12px; border: none; width: 100%; height: 3.5em; font-weight: bold;
    }
</style>
""", unsafe_allow_html=True)

# --- FUNCTIONS ---
def send_otp(email, user, pw):
    otp = str(random.randint(100000, 999999))
    msg = EmailMessage()
    msg.set_content(f"Nebula Chat OTP Code: {otp}")
    msg['Subject'] = 'Nebula Verification'
    msg['From'] = user
    msg['To'] = email
    with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
        smtp.login(user, pw)
        smtp.send_message(msg)
    return otp

# --- APP FLOW ---
if "page" not in st.session_state: st.session_state.page = "welcome"

# 1. Welcome
if st.session_state.page == "welcome":
    st.markdown("<br><h1 style='text-align:center;'>🌌 Nebula Chat</h1>", unsafe_allow_html=True)
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
    st.subheader("Create Account")
    email = st.text_input("Gmail Address")
    if "otp_sent" not in st.session_state:
        if st.button("Send OTP"):
            st.session_state.gen_otp = send_otp(email, st.secrets["GMAIL_USER"], st.secrets["GMAIL_PASS"])
            st.session_state.otp_sent = True
            st.rerun()
    else:
        u_otp = st.text_input("OTP Code")
        u_name = st.text_input("Username")
        d_name = st.text_input("Display Name")
        pw = st.text_input("Password", type="password")
        if st.button("Register"):
            if u_otp == st.session_state.gen_otp:
                # Save to Google Sheet
                new_data = pd.DataFrame([{"email": email, "username": u_name, "display_name": d_name, "password": pw}])
                existing_data = conn.read()
                updated_data = pd.concat([existing_data, new_data], ignore_index=True)
                conn.update(data=updated_data)
                st.success("Registration Complete!")
                st.session_state.page = "login"
                st.rerun()

# 4. Login
elif st.session_state.page == "login":
    st.subheader("Login")
    l_user = st.text_input("Username")
    l_pass = st.text_input("Password", type="password")
    if st.button("Login"):
        data = conn.read()
        user_row = data[data['username'] == l_user]
        if not user_row.empty and str(user_row.iloc[0]['password']) == l_pass:
            st.session_state.user = user_row.iloc[0].to_dict()
            st.session_state.page = "chat"
            st.rerun()
        else: st.error("မှားယွင်းနေပါသည်။")

# 5. Chat Interface
elif st.session_state.page == "chat":
    st.title(f"Welcome, {st.session_state.user['display_name']}!")
    st.write("စကားပြောခန်းကို မကြာမီ ထပ်မံဖြည့်စွက်ပေးပါမည်။")
