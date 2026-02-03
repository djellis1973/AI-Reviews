import streamlit as st
from openai import OpenAI

st.set_page_config(
    page_title="Restaurant Review",
    page_icon="🍴",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Hide sidebar completely
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
            margin-bottom: 0.8rem;
        }
        h2 {
            margin-top: 0;
            text-align: center;
            color: #555;
        }
        hr {
            margin: 1.8rem 0;
        }
    </style>
""", unsafe_allow_html=True)

# Load API key
if "OPENAI_API_KEY" not in st.secrets:
    st.error("OPENAI_API_KEY missing in secrets.")
    st.stop()

client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

# Updated system prompt — tells model to lead with reviews and expand on them
SYSTEM_PROMPT = """
You are a friendly restaurant reviewer and food expert.

When asked about a restaurant, structure your answer like this:
1. Start with the most interesting and balanced REVIEW HIGHLIGHTS from recent visitors.
   - Include direct quotes or very close paraphrases from real reviews
   - Mention common praise AND common complaints
   - Talk about service, atmosphere, value for money, consistency
   - Expand on this section — make it the longest / most detailed part

2. Then briefly cover:
   - location & overall vibe
   - specialties / most recommended dishes
   - who it's good for (families, couples, solo, business, tourists…)

3. Finish with clear recommendation:
   - Yes / Maybe / Skip + short reason

Be factual, use markdown (bullet points, bold, quotes), stay balanced and helpful.
"""

# Initialize messages
if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "system", "content": SYSTEM_PROMPT}
    ]

# Get restaurant name from URL (?query=...)
pre_filled = None
if "query" in st.query_params:
    val = st.query_params["query"]
    pre_filled = val[0] if isinstance(val, list) else val

# Fallback for older Streamlit versions
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

# Clean name (remove "Review of ..." if someone added it)
review_prefix = "Review of "
if pre_filled.lower().startswith(review_prefix.lower()):
    clean_name = pre_filled[len(review_prefix):].strip()
else:
    clean_name = pre_filled.strip()

# Create nice-looking titles
main_title = f"Review of {clean_name}"
subtitle = f"Reviews – {clean_name.split(' in ')[0].strip()}"   # e.g. "Reviews – La Tagliatella Travessera De Gràcia"

# Set browser tab title
st.set_page_config(page_title=main_title, page_icon="🍴", layout="wide")

# ── Header ────────────────────────────────────────────────
st.title(main_title)
st.markdown(f"### {subtitle}")           # smaller centered sub-header
st.markdown("---")

# Add user query only once
if len(st.session_state.messages) == 1:
    st.session_state.messages.append({"role": "user", "content": pre_filled})

# Generate review only once
if len(st.session_state.messages) == 2:
    with st.spinner("Gathering reviews & insights..."):
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

# Show already generated content
elif len(st.session_state.messages) > 2:
    last_msg = st.session_state.messages[-1]
    if last_msg["role"] == "assistant":
        st.markdown(last_msg["content"])
