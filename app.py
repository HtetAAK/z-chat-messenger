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

# --- LUXURY CSS STYLING ---
st.markdown("""
<style>
    /* Background & Global Styles */
    .stApp { background-color: #0b0e14; color: #e1e1e1; }
    
    /* Custom Scrollbar */
    ::-webkit-scrollbar { width: 5px; }
    ::-webkit-scrollbar-track { background: #0b0e14; }
    ::-webkit-scrollbar-thumb { background: #1f2937; border-radius: 10px; }

    /* Chat Bubbles */
    .chat-container { display: flex; flex-direction: column; gap: 8px; padding: 10px; }
    .msg-row { display: flex; width: 100%; margin-bottom: 4px; }
    .sent { justify-content: flex-end; }
    .received { justify-content: flex-start; }
    
    .bubble {
        max-width: 60%; padding: 10px 16px; border-radius: 20px;
        font-size: 14px; line-height: 1.5; position: relative;
        box-shadow: 0 4px 15px rgba(0,0,0,0.2);
    }
    .sent .bubble {
        background: linear-gradient(135deg, #6366f1, #a855f7);
        color: white; border-bottom-right-radius: 4px;
        border: 1px solid rgba(255,255,255,0.1);
    }
    .received .bubble {
        background: #1f2937; color: #f3f4f6;
        border-bottom-left-radius: 4px; border: 1px solid #374151;
    }

    /* Meta Info */
    .sender-name { font-size: 11px; color: #9ca3af; margin-bottom: 4px; margin-left: 8px; font-weight: 500; }
    .sent .sender-name { text-align: right; margin-right: 8px; }
    .time-stamp { font-size: 9px; color: rgba(255,255,255,0.5); margin-top: 5px; display: block; text-align: right; }

    /* Sidebar Styling */
    section[data-testid="stSidebar"] { background-color: #111827 !important; border-right: 1px solid #1f2937; }
    .stButton>button { border-radius: 10px; border: none; transition: 0.3s; }
    .stButton>button:hover { background: #4f46e5 !important; color: white !important; }
</style>
""", unsafe_allow_html=True)

# --- SESSION & NAVIGATION ---
if "page" not in st.session_state: st.session_state.page = "welcome"
if "user" not in st.session_state: st.session_state.page = "welcome"

# --- PAGES ---
if st.session_state.page == "welcome":
    st.markdown("<div style='text-align:center; margin-top:100px;'>", unsafe_allow_html=True)
    st.title("🌌 NEBULA")
    st.markdown("<p style='color:#9ca3af;'>Next-gen messenger for deep space explorers.</p>", unsafe_allow_html=True)
    if st.button("Enter Nebula", use_container_width=True):
        st.session_state.page = "login"
        st.rerun()
    st.markdown("</div>", unsafe_allow_html=True)

elif st.session_state.page == "login":
    with st.container():
        st.subheader("🚀 Welcome Back")
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
            else: st.error("Access Denied.")

elif st.session_state.page == "chat_room":
    # Sidebar
    with st.sidebar:
        st.markdown(f"### 👨‍🚀 {st.session_state.user['display_name']}")
        st.caption(f"@{st.session_state.user['username']}")
        st.divider()
        if st.button("🌐 Global Channel", use_container_width=True):
            st.session_state.chat_mode = "Global"
            st.rerun()
        
        st.subheader("Contacts")
        users_df = conn.read(spreadsheet=SHEET_URL, worksheet="Sheet1", ttl=0).dropna(subset=['display_name'])
        for _, u in users_df.iterrows():
            if str(u['display_name']) != str(st.session_state.user['display_name']):
                if st.button(f"👤 {u['display_name']}", key=f"u_{u['username']}", use_container_width=True):
                    st.session_state.chat_mode = "Private"
                    st.session_state.chat_with = u['display_name']
                    st.rerun()
        
        st.divider()
        if st.sidebar.button("Log out"):
            st.session_state.clear()
            st.rerun()

    # Chat Header
    mode_label = "🌐 Global Channel" if st.session_state.chat_mode == "Global" else f"💬 Chat with {st.session_state.chat_with}"
    st.subheader(mode_label)

    # Load Messages
    ws = "Sheet2" if st.session_state.chat_mode == "Global" else "Sheet3"
    try:
        df = conn.read(spreadsheet=SHEET_URL, worksheet=ws, ttl=0).fillna("")
        if st.session_state.chat_mode == "Private":
            me, other = st.session_state.user['display_name'], st.session_state.chat_with
            display_df = df[((df['sender'] == me) & (df['receiver'] == other)) | ((df['sender'] == other) & (df['receiver'] == me))]
        else:
            display_df = df.tail(30)

        # Rendering
        st.markdown('<div class="chat-container">', unsafe_allow_html=True)
        for _, row in display_df.iterrows():
            is_me = str(row['sender']) == str(st.session_state.user['display_name'])
            side = "sent" if is_me else "received"
            st.markdown(f'''
                <div class="msg-row {side}">
                    <div style="width: 100%;">
                        <div class="sender-name">{row['sender']}</div>
                        <div class="bubble">
                            {row['message']}
                            <span class="time-stamp">{row['timestamp']}</span>
                        </div>
                    </div>
                </div>
            ''', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)
    except: st.info("No transmissions found...")

    # Input
    msg = st.chat_input("Type your message...")
    if msg:
        now = datetime.datetime.now().strftime("%I:%M %p")
        new_row = {"sender": st.session_state.user['display_name'], "message": msg, "timestamp": now}
        if st.session_state.chat_mode == "Private": new_row["receiver"] = st.session_state.chat_with
        all_df = conn.read(spreadsheet=SHEET_URL, worksheet=ws, ttl=0)
        conn.update(spreadsheet=SHEET_URL, worksheet=ws, data=pd.concat([all_df, pd.DataFrame([new_row])], ignore_index=True))
        st.rerun()

    # Auto-refresh logic (5s)
    time.sleep(5)
    st.rerun()
