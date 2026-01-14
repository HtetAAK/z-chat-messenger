import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
import random
import smtplib
import re
from email.message import EmailMessage

# --- PAGE CONFIG ---
st.set_page_config(page_title="Nebula Chat", page_icon="🌌", layout="centered")

# --- DATABASE CONNECTION ---
# Google Sheet နဲ့ ချိတ်ဆက်ခြင်း
conn = st.connection("gsheets", type=GSheetsConnection)

# --- CSS STYLING (Glassmorphism UI) ---
st.markdown("""
<style>
    .stApp { background: radial-gradient(circle at top, #2D0B5A 0%, #0E1117 100%); color: white; }
    .glass-card {
        background: rgba(255, 255, 255, 0.05); backdrop-filter: blur(15px);
        border-radius: 20px; padding: 30px; border: 1px solid rgba(255, 255, 255, 0.1);
        margin-bottom: 20px;
    }
    .stButton>button {
        background: linear-gradient(90deg, #8A2BE2 0%, #D02BE2 100%);
        color: white; border-radius: 12px; border: none; width: 100%; height: 3.5em; font-weight: bold;
    }
    .stTextInput>div>div>input {
        background-color: rgba(255, 255, 255, 0.07) !important;
        color: white !important; border-radius: 10px !important;
    }
</style>
""", unsafe_allow_html=True)

# --- FUNCTIONS ---
def send_otp(target_email):
    """Gmail OTP ပို့ပေးသော Function (TLS Port 587 ကိုသုံးသည်)"""
    otp = str(random.randint(100000, 999999))
    user_email = st.secrets["GMAIL_USER"]
    # App Password ထဲက space တွေကို အလိုအလျောက် ဖြုတ်ပေးမည်
    app_password = st.secrets["GMAIL_PASS"].replace(" ", "")
    
    msg = EmailMessage()
    msg.set_content(f"Nebula Chat အတွက် သင်၏ OTP ကုဒ်မှာ {otp} ဖြစ်ပါသည်။")
    msg['Subject'] = 'Nebula Verification'
    msg['From'] = user_email
    msg['To'] = target_email
    
    try:
        # SMTP Server Setup
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls() # TLS လုံခြုံရေး စတင်ခြင်း
        server.login(user_email, app_password)
        server.send_message(msg)
        server.quit()
        return otp
    except Exception as e:
        st.error(f"Error: Gmail Authentication မအောင်မြင်ပါ။ Secrets ထဲက Password ကို ပြန်စစ်ပါ။ ({e})")
        return None

# --- APP NAVIGATION ---
if "page" not in st.session_state: st.session_state.page = "welcome"

# 1. Welcome Screen
if st.session_state.page == "welcome":
    st.markdown("<br><h1 style='text-align:center;'>🌌 Nebula Chat</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align:center;'>Secure & Fast Messaging System</p>", unsafe_allow_html=True)
    st.write("---")
    if st.button("စတင်အသုံးပြုမည်"):
        st.session_state.page = "auth_choice"
        st.rerun()

# 2. Auth Choice
elif st.session_state.page == "auth_choice":
    st.markdown("<div class='glass-card'>", unsafe_allow_html=True)
    st.subheader("Login သို့မဟုတ် Sign Up ရွေးချယ်ပါ")
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
    st.subheader("📝 အကောင့်အသစ်ဖွင့်ရန်")
    email = st.text_input("Gmail Address")
    
    if "otp_sent" not in st.session_state:
        if st.button("Send OTP"):
            if "@gmail.com" in email:
                res = send_otp(email)
                if res:
                    st.session_state.gen_otp = res
                    st.session_state.otp_sent = True
                    st.success("OTP ကုဒ်ကို သင့် Gmail ထဲ ပို့လိုက်ပါပြီ။")
                    st.rerun()
            else: st.error("မှန်ကန်သော Gmail လိပ်စာ ရိုက်ထည့်ပါ။")
    else:
        u_otp = st.text_input("Enter 6-digit OTP")
        u_name = st.text_input("Username (ရှာဖွေရလွယ်ကူရန်)")
        d_name = st.text_input("Display Name (Chat တွင် ပြမည့်အမည်)")
        pw = st.text_input("Password", type="password")
        
        if st.button("အကောင့်ဖွင့်မည်"):
            if u_otp == st.session_state.gen_otp:
                try:
                    # Google Sheet ထဲသို့ Data အသစ်ထည့်ခြင်း
                    new_user = pd.DataFrame([{"email": email, "username": u_name, "display_name": d_name, "password": pw}])
                    existing_data = conn.read()
                    updated_data = pd.concat([existing_data, new_user], ignore_index=True)
                    conn.update(data=updated_data)
                    st.success("Registration အောင်မြင်ပါသည်။ ယခု Login ဝင်နိုင်ပါပြီ။")
                    st.session_state.page = "login"
                    # Reset OTP state
                    del st.session_state.otp_sent
                    st.rerun()
                except Exception as e:
                    st.error(f"Database Error: {e}")
            else: st.error("OTP ကုဒ် မှားယွင်းနေပါသည်။")
    st.markdown("</div>", unsafe_allow_html=True)

# 4. Login
elif st.session_state.page == "login":
    st.markdown("<div class='glass-card'>", unsafe_allow_html=True)
    st.subheader("🔐 Login")
    l_user = st.text_input("Username")
    l_pass = st.text_input("Password", type="password")
    
    if st.button("Continue"):
        data = conn.read()
        user_row = data[data['username'] == l_user]
        if not user_row.empty and str(user_row.iloc[0]['password']) == l_pass:
            st.session_state.user = user_row.iloc[0].to_dict()
            st.session_state.page = "main_chat"
            st.rerun()
        else: st.error("Username သို့မဟုတ် Password မှားယွင်းနေပါသည်။")
    st.markdown("</div>", unsafe_allow_html=True)

# 5. Main Chat
elif st.session_state.page == "main_chat":
    st.sidebar.title(f"Hi, {st.session_state.user['display_name']}!")
    if st.sidebar.button("Logout"):
        st.session_state.page = "welcome"
        st.rerun()
    
    st.write("### 💬 Nebula Chat Room")
    st.info("Chat စနစ်အား မကြာမီ Update ပြုလုပ်ပေးပါမည်။")
