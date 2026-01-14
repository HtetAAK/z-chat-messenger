import streamlit as st
import requests

# Token တွေကို Secrets ထဲကနေ လှမ်းယူမယ်
BOT_TOKEN = st.secrets["8509711435:AAFWcJbG0rZumpsxOgdaPOK4p4IW9kmGzVU"]
CHAT_ID = st.secrets["1003271238644"]

st.set_page_config(page_title="Z-Chat Messenger", page_icon="💬")

if "messages" not in st.session_state:
    st.session_state.messages = []

st.title("💬 Z-Chat Messenger")

# Username သတ်မှတ်ခြင်း
if "username" not in st.session_state or not st.session_state.username:
    username = st.text_input("Username ရိုက်ထည့်ပါ")
    if st.button("ဝင်မည်"):
        st.session_state.username = username
        st.rerun()
else:
    # Message ပြသခြင်း
    for m in st.session_state.messages:
        with st.chat_message(m["user"]):
            st.write(f"**{m['user']}**: {m['text']}")

    # စာပို့ခြင်း
    if prompt := st.chat_input("တစ်ခုခု ရေးပါ..."):
        st.session_state.messages.append({"user": st.session_state.username, "text": prompt})
        # Telegram ဆီ ပို့ခြင်း
        requests.get(f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage?chat_id={CHAT_ID}&text={st.session_state.username}: {prompt}")
        st.rerun()

    # Video Call & Media Sidebar
    with st.sidebar:
        st.write(f"Logged in as: **{st.session_state.username}**")
        if st.button("Video Call ခေါ်မည်"):
            st.write(f"[ဒီမှာနှိပ်ပြီး ဝင်ပါ](https://meet.jit.si/zchat-{CHAT_ID})")
