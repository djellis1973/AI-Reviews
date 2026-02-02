# app.py
# AI Menu Assistant – powered by GPT-4o-mini
# For your restaurant / menu website

import streamlit as st
from openai import OpenAI

# ────────────────────────────────────────────────
# Page configuration
# ────────────────────────────────────────────────
st.set_page_config(
    page_title="AI Menu Assistant",
    page_icon="🍽️",
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
# System prompt – customize this to match your restaurant/menu
# ────────────────────────────────────────────────
SYSTEM_PROMPT = """
You are a friendly, helpful assistant for a restaurant menu.
You know our menu very well and love recommending dishes.

Key facts about our restaurant:
- We serve a mix of Vietnamese street food, French-inspired dishes, and some international favorites.
- Popular items: phở, bún chả, bánh mì, dim sum baskets, coq au vin, crème brûlée.
- We have vegetarian, vegan, and gluten-free options.
- Price range: €€ (mid-range, good value).
- Location vibe: cozy, modern, great for dates or small groups.

Rules:
- Be warm, enthusiastic and concise.
- Always suggest 1–3 dishes based on what the user says.
- If they mention budget, preferences (spicy, vegetarian, etc.), allergies or occasion → adapt recommendations.
- If unsure, ask clarifying questions.
- Never make up prices or unavailable items.
- End responses naturally – invite more questions.
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
st.title("🍽️ AI Menu Assistant")
st.markdown("Ask me anything about our menu, get recommendations, or find the perfect dish for you!")

with st.sidebar:
    st.header("Quick Actions")
    if st.button("Clear Chat History"):
        st.session_state.messages = [{"role": "system", "content": SYSTEM_PROMPT}]
        st.rerun()
    
    st.markdown("---")
    st.caption("Powered by GPT-4o-mini • Your API key is securely stored in secrets")

# ────────────────────────────────────────────────
# Display chat history
# ────────────────────────────────────────────────
for message in st.session_state.messages[1:]:  # skip system prompt
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# ────────────────────────────────────────────────
# User input
# ────────────────────────────────────────────────
if prompt := st.chat_input("What would you like to eat today? 😊"):
    
    # Add user message to history and display
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # Generate assistant response
    with st.chat_message("assistant"):
        message_placeholder = st.empty()
        full_response = ""

        try:
            stream = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=st.session_state.messages,
                temperature=0.7,
                max_tokens=500,
                stream=True
            )

            for chunk in stream:
                if chunk.choices[0].delta.content is not None:
                    full_response += chunk.choices[0].delta.content
                    message_placeholder.markdown(full_response + "▌")

            message_placeholder.markdown(full_response)

        except Exception as e:
            st.error(f"Something went wrong: {str(e)}")
            full_response = "Sorry, I couldn't connect right now. Please try again!"

    # Save assistant response
    st.session_state.messages.append({"role": "assistant", "content": full_response})
