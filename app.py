import streamlit as st
import requests

# --- ၁။ တိုက်ရိုက်ထည့်မည့်အစား Secrets မှ ခေါ်ယူခြင်း (ပိုမိုကောင်းမွန်သောနည်းလမ်း) ---
# သတိပြုရန် - ဤနေရာတွင် BOT_TOKEN ဟုသာ ရေးရပါမည်။ ဂဏန်းများကို အောက်ပါ Secrets အဆင့်တွင် ထည့်ရပါမည်။
try:
    BOT_TOKEN = st.secrets["BOT_TOKEN"]
    CHAT_ID = st.secrets["CHAT_ID"]
except KeyError:
    st.error("Error: Streamlit Settings > Secrets ထဲမှာ Token နဲ့ ID ကို မထည့်ရသေးပါဘူး။")
    st.info("အောက်က 'အရေးကြီးဆုံးအဆင့်' ကို ဖတ်ပေးပါ။")
    st.stop()

# --- ၂။ Website UI ပိုင်း ---
st.set_page_config(page_title="Z-Chat Messenger", page_icon="💬")
st.title("💬 Z-Chat Messenger")

if "messages" not in st.session_state:
    st.session_state.messages = []

# Username သတ်မှတ်ခြင်း
if "username" not in st.session_state or not st.session_state.username:
    user = st.text_input("Username ပေးပါ")
    if st.button("စတင်မည်"):
        if user:
            st.session_state.username = user
            st.rerun()
else:
    st.write(f"ဝင်ရောက်ထားသူ: **{st.session_state.username}**")

    # Chat ပြသခြင်း
    for m in st.session_state.messages:
        with st.chat_message("user"):
            st.write(f"**{m['user']}**: {m['text']}")

    # စာရိုက်ပြီး Telegram ပို့ခြင်း
    if prompt := st.chat_input("စာရိုက်ပါ..."):
        st.session_state.messages.append({"user": st.session_state.username, "text": prompt})
        
        # Telegram API သို့ ပို့ခြင်း
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
        payload = {"chat_id": CHAT_ID, "text": f"{st.session_state.username}: {prompt}"}
        requests.post(url, json=payload)
        st.rerun()
        if st.button("Video Call ခေါ်မည်"):
            st.write(f"[ဒီမှာနှိပ်ပြီး ဝင်ပါ](https://meet.jit.si/zchat-{CHAT_ID})")
