import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
import datetime
import time
import random
import smtplib
import ssl
from email.message import EmailMessage

# --- PAGE SETUP ---
st.set_page_config(page_title="Nebula Global Chat", page_icon="🌌", layout="centered")

# --- DATABASE CONNECTION ---
SHEET_URL = "https://docs.google.com/spreadsheets/d/1aQvBwZ-ucJNlGNFiuS5ep60mvD5ezWzqOM2g0ZOH6S0/edit?usp=sharing"

# Connection ကို Error မတက်အောင် သီးသန့် function နဲ့ ချိတ်ပါမယ်
def get_connection():
    try:
        return st.connection("gsheets", type=GSheetsConnection)
    except Exception as e:
        st.error(f"Connection Error: {e}")
        return None

conn = get_connection()

# --- CSS STYLING ---
st.markdown("""
<style>
    .stApp { background: #09090b; color: white; }
    .chat-bubble { background: rgba(255, 255, 255, 0.1); padding: 10px 15px; border-radius: 15px; margin-bottom: 10px; border-left: 5px solid #8A2BE2; }
    .glass-card { background: rgba(255, 255, 255, 0.05); backdrop-filter: blur(10px); border-radius: 15px; padding: 20px; }
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
        st.error(f"Gmail Error: {e}")
        return None

# --- APP FLOW ---
if "page" not in st.session_state: 
    st.session_state.page = "welcome"

# 1. Welcome Page
if st.session_state.page == "welcome":
    st.markdown("<h1 style='text-align:center;'>🌌 Nebula Messenger</h1>", unsafe_allow_html=True)
    st.write("---")
    if st.button("စတင်အသုံးပြုမည်", use_container_width=True):
        st.session_state.page = "auth_choice"
        st.rerun()

# 2. Auth Choice
elif st.session_state.page == "auth_choice":
    st.markdown("<div class='glass-card'>", unsafe_allow_html=True)
    if st.button("Login ဝင်ရန်", use_container_width=True):
        st.session_state.page = "login"
        st.rerun()
    st.write("")
    if st.button("အကောင့်အသစ်ဖွင့်ရန်", use_container_width=True):
        st.session_state.page = "signup"
        st.rerun()
    st.markdown("</div>", unsafe_allow_html=True)

# 3. Signup Page
elif st.session_state.page == "signup":
    st.subheader("📝 Sign Up")
    email = st.text_input("Gmail")
    if "otp_sent" not in st.session_state:
        if st.button("OTP ပို့ရန်"):
            res = send_otp(email)
            if res:
                st.session_state.gen_otp, st.session_state.otp_sent = res, True
                st.success("OTP ပို့ပြီးပါပြီ။")
                st.rerun()
    else:
        u_otp = st.text_input("OTP Code")
        u_id = st.text_input("Username")
        d_name = st.text_input("Display Name")
        pw = st.text_input("Password", type="password")
        if st.button("Register Account"):
            if u_otp == st.session_state.gen_otp:
                try:
                    df = conn.read(spreadsheet=SHEET_URL, worksheet="Sheet1", ttl=0)
                    new_row = pd.DataFrame([{"email": email, "username": u_id, "display_name": d_name, "password": pw}])
                    updated_df = pd.concat([df, new_row], ignore_index=True)
                    conn.update(spreadsheet=SHEET_URL, worksheet="Sheet1", data=updated_df)
                    st.success("အောင်မြင်ပါပြီ။")
                    st.session_state.page = "login"
                    del st.session_state.otp_sent
                    st.rerun()
                except Exception as e:
                    st.error(f"Database Error (Sheet1): {e}")

# 4. Login Page
elif st.session_state.page == "login":
    st.subheader("🔐 Login")
    l_user = st.text_input("Username")
    l_pass = st.text_input("Password", type="password")
    if st.button("Login"):
        try:
            data = conn.read(spreadsheet=SHEET_URL, worksheet="Sheet1", ttl=0)
            user_match = data[data['username'].astype(str) == str(l_user)]
            if not user_match.empty and str(user_match.iloc[0]['password']) == str(l_pass):
                st.session_state.user = user_match.iloc[0].to_dict()
                st.session_state.page = "chat_room"
                st.rerun()
            else: 
                st.error("အချက်အလက်မှားနေပါသည်။")
        except Exception as e:
            st.error(f"Database Error (Login): {e}")

# 5. Global Chat Room
elif st.session_state.page == "chat_room":
    st.title("💬 Global Chat")
    st.sidebar.write(f"Logged in as: **{st.session_state.user['display_name']}**")
    if st.sidebar.button("Logout"):
        st.session_state.page = "welcome"
        st.rerun()

    # Chat ဖတ်ခြင်း (Error ဖြစ်ရင် ဘာမှမပြဘဲ နေပါမယ်)
    try:
        messages_df = conn.read(spreadsheet=SHEET_URL, worksheet="Sheet2", ttl=0)
    except Exception as e:
        messages_df = pd.DataFrame(columns=["sender", "message", "timestamp"])
        st.warning("Chat history ကို ဖတ်၍မရသေးပါ။ Sheet2 ကို စစ်ဆေးပါ။")

    # စာပြသခြင်း
    for index, row in messages_df.tail(15).iterrows():
        st.markdown(f'<div class="chat-bubble"><b>{row["sender"]}</b>: {row["message"]}</div>', unsafe_allow_html=True)

    # စာပို့ခြင်း
    user_msg = st.chat_input("စာရိုက်ပါ...")
    if user_msg:
        try:
            new_msg = pd.DataFrame([{"sender": st.session_state.user['display_name'], "message": user_msg, "timestamp": datetime.datetime.now().strftime("%H:%M:%S")}])
            updated_chat = pd.concat([messages_df, new_msg], ignore_index=True)
            conn.update(spreadsheet=SHEET_URL, worksheet="Sheet2", data=updated_chat)
            st.rerun()
        except Exception as e:
            st.error(f"စာပို့၍မရပါ: {e}")

    # Auto refresh (Auto rerun လုပ်တဲ့အခါ Error တက်တတ်လို့ ခဏပိတ်ထားနိုင်ပါတယ်)
    # time.sleep(5)
    # st.rerun()
