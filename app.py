import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
import random
import smtplib
import ssl
from email.message import EmailMessage

# --- PAGE CONFIG ---
st.set_page_config(page_title="Nebula Messenger", page_icon="🌌")

# --- DATABASE CONNECTION ---
conn = st.connection("gsheets", type=GSheetsConnection)

# --- CSS ---
st.markdown("""
<style>
    .stApp { background: radial-gradient(circle at top, #1a0b2e, #09090b); color: white; }
    .glass-card { background: rgba(255, 255, 255, 0.05); padding: 25px; border-radius: 15px; border: 1px solid rgba(255,255,255,0.1); }
</style>
""", unsafe_allow_html=True)

# --- OTP FUNCTION (With Detailed Error Feedback) ---
def send_otp(target_email):
    otp = str(random.randint(100000, 999999))
    try:
        sender = st.secrets["GMAIL_USER"].strip()
        pw = st.secrets["GMAIL_PASS"].strip().replace(" ", "")
        
        msg = EmailMessage()
        msg.set_content(f"Nebula Chat OTP Code: {otp}")
        msg['Subject'] = 'Verification Code'
        msg['From'] = sender
        msg['To'] = target_email
        
        context = ssl.create_default_context()
        with smtplib.SMTP_SSL("smtp.gmail.com", 465, context=context) as server:
            server.login(sender, pw)
            server.send_message(msg)
            return otp
    except Exception as e:
        # ဘာကြောင့် OTP ပို့မရလဲဆိုတာကို ပြပေးမယ်
        st.error(f"OTP ပို့လို့မရပါ- {str(e)}")
        return None

# --- NAVIGATION ---
if "page" not in st.session_state: st.session_state.page = "welcome"

if st.session_state.page == "welcome":
    st.title("🌌 Nebula Messenger")
    if st.button("Get Started", use_container_width=True):
        st.session_state.page = "auth_choice"
        st.rerun()

elif st.session_state.page == "auth_choice":
    if st.button("Sign In (Login)", use_container_width=True):
        st.session_state.page = "login"
        st.rerun()
    if st.button("Sign Up (New Account)", use_container_width=True):
        st.session_state.page = "signup"
        st.rerun()

elif st.session_state.page == "signup":
    st.subheader("📝 Sign Up")
    email = st.text_input("Gmail Address")
    
    # OTP ပို့ပြီး/မပြီး အခြေအနေကို စစ်ဆေးခြင်း
    if "otp_sent" not in st.session_state:
        if st.button("Send OTP"):
            if email:
                with st.spinner("OTP ပို့နေသည်..."):
                    res = send_otp(email)
                    if res:
                        st.session_state.gen_otp = res
                        st.session_state.otp_sent = True
                        st.success("OTP ပို့ပြီးပါပြီ။ Gmail ကို စစ်ဆေးပါ။")
                        time_to_wait = 2 # စာသားပြဖို့ ခဏစောင့်မယ်
                        st.rerun()
            else:
                st.warning("Email အရင်ရိုက်ပါ။")
    else:
        # OTP ပို့ပြီးမှ ပေါ်လာမည့် input များ
        u_otp = st.text_input("Enter OTP Code")
        u_id = st.text_input("Username (@id)")
        d_name = st.text_input("Display Name")
        pw = st.text_input("Password", type="password")
        
        if st.button("Register Account"):
            if u_otp == st.session_state.gen_otp:
                try:
                    df = conn.read()
                    new_user = pd.DataFrame([{"email": email, "username": u_id, "display_name": d_name, "password": pw}])
                    updated_df = pd.concat([df, new_user], ignore_index=True)
                    conn.update(data=updated_df)
                    st.success("Registration အောင်မြင်ပါသည်။ Login ဝင်ပါ။")
                    st.session_state.page = "login"
                    del st.session_state.otp_sent # OTP status ကို reset ချမယ်
                    st.rerun()
                except Exception as e:
                    st.error(f"Database Error: {e}")
            else:
                st.error("OTP ကုဒ် မှားယွင်းနေပါသည်။")

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
        else:
            st.error("Username သို့မဟုတ် Password မှားနေပါသည်။")

elif st.session_state.page == "main_chat":
    st.success(f"Welcome {st.session_state.user['display_name']}!")
    if st.button("Logout"):
        st.session_state.page = "welcome"
        st.rerun()
