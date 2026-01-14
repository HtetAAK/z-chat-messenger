import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
import datetime
import time

# --- PAGE SETUP ---
st.set_page_config(page_title="Nebula Premium", page_icon="🌌", layout="wide")

# --- DATABASE CONNECTION ---
SHEET_URL = "https://docs.google.com/spreadsheets/d/1aQvBwZ-ucJNlGNFiuS5ep60mvD5ezWzqOM2g0ZOH6S0/edit?usp=sharing"
conn = st.connection("gsheets", type=GSheetsConnection)

# --- NAVIGATION FUNCTIONS ---
def change_page(page_name):
    st.session_state.page = page_name

# --- INITIAL STATE ---
if "page" not in st.session_state:
    st.session_state.page = "welcome"

# --- LUXURY CSS ---
st.markdown("""
<style>
    .stApp { background-color: #0b0e14; color: #e1e1e1; }
    .chat-container { display: flex; flex-direction: column; gap: 8px; padding: 10px; }
    .msg-row { display: flex; width: 100%; margin-bottom: 4px; }
    .sent { justify-content: flex-end; }
    .received { justify-content: flex-start; }
    .bubble {
        max-width: 65%; padding: 10px 16px; border-radius: 20px;
        font-size: 14px; position: relative;
    }
    .sent .bubble { background: linear-gradient(135deg, #6366f1, #a855f7); color: white; border-bottom-right-radius: 4px; }
    .received .bubble { background: #1f2937; color: #f3f4f6; border-bottom-left-radius: 4px; border: 1px solid #374151; }
    .sender-name { font-size: 11px; color: #9ca3af; margin-bottom: 4px; }
</style>
""", unsafe_allow_html=True)

# --- WELCOME PAGE ---
if st.session_state.page == "welcome":
    st.markdown("<div style='text-align:center; margin-top:100px;'>", unsafe_allow_html=True)
    st.title("🌌 NEBULA")
    st.write("The future of communication is here.")
    # On_click သုံးပြီး page ပြောင်းတာ ပိုစိတ်ချရပါတယ်
    st.button("Enter Nebula", use_container_width=True, on_click=change_page, args=("login",))
    st.markdown("</div>", unsafe_allow_html=True)

# --- LOGIN PAGE ---
elif st.session_state.page == "login":
    st.markdown("<div style='max-width:400px; margin:auto;'>", unsafe_allow_html=True)
    st.subheader("🚀 Login to Nebula")
    l_user = st.text_input("Username")
    l_pass = st.text_input("Password", type="password")
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("Login", use_container_width=True):
            data = conn.read(spreadsheet=SHEET_URL, worksheet="Sheet1", ttl=0)
            user_match = data[data['username'].astype(str) == str(l_user)]
            if not user_match.empty and str(user_match.iloc[0]['password']) == str(l_pass):
                st.session_state.user = user_match.iloc[0].to_dict()
                st.session_state.page = "chat_room"
                st.session_state.chat_mode = "Global"
                st.rerun()
            else:
                st.error("Access Denied.")
    with col2:
        st.button("Sign Up", use_container_width=True, on_click=change_page, args=("signup",))
    st.markdown("</div>", unsafe_allow_html=True)

# --- SIGNUP PAGE ---
elif st.session_state.page == "signup":
    st.subheader("📝 Join Nebula")
    email = st.text_input("Email")
    u_id = st.text_input("New Username")
    d_name = st.text_input("Display Name")
    pw = st.text_input("Password", type="password")
    if st.button("Create Account", use_container_width=True):
        df = conn.read(spreadsheet=SHEET_URL, worksheet="Sheet1", ttl=0)
        new_row = pd.DataFrame([{"email":email, "username":u_id, "display_name":d_name, "password":pw, "profile_pic":""}])
        conn.update(spreadsheet=SHEET_URL, worksheet="Sheet1", data=pd.concat([df, new_row], ignore_index=True))
        st.success("Account Created!")
        st.session_state.page = "login"
        st.rerun()
    st.button("Back to Login", on_click=change_page, args=("login",))

# --- CHAT ROOM ---
elif st.session_state.page == "chat_room":
    # Sidebar
    with st.sidebar:
        st.title("👨‍🚀 " + st.session_state.user['display_name'])
        if st.button("🌐 Global Channel", use_container_width=True):
            st.session_state.chat_mode = "Global"
            st.rerun()
        
        st.subheader("Users")
        users_df = conn.read(spreadsheet=SHEET_URL, worksheet="Sheet1", ttl=0).dropna(subset=['display_name'])
        for _, u in users_df.iterrows():
            if str(u['display_name']) != str(st.session_state.user['display_name']):
                if st.button(f"👤 {u['display_name']}", key=f"user_{u['username']}", use_container_width=True):
                    st.session_state.chat_mode = "Private"
                    st.session_state.chat_with = u['display_name']
                    st.rerun()
        st.divider()
        if st.button("Logout"):
            st.session_state.clear()
            st.rerun()

    # Chat Content
    ws = "Sheet2" if st.session_state.chat_mode == "Global" else "Sheet3"
    st.subheader("🌐 Global" if st.session_state.chat_mode == "Global" else f"💬 {st.session_state.chat_with}")

    try:
        df = conn.read(spreadsheet=SHEET_URL, worksheet=ws, ttl=0).fillna("")
        if st.session_state.chat_mode == "Private":
            me, other = st.session_state.user['display_name'], st.session_state.chat_with
            display_df = df[((df['sender'] == me) & (df['receiver'] == other)) | ((df['sender'] == other) & (df['receiver'] == me))]
        else:
            display_df = df.tail(20)

        for _, row in display_df.iterrows():
            is_me = str(row['sender']) == str(st.session_state.user['display_name'])
            side = "sent" if is_me else "received"
            st.markdown(f'<div class="msg-row {side}"><div><div class="sender-name">{row["sender"]}</div><div class="bubble">{row["message"]}</div></div></div>', unsafe_allow_html=True)
    except: st.write("Waiting for transmissions...")

    # Input
    msg = st.chat_input("Enter transmission...")
    if msg:
        new_msg = {"sender": st.session_state.user['display_name'], "message": msg, "timestamp": datetime.datetime.now().strftime("%I:%M %p")}
        if st.session_state.chat_mode == "Private": new_msg["receiver"] = st.session_state.chat_with
        all_msgs = conn.read(spreadsheet=SHEET_URL, worksheet=ws, ttl=0)
        conn.update(spreadsheet=SHEET_URL, worksheet=ws, data=pd.concat([all_msgs, pd.DataFrame([new_msg])], ignore_index=True))
        st.rerun()

    time.sleep(5)
    st.rerun()
