import streamlit as st
import requests
from datetime import datetime
import uuid

# ------------------------ Page Config ------------------------
st.set_page_config(
    page_title="TailorTalk",
    page_icon="📅",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ------------------------ State Initialization ------------------------
if "messages" not in st.session_state:
    st.session_state.messages = []
    st.session_state.user_id = str(uuid.uuid4())
    st.session_state.quick_message = ""
    st.session_state.send_quick = False

# ------------------------ Styles ------------------------
st.markdown("""
<style>
.main-header {
    text-align: center;
    color: #1f77b4;
    margin-bottom: 30px;
    font-size: 3em;
    font-weight: bold;
}
.chat-message {
    padding: 12px 16px;
    margin: 8px 0;
    border-radius: 18px;
    max-width: 80%;
    word-wrap: break-word;
}
.user-message {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    color: white;
    margin-left: auto;
    text-align: right;
}
.bot-message {
    background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
    color: white;
    margin-right: auto;
    text-align: left;
}
</style>
""", unsafe_allow_html=True)

# ------------------------ Header ------------------------
st.markdown("<h1 class='main-header'>📅 TailorTalk</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center; font-size: 1.2em; color: #666;'>Your AI-Powered Calendar Assistant</p>", unsafe_allow_html=True)

# ------------------------ Sidebar ------------------------
    # ✅ Open calendar in new tab via HTML <a> tag
with st.sidebar:
    st.markdown(
        """
        <a href="http://localhost:9000/calender.html" 
           target="_blank" 
           style="text-decoration: none;">
            <button style="width:100%; padding: 0.4rem 1rem; font-size: 1rem;
                           background-color: #1f77b4; color: white; border: none;
                           border-radius: 5px; cursor: pointer;">
                📅 Open Live Calendar
            </button>
        </a>
        """,
        unsafe_allow_html=True
    )


    st.header("⚡ Quick Actions")
    col1, col2 = st.columns(2)
    with col1:
        if st.button("📊 Check Availability", key="quick_avail"):
            st.session_state.quick_message = "Check my availability"
            st.session_state.send_quick = True
    with col2:
        if st.button("📋 List Events", key="quick_list"):
            st.session_state.quick_message = "List my upcoming events"
            st.session_state.send_quick = True

    if st.button("🗑️ Clear Chat", type="secondary"):
        st.session_state.messages = []
        st.session_state.user_id = None
        st.rerun()

    st.header("🚀 Quick Start")
    st.markdown("""
    - "Check my availability"
    - "Book a meeting tomorrow at 2 PM"
    - "List my upcoming events"
    - "Schedule a project review on 2025-06-30 at 10:00 for 2 hours"
    """)

    st.header("📋 Command Examples")
    with st.expander("Checking Availability"):
        st.markdown("- \"What's my availability this week?\"\n- \"Am I free tomorrow?\"")
    with st.expander("Booking Meetings"):
        st.markdown("- \"Book a meeting on 2025-06-28 at 15:00\"\n- \"Schedule a 2-hour team sync on July 1st at 9 AM\"")
    with st.expander("Listing Events"):
        st.markdown("- \"What's on my calendar?\"\n- \"Show my upcoming meetings\"")

# ------------------------ Welcome Message ------------------------
if not st.session_state.messages:
    st.session_state.messages.append(("TailorTalk", """👋 Hi! I'm TailorTalk, your AI calendar assistant powered by Google Gemini.

I can help you:
• Check your calendar availability
• Book new meetings and events
• List your upcoming events

Just type what you'd like to do with your calendar, and I'll take care of the rest!"""))

# ------------------------ Display Chat ------------------------
st.markdown("### 💬 Chat")
chat_placeholder = st.empty()

def display_chat():
    with chat_placeholder.container():
        for sender, message in st.session_state.messages:
            css_class = "user-message" if sender == "You" else "bot-message"
            icon = "🧑" if sender == "You" else "🤖"
            st.markdown(f'<div class="chat-message {css_class}">{icon} <strong>{sender}:</strong><br>{message}</div>', unsafe_allow_html=True)

display_chat()

# ------------------------ Input Area ------------------------
st.markdown("---")
with st.form("chat_form", clear_on_submit=True):
    col1, col2, col3 = st.columns([6, 1, 1])
    with col1:
        user_input = st.text_input(
            "Type your message here...",
            key="user_input_field",
            placeholder="e.g., 'Check my availability'",
            value=st.session_state.quick_message if st.session_state.send_quick else "",
            label_visibility="collapsed"
        )
    with col2:
        send_clicked = st.form_submit_button("📤", use_container_width=True)
    with col3:
        help_clicked = st.form_submit_button("❓", use_container_width=True)

# ------------------------ Handle Input Submission ------------------------
def process_message(message):
    if message.strip():
        st.session_state.messages.append(("You", message))
        with st.spinner("🤔 TailorTalk is thinking..."):
            try:
                payload = {
                    "message": message,
                    "user_id": st.session_state.user_id
                }
                response = requests.post("http://localhost:8000/chat", json=payload, timeout=30)
                if response.status_code == 200:
                    result = response.json()
                    st.session_state.user_id = result.get("user_id", st.session_state.user_id)
                    st.session_state.messages.append(("TailorTalk", result.get("response", "[No response]")))
                else:
                    st.session_state.messages.append(("TailorTalk", f"❌ API Error: {response.status_code}"))
            except requests.exceptions.RequestException as e:
                st.session_state.messages.append(("TailorTalk", f"❌ Connection error: {e}"))

if help_clicked:
    st.session_state.messages.append(("TailorTalk", """Here are some example commands you can try:

**Availability:**
• "Check my availability"
• "Am I free tomorrow?"

**Booking:**
• "Book a meeting on 2025-06-30 at 14:00"
• "Schedule a 2-hour team sync tomorrow at 9 AM"

**Events:**
• "List my upcoming events"
• "What's on my calendar?"
"""))
    st.rerun()

if send_clicked or st.session_state.send_quick:
    msg = user_input if not st.session_state.send_quick else st.session_state.quick_message
    process_message(msg)
    st.session_state.quick_message = ""
    st.session_state.send_quick = False
    st.rerun()

# ------------------------ Footer ------------------------
st.markdown("---")
col1, col2, col3 = st.columns(3)
col1.caption(f"🕐 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
col2.caption(f"👤 Session ID: {st.session_state.user_id[:8]}...")
col3.caption(f"💬 Messages: {len(st.session_state.messages)}")
