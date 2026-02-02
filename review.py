# app.py
# Restaurant Reviewer & Menu AI – with URL pre-population support
# Powered by GPT-4o-mini

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
# System prompt (general restaurant reviewer mode)
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
# Handle pre-filled query from URL (?query=...)
# ────────────────────────────────────────────────
pre_filled = st.query_params.get("query", None)
if pre_filled and isinstance(pre_filled, str):
    decoded_query = pre_filled  # already decoded by Streamlit in recent versions
    # Only add if chat is fresh (prevents duplicates on refresh)
    if len(st.session_state.messages) == 1:  # only system prompt exists
        st.session_state.messages.append({"role": "user", "content": decoded_query})

# ────────────────────────────────────────────────
# Quick search buttons logic
# ────────────────────────────────────────────────
def add_quick_query(query):
    if st.session_state.messages and st.session_state.messages[-1]["content"] == query:
        return
    st.session_state.messages.append({"role": "user", "content": query})
    st.rerun()

# ────────────────────────────────────────────────
# UI – Main area
# ────────────────────────────────────────────────
st.title("🍴 Restaurant Reviewer & Menu AI")
st.markdown(
    "Review restaurants worldwide or get dish/menu recommendations. "
    "Use quick buttons or type your question!"
)

# ────────────────────────────────────────────────
# Sidebar with quick buttons
# ────────────────────────────────────────────────
with st.sidebar:
    st.header("Quick Searches")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("Best dim sum Paris", use_container_width=True):
            add_quick_query("Best dim sum in Paris")
        
        if st.button("Okinawan Tokyo", use_container_width=True):
            add_quick_query("Best Okinawan food in Tokyo")
        
        if st.button("Hanoi Old Quarter eats", use_container_width=True):
            add_quick_query("Best street food and restaurants in Hanoi Old Quarter under 20€")
    
    with col2:
        if st.button("Ryukyu Shokudo review", use_container_width=True):
            add_quick_query("Review Ryukyu Shokudo in Tokyo")
        
        if st.button("Paris Chinese food", use_container_width=True):
            add_quick_query("Best Chinese restaurants in Paris 13th arrondissement")
        
        if st.button("Budget Hanoi dinner", use_container_width=True):
            add_quick_query("Good dinner options in Hanoi under 20 euros")

    st.markdown("---")
    
    if st.button("Clear Chat History", type="primary"):
        st.session_state.messages = [{"role": "system", "content": SYSTEM_PROMPT}]
        st.rerun()
    
    st.caption("Powered by GPT-4o-mini • API key in secrets")

# ────────────────────────────────────────────────
# Display chat messages (skip system prompt)
# ────────────────────────────────────────────────
for message in st.session_state.messages[1:]:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# ────────────────────────────────────────────────
# Auto-generate response if needed (for pre-filled query or quick buttons)
# ────────────────────────────────────────────────
if st.session_state.messages and st.session_state.messages[-1]["role"] == "user":
    # Generate only if no assistant reply yet for the last user message
    if len(st.session_state.messages) % 2 == 0:  # even length means user just added, no reply
        with st.chat_message("assistant"):
            message_placeholder = st.empty()
            full_response = ""

            try:
                stream = client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=st.session_state.messages,
                    temperature=0.75,
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
                full_response = "Sorry — couldn't get a response. Try again?"

            st.session_state.messages.append({"role": "assistant", "content": full_response})

# ────────────────────────────────────────────────
# Normal chat input
# ────────────────────────────────────────────────
if prompt := st.chat_input("Ask about any restaurant or menu..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        message_placeholder = st.empty()
        full_response = ""

        try:
            stream = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=st.session_state.messages,
                temperature=0.75,
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
            full_response = "Sorry — I couldn't respond right now."

    st.session_state.messages.append({"role": "assistant", "content": full_response})
