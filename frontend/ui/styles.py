"""Load the standalone CSS stylesheet for the Streamlit interface."""

from pathlib import Path

import streamlit as st


def load_css(dark_mode: bool = False) -> None:
    css_path = Path(__file__).with_name("styles.css")
    css = css_path.read_text(encoding="utf-8")
    if dark_mode:
        css += """
        :root { --app-bg:#111629; --surface:#1c2440; --surface-solid:#202844; --ink:#edf0ff; --muted:#a8b1d0; --line:#343d60; }
        .stApp { background:radial-gradient(ellipse at 70% 7%,rgba(104,82,255,.18),transparent 33%),#111629 !important; color:#edf0ff; }
        .hero-title,.section-heading,.chat-header,.video-title,.video-meta,.timeline-title { color:#edf0ff !important; }
        .hero-copy { color:#cbd2ed !important; }
        [data-testid="stVerticalBlockBorderWrapper"],.result-card,.transcript-card,.timeline-card { background:rgba(29,37,64,.96) !important; border-color:#343d62 !important; }
        .result-card .card-title,.result-card p,.result-card ul,.transcript-title-row,.chat-bubble { color:#e0e5fb !important; }
        .chat-bubble.assistant { background:#252c4d !important; border-color:#39416a !important; }
        .chat-bubble.user { background:#343263 !important; border-color:#4b4689 !important; }
        .chat-suggestion { background:#222b49 !important; color:#dfe4ff !important; border-color:#454d75 !important; }
        [data-testid="stTextInput"] input,[data-testid="stSelectbox"] div[data-baseweb="select"] > div,[data-testid="stChatInput"] textarea { background:#202844 !important; color:#edf0ff !important; border-color:#424b70 !important; }
        [data-testid="stFileUploader"] section { background:#202844 !important; border-color:#555d8c !important; }
        [data-testid="stExpander"] { background:#202844 !important; border-color:#343d62 !important; }
        """
    st.markdown(f"<style>{css}</style>", unsafe_allow_html=True)
