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

# --- CSS STYLING (ဘယ်/ညာ ခွဲရန်) ---
st.markdown("""
<style>
    .stApp { background: #0f172a; color: white; }
    .message-row { display: flex; width: 100%; margin-bottom: 10px; }
    .sent { justify-content: flex-end; }
    .received { justify-content: flex-start; }
    .bubble {
        max-width: 75%; padding: 12px; border-radius: 18px;
        font-size: 15px; position: relative;
    }
    .sent .bubble { background: #8A2BE2; color: white; border-bottom-right-radius: 2px; }
    .received .bubble { background: #334155; color: white; border-bottom-left-radius: 2px; }
    .sender-name { font-size: 10px; color: #94a3b8; margin-bottom: 2px; }
</style>
""", unsafe_allow_html=True)

# --- IMAGE HANDLER ---
def image_to_base64(uploaded_file):
    if uploaded_file is not None:
        return base64.b64encode(uploaded_file.read()).decode()
    return ""

# --- APP FLOW ---
if "user" not in st.session_state:
    st.warning("Please Login First")
    if st.button("Go to Login"):
        st.session_state.page = "login"
        st.rerun()
    st.stop()

# --- CHAT ROOM ---
st.title("🌌 Nebula Messenger")

# စာဖတ်ခြင်း
try:
    df = conn.read(spreadsheet=SHEET_URL, worksheet="Sheet2", ttl=0)
    df = df.fillna("")
except Exception as e:
    st.error(f"Database Error: {e}")
    df = pd.DataFrame(columns=["sender", "message", "timestamp", "image_url"])

# စာများပြသခြင်း
for _, row in df.tail(15).iterrows():
    is_me = str(row['sender']) == str(st.session_state.user['display_name'])
    align_class = "sent" if is_me else "received"
    
    st.markdown(f'''
        <div class="message-row {align_class}">
            <div>
                <div class="sender-name">{row['sender']}</div>
                <div class="bubble">
                    {row['message']}
                    {f'<br><img src="data:image/png;base64,{row["image_url"]}" style="width:100%; border-radius:10px; margin-top:5px;">' if row['image_url'] else ""}
                </div>
            </div>
        </div>
    ''', unsafe_allow_html=True)

# --- INPUT AREA ---
with st.container():
    msg = st.chat_input("Write a message...")
    img_file = st.sidebar.file_uploader("Share Photo 📷", type=['png', 'jpg', 'jpeg'])
    
    if msg or img_file:
        try:
            img_data = image_to_base64(img_file) if img_file else ""
            new_msg = pd.DataFrame([{
                "sender": st.session_state.user['display_name'],
                "message": msg if msg else "",
                "timestamp": datetime.datetime.now().strftime("%H:%M"),
                "image_url": img_data
            }])
            updated_df = pd.concat([df, new_msg], ignore_index=True)
            conn.update(spreadsheet=SHEET_URL, worksheet="Sheet2", data=updated_df)
            st.rerun()
        except Exception as e:
            st.error(f"Sending Error: {e}")

if st.sidebar.button("Logout"):
    del st.session_state.user
    st.rerun()

time.sleep(5)
st.rerun()
