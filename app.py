import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
import datetime
import time
import base64
import random
import smtplib
import ssl
from email.message import EmailMessage

# --- PAGE SETUP ---
st.set_page_config(page_title="Nebula Chat", page_icon="🌌", layout="centered")

# --- DATABASE CONNECTION ---
SHEET_URL = "https://docs.google.com/spreadsheets/d/1aQvBwZ-ucJNlGNFiuS5ep60mvD5ezWzqOM2g0ZOH6S0/edit?usp=sharing"
conn = st.connection("gsheets", type=GSheetsConnection)

# --- CSS STYLING ---
st.markdown("""
<style>
    .stApp { background: #0f172a; color: white; }
    .message-row { display: flex; width: 100%; margin-bottom: 10px; }
    .sent { justify-content: flex-end; }
    .received { justify-content: flex-start; }
    .bubble { max-width: 75%; padding: 12px; border-radius: 18px; font-size: 15px; }
    .sent .bubble { background: #8A2BE2; color: white; border-bottom-right-radius: 2px; }
    .received .bubble { background: #334155; color: white; border-bottom-left-radius: 2px; }
    .sender-name { font-size: 10px; color: #94a3b8; margin-bottom: 2px; }
</style>
""", unsafe_allow_html=True)

# --- INITIAL STATE ---
if "page" not in st.session_state:
    st.session_state.page = "welcome"

# --- LOGIN & SIGNUP Logic ---
if st.session_state.page == "welcome":
    st.title("🌌 Nebula Messenger")
    if st.button("စတင်အသုံးပြုမည်", use_container_width=True):
        st.session_state.page = "login"
        st.rerun()

elif st.session_state.page == "login":
    st.subheader("🔐 Login")
    l_user = st.text_input("Username")
    l_pass = st.text_input("Password", type="password")
    if st.button("Login"):
        data = conn.read(spreadsheet=SHEET_URL, worksheet="Sheet1", ttl=0)
        user_match = data[data['username'].astype(str) == str(l_user)]
        if not user_match.empty and str(user_match.iloc[0]['password']) == str(l_pass):
            st.session_state.user = user_match.iloc[0].to_dict()
            st.session_state.page = "chat_room"
            st.rerun()
        else: st.error("မှားယွင်းနေပါသည်။")

# --- CHAT ROOM ---
elif st.session_state.page == "chat_room":
    st.title("💬 Global Chat")
    if st.sidebar.button("Logout"):
        del st.session_state.user
        st.session_state.page = "login"
        st.rerun()

    # စာဖတ်ခြင်း
    try:
        df = conn.read(spreadsheet=SHEET_URL, worksheet="Sheet2", ttl=0).fillna("")
    except:
        df = pd.DataFrame(columns=["sender", "message", "timestamp", "image_url"])

    # စာပြသခြင်း
    for _, row in df.tail(15).iterrows():
        is_me = str(row['sender']) == str(st.session_state.user['display_name'])
        align_class = "sent" if is_me else "received"
        st.markdown(f'<div class="message-row {align_class}"><div><div class="sender-name">{row["sender"]}</div><div class="bubble">{row["message"]}</div></div></div>', unsafe_allow_html=True)

    # စာပို့ခြင်း
    msg = st.chat_input("Write a message...")
    if msg:
        new_msg = pd.DataFrame([{"sender": st.session_state.user['display_name'], "message": msg, "timestamp": datetime.datetime.now().strftime("%H:%M"), "image_url": ""}])
        conn.update(spreadsheet=SHEET_URL, worksheet="Sheet2", data=pd.concat([df, new_msg], ignore_index=True))
        st.rerun()

    time.sleep(5)
    st.rerun()
