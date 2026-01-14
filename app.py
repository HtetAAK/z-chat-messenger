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
        color: white; border-radius: 12px; width: 100%; height: 3.5em; font-weight: bold;
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

# 1. Welcome
if st.session_state.page == "welcome":
    st.markdown("<h1 style='text-align:center;'>🌌 Nebula Messenger</h1>", unsafe_allow_html=True)
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
    if st.button("Sign Up (အကောင့်အသစ်ဖွင့်ရန်)"):
        st.session_state.page = "signup"
        st.rerun()
    st.markdown("</div>", unsafe_allow_html=True)

# 3. Sign Up
elif st.session_state.page == "signup":
    st.subheader("📝 အကောင့်အသစ်ဖွင့်ခြင်း")
    email = st.text_input("သင့် Gmail ကိုရိုက်ထည့်ပါ")
    
    if "otp_sent" not in st.session_state:
        if st.button("OTP ကုဒ်ပို့ရန်"):
            if "@gmail.com" in email:
                with st.spinner("OTP ပို့နေသည်..."):
                    res = send_otp(email)
                    if res:
                        st.session_state.gen_otp = res
                        st.session_state.otp_sent = True
                        st.success("OTP ပို့ပြီးပါပြီ။ Gmail ကိုစစ်ပါ။")
                        st.rerun()
            else: st.error("Gmail အမှန်ရိုက်ထည့်ပါ။")
    else:
        u_otp = st.text_input("OTP ကုဒ် ၆ လုံး")
        u_id = st.text_input("Username (ဥပမာ- arkar123)")
        d_name = st.text_input("Display Name (အမည်ရင်း)")
        pw = st.text_input("Password", type="password")
        
        if st.button("Register Account"):
            if u_otp == st.session_state.gen_otp:
                try:
                    df = conn.read()
                    # Username ရှိပြီးသားလားစစ်မယ်
                    if u_id in df['username'].values:
                        st.error("ဒီ Username က ရှိပြီးသားဖြစ်နေပါတယ်။ အခြားတစ်ခုပြောင်းပါ။")
                    else:
                        new_user = pd.DataFrame([{"email": email, "username": u_id, "display_name": d_name, "password": pw}])
                        updated_df = pd.concat([df, new_user], ignore_index=True)
                        conn.update(data=updated_df)
                        st.success("အကောင့်ဖွင့်ခြင်း အောင်မြင်ပါပြီ။")
                        time.sleep(2)
                        st.session_state.page = "login"
                        del st.session_state.otp_sent
                        st.rerun()
                except Exception as e:
                    st.error(f"Database Error: {e}")
            else: st.error("OTP ကုဒ် မှားနေပါသည်။")

# 4. Login
elif st.session_state.page == "login":
    st.subheader("🔐 Login ဝင်ရန်")
    l_user = st.text_input("Username")
    l_pass = st.text_input("Password", type="password")
    
    if st.button("Login"):
        data = conn.read()
        user_row = data[data['username'] == l_user]
        if not user_row.empty and str(user_row.iloc[0]['password']) == l_pass:
            st.session_state.user = user_row.iloc[0].to_dict()
            st.session_state.page = "chat"
            st.rerun()
        else: st.error("အချက်အလက် မှားယွင်းနေပါသည်။")
    
    if st.button("Back"):
        st.session_state.page = "auth_choice"
        st.rerun()

# 5. Global Chat
elif st.session_state.page == "chat":
    st.sidebar.title(f"🌌 {st.session_state.user['display_name']}")
    if st.sidebar.button("Logout"):
        del st.session_state.user
        st.session_state.page = "welcome"
        st.rerun()
    
    st.title("💬 Global Chat")
    st.write("Nebula Messenger မှ ကြိုဆိုပါတယ်။")
    
    # Message box
    chat_input = st.chat_input("စာရိုက်ရန်...")
    if chat_input:
        st.write(f"**သင်:** {chat_input}")
        st.toast("စာပို့ပြီးပါပြီ (History သိမ်းဆည်းရန် နောက်တစ်ဆင့်တွင် ပြုလုပ်မည်)")
