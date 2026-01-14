import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
import datetime
import time
import base64

# --- PAGE SETUP ---
st.set_page_config(page_title="Nebula Messenger", page_icon="🌌", layout="centered")

# --- DATABASE CONNECTION ---
SHEET_URL = "https://docs.google.com/spreadsheets/d/1aQvBwZ-ucJNlGNFiuS5ep60mvD5ezWzqOM2g0ZOH6S0/edit?usp=sharing"
conn = st.connection("gsheets", type=GSheetsConnection)

# --- ADVANCED CSS ---
st.markdown("""
<style>
    .stApp { background: #0f172a; color: white; }
    .chat-container { display: flex; flex-direction: column; padding: 10px; }
    .msg-box { display: flex; align-items: flex-end; margin-bottom: 15px; width: 100%; }
    .sent { flex-direction: row-reverse; }
    .received { flex-direction: row; }
    
    .profile-img { width: 35px; height: 35px; border-radius: 50%; margin: 0 10px; border: 2px solid #8A2BE2; }
    
    .bubble {
        max-width: 65%; padding: 12px 16px; border-radius: 20px;
        font-size: 14px; position: relative; box-shadow: 0 2px 5px rgba(0,0,0,0.2);
    }
    .sent .bubble { background: linear-gradient(135deg, #7c3aed, #4f46e5); color: white; border-bottom-right-radius: 4px; }
    .received .bubble { background: #1e293b; color: #e2e8f0; border-bottom-left-radius: 4px; border: 1px solid #334155; }
    
    .timestamp { font-size: 9px; color: #64748b; margin-top: 4px; display: block; }
</style>
""", unsafe_allow_html=True)

# --- IMAGE CONVERTER ---
def to_b64(img_file):
    return base64.b64encode(img_file.read()).decode() if img_file else ""

# --- APP NAVIGATION ---
if "user" not in st.session_state:
    st.title("🌌 Welcome to Nebula")
    if st.button("Login"):
        st.session_state.user = "pending" # ခဏပြောင်းထားခြင်း
        st.rerun()
    st.stop()

# --- CHAT ROOM ---
st.title("💬 Global Chat")

# Sidebar: Profile & Logout
with st.sidebar:
    st.subheader("👤 Your Profile")
    st.write(f"Name: **{st.session_state.user['display_name']}**")
    new_pf = st.file_uploader("Change Profile Pic", type=['jpg','png'])
    if st.button("Save Profile"):
        # Profile Update logic (Optional: နောက်မှထည့်မည်)
        st.success("Profile Updated!")
    if st.button("Logout"):
        del st.session_state.user
        st.rerun()

# စာဖတ်ခြင်း
try:
    msgs = conn.read(spreadsheet=SHEET_URL, worksheet="Sheet2", ttl=0).fillna("")
    # User Profile ပုံတွေပါ သိအောင် Sheet1 နဲ့ ချိတ်ဖတ်မည်
    users_df = conn.read(spreadsheet=SHEET_URL, worksheet="Sheet1", ttl=0).fillna("")
except:
    msgs = pd.DataFrame(columns=["sender", "message", "timestamp", "image_url"])

# စာများပြသခြင်း
st.markdown('<div class="chat-container">', unsafe_allow_html=True)
for _, row in msgs.tail(15).iterrows():
    is_me = str(row['sender']) == str(st.session_state.user['display_name'])
    align = "sent" if is_me else "received"
    
    # Profile ပုံ ရှာခြင်း
    u_info = users_df[users_df['display_name'] == row['sender']]
    pf_img = u_info.iloc[0]['profile_pic'] if not u_info.empty and u_info.iloc[0]['profile_pic'] else ""
    pf_src = f"data:image/png;base64,{pf_img}" if pf_img else "https://www.w3schools.com/howto/img_avatar.png"

    st.markdown(f'''
        <div class="msg-box {align}">
            <img src="{pf_src}" class="profile-img">
            <div class="bubble">
                <div style="font-weight:bold; font-size:11px; margin-bottom:3px; color:#a78bfa;">{row['sender']}</div>
                {row['message']}
                <span class="timestamp">{row['timestamp']}</span>
            </div>
        </div>
    ''', unsafe_allow_html=True)
st.markdown('</div>', unsafe_allow_html=True)

# စာပို့ခြင်း
msg_input = st.chat_input("Type something...")
if msg_input:
    new_data = pd.DataFrame([{
        "sender": st.session_state.user['display_name'],
        "message": msg_input,
        "timestamp": datetime.datetime.now().strftime("%I:%M %p"),
        "image_url": ""
    }])
    conn.update(spreadsheet=SHEET_URL, worksheet="Sheet2", data=pd.concat([msgs, new_data], ignore_index=True))
    st.rerun()

time.sleep(5)
st.rerun()
