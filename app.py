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
# သင့် Sheet URL
SHEET_URL = "https://docs.google.com/spreadsheets/d/1aQvBwZ-ucJNlGNFiuS5ep60mvD5ezWzqOM2g0ZOH6S0/edit?usp=sharing"

# Connection တည်ဆောက်ခြင်း
conn = st.connection("gsheets", type=GSheetsConnection)

# --- CSS STYLING ---
st.markdown("""
<style>
    .stApp { background: radial-gradient(circle at top, #1a0b2e, #09090b); color: white; }
    .glass-card {
        background: rgba(255, 255, 255, 0.05); backdrop-filter: blur(15px);
        border-radius: 20px; padding: 30px; border: 1px solid rgba(255, 255, 255, 0.1);
    }
    .stButton>button {
        background: linear-gradient(90deg, #8A2BE2 0%, #D02BE2 100%);
        color: white; border-radius: 12px; border: none; width: 100%; height: 3em; font-weight: bold;
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

# 1. Welcome Screen
if st.session_state.page == "welcome":
    st.markdown("<h1 style='text-align:center;'>🌌 Nebula Messenger</h1>", unsafe_allow_html=True)
    if st.button("စတင်အသုံးပြုမည်", use_container_width=True):
        st.session_state.page = "auth_choice"
        st.rerun()

# 2. Choice Screen
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

# 3. Sign Up Screen
elif st.session_state.page == "signup":
    st.subheader("📝 Sign Up")
    email = st.text_input("Gmail")
    
    if "otp_sent" not in st.session_state:
        if st.button("OTP ပို့ရန်"):
            if "@gmail.com" in email:
                res = send_otp(email)
                if res:
                    st.session_state.gen_otp, st.session_state.otp_sent = res, True
                    st.success("OTP ပို့ပြီးပါပြီ။")
                    st.rerun()
            else: st.error("Gmail အမှန်ရိုက်ပါ။")
    else:
        u_otp = st.text_input("OTP ကုဒ်")
        u_id = st.text_input("Username (ဥပမာ- arkar123)")
        d_name = st.text_input("Display Name")
        pw = st.text_input("Password", type="password")
        
        if st.button("Register Account"):
            if u_otp == st.session_state.gen_otp:
                try:
                    # Database ဖတ်မယ် (Worksheet="Sheet1" ဟု အသေသတ်မှတ်ထားသည်)
                    df = conn.read(spreadsheet=SHEET_URL, worksheet="Sheet1", ttl=0)
                    
                    # Username စစ်မယ်
                    if u_id in df['username'].astype(str).values:
                        st.error("ဒီ Username ရှိပြီးသားပါ။ တခြားပြောင်းပါ။")
                    else:
                        new_row = pd.DataFrame([{"email": email, "username": u_id, "display_name": d_name, "password": pw}])
                        updated_df = pd.concat([df, new_row], ignore_index=True)
                        conn.update(spreadsheet=SHEET_URL, worksheet="Sheet1", data=updated_df)
                        st.success("အကောင့်ဖွင့်ခြင်း အောင်မြင်ပါပြီ။")
                        time.sleep(2)
                        st.session_state.page = "login"
                        del st.session_state.otp_sent
                        st.rerun()
                except Exception as e:
                    st.error(f"Database Error: {e}")
            else: st.error("OTP ကုဒ် မှားနေပါသည်။")

# 4. Login Screen
elif st.session_state.page == "login":
    st.subheader("🔐 Login")
    l_user = st.text_input("Username")
    l_pass = st.text_input("Password", type="password")
    
    if st.button("Login"):
        try:
            # ttl=0 ထည့်ခြင်းဖြင့် Cache မလုပ်ဘဲ Data အသစ်ကို အမြဲဖတ်ပါမယ်
            data = conn.read(spreadsheet=SHEET_URL, worksheet="Sheet1", ttl=0)
            
            # Username ရှိမရှိ စစ်ဆေးခြင်း
            user_match = data[data['username'].astype(str) == str(l_user)]
            
            if not user_match.empty:
                stored_pass = str(user_match.iloc[0]['password'])
                if stored_pass == str(l_pass):
                    st.session_state.user = user_match.iloc[0].to_dict()
                    st.session_state.page = "chat_room"
                    st.rerun()
                else: st.error("Password မှားယွင်းနေပါသည်။")
            else: st.error("Username ရှာမတွေ့ပါ။ အကောင့်အရင်ဖွင့်ပါ။")
        except Exception as e:
            st.error(f"Login Database Error: {e}")

# 5. Chat Room
elif st.session_state.page == "chat_room":
    st.success(f"Welcome {st.session_state.user['display_name']}!")
    if st.button("Logout"):
        st.session_state.page = "welcome"
        st.rerun()
