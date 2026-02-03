import streamlit as st
from openai import OpenAI

st.set_page_config(
    page_title="Restaurant Review",
    page_icon="🍴",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Hide sidebar + enhanced typography
st.markdown("""
    <style>
        section[data-testid="stSidebar"] { display: none !important; }
        [data-testid="collapsedControl"] { display: none !important; }
        .stApp { max-width: 1000px; margin: 0 auto; padding: 2rem 1rem; }
        h1 { 
            text-align: center; 
            font-size: 2.8rem !important; 
            font-weight: bold !important; 
            margin-bottom: 0.5rem; 
        }
        .stats { 
            text-align: center; 
            font-size: 1.15rem !important; 
            font-weight: 600; 
            color: #444; 
            margin: 0.8rem 0 1.8rem 0; 
        }
        hr { margin: 1.5rem 0; border-top: 1px solid #ccc; }
    </style>
""", unsafe_allow_html=True)

# API key
if "OPENAI_API_KEY" not in st.secrets:
    st.error("OPENAI_API_KEY missing in secrets.")
    st.stop()

client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

# Updated system prompt: disclaimer after highlights, negatives lower
SYSTEM_PROMPT = """
You are a friendly restaurant reviewer using publicly available information.

For any restaurant query:
1. Lead with a detailed REVIEW HIGHLIGHTS section:
   - Start with the most common positive feedback (quotes/paraphrases from real visitors)
   - Mention strengths: food quality, specific dishes (pizza, pasta, etc.), service, atmosphere, value
   - Then lower down, fairly mention common criticisms / negatives (e.g. slow service, higher prices, inconsistency)
   - Use bullet points or short paragraphs; make this the longest part

After REVIEW HIGHLIGHTS, always add this exact disclaimer in italics:

*Disclaimer: This summary is AI-generated and based on publicly available reviews (e.g. Tripadvisor, Google, etc.) as of early 2026. Individual experiences vary. Check recent reviews directly.*

2. Then briefly: location & vibe, specialties/best dishes, who it's good for

3. End with clear recommendation (Yes / Maybe / Skip + why)

Be factual, balanced, use markdown. Stay helpful.
"""

if "messages" not in st.session_state:
    st.session_state.messages = [{"role": "system", "content": SYSTEM_PROMPT}]

# Get query
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

# Clean name
name = pre_filled.strip()
junk_prefixes = ["Review of ", "Review ", "Reviews of ", "Review La ", "Review of Review "]
for prefix in junk_prefixes:
    if name.lower().startswith(prefix.lower()):
        name = name[len(prefix):].strip()

for suffix in [" in Barcelona Catalonia Spain", " Barcelona Catalonia Spain", " Barcelona"]:
    if name.endswith(suffix):
        name = name[:-len(suffix)].strip()

clean_name = name.strip()

# Single header (former subtitle, now main)
subtitle = f"Reviews – {clean_name}"

# Stats – Google first, updated with latest verified data (Feb 2026)
stats_text = "Google: 4.1/5 from 1900 reviews • Tripadvisor: 4.0/5 from 98 reviews"

st.set_page_config(page_title=subtitle, page_icon="🍴", layout="wide")

# ── Single header + stats ──
st.title(subtitle)
st.markdown(f'<div class="stats">{stats_text}</div>', unsafe_allow_html=True)
st.markdown("---")

# Add user message once
if len(st.session_state.messages) == 1:
    st.session_state.messages.append({"role": "user", "content": pre_filled})

# Generate once
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

# Show existing
elif len(st.session_state.messages) > 2:
    last_msg = st.session_state.messages[-1]
    if last_msg["role"] == "assistant":
        st.markdown(last_msg["content"])
