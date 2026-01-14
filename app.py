import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
import datetime
import time

# --- PAGE SETUP ---
st.set_page_config(page_title="Nebula Messenger", page_icon="🌌", layout="wide")

# --- DATABASE CONNECTION ---
SHEET_URL = "https://docs.google.com/spreadsheets/d/1aQvBwZ-ucJNlGNFiuS5ep60mvD5ezWzqOM2g0ZOH6S0/edit?usp=sharing"
conn = st.connection("gsheets", type=GSheetsConnection)

# --- CSS (ဘယ်/ညာ ခွဲခြားမှု ပိုကောင်းအောင် ပြင်ထားသည်) ---
st.markdown("""
<style>
    .stApp { background: #0f172a; color: white; }
    .msg-row { display: flex; width: 100%; margin-bottom: 12px; }
    .sent { justify-content: flex-end; }
    .received { justify-content: flex-start; }
    .bubble { max-width: 70%; padding: 12px; border-radius: 18px; font-size: 14px; box-shadow: 0 2px 4px rgba(0,0,0,0.3); }
    .sent .bubble { background: #7c3aed; color: white; border-bottom-right-radius: 2px; }
    .received .bubble { background: #1e293b; color: white; border-bottom-left-radius: 2px; border: 1px solid #334155; }
    .sender-tag { font-size: 10px; color: #94a3b8; margin-bottom: 3px; }
</style>
""", unsafe_allow_html=True)

# --- NAVIGATION ---
if "user" not in st.session_state:
    st.info("အကောင့်ပြန်ဝင်ပေးပါခင်ဗျာ။")
    st.stop()

if "chat_mode" not in st.session_state:
    st.session_state.chat_mode = "Global"

# --- SIDEBAR (Friends List) ---
with st.sidebar:
    st.title("🌌 Nebula")
    st.write(f"Logged in: **{st.session_state.user['display_name']}**")
    st.divider()
    
    if st.button("🌐 Global Chat Room", use_container_width=True):
        st.session_state.chat_mode = "Global"
        st.rerun()
    
    st.subheader("👥 Online Users")
    all_users = conn.read(spreadsheet=SHEET_URL, worksheet="Sheet1", ttl=0)
    for _, user in all_users.iterrows():
        if user['display_name'] != st.session_state.user['display_name']:
            if st.button(f"💬 {user['display_name']}", key=user['username'], use_container_width=True):
                st.session_state.chat_mode = "Private"
                st.session_state.chat_with = user['display_name']
                st.rerun()
    
    st.divider()
    if st.button("🚪 Logout"):
        del st.session_state.user
        st.rerun()

# --- CHAT INTERFACE ---
if st.session_state.chat_mode == "Global":
    st.subheader("🌐 Global Chat Room")
    ws = "Sheet2"
    filter_logic = None
else:
    st.subheader(f"💬 Private Chat with {st.session_state.chat_with}")
    ws = "Sheet3"

# Data ဖတ်ခြင်း
try:
    df = conn.read(spreadsheet=SHEET_URL, worksheet=ws, ttl=0).fillna("")
    if st.session_state.chat_mode == "Private":
        # မိမိ ပို့ထားသောစာ နှင့် မိမိဆီ ပို့ထားသောစာများကိုသာ စစ်ထုတ်မည်
        me = st.session_state.user['display_name']
        other = st.session_state.chat_with
        df = df[((df['sender'] == me) & (df['receiver'] == other)) | 
                ((df['sender'] == other) & (df['receiver'] == me))]
except:
    df = pd.DataFrame()

# စာများပြသခြင်း
chat_box = st.container()
with chat_box:
    for _, row in df.tail(20).iterrows():
        is_me = row['sender'] == st.session_state.user['display_name']
        cls = "sent" if is_me else "received"
        st.markdown(f'''
            <div class="msg-row {cls}">
                <div>
                    <div class="sender-tag">{row['sender']}</div>
                    <div class="bubble">{row['message']}</div>
                </div>
            </div>
        ''', unsafe_allow_html=True)

# စာပို့ခြင်း
msg = st.chat_input("စာရိုက်ပါ...")
if msg:
    new_data = {
        "sender": st.session_state.user['display_name'],
        "message": msg,
        "timestamp": datetime.datetime.now().strftime("%I:%M %p")
    }
    if st.session_state.chat_mode == "Private":
        new_data["receiver"] = st.session_state.chat_with
    
    full_df = conn.read(spreadsheet=SHEET_URL, worksheet=ws, ttl=0)
    updated_df = pd.concat([full_df, pd.DataFrame([new_data])], ignore_index=True)
    conn.update(spreadsheet=SHEET_URL, worksheet=ws, data=updated_df)
    st.rerun()

time.sleep(5)
st.rerun()
