"""Reusable presentation components for the AI Video Assistant Streamlit UI."""

from __future__ import annotations

import html
import re
from collections.abc import Mapping, Sequence
from typing import Any

import streamlit as st


def esc(value: Any) -> str:
    """HTML-escape values before placing backend content into custom HTML."""
    if value is None:
        return ""
    return html.escape(str(value), quote=True)


def render_brand() -> None:
    st.markdown(
        """
        <div class="brand-lockup">
          <div class="brand-symbol">▶</div>
          <div class="brand-name">AI Video<br>Assistant</div>
        </div>
        <div class="brand-tagline">Analyze · Summarize · Chat</div>
        """,
        unsafe_allow_html=True,
    )


def render_sidebar_promo() -> None:
    st.markdown(
        """
        <div class="sidebar-promo">
          <div class="spark">✦ ✧</div>
          <strong>Your personal<br>AI video assistant</strong>
          <span>for smarter insights</span>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_topbar() -> None:
    st.markdown(
        """
        <div class="topbar">
          <div class="topbar-icon" title="Notifications">♧</div>
          <div class="topbar-avatar">A</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_hero_heading() -> None:
    st.markdown(
        """
        <div class="hero-title">
          Turn Any Video into<br>
          <span class="gradient-text">Actionable Insights ✦</span>
        </div>
        <p class="hero-copy">
          Upload a video or provide a URL, and let AI do the rest —<br>
          summarize, extract key points, and chat about your content.
        </p>
        """,
        unsafe_allow_html=True,
    )


def render_hero_visual() -> None:
    """Decorative hero illustration; deliberately independent of the user's media."""
    st.markdown(
        """
        <div class="hero-art">
          <div class="glow"></div>
          <div class="hero-orbit"></div>
          <div class="hero-spark s1">✧</div>
          <div class="hero-spark s2">✦</div>
          <div class="hero-video-frame">
            <svg viewBox="0 0 520 300" role="img" aria-label="Decorative mountain video illustration" xmlns="http://www.w3.org/2000/svg">
              <defs>
                <linearGradient id="sky" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="0" stop-color="#f5b6d2"/><stop offset=".55" stop-color="#7d9bca"/><stop offset="1" stop-color="#263b69"/>
                </linearGradient>
                <linearGradient id="lake" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="0" stop-color="#42658c"/><stop offset="1" stop-color="#172e52"/>
                </linearGradient>
              </defs>
              <rect width="520" height="300" fill="url(#sky)"/>
              <circle cx="385" cy="80" r="34" fill="#ffe2d5" opacity=".78"/>
              <path d="M0 178 L80 100 132 154 220 53 304 156 376 82 520 180 V300 H0Z" fill="#526d91"/>
              <path d="M176 97 L220 53 265 109 236 97 220 112 205 92 191 106Z" fill="#f0eff7"/>
              <path d="M320 165 L376 82 450 159 412 140 390 152 375 128 353 151Z" fill="#edf0f6"/>
              <path d="M0 181 Q105 158 205 180 T520 175 V300 H0Z" fill="url(#lake)"/>
              <path d="M30 218 Q150 202 270 221 T500 216" stroke="#d2d9ef" stroke-width="3" opacity=".45" fill="none"/>
              <path d="M55 246 Q170 232 300 248 T475 244" stroke="#a6c0e2" stroke-width="2" opacity=".35" fill="none"/>
              <path d="M0 184 L520 184" stroke="#f9d3df" stroke-width="2" opacity=".55"/>
            </svg>
            <div class="hero-play">▶</div>
          </div>
          <div class="float-status one"><span class="status-wave">▥</span>Transcribing...</div>
          <div class="float-status two">
            <div><span class="status-check">●</span>Summarizing...</div>
            <div style="margin-top:7px"><span class="status-check">●</span>Extracting info...</div>
            <div style="margin-top:7px"><span class="status-check">●</span>RAG indexing...</div>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def _normalise_items(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, Mapping):
        items: list[str] = []
        for key, item in value.items():
            if item is None or str(item).strip() == "":
                continue
            if isinstance(item, (list, tuple)):
                items.extend(f"{key}: {part}" for part in item if str(part).strip())
            else:
                items.append(f"{key}: {item}")
        return items
    if isinstance(value, (list, tuple, set)):
        return [str(item).strip() for item in value if item is not None and str(item).strip()]
    text = str(value).strip()
    if not text:
        return []
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    if len(lines) <= 1:
        return [text]
    cleaned = [re.sub(r"^\s*(?:[-*•]+|\d+[.)])\s*", "", line).strip() for line in lines]
    return [line for line in cleaned if line]


def render_section_heading(title: str = "Analysis Results", completed: bool = False) -> None:
    badge = '<span class="completed-pill">Completed&nbsp; ✓</span>' if completed else '<span class="completed-pill" style="background:#eef0fb;color:#69728f">Awaiting analysis</span>'
    st.markdown(
        f'<div class="section-heading"><span class="section-icon">▶</span>{esc(title)}{badge}</div>',
        unsafe_allow_html=True,
    )


def render_video_overview(results: Mapping[str, Any] | None) -> None:
    if not results:
        st.markdown(
            """
            <div class="video-overview">
              <div class="video-thumb" style="display:grid;place-items:center;color:#777ca8;font-size:2.3rem">▷</div>
              <div>
                <div class="video-meta-label">Your video analysis</div>
                <div class="video-title">Your insights will appear here</div>
                <div class="video-meta">Add a URL or upload a media file to get started.</div>
              </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        return

    title = results.get("title") or "Untitled analysis"
    transcript = str(results.get("transcript") or "")
    words = len(transcript.split())
    reading_minutes = max(1, round(words / 160)) if words else 0
    video_id = results.get("video_id")
    meta_parts = [f"{words:,} words"] if words else []
    if reading_minutes:
        meta_parts.append(f"{reading_minutes} min read")
    if video_id:
        meta_parts.append(f"ID: {video_id}")
    meta = "&nbsp;&nbsp;·&nbsp;&nbsp;".join(esc(part) for part in meta_parts) or "Analysis generated successfully"

    st.markdown(
        f"""
        <div class="video-overview">
          <div class="video-thumb">
            <svg viewBox="0 0 360 180" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Video preview placeholder">
              <defs><linearGradient id="thumbBg" x1="0" y1="0" x2="1" y2="1"><stop stop-color="#cad7f8"/><stop offset="1" stop-color="#8e8dc9"/></linearGradient></defs>
              <rect width="360" height="180" fill="url(#thumbBg)"/>
              <rect x="76" y="38" width="205" height="112" rx="8" fill="#252e4b"/>
              <rect x="85" y="47" width="187" height="92" rx="3" fill="#a7c0db"/>
              <rect x="98" y="60" width="75" height="10" rx="3" fill="#506b8f"/>
              <rect x="98" y="78" width="145" height="5" rx="2" fill="#6f82a6" opacity=".75"/>
              <rect x="98" y="90" width="125" height="5" rx="2" fill="#6f82a6" opacity=".55"/>
              <rect x="98" y="110" width="57" height="20" rx="4" fill="#5d55ce"/>
              <path d="M58 151 H300 L318 166 H42Z" fill="#d8deec"/>
              <rect x="24" y="132" width="25" height="20" rx="4" fill="#657ba2" opacity=".8"/>
            </svg>
            <div class="video-thumb-play">▶</div>
          </div>
          <div>
            <div class="video-meta-label">Video Title</div>
            <div class="video-title">{esc(title)}</div>
            <div class="video-meta">◷&nbsp; {meta}</div>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_summary_card(summary: Any) -> None:
    text = str(summary).strip() if summary is not None else ""
    body = f"<p>{esc(text)}</p>" if text else '<p class="card-empty">The generated summary will appear here.</p>'
    st.markdown(
        f'<div class="result-card tone-blue"><div class="card-title"><span class="card-icon">▤</span>Summary</div>{body}</div>',
        unsafe_allow_html=True,
    )


def render_list_card(title: str, value: Any, tone: str, icon: str, empty_text: str) -> None:
    items = _normalise_items(value)
    if items:
        body = "<ul>" + "".join(f"<li>{esc(item)}</li>" for item in items[:8]) + "</ul>"
        if len(items) > 8:
            body += f'<p class="small-muted">+ {len(items) - 8} more items</p>'
    else:
        body = f'<p class="card-empty">{esc(empty_text)}</p>'
    st.markdown(
        f'<div class="result-card tone-{esc(tone)}"><div class="card-title"><span class="card-icon">{esc(icon)}</span>{esc(title)}</div>{body}</div>',
        unsafe_allow_html=True,
    )


def render_transcript_card(transcript: str) -> None:
    words = len(transcript.split()) if transcript else 0
    read_time = max(1, round(words / 160)) if words else 0
    stat_text = f"{words:,} words · {read_time} min read" if words else "Transcript will appear after analysis"
    st.markdown(
        f"""
        <div class="transcript-card">
          <div class="transcript-title-row"><span class="transcript-icon">▤</span>Transcript</div>
          <div class="transcript-stats">{esc(stat_text)}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    if transcript:
        with st.expander("View and copy transcript", expanded=False):
            st.code(transcript, language=None, wrap_lines=True)
        st.download_button(
            "↓  Download TXT",
            data=transcript,
            file_name="ai_video_assistant_transcript.txt",
            mime="text/plain",
            use_container_width=True,
            key="download_transcript",
        )
    else:
        st.button("↓  Download TXT", disabled=True, use_container_width=True, key="download_transcript_disabled")


def render_timeline(completed: bool) -> None:
    labels = [
        "Audio<br>Processing",
        "Transcription",
        "LLM<br>Initialization",
        "Summary<br>Generation",
        "Information<br>Extraction",
        "RAG<br>Indexing",
    ]
    steps = "".join(
        f'<div class="timeline-step"><div class="timeline-dot">{"✓" if completed else "·"}</div><div class="timeline-label">{label}</div></div>'
        for label in labels
    )
    state_class = "done" if completed else "pending"
    state_label = "All stages completed" if completed else "Stages will update after you run an analysis"
    st.markdown(
        f"""
        <div class="timeline-card">
          <div class="timeline-title"><span>▥&nbsp; Processing Stages</span><span class="small-muted">{esc(state_label)}</span></div>
          <div class="timeline-track {state_class}">{steps}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_chat_header(has_analysis: bool) -> None:
    status = '<span class="online-pill">●&nbsp; AI Ready</span>' if has_analysis else '<span class="online-pill" style="background:#f0f1f8;color:#77809b">●&nbsp; Waiting for analysis</span>'
    st.markdown(
        f'<div class="chat-header"><span class="chat-header-icon">☏</span>Ask About This Video{status}</div>',
        unsafe_allow_html=True,
    )


def render_chat_messages(messages: Sequence[Mapping[str, str]]) -> None:
    if not messages:
        st.markdown(
            """
            <div class="chat-empty">
              <div class="chat-empty-icon">✦</div>
              <strong style="color:#313b62">Your video, ready to explore</strong>
              <div style="font-size:.76rem;max-width:260px;margin-top:6px">Analyze a video, then ask questions about its summary, decisions, action items, or transcript.</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        return

    bubbles = []
    for message in messages:
        role = "user" if message.get("role") == "user" else "assistant"
        content = esc(message.get("content", "")).replace("\n", "<br>")
        if role == "assistant":
            bubbles.append(f'<div class="chat-bubble assistant"><span class="chat-avatar">▶</span>{content}</div>')
        else:
            bubbles.append(f'<div class="chat-bubble user">{content}</div>')
    st.markdown("".join(bubbles), unsafe_allow_html=True)


def render_suggestions() -> list[str]:
    return [
        "What are the main takeaways?",
        "What action items were identified?",
        "Summarize the key decisions.",
        "What questions remain unresolved?",
    ]


def render_empty_state() -> None:
    st.markdown(
        """
        <div style="border:1px dashed #d9ddf3;border-radius:14px;padding:20px;text-align:center;background:rgba(255,255,255,.55);margin:.2rem 0 .8rem">
          <div style="font-size:1.25rem;color:#7254ed;margin-bottom:5px">✧</div>
          <div style="font-weight:700;color:#313958;font-size:.88rem">Your analysis will appear here</div>
          <div style="color:#78819e;font-size:.74rem;margin-top:4px">Add a video URL or upload a media file to generate insights.</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
