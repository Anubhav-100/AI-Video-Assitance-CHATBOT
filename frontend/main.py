from __future__ import annotations

import streamlit as st

from ui.about_page import render_about_page
from ui.components import render_brand, render_sidebar_promo, render_topbar
from ui.dashboard_page import render_dashboard
from ui.history_page import render_history_page
from ui.styles import load_css

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
MEDIA_TYPES = ["mp4", "mov", "mkv", "webm", "avi", "mp3", "wav", "m4a", "flac", "aac", "ogg"]

st.set_page_config(
    page_title="AI Video Assistant",
    page_icon="▶",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ---------------------------------------------------------------------------
# Helper / state functions
# ---------------------------------------------------------------------------

def init_state() -> None:
    """Initialize Streamlit session state."""
    defaults = {
        "analysis_results": None,
        "session_id": None,
        "chat_history": [],
        "source_mode": "Video URL",
        "engine": "whisper",
        "dark_mode": True,
        "navigation": "Dashboard",
        "pending_navigation": None,
        "auto_restore_attempted": False,
        "url_input": "",
        "media_upload": None,
    }

    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value

    if st.session_state.analysis_results is None and not st.session_state.auto_restore_attempted:
        auto_restore_current_analysis()


def auto_restore_current_analysis() -> None:
    """Restore the active analysis from query params or latest SQLite history on page refresh."""
    st.session_state.auto_restore_attempted = True
    try:
        import importlib
        import api_client

        if not hasattr(api_client, "list_analysis_history"):
            importlib.reload(api_client)

        raw_id = st.query_params.get("analysis_id")
        detail = None
        if raw_id and str(raw_id).isdigit():
            try:
                detail = api_client.get_analysis_history(int(raw_id))
            except Exception:
                st.query_params.pop("analysis_id", None)
                detail = None

        if detail is None:
            items = api_client.list_analysis_history(limit=1)
            if items:
                detail = api_client.get_analysis_history(items[0]["id"])

        if detail:
            st.session_state.analysis_results = {
                "title": detail.get("title", ""),
                "transcript": detail.get("transcript", ""),
                "summary": detail.get("summary", ""),
                "action_items": detail.get("action_items", ""),
                "key_decisions": detail.get("key_decisions", ""),
                "open_questions": detail.get("open_questions", ""),
                "video_id": detail.get("video_id"),
                "source": detail.get("source", ""),
                "engine": detail.get("engine", ""),
            }
            st.session_state.session_id = detail.get("session_id")
            st.session_state.chat_history = []
            if detail.get("id") is not None:
                st.query_params["analysis_id"] = str(detail["id"])
    except Exception:
        # Backend may be offline on initial load; render empty dashboard gracefully.
        pass


def reset_current_analysis(clear_inputs: bool = False) -> None:
    """Reset analysis-related session state."""
    st.session_state.analysis_results = None
    st.session_state.session_id = None
    st.session_state.chat_history = []
    st.session_state.auto_restore_attempted = True
    st.query_params.pop("analysis_id", None)

    if clear_inputs:
        st.session_state.url_input = ""
        st.session_state.source_mode = "Video URL"
        st.session_state.media_upload = None


# ---------------------------------------------------------------------------
# Sidebar & shared pages
# ---------------------------------------------------------------------------

def render_sidebar() -> str:
    if st.session_state.get("pending_navigation"):
        st.session_state.navigation = st.session_state.pending_navigation
        st.session_state.pending_navigation = None

    with st.sidebar:
        render_brand()
        st.markdown("<div style='height:5px'></div>", unsafe_allow_html=True)
        if st.button("＋  New analysis", use_container_width=True, key="new_analysis_sidebar"):
            reset_current_analysis(clear_inputs=True)
            st.session_state.pending_navigation = "Dashboard"
            st.rerun()
        page = st.radio(
            "Navigation",
            ["Dashboard", "History", "Settings", "About"],
            format_func=lambda item: {
                "Dashboard": "⌂   Dashboard",
                "History": "◷   History",
                "Settings": "⚙   Settings",
                "About": "ⓘ   About",
            }[item],
            label_visibility="collapsed",
            key="navigation",
        )
        render_sidebar_promo()
        st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)
        st.toggle("Dark appearance", key="dark_mode")
    return page


def render_settings_page() -> None:
    render_topbar()
    st.markdown("## Settings")
    st.caption("Basic interface preferences. Backend engine credentials remain in your existing environment configuration.")
    st.selectbox("Default transcription engine", ["Whisper", "Sarvam"], key="default_engine_setting")
    st.info("Supported media extensions are configured in MEDIA_TYPES near the top of main.py. Match this list to core.audio_processor.py.")


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    init_state()
    load_css(dark_mode=st.session_state.dark_mode)
    page = render_sidebar()
    if page == "Dashboard":
        render_dashboard(MEDIA_TYPES)
    elif page == "History":
        render_history_page()
    elif page == "Settings":
        render_settings_page()
    else:
        render_about_page()
