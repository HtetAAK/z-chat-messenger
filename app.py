import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime
import requests
import time

# --- Database & Config ---
conn = st.connection("gsheets", type=GSheetsConnection)
BOT_TOKEN = st.secrets["BOT_TOKEN"]
CHAT_ID = st.secrets["CHAT_ID"]

st.set_page_config(page_title="Z-Chat Premium", page_icon="⚡", layout="wide")

# --- Custom UI Styling (ခပ်မိုက်မိုက် Dark Mode) ---
st.markdown("""
    <style>
    .stApp { background-color: #0b0e14; color: #e0e0e0; }
    [data-testid="stSidebar"] { background-color: #151921; border-right: 1px solid #2d343f; }
    .stButton>button { width: 100%; border-radius: 8px; background-color: #3d5afe; color: white; border: none; }
    .stTextInput>div>div>input { background-color: #1e2530; color: white; border: 1px solid #3d4756; border-radius: 8px; }
    .chat-bubble { padding: 12px; border-radius: 15px; margin-bottom: 10px; max-width: 80%; }
    .my-msg { background-color: #3d5afe; align-self: flex-end; margin-left: auto; }
    .their-msg { background-color: #262c38; }
    </style>
    """, unsafe_allow_html=True)

# --- Login & Profile Logic ---
if "logged_in" not in st.session_state:
    st.title("⚡ Welcome to Z-Chat")
    tab1, tab2 = st.tabs(["Login", "About"])
    
    with tab1:
        u_name = st.text_input("Username (ပြသရန်အမည်)")
        u_id = st.text_input("User ID (Unique ID - ဥပမာ: ark123)")
        if st.button("Start Chatting"):
            if u_name and u_id:
                st.session_state.username = u_name
                st.session_state.my_id = u_id.lower().strip()
                st.session_state.logged_in = True
                st.rerun()
            else:
                st.warning("အချက်အလက် အကုန်ဖြည့်ပါ။")
    st.stop()

# --- Sidebar (Profile & Contacts) ---
with st.sidebar:
    st.title("⚙️ Profile")
    if st.toggle("Edit Profile"):
        new_name = st.text_input("Edit Name", value=st.session_state.username)
        if st.button("Save Changes"):
            st.session_state.username = new_name
            st.success("Updated!")
            st.rerun()
    else:
        st.write(f"**Name:** {st.session_state.username}")
        st.write(f"**ID:** @{st.session_state.my_id}")
    
    st.divider()
    target_id = st.text_input("🔍 Chat with (Enter User ID)", placeholder="e.g. user789").lower().strip()
    
    if st.button("🚪 Logout"):
        st.session_state.clear()
        st.rerun()

# --- Chat Interface ---
st.title(f"💬 Chat: {target_id if target_id else 'Select a User'}")

try:
    df = conn.read(ttl=2)
except:
    df = pd.DataFrame(columns=["from", "to", "message", "time", "sender_name"])

if target_id:
    # Filter Messages
    mask = (
        ((df["from"] == st.session_state.my_id) & (df["to"] == target_id)) |
        ((df["from"] == target_id) & (df["to"] == st.session_state.my_id))
    )
    chat_history = df[mask]

    # Show Messages
    chat_container = st.container()
    with chat_container:
        for _, row in chat_history.iterrows():
            is_me = row["from"] == st.session_state.my_id
            div_class = "my-msg" if is_me else "their-msg"
            st.markdown(f"""
                <div class="chat-bubble {div_class}">
                    <small style="color: #adb5bd;">{row['sender_name']} • {row['time']}</small><br>
                    {row['message']}
                </div>
                """, unsafe_allow_html=True)

    # Send Message
    if prompt := st.chat_input("Write a message..."):
        new_row = pd.DataFrame([{
            "from": st.session_state.my_id,
            "to": target_id,
            "message": prompt,
            "time": datetime.now().strftime("%H:%M"),
            "sender_name": st.session_state.username
        }])
        updated_df = pd.concat([df, new_row], ignore_index=True)
        conn.update(data=updated_df)
        
        # Telegram Log
        log = f"🚀 {st.session_state.username} (@{st.session_state.my_id}) -> {target_id}: {prompt}"
        requests.post(f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage", json={"chat_id": CHAT_ID, "text": log})
        st.rerun()
else:
    st.info("ဘယ်ဘက်မှာ သင်စကားပြောချင်တဲ့သူရဲ့ ID ကိုရိုက်ပြီး Chat ကိုစတင်ပါ။")

time.sleep(4)
st.rerun()
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
