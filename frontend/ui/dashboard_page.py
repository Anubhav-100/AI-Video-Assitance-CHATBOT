from __future__ import annotations

import tempfile
from pathlib import Path
from typing import Any, List, Optional, Tuple

import streamlit as st

from ui.components import (
    render_chat_header,
    render_chat_messages,
    render_empty_state,
    render_hero_heading,
    render_hero_visual,
    render_list_card,
    render_section_heading,
    render_summary_card,
    render_suggestions,
    render_timeline,
    render_topbar,
    render_transcript_card,
    render_video_overview,
)


DASHBOARD_CSS_PATH = Path(__file__).with_name("dashboard.css")
DEFAULT_MEDIA_TYPES = ["mp4", "mov", "mkv", "webm", "avi", "mp3", "wav", "m4a", "flac", "aac", "ogg"]


def _load_dashboard_css() -> None:
    """Load styles used only by the Dashboard page."""
    try:
        css = DASHBOARD_CSS_PATH.read_text(encoding="utf-8")
        st.markdown(f"<style>{css}</style>", unsafe_allow_html=True)
    except OSError as exc:
        st.warning(f"Could not load Dashboard page styles: {exc}")


def _get_backend_functions() -> Tuple[Optional[Any], Optional[Any], Optional[Any]]:
    """Import API client functions lazily."""
    try:
        from api_client import run_pipeline, rag_query

        return run_pipeline, rag_query, None
    except Exception as exc:
        st.error(f"API Client Import Error: {type(exc).__name__}: {exc}")
        return None, None, exc


def execute_analysis(source: str, engine: str, uploaded_file: Optional[Any] = None) -> bool:
    """Run video analysis through the FastAPI backend."""
    st.session_state.analysis_results = None
    st.session_state.session_id = None
    st.session_state.chat_history = []

    run_pipeline, _, import_error = _get_backend_functions()
    if run_pipeline is None:
        st.error("Could not import the API client.")
        st.caption(f"Import detail: {type(import_error).__name__}: {import_error}")
        return False

    actual_source = source
    temporary_path: Optional[Path] = None

    try:
        if uploaded_file is not None:
            suffix = Path(uploaded_file.name).suffix.lower() or ".media"
            with tempfile.NamedTemporaryFile(
                prefix="ai_video_upload_",
                suffix=suffix,
                delete=False,
            ) as temp_file:
                temp_file.write(uploaded_file.getvalue())
                temporary_path = Path(temp_file.name)
            actual_source = str(temporary_path)

        with st.status("Analyzing your video...", expanded=True) as status:
            st.write("Processing media, transcribing, generating insights, and building the RAG index.")
            output = run_pipeline(actual_source, engine)

            if not isinstance(output, dict):
                raise TypeError("run_pipeline() did not return a dictionary.")

            session_id = output.get("session_id")
            if not session_id:
                raise ValueError("Backend response does not contain a session_id.")

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
                st.warning("The temporary upload could not be removed automatically.")


def submit_chat_question(question: str) -> None:
    """Send a question to the FastAPI RAG endpoint."""
    question = question.strip()
    if not question:
        return

    session_id = st.session_state.session_id
    if not session_id:
        st.warning("Analyze a video first to enable chat.")
        return

    _, rag_query, import_error = _get_backend_functions()
    if rag_query is None:
        st.error(f"Could not import rag_query(): {import_error}")
        return

    st.session_state.chat_history.append({"role": "user", "content": question})

    try:
        with st.spinner("Thinking about your video..."):
            answer = rag_query(session_id, question)

        st.session_state.chat_history.append({"role": "assistant", "content": str(answer)})
    except Exception as exc:
        st.session_state.chat_history.append(
            {"role": "assistant", "content": f"An error occurred: {exc}"}
        )


def render_source_input(media_types: Optional[List[str]] = None) -> None:
    """Render the video URL / file upload input box."""
    allowed_types = media_types or DEFAULT_MEDIA_TYPES
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
                    type=allowed_types,
                    label_visibility="collapsed",
                    help="Adjust MEDIA_TYPES in main.py to match the formats accepted by core.audio_processor.",
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


def render_dashboard(media_types: Optional[List[str]] = None) -> None:
    """Render the main Dashboard page."""
    _load_dashboard_css()
    render_topbar()
    hero_col, art_col = st.columns([1.12, 1.0], gap="small", vertical_alignment="center")
    with hero_col:
        render_hero_heading()
        render_source_input(media_types)
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

        with st.container():
            render_summary_card(results.get("summary") if results else None)

        st.markdown('<div class="dashboard-section-gap"></div>', unsafe_allow_html=True)

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

        st.markdown('<div class="dashboard-section-gap"></div>', unsafe_allow_html=True)
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

        st.markdown('<div class="dashboard-section-gap"></div>', unsafe_allow_html=True)
        render_timeline(completed=bool(st.session_state.analysis_results))

    with chat_col:
        with st.container(border=True):
            has_analysis = bool(st.session_state.session_id)
            render_chat_header(has_analysis)
            render_chat_messages(st.session_state.chat_history)

            if has_analysis:
                st.markdown('<div class="small-muted dashboard-suggestions-label">SUGGESTED QUESTIONS</div>', unsafe_allow_html=True)
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
                    '<div class="small-muted dashboard-suggestions-empty">Example questions will be available after analysis.</div>',
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
