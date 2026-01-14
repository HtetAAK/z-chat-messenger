import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
import datetime
import time

# --- PAGE SETUP ---
st.set_page_config(page_title="Nebula All-in-One", page_icon="🌌", layout="wide")

# --- DATABASE CONNECTION ---
SHEET_URL = "https://docs.google.com/spreadsheets/d/1aQvBwZ-ucJNlGNFiuS5ep60mvD5ezWzqOM2g0ZOH6S0/edit?usp=sharing"
conn = st.connection("gsheets", type=GSheetsConnection)

# --- CSS STYLING ---
st.markdown("""
<style>
    .stApp { background: #0f172a; color: white; }
    .msg-row { display: flex; width: 100%; margin-bottom: 12px; }
    .sent { justify-content: flex-end; }
    .received { justify-content: flex-start; }
    .bubble { max-width: 70%; padding: 12px; border-radius: 18px; font-size: 14px; }
    .sent .bubble { background: #7c3aed; color: white; border-bottom-right-radius: 2px; }
    .received .bubble { background: #1e293b; color: white; border-bottom-left-radius: 2px; border: 1px solid #334155; }
    .sender-tag { font-size: 10px; color: #94a3b8; margin-bottom: 3px; }
    .glass-card { background: rgba(255, 255, 255, 0.05); border-radius: 15px; padding: 25px; border: 1px solid rgba(255,255,255,0.1); }
</style>
""", unsafe_allow_html=True)

# --- APP NAVIGATION ---
if "page" not in st.session_state:
    st.session_state.page = "welcome"

# --- 1. WELCOME PAGE ---
if st.session_state.page == "welcome":
    st.markdown("<div style='text-align:center; padding-top:50px;'>", unsafe_allow_html=True)
    st.title("🌌 Nebula Messenger")
    st.write("ကြိုဆိုပါတယ်! အခုပဲ စတင်စကားပြောလိုက်ပါ။")
    if st.button("ရှေ့ဆက်မည်", use_container_width=True):
        st.session_state.page = "auth_choice"
        st.rerun()
    st.markdown("</div>", unsafe_allow_html=True)

# --- 2. AUTH CHOICE ---
elif st.session_state.page == "auth_choice":
    st.markdown("<div class='glass-card' style='max-width:400px; margin:auto;'>", unsafe_allow_html=True)
    st.subheader("စတင်အသုံးပြုရန်")
    if st.button("Login ဝင်ရန်", use_container_width=True):
        st.session_state.page = "login"
        st.rerun()
    st.write("")
    if st.button("အကောင့်သစ်ဖွင့်ရန်", use_container_width=True):
        st.session_state.page = "signup"
        st.rerun()
    st.markdown("</div>", unsafe_allow_html=True)

# --- 3. LOGIN PAGE ---
elif st.session_state.page == "login":
    st.markdown("<div class='glass-card' style='max-width:400px; margin:auto;'>", unsafe_allow_html=True)
    st.subheader("🔐 Login")
    l_user = st.text_input("Username")
    l_pass = st.text_input("Password", type="password")
    if st.button("Login", use_container_width=True):
        data = conn.read(spreadsheet=SHEET_URL, worksheet="Sheet1", ttl=0)
        user_match = data[data['username'].astype(str) == str(l_user)]
        if not user_match.empty and str(user_match.iloc[0]['password']) == str(l_pass):
            st.session_state.user = user_match.iloc[0].to_dict()
            st.session_state.page = "chat_room"
            st.session_state.chat_mode = "Global"
            st.rerun()
        else: st.error("အချက်အလက် မှားယွင်းနေပါသည်။")
    if st.button("Back"):
        st.session_state.page = "auth_choice"
        st.rerun()
    st.markdown("</div>", unsafe_allow_html=True)

# --- 4. SIGNUP PAGE ---
elif st.session_state.page == "signup":
    st.markdown("<div class='glass-card' style='max-width:400px; margin:auto;'>", unsafe_allow_html=True)
    st.subheader("📝 Sign Up")
    email = st.text_input("Gmail Address")
    u_id = st.text_input("Username")
    d_name = st.text_input("Display Name")
    pw = st.text_input("Password", type="password")
    if st.button("Register", use_container_width=True):
        df = conn.read(spreadsheet=SHEET_URL, worksheet="Sheet1", ttl=0)
        new_user = pd.DataFrame([{"email": email, "username": u_id, "display_name": d_name, "password": pw, "profile_pic": ""}])
        conn.update(spreadsheet=SHEET_URL, worksheet="Sheet1", data=pd.concat([df, new_user], ignore_index=True))
        st.success("အကောင့်ဖွင့်ခြင်း အောင်မြင်ပါသည်။")
        st.session_state.page = "login"
        st.rerun()
    if st.button("Back"):
        st.session_state.page = "auth_choice"
        st.rerun()
    st.markdown("</div>", unsafe_allow_html=True)

# --- 5. MAIN CHAT SYSTEM ---
elif st.session_state.page == "chat_room":
    # Sidebar: User List & Navigation
    with st.sidebar:
        st.title("🌌 Nebula")
        st.write(f"Logged in as: **{st.session_state.user['display_name']}**")
        st.divider()
        if st.button("🌐 Global Chat", use_container_width=True):
            st.session_state.chat_mode = "Global"
            st.rerun()
        
        st.subheader("👥 Contacts")
        users_df = conn.read(spreadsheet=SHEET_URL, worksheet="Sheet1", ttl=0).dropna(subset=['display_name'])
        for _, u in users_df.iterrows():
            if str(u['display_name']) != str(st.session_state.user['display_name']):
                if st.button(f"💬 {u['display_name']}", key=f"user_{u['username']}", use_container_width=True):
                    st.session_state.chat_mode = "Private"
                    st.session_state.chat_with = u['display_name']
                    st.rerun()
        
        st.divider()
        if st.button("Logout"):
            del st.session_state.user
            st.session_state.page = "welcome"
            st.rerun()

    # Chat Room Content
    ws = "Sheet2" if st.session_state.chat_mode == "Global" else "Sheet3"
    st.subheader("🌐 Global Chat" if st.session_state.chat_mode == "Global" else f"💬 Chat with {st.session_state.chat_with}")

    try:
        df = conn.read(spreadsheet=SHEET_URL, worksheet=ws, ttl=0).fillna("")
        if st.session_state.chat_mode == "Private":
            me, other = st.session_state.user['display_name'], st.session_state.chat_with
            display_df = df[((df['sender'] == me) & (df['receiver'] == other)) | ((df['sender'] == other) & (df['receiver'] == me))]
        else:
            display_df = df.tail(20)

        for _, row in display_df.iterrows():
            is_me = str(row['sender']) == str(st.session_state.user['display_name'])
            st.markdown(f'<div class="msg-row {"sent" if is_me else "received"}"><div><div class="sender-tag">{row["sender"]}</div><div class="bubble">{row["message"]}</div></div></div>', unsafe_allow_html=True)
    except: st.info("စကားပြောခြင်း မရှိသေးပါ။")

    msg = st.chat_input("စာရိုက်ပါ...")
    if msg:
        new_row = {"sender": st.session_state.user['display_name'], "message": msg, "timestamp": datetime.datetime.now().strftime("%I:%M %p")}
        if st.session_state.chat_mode == "Private": new_row["receiver"] = st.session_state.chat_with
        all_df = conn.read(spreadsheet=SHEET_URL, worksheet=ws, ttl=0)
        conn.update(spreadsheet=SHEET_URL, worksheet=ws, data=pd.concat([all_df, pd.DataFrame([new_row])], ignore_index=True))
        st.rerun()

    time.sleep(1)
    st.rerun()
