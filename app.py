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
</style>
""", unsafe_allow_html=True)

# --- SESSION CHECK ---
if "user" not in st.session_state:
    st.info("Login အရင်ဝင်ပေးပါခင်ဗျာ။")
    st.stop()

if "chat_mode" not in st.session_state:
    st.session_state.chat_mode = "Global"

# --- SIDEBAR ---
with st.sidebar:
    st.title("🌌 Nebula")
    st.write(f"Logged in: **{st.session_state.user['display_name']}**")
    st.divider()
    
    if st.button("🌐 Global Chat Room", use_container_width=True):
        st.session_state.chat_mode = "Global"
        st.rerun()
    
    st.subheader("👥 Online Users")
    try:
        # Sheet1 မှ user အားလုံးကို ဖတ်သည်
        users_df = conn.read(spreadsheet=SHEET_URL, worksheet="Sheet1", ttl=0).dropna(subset=['display_name'])
        
        for _, u in users_df.iterrows():
            u_name = str(u['display_name']).strip()
            my_name = str(st.session_state.user['display_name']).strip()
            
            # ကိုယ့်နာမည်ကိုယ် ပြန်မပြရန်
            if u_name != my_name:
                if st.button(f"💬 {u_name}", key=f"btn_{u['username']}", use_container_width=True):
                    st.session_state.chat_mode = "Private"
                    st.session_state.chat_with = u_name
                    st.rerun()
    except Exception as e:
        st.error(f"User list error: {e}")

# --- CHAT ROOM LOGIC ---
ws_name = "Sheet2" if st.session_state.chat_mode == "Global" else "Sheet3"
st.subheader("🌐 Global Chat" if st.session_state.chat_mode == "Global" else f"💬 Chat with {st.session_state.chat_with}")

try:
    df = conn.read(spreadsheet=SHEET_URL, worksheet=ws_name, ttl=0).fillna("")
    
    if st.session_state.chat_mode == "Private":
        me = str(st.session_state.user['display_name']).strip()
        other = str(st.session_state.chat_with).strip()
        display_df = df[((df['sender'].astype(str) == me) & (df['receiver'].astype(str) == other)) | 
                        ((df['sender'].astype(str) == other) & (df['receiver'].astype(str) == me))]
    else:
        display_df = df.tail(20)

    # စာများပြသခြင်း
    for _, row in display_df.iterrows():
        is_me = str(row['sender']) == str(st.session_state.user['display_name'])
        cls = "sent" if is_me else "received"
        st.markdown(f'<div class="msg-row {cls}"><div><div class="sender-tag">{row["sender"]}</div><div class="bubble">{row["message"]}</div></div></div>', unsafe_allow_html=True)
except Exception as e:
    st.error(f"Display Error: {e}")

# --- SEND MESSAGE ---
msg = st.chat_input("စာရိုက်ပါ...")
if msg:
    try:
        new_row = {
            "sender": st.session_state.user['display_name'],
            "message": msg,
            "timestamp": datetime.datetime.now().strftime("%I:%M %p")
        }
        if st.session_state.chat_mode == "Private":
            new_row["receiver"] = st.session_state.chat_with
            
        # Sheet အသစ်ဖတ်ပြီးမှ update လုပ်ခြင်း (Conflict လျော့စေရန်)
        current_all = conn.read(spreadsheet=SHEET_URL, worksheet=ws_name, ttl=0)
        updated_df = pd.concat([current_all, pd.DataFrame([new_row])], ignore_index=True)
        conn.update(spreadsheet=SHEET_URL, worksheet=ws_name, data=updated_df)
        st.rerun()
    except Exception as e:
        st.error(f"ပို့မရပါ: {e}")

time.sleep(5)
st.rerun()
