from __future__ import annotations

from datetime import datetime
import importlib
from pathlib import Path
from typing import Optional

import streamlit as st

from ui.components import render_topbar


HISTORY_CSS_PATH = Path(__file__).with_name("history.css")


def _load_history_css() -> None:
    """Load styles used only by the History page."""
    try:
        css = HISTORY_CSS_PATH.read_text(encoding="utf-8")
        st.markdown(f"<style>{css}</style>", unsafe_allow_html=True)
    except OSError as exc:
        st.warning(f"Could not load History page styles: {exc}")


def _format_history_date(raw_dt: Optional[str]) -> str:
    """Format an ISO-8601 timestamp string for display."""
    if not raw_dt:
        return "Unknown date"
    try:
        dt = datetime.fromisoformat(raw_dt.replace("Z", "+00:00"))
        return dt.strftime("%Y-%m-%d %H:%M")
    except Exception:
        return str(raw_dt)


def render_history_page() -> None:
    """Render the persistent Analysis History page."""
    _load_history_css()
    render_topbar()
    st.markdown("## Analysis History")
    st.caption("Saved analyses are stored permanently in SQLite and remain available across restarts.")

    try:
        import api_client

        if not hasattr(api_client, "list_analysis_history"):
            importlib.reload(api_client)
        list_analysis_history = api_client.list_analysis_history
        get_analysis_history = api_client.get_analysis_history
        delete_analysis_history = api_client.delete_analysis_history
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
            st.markdown(f'<div class="history-card-title">{title}</div>', unsafe_allow_html=True)
            st.markdown(
                f'<div class="history-card-meta">Date: {created_at} · Engine: {engine} · Source: {source}</div>',
                unsafe_allow_html=True,
            )
            if summary_preview:
                st.markdown(
                    f'<div class="history-summary-preview">{summary_preview}</div>',
                    unsafe_allow_html=True,
                )

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
                        st.session_state.pending_navigation = "Dashboard"
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
