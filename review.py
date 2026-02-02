# app.py
# General Restaurant Reviewer & Menu Assistant – powered by GPT-4o-mini

import streamlit as st
from openai import OpenAI

# ────────────────────────────────────────────────
# Page configuration
# ────────────────────────────────────────────────
st.set_page_config(
    page_title="Restaurant Reviewer & Menu AI",
    page_icon="🍴",
    layout="centered",
    initial_sidebar_state="expanded"
)

# ────────────────────────────────────────────────
# Securely load OpenAI client from Streamlit secrets
# ────────────────────────────────────────────────
if "OPENAI_API_KEY" not in st.secrets:
    st.error("OPENAI_API_KEY is missing from secrets. Add it in Settings → Secrets.")
    st.stop()

client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

# ────────────────────────────────────────────────
# System prompt – now focused on general restaurant reviews + menu help
# ────────────────────────────────────────────────
SYSTEM_PROMPT = """
You are a knowledgeable, friendly restaurant reviewer and food expert with broad knowledge of dining worldwide (Paris, Tokyo, Hanoi, etc.).
You provide honest, detailed, balanced reviews based on common sources like Tabelog, Tripadvisor, Google, local guides.

When a user asks about a specific restaurant (name + location if given):
- Include: location/vibe, specialties/standout dishes, ratings & review highlights (pros/cons), who it's good for, overall recommendation (yes/maybe/skip + why).
- Be factual and mention if info seems limited or dated.
- Keep responses 200–400 words unless asked for more.

If the user asks for recommendations, menu suggestions, pairings, or talks about food preferences:
- Suggest dishes thoughtfully (consider budget, dietary needs, occasion).
- If no specific restaurant is mentioned, you can offer general ideas or ask for more details.

Be warm, enthusiastic, concise and helpful.
Always invite follow-up questions.
Use markdown for formatting (bold, lists, etc.) when it improves readability.
"""

# ────────────────────────────────────────────────
# Initialize chat history
# ────────────────────────────────────────────────
if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "system", "content": SYSTEM_PROMPT}
    ]

# ────────────────────────────────────────────────
# UI – Header & Sidebar
# ────────────────────────────────────────────────
st.title("🍴 Restaurant Reviewer & Menu AI")
st.markdown(
    "Ask me to review any restaurant (e.g. 'Review Ryukyu Shokudo Tokyo' or 'Best dim sum in Paris') "
    "or get menu recommendations, dish suggestions, pairings, etc."
)

with st.sidebar:
    st.header("Quick Controls")
    if st.button("Clear Chat History"):
        st.session_state.messages = [{"role": "system", "content": SYSTEM_PROMPT}]
        st.rerun()
    
    st.markdown("---")
    st.caption("Powered by GPT-4o-mini • API key stored securely in secrets")

# ────────────────────────────────────────────────
# Display existing chat messages (skip system prompt)
# ────────────────────────────────────────────────
for message in st.session_state.messages[1:]:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# ────────────────────────────────────────────────
# User input handling
# ────────────────────────────────────────────────
if prompt := st.chat_input("Ask about a restaurant or menu..."):
    
    # Add & display user message
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # Generate response
    with st.chat_message("assistant"):
        message_placeholder = st.empty()
        full_response = ""

        try:
            stream = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=st.session_state.messages,
                temperature=0.75,          # slightly more creative for reviews
                max_tokens=800,
                stream=True
            )

            for chunk in stream:
                if chunk.choices[0].delta.content is not None:
                    full_response += chunk.choices[0].delta.content
                    message_placeholder.markdown(full_response + "▌")

            message_placeholder.markdown(full_response)

        except Exception as e:
            st.error(f"Error: {str(e)}")
            full_response = "Sorry — I couldn't get a response right now. Try again?"

    # Save assistant's reply
    st.session_state.messages.append({"role": "assistant", "content": full_response})
