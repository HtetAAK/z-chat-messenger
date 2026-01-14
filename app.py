import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
import datetime
import time

# --- PAGE SETUP ---
st.set_page_config(page_title="Nebula Global Chat", page_icon="🌌")

# --- DATABASE CONNECTION ---
SHEET_URL = "https://docs.google.com/spreadsheets/d/1aQvBwZ-ucJNlGNFiuS5ep60mvD5ezWzqOM2g0ZOH6S0/edit?usp=sharing"
conn = st.connection("gsheets", type=GSheetsConnection)

# --- CSS STYLING ---
st.markdown("""
<style>
    .stApp { background: #09090b; color: white; }
    .chat-bubble { background: rgba(255, 255, 255, 0.1); padding: 10px 15px; border-radius: 15px; margin-bottom: 10px; border-left: 5px solid #8A2BE2; }
</style>
""", unsafe_allow_html=True)

# --- APP NAVIGATION ---
if "page" not in st.session_state: st.session_state.page = "login"

# --- LOGIN & SIGNUP Logic (အရင်အတိုင်းထားရှိပါသည်) ---
# ... (မှတ်ချက် - နေရာလွတ်စေရန် အပေါ်က code များကို အတိုချုံးထားပါသည်၊ Chat အပိုင်းကို အဓိကကြည့်ပါ)

# --- GLOBAL CHAT PAGE ---
if st.session_state.page == "chat_room":
    st.title("🌌 Nebula Global Chat")
    st.sidebar.write(f"Logged in as: **{st.session_state.user['display_name']}**")
    
    if st.sidebar.button("Logout"):
        st.session_state.page = "welcome"
        st.rerun()

    # --- CHAT DISPLAY ---
    chat_container = st.container()
    
    # စာဟောင်းများကို Sheet2 မှ ဖတ်မည်
    try:
        messages_df = conn.read(spreadsheet=SHEET_URL, worksheet="Sheet2", ttl=0)
    except:
        messages_df = pd.DataFrame(columns=["sender", "message", "timestamp"])

    with chat_container:
        for index, row in messages_df.tail(20).iterrows(): # နောက်ဆုံးစာ ၂၀ စောင်ကို ပြမည်
            st.markdown(f"""
            <div class="chat-bubble">
                <small style="color: #D02BE2;">@{row['sender']}</small><br>
                {row['message']}
            </div>
            """, unsafe_allow_html=True)

    # --- CHAT INPUT ---
    user_msg = st.chat_input("စာရိုက်ရန်...")
    
    if user_msg:
        # စာအသစ်ကို DataFrame ဆောက်ပြီး သိမ်းမည်
        new_msg = pd.DataFrame([{
            "sender": st.session_state.user['username'],
            "message": user_msg,
            "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }])
        
        # Sheet2 ထဲသို့ Update လုပ်မည်
        updated_chat = pd.concat([messages_df, new_msg], ignore_index=True)
        conn.update(spreadsheet=SHEET_URL, worksheet="Sheet2", data=updated_chat)
        
        # ချက်ချင်း Refresh ဖြစ်အောင် လုပ်မည်
        st.rerun()

    # ၅ စက္ကန့်တစ်ခါ စာအသစ်များကို အလိုအလျောက် စစ်ဆေးရန် (Auto-refresh)
    time.sleep(5)
    st.rerun()
