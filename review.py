import streamlit as st
from openai import OpenAI

st.set_page_config(
    page_title="Restaurant AI",
    page_icon="🍴",
    layout="centered"
)

# Load API key from secrets
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

# Handle pre-filled query from URL (?query=...)
query_from_url = st.query_params.get("query", None)
if query_from_url and len(st.session_state.messages) == 1:
    # Take first value if it's a list (Streamlit sometimes returns list)
    if isinstance(query_from_url, list):
        query_from_url = query_from_url[0]
    st.session_state.messages.append({"role": "user", "content": query_from_url})

# Title
st.title("Restaurant AI")

# Show chat history (skip system message)
for msg in st.session_state.messages[1:]:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# Auto-respond if last message is from user (prefill or manual input)
if st.session_state.messages and st.session_state.messages[-1]["role"] == "user":
    if len(st.session_state.messages) % 2 == 0:  # no assistant reply yet
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
            except Exception as e:
                st.error("Could not get response. Try again.")
                response = ""

            st.session_state.messages.append({"role": "assistant", "content": response})

# Normal chat input
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
        except Exception as e:
            st.error("Could not get response. Try again.")
            response = ""

        st.session_state.messages.append({"role": "assistant", "content": response})

# Small clear button in sidebar
with st.sidebar:
    if st.button("Clear chat"):
        st.session_state.messages = [{"role": "system", "content": SYSTEM_PROMPT}]
        st.rerun()
