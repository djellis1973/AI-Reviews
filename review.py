import streamlit as st
from openai import OpenAI

st.set_page_config(
    page_title="Restaurant AI",
    page_icon="🍴",
    layout="wide",
    initial_sidebar_state="collapsed"          # Sidebar starts closed — what you wanted
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

# Initialize chat history
if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "system", "content": SYSTEM_PROMPT}
    ]

# Get pre-filled query from URL (?query=...) — robust handling
pre_filled = None

# Preferred modern way
if "query" in st.query_params:
    val = st.query_params["query"]
    pre_filled = val[0] if isinstance(val, list) else val

# Fallback for older Streamlit Cloud behavior
if not pre_filled:
    try:
        old_params = st.experimental_get_query_params()
        if "query" in old_params:
            pre_filled = old_params["query"][0]
    except:
        pass

# Add pre-filled message only once (on first load / fresh session)
if pre_filled and len(st.session_state.messages) == 1:
    st.session_state.messages.append({"role": "user", "content": pre_filled})

# Main title
st.title("Restaurant AI")

# Display chat history (skip system prompt)
for msg in st.session_state.messages[1:]:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# Auto-generate AI response when last message is from user (pre-fill or user input)
# Only trigger if we haven't answered yet (length even after user message added)
if (
    st.session_state.messages
    and st.session_state.messages[-1]["role"] == "user"
    and len(st.session_state.messages) % 2 == 0   # even length = just added user → needs reply
):
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
            st.error(f"Could not get response: {str(e)}")

# User chat input (manual questions)
if prompt := st.chat_input("Ask about any restaurant..."):
    # Add user message
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # Generate assistant response
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
            st.error(f"Could not get response: {str(e)}")

# Sidebar (only visible when user clicks the arrow)
with st.sidebar:
    st.markdown("### Chat Controls")
    if st.button("Clear chat"):
        st.session_state.messages = [{"role": "system", "content": SYSTEM_PROMPT}]
        st.rerun()

    st.caption("Sidebar is collapsed by default. Click ← in top-left to open.")
