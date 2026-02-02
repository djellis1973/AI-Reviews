import streamlit as st
from openai import OpenAI

st.set_page_config(
    page_title="Restaurant AI",
    page_icon="🍴",
    layout="wide",                  # Better for embeds/iframes
    initial_sidebar_state="collapsed"  # ← Starts with sidebar closed/hidden
)

# Load API key
if "OPENAI_API_KEY" not in st.secrets:
    st.error("OPENAI_API_KEY missing in secrets.")
    st.stop()

client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

# System prompt
SYSTEM_PROMPT = """
You are a friendly restaurant reviewer and food expert.
When asked about a restaurant, give a balanced summary:
- location & vibe
- specialties / best dishes
- ratings & review highlights
- who it's good for
- recommendation (yes/maybe/skip + why)
Be factual, concise, helpful. Use markdown when useful.
"""

# Initialize messages
if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "system", "content": SYSTEM_PROMPT}
    ]

# Try to get pre-filled query (robust fallback for Cloud quirks)
pre_filled = None
# Modern method
if "query" in st.query_params:
    val = st.query_params["query"]
    pre_filled = val[0] if isinstance(val, list) else val
# Fallback to experimental (often more reliable on Cloud initial load)
if not pre_filled:
    try:
        old_params = st.experimental_get_query_params()
        if "query" in old_params:
            pre_filled = old_params["query"][0]
    except:
        pass

# Apply prefill only on fresh chat
if pre_filled and len(st.session_state.messages) == 1:
    st.session_state.messages.append({"role": "user", "content": pre_filled})

# Title
st.title("Restaurant AI")

# Show messages
for msg in st.session_state.messages[1:]:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# Auto-respond if last is user (and not already responded)
if st.session_state.messages and st.session_state.messages[-1]["role"] == "user":
    # Only auto-respond once per user message
    if len(st.session_state.messages) % 2 == 1:  # odd length after adding user → needs assistant reply
        with st.chat_message("assistant"):
            placeholder = st.empty()
            response = ""
            try:
                stream = client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=st.session_state.messages,
                    temperature=0.7,
                    stream=True
                )
                for chunk in stream:
                    if chunk.choices[0].delta.content is not None:
                        response += chunk.choices[0].delta.content
                        placeholder.markdown(response + "▌")
                placeholder.markdown(response)
                st.session_state.messages.append({"role": "assistant", "content": response})
            except Exception as e:
                st.error("Could not get response. Try again.")
                # Optionally log e somewhere

# Chat input
if prompt := st.chat_input("Ask about any restaurant..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)
    
    with st.chat_message("assistant"):
        placeholder = st.empty()
        response = ""
        try:
            stream = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=st.session_state.messages,
                temperature=0.7,
                stream=True
            )
            for chunk in stream:
                if chunk.choices[0].delta.content is not None:
                    response += chunk.choices[0].delta.content
                    placeholder.markdown(response + "▌")
            placeholder.markdown(response)
            st.session_state.messages.append({"role": "assistant", "content": response})
        except Exception as e:
            st.error("Could not get response. Try again.")

# Sidebar content (only visible when expanded)
with st.sidebar:
    st.markdown("### Controls")
    if st.button("Clear chat"):
        st.session_state.messages = [{"role": "system", "content": SYSTEM_PROMPT}]
        st.rerun()
    
    st.caption("Sidebar starts collapsed. Click the ← arrow in the top-left to open.")
