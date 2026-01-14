import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime
import requests
import time

# --- Database Connection ---
conn = st.connection("gsheets", type=GSheetsConnection)

# --- Telegram Settings ---
BOT_TOKEN = st.secrets["BOT_TOKEN"]
CHAT_ID = st.secrets["CHAT_ID"]

st.set_page_config(page_title="Z-Chat Messenger", page_icon="💬")

# CSS for styling
st.markdown("""
    <style>
    .stApp { background-color: #0e1117; color: white; }
    .stChatMessage { border-radius: 15px; }
    </style>
    """, unsafe_allow_html=True)

# --- Login Logic ---
if "my_id" not in st.session_state:
    st.title("🔐 Login to Z-Chat")
    my_id_input = st.text_input("သင့်ရဲ့ ID (Username) ကို ရိုက်ထည့်ပါ")
    if st.button("အကောင့်ဝင်မည်"):
        if my_id_input:
            st.session_state.my_id = my_id_input
            st.rerun()
        else:
            st.warning("ID တစ်ခုခု ရိုက်ထည့်ပါ။")
else:
    # --- UI Header ---
    st.sidebar.title(f"👤 {st.session_state.my_id}")
    target_id = st.sidebar.text_input("စကားပြောမည့်သူ၏ ID", placeholder="Receiver ID")
    
    if st.sidebar.button("Logout"):
        del st.session_state.my_id
        st.rerun()

    st.title(f"💬 Chat: {target_id if target_id else '...'}")

    # --- Read Database ---
    try:
        # ၂ စက္ကန့်တိုင်း အသစ်စစ်ရန် (ttl=2)
        df = conn.read(ttl=2)
    except:
        df = pd.DataFrame(columns=["from", "to", "message", "time"])

    # --- Display Messages ---
    if target_id:
        # ကိုယ်နဲ့ တစ်ဖက်လူ ပြောထားတဲ့စာတွေကိုပဲ စစ်ထုတ်ယူမယ်
        mask = (
            ((df["from"] == st.session_state.my_id) & (df["to"] == target_id)) |
            ((df["from"] == target_id) & (df["to"] == st.session_state.my_id))
        )
        chat_history = df[mask]

        for _, row in chat_history.iterrows():
            role = "user" if row["from"] == st.session_state.my_id else "assistant"
            with st.chat_message(role):
                st.write(f"**{row['from']}**: {row['message']}")

        # --- Send Message ---
        if prompt := st.chat_input("မက်ဆေ့ချ် ရေးပါ..."):
            # ၁။ Google Sheet ထဲ သိမ်းရန်
            new_row = pd.DataFrame([{
                "from": st.session_state.my_id,
                "to": target_id,
                "message": prompt,
                "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }])
            updated_df = pd.concat([df, new_row], ignore_index=True)
            conn.update(data=updated_df)
            
            # ၂။ Telegram ဆီ Admin အနေနဲ့ ပို့ရန်
            log_msg = f"📩 {st.session_state.my_id} -> {target_id}: {prompt}"
            requests.post(f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage", 
                          json={"chat_id": CHAT_ID, "text": log_msg})
            
            st.rerun()
    else:
        st.info("ဘယ်ဘက် Sidebar မှာ သင်စကားပြောချင်တဲ့သူရဲ့ ID ကို အရင်ရိုက်ထည့်ပါ။")

    # အလိုအလျောက် Update ဖြစ်စေရန်
    time.sleep(3)
    st.rerun()
    if prompt := st.chat_input("စာရိုက်ပါ..."):
        st.session_state.messages.append({"user": st.session_state.username, "text": prompt})
        
        # Telegram API သို့ ပို့ခြင်း
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
        payload = {"chat_id": CHAT_ID, "text": f"{st.session_state.username}: {prompt}"}
        requests.post(url, json=payload)
        st.rerun()
        if st.button("Video Call ခေါ်မည်"):
            st.write(f"[ဒီမှာနှိပ်ပြီး ဝင်ပါ](https://meet.jit.si/zchat-{CHAT_ID})")
