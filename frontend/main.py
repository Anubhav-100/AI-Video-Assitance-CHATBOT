from __future__ import annotations
from ui.about_page import render_about_page

import tempfile
from pathlib import Path
from typing import Any, Tuple, Optional

import streamlit as st

from ui.components import (
    render_brand,
    render_chat_header,
    render_chat_messages,
    render_empty_state,
    render_hero_heading,
    render_hero_visual,
    render_list_card,
    render_section_heading,
    render_sidebar_promo,
    render_summary_card,
    render_suggestions,
    render_timeline,
    render_topbar,
    render_transcript_card,
    render_video_overview,
)
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
        "url_input": "",
        "media_upload": None,
    }

    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


def get_backend_functions() -> Tuple[Optional[Any], Optional[Any], Optional[Any]]:
    """Import API client functions lazily."""
    try:
        from api_client import run_pipeline, rag_query

        return run_pipeline, rag_query, None

    except Exception as exc:
        st.error(f"API Client Import Error: {type(exc).__name__}: {exc}")
        return None, None, exc

def reset_current_analysis(clear_inputs: bool = False) -> None:
    """Reset analysis-related session state."""
    st.session_state.analysis_results = None
    st.session_state.session_id = None
    st.session_state.chat_history = []

    if clear_inputs:
        st.session_state.url_input = ""
        st.session_state.source_mode = "Video URL"
        st.session_state.media_upload = None

# ---------------------------------------------------------------------------
# Core actions
# ---------------------------------------------------------------------------

def execute_analysis(source: str, engine: str, uploaded_file: Optional[Any] = None) -> bool:
    """Run video analysis through the FastAPI backend."""

    reset_current_analysis()

    run_pipeline, _, import_error = get_backend_functions()

    if run_pipeline is None:
        st.error("Could not import the API client.")
        st.caption(f"Import detail: {type(import_error).__name__}: {import_error}")  
        return False

    actual_source = source
    temporary_path: Optional[Path] = None

    try:
        # Handle uploaded media
        if uploaded_file is not None:
            suffix = Path(uploaded_file.name).suffix.lower() or ".media"

            with tempfile.NamedTemporaryFile(
                prefix="ai_video_upload_",
                suffix=suffix,
                delete=False
            ) as temp_file:
                temp_file.write(uploaded_file.getvalue())
                temporary_path = Path(temp_file.name)

            actual_source = str(temporary_path)

        with st.status("Analyzing your video...", expanded=True) as status:

            st.write("Processing media, transcribing, generating insights, and building the RAG index.")

            output = run_pipeline(actual_source, engine)

            # Validate backend response
            if not isinstance(output, dict):
                raise TypeError("run_pipeline() did not return a dictionary.")

            session_id = output.get("session_id")

            if not session_id:
                raise ValueError("Backend response does not contain a session_id.")

            # Store analysis results
            results = {
                key: value
                for key, value in output.items()
                if key != "session_id"
            }

            st.session_state.analysis_results = results
            st.session_state.session_id = session_id
            st.session_state.chat_history = []

            status.update(label="Analysis completed successfully", state="complete", expanded=False)

        st.toast("Your video analysis is ready.", icon="✅")

        return True

    except Exception as exc:
        st.error(f"Analysis failed: {exc}")
        st.info(
            "Check the FastAPI backend logs and verify "
            "that the media source and transcription engine are supported."
        )
        return False

    finally:
        if temporary_path is not None:
            try:
                temporary_path.unlink(missing_ok=True)
            except OSError:
                st.warning(
                    "The temporary upload could not be removed automatically."
                )


def submit_chat_question(question: str) -> None:
    """Send a question to the FastAPI RAG endpoint."""

    question = question.strip()

    if not question:
        return

    session_id = st.session_state.session_id

    if not session_id:
        st.warning("Analyze a video first to enable chat.")
        return

    _, rag_query, import_error = get_backend_functions()

    if rag_query is None:
        st.error(f"Could not import rag_query(): {import_error}")
        return

    st.session_state.chat_history.append(
        {"role": "user", "content": question}
    )

    try:
        with st.spinner("Thinking about your video..."):

            answer = rag_query(session_id, question)

        st.session_state.chat_history.append(
            {
                "role": "assistant",
                "content": str(answer)
            }
        )

    except Exception as exc:
        st.session_state.chat_history.append(
            {
                "role": "assistant",
                "content": f"An error occurred: {exc}"
            }
        )

# ---------------------------------------------------------------------------
# UI rendering functions
# ---------------------------------------------------------------------------
def render_sidebar() -> str:
    with st.sidebar:
        render_brand()
        st.markdown("<div style='height:5px'></div>", unsafe_allow_html=True)
        if st.button("＋  New analysis", use_container_width=True, key="new_analysis_sidebar"):
            reset_current_analysis(clear_inputs=True)
            st.session_state.navigation = "Dashboard"
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

def render_source_input() -> None:
    with st.container(border=True):
        st.markdown('<div class="source-box-label">Choose your video or audio source</div>', unsafe_allow_html=True)
        mode = st.radio(
            "Input method",
            ["Video URL", "Upload File"],
            horizontal=True,
            label_visibility="collapsed",
            key="source_mode",
            format_func=lambda item: "↗  Video URL" if item == "Video URL" else "⇧  Upload File",
        )

        if mode == "Video URL":
            source_col, engine_col, button_col = st.columns([2.45, 0.9, 1.0], gap="small", vertical_alignment="bottom")
            with source_col:
                url = st.text_input(
                    "Video URL",
                    placeholder="Paste a video or audio URL...",
                    label_visibility="collapsed",
                    key="url_input",
                )
            with engine_col:
                engine_label = st.selectbox("Engine", ["Whisper", "Sarvam"], label_visibility="collapsed", key="engine_select_url")
            with button_col:
                clicked = st.button("✦  Analyze", type="primary", use_container_width=True, key="analyze_url")
            if clicked:
                if not url.strip():
                    st.warning("Enter a video or audio URL before starting the analysis.")
                elif execute_analysis(url.strip(), "sarvam" if engine_label == "Sarvam" else "whisper"):
                    st.rerun()
        else:
            file_col, engine_col, button_col = st.columns([2.45, 0.9, 1.0], gap="small", vertical_alignment="bottom")
            with file_col:
                uploaded_file = st.file_uploader(
                    "Choose an audio or video file",
                    type=MEDIA_TYPES,
                    label_visibility="collapsed",
                    help="Adjust MEDIA_TYPES in app.py to match the formats accepted by core.audio_processor.",
                    key="media_upload",
                )

            with engine_col:
                engine_label = st.selectbox("Engine", ["Whisper", "Sarvam"], label_visibility="collapsed", key="engine_select_upload")
            with button_col:
                clicked = st.button("✦  Analyze", type="primary", use_container_width=True, key="analyze_upload")
            if clicked:
                if uploaded_file is None:
                    st.warning("Choose a media file before starting the analysis.")
                elif execute_analysis("", "sarvam" if engine_label == "Sarvam" else "whisper", uploaded_file=uploaded_file):
                    st.rerun()

def render_dashboard() -> None:
    render_topbar()
    hero_col, art_col = st.columns([1.12, 1.0], gap="small", vertical_alignment="center")
    with hero_col:
        render_hero_heading()
        render_source_input()
    with art_col:
        render_hero_visual()

    st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)
    analysis_col, chat_col = st.columns([1.68, 1.0], gap="small")

    with analysis_col:
        with st.container(border=True):
            results = st.session_state.analysis_results
            render_section_heading(completed=bool(results))
            if results:
                render_video_overview(results)
            else:
                render_empty_state()

        # Row 1: Summary
        with st.container():
            render_summary_card(results.get("summary") if results else None)
        
        st.markdown("<div style='height:10px'></div>", unsafe_allow_html=True)

        # Row 2: Action Items and Key Decisions
        actions_col, decisions_col = st.columns(2, gap="small")

        with actions_col:
            render_list_card(
                "Action Items",
                results.get("action_items") if results else None,
                "green",
                "✓",
                "Extracted tasks will appear here.",
            )

        with decisions_col:
            render_list_card(
                "Key Decisions",
                results.get("key_decisions") if results else None,
                "orange",
                "◆",
                "Important decisions will appear here.",
            )

        st.markdown("<div style='height:10px'></div>", unsafe_allow_html=True)
        q_col, t_col = st.columns(2, gap="small")
        with q_col:
            render_list_card(
                "Open Questions",
                results.get("open_questions") if results else None,
                "purple",
                "?",
                "Unanswered questions will appear here.",
            )
        with t_col:
            render_transcript_card(str(results.get("transcript") or "") if results else "")

        st.markdown("<div style='height:10px'></div>", unsafe_allow_html=True)
        render_timeline(completed=bool(st.session_state.analysis_results))

    with chat_col:
        with st.container(border=True):
            has_analysis = bool(st.session_state.session_id)
            render_chat_header(has_analysis)
            render_chat_messages(st.session_state.chat_history)

            if has_analysis:
                st.markdown('<div class="small-muted" style="font-weight:700;margin:12px 0 5px">SUGGESTED QUESTIONS</div>', unsafe_allow_html=True)
                suggestion_cols = st.columns(2, gap="small")
                for idx, question in enumerate(render_suggestions()[:2]):
                    with suggestion_cols[idx]:
                        if st.button(question, key=f"suggestion_{idx}", use_container_width=True):
                            submit_chat_question(question)
                            st.rerun()
                suggestion_cols_2 = st.columns(2, gap="small")
                for idx, question in enumerate(render_suggestions()[2:]):
                    with suggestion_cols_2[idx]:
                        if st.button(question, key=f"suggestion_more_{idx}", use_container_width=True):
                            submit_chat_question(question)
                            st.rerun()
            else:
                st.markdown(
                    '<div class="small-muted" style="text-align:center;margin:10px 0 14px">Example questions will be available after analysis.</div>',
                    unsafe_allow_html=True,
                )

            prompt = st.chat_input(
                "Ask anything about your video...",
                key="video_chat_input",
                disabled=not has_analysis,
            )
            if prompt:
                submit_chat_question(prompt)
                st.rerun()

def _format_history_date(raw_dt: Optional[str]) -> str:
    """Format an ISO-8601 timestamp string for display."""
    if not raw_dt:
        return "Unknown date"
    try:
        from datetime import datetime
        dt = datetime.fromisoformat(raw_dt.replace("Z", "+00:00"))
        return dt.strftime("%Y-%m-%d %H:%M")
    except Exception:
        return str(raw_dt)


def render_history_page() -> None:
    render_topbar()
    st.markdown("## Analysis History")
    st.caption("Saved analyses are stored permanently in SQLite and remain available across restarts.")

    try:
        from api_client import (
            list_analysis_history,
            get_analysis_history,
            delete_analysis_history,
        )
    except Exception as exc:
        st.error(f"API Client Import Error: {type(exc).__name__}: {exc}")
        return

    try:
        history = list_analysis_history()
    except Exception as exc:
        st.error(f"Could not load analysis history from backend: {exc}")
        return

    if not history:
        st.info("No saved analyses yet. Start a new analysis from the Dashboard.")
        return

    for idx, item in enumerate(history):
        analysis_id = item.get("id")
        title = item.get("title") or f"Analysis {idx + 1}"
        created_at = _format_history_date(item.get("created_at"))
        source = item.get("source") or "N/A"
        engine = item.get("engine") or "N/A"
        summary = (item.get("summary") or "").strip()
        summary_preview = f"{summary[:220]}..." if len(summary) > 220 else summary

        with st.container(border=True):
            st.markdown(f"**{title}**")
            st.caption(f"Date: {created_at} · Engine: {engine} · Source: {source}")
            if summary_preview:
                st.write(summary_preview)

            col_open, col_delete, _ = st.columns([1, 1, 4])
            with col_open:
                if st.button("Open Analysis", key=f"open_history_{analysis_id}"):
                    try:
                        detail = get_analysis_history(analysis_id)
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
                        st.session_state.navigation = "Dashboard"
                        st.rerun()
                    except Exception as exc:
                        st.error(f"Failed to open analysis: {exc}")
            with col_delete:
                if st.button("Delete", key=f"delete_history_{analysis_id}"):
                    try:
                        delete_analysis_history(analysis_id)
                        st.toast("Analysis deleted.", icon="🗑️")
                        st.rerun()
                    except Exception as exc:
                        st.error(f"Failed to delete analysis: {exc}")

def render_settings_page() -> None:
    render_topbar()
    st.markdown("## Settings")
    st.caption("Basic interface preferences. Backend engine credentials remain in your existing environment configuration.")
    st.selectbox("Default transcription engine", ["Whisper", "Sarvam"], key="default_engine_setting")
    st.info("Supported media extensions are configured in MEDIA_TYPES near the top of app.py. Match this list to core.audio_processor.py.")

# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    init_state()
    load_css(dark_mode=st.session_state.dark_mode)
    page = render_sidebar()
    if page == "Dashboard":
        render_dashboard()
    elif page == "History":
        render_history_page()
    elif page == "Settings":
        render_settings_page()
    else:
        render_about_page()
