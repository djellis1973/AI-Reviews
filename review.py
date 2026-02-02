import streamlit as st
from openai import OpenAI

st.set_page_config(
    page_title="Restaurant Review",
    page_icon="🍴",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Completely hide sidebar & collapse button
st.markdown("""
    <style>
        section[data-testid="stSidebar"] {
            display: none !important;
        }
        [data-testid="collapsedControl"] {
            display: none !important;
        }
        .stApp {
            max-width: 1000px;
            margin: 0 auto;
            padding: 2rem 1rem;
        }
        h1 {
            text-align: center;
            margin-bottom: 2rem;
        }
        hr {
            margin: 2rem 0;
        }
    </style>
""", unsafe_allow_html=True)

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

# Get query from URL
pre_filled = None

if "query" in st.query_params:
    val = st.query_params["query"]
    pre_filled = val[0] if isinstance(val, list) else val

if not pre_filled:
    try:
        old_params = st.experimental_get_query_params()
        if "query" in old_params:
            pre_filled = old_params["query"][0]
    except:
        pass

if not pre_filled:
    st.warning("No restaurant specified. Please add ?query=... to the URL.")
    st.stop()

# Clean up the title: remove leading "Review " if present, capitalize nicely
review_prefix = "Review "
if pre_filled.lower().startswith(review_prefix.lower()):
    clean_name = pre_filled[len(review_prefix):].strip()
else:
    clean_name = pre_filled.strip()

# Make title case look good (you can adjust this logic if needed)
page_title = f"Review of {clean_name}"

# Set dynamic page title (browser tab)
st.set_page_config(page_title=page_title, page_icon="🍴", layout="wide")

# Show nice H1 header
st.title(page_title)

st.markdown("---")

# Add query to messages only once (for the AI)
if len(st.session_state.messages) == 1:
    st.session_state.messages.append({"role": "user", "content": pre_filled})

# Generate review only once
if len(st.session_state.messages) == 2:
    with st.spinner("Loading review..."):
        try:
            stream = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=st.session_state.messages,
                temperature=0.7,
                stream=True
            )

            response_container = st.empty()
            response = ""

            for chunk in stream:
                if chunk.choices[0].delta.content is not None:
                    response += chunk.choices[0].delta.content
                    response_container.markdown(response + "▌")

            response_container.markdown(response)

            st.session_state.messages.append({"role": "assistant", "content": response})

        except Exception as e:
            st.error(f"Could not generate review: {str(e)}")

# Show already generated review
elif len(st.session_state.messages) > 2:
    last_msg = st.session_state.messages[-1]
    if last_msg["role"] == "assistant":
        st.markdown(last_msg["content"])
