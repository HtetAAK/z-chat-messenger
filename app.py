import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
import datetime
import time
import base64

# --- PAGE SETUP ---
st.set_page_config(page_title="Nebula Premium Chat", page_icon="🌌", layout="centered")

# --- DATABASE CONNECTION ---
SHEET_URL = "https://docs.google.com/spreadsheets/d/1aQvBwZ-ucJNlGNFiuS5ep60mvD5ezWzqOM2g0ZOH6S0/edit?usp=sharing"
conn = st.connection("gsheets", type=GSheetsConnection)

# --- ADVANCED CSS FOR CHAT BUBBLES ---
st.markdown("""
<style>
    .stApp { background: #0f172a; color: white; }
    .main-chat { display: flex; flex-direction: column; gap: 10px; padding: 10px; }
    .message-row { display: flex; width: 100%; margin-bottom: 5px; }
    .sent { justify-content: flex-end; }
    .received { justify-content: flex-start; }
    
    .bubble {
        max-width: 70%; padding: 10px 15px; border-radius: 20px;
        position: relative; font-size: 15px; line-height: 1.4;
    }
    .sent .bubble {
        background: linear-gradient(135deg, #8A2BE2, #4F46E5);
        color: white; border-bottom-right-radius: 2px;
    }
    .received .bubble {
        background: #334155;
        color: #f1f5f9; border-bottom-left-radius: 2px;
    }
    .sender-name { font-size: 11px; margin-bottom: 3px; color: #94a3b8; }
</style>
""", unsafe_allow_html=True)

# --- IMAGE HANDLER ---
def image_to_base64(uploaded_file):
    return base64.b64encode(uploaded_file.read()).decode()

# --- CHAT ROOM PAGE ---
if "user" in st.session_state:
    st.title("🌌 Nebula Messenger")
    
    # စာဖတ်ခြင်း
    try:
        df = conn.read(spreadsheet=SHEET_URL, worksheet="Sheet2", ttl=0)
        df = df.fillna("")
    except:
        df = pd.DataFrame(columns=["sender", "message", "timestamp", "image_url"])

    # စာများပြသခြင်း
    st.markdown('<div class="main-chat">', unsafe_allow_html=True)
    for _, row in df.tail(20).iterrows():
        is_me = row['sender'] == st.session_state.user['display_name']
        align_class = "sent" if is_me else "received"
        
        st.markdown(f'''
            <div class="message-row {align_class}">
                <div class="bubble-container">
                    <div class="sender-name">{"You" if is_me else row['sender']}</div>
                    <div class="bubble">
                        {row['message']}
                        {f'<br><img src="data:image/png;base64,{row["image_url"]}" style="width:100%; border-radius:10px; margin-top:5px;">' if row['image_url'] else ""}
                    </div>
                </div>
            </div>
        ''', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

    # --- INPUT AREA ---
    with st.container():
        msg = st.chat_input("Write a message...")
        img_file = st.sidebar.file_uploader("Share Photo 📷", type=['png', 'jpg', 'jpeg'])
        
        if msg or img_file:
            img_data = ""
            if img_file:
                img_data = image_to_base64(img_file)
            
            new_msg = pd.DataFrame([{
                "sender": st.session_state.user['display_name'],
                "message": msg if msg else "",
                "timestamp": datetime.datetime.now().strftime("%H:%M"),
                "image_url": img_data
            }])
            
            updated_df = pd.concat([df, new_msg], ignore_index=True)
            conn.update(spreadsheet=SHEET_URL, worksheet="Sheet2", data=updated_df)
            st.rerun()

    # Sidebar Logout
    if st.sidebar.button("Log Out"):
        del st.session_state.user
        st.session_state.page = "login"
        st.rerun()

    time.sleep(5)
    st.rerun()
