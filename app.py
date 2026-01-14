import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
import datetime
import time

# --- PAGE SETUP ---
st.set_page_config(page_title="Nebula Chat", page_icon="🌌", layout="wide")

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

# --- INITIAL STATE ---
if "user" not in st.session_state:
    st.info("Login အရင်ဝင်ပေးပါခင်ဗျာ။")
    st.stop()

if "chat_mode" not in st.session_state:
    st.session_state.chat_mode = "Global"

# --- SIDEBAR (User List Fix) ---
with st.sidebar:
    st.title("🌌 Nebula")
    st.write(f"Logged in: **{st.session_state.user['display_name']}**")
    
    if st.button("🌐 Global Chat", use_container_width=True):
        st.session_state.chat_mode = "Global"
        st.rerun()
    
    st.subheader("👥 Online Users")
    try:
        # Sheet1 မှ user list ကို ဖတ်သည်
        users_df = conn.read(spreadsheet=SHEET_URL, worksheet="Sheet1", ttl=0).fillna("")
        
        # User list ကို ပေါ်လာအောင် လုပ်ခြင်း
        if not users_df.empty:
            for _, u in users_df.iterrows():
                # ကိုယ့်နာမည်ကိုယ် ပြန်မပြရန်
                if str(u['display_name']) != str(st.session_state.user['display_name']):
                    if st.button(f"💬 {u['display_name']}", key=f"user_{u['username']}", use_container_width=True):
                        st.session_state.chat_mode = "Private"
                        st.session_state.chat_with = u['display_name']
                        st.rerun()
        else:
            st.write("အကောင့်ဖွင့်ထားသူ မရှိသေးပါ။")
    except Exception as e:
        st.error(f"User list error: {e}")

# --- CHAT LOGIC ---
ws_name = "Sheet2" if st.session_state.chat_mode == "Global" else "Sheet3"
st.subheader("🌐 Global Chat" if st.session_state.chat_mode == "Global" else f"💬 Chat with {st.session_state.chat_with}")

try:
    # စာဖတ်ခြင်း
    df = conn.read(spreadsheet=SHEET_URL, worksheet=ws_name, ttl=0).fillna("")
    
    if st.session_state.chat_mode == "Private":
        me = st.session_state.user['display_name']
        other = st.session_state.chat_with
        # Private chat စစ်ထုတ်ခြင်း
        display_df = df[((df['sender'] == me) & (df['receiver'] == other)) | 
                        ((df['sender'] == other) & (df['receiver'] == me))]
    else:
        display_df = df.tail(20)

    # ပြသခြင်း
    for _, row in display_df.iterrows():
        is_me = str(row['sender']) == str(st.session_state.user['display_name'])
        cls = "sent" if is_me else "received"
        st.markdown(f'''
            <div class="msg-row {cls}">
                <div>
                    <div class="sender-tag">{row["sender"]}</div>
                    <div class="bubble">{row["message"]}</div>
                </div>
            </div>
        ''', unsafe_allow_html=True)
except Exception as e:
    st.error(f"Error: {e}")

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
            
        # Data Update လုပ်ခြင်း
        updated_df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
        conn.update(spreadsheet=SHEET_URL, worksheet=ws_name, data=updated_df)
        st.rerun()
    except Exception as e:
        st.error(f"ပို့မရပါ: {e}")

time.sleep(5)
st.rerun()
