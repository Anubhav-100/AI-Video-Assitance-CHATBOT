from pathlib import Path

import streamlit as st

from ui.components import render_topbar


ABOUT_CSS_PATH = Path(__file__).with_name("about.css")


def _load_about_css() -> None:
    """Load styles used only by the About page."""
    try:
        css = ABOUT_CSS_PATH.read_text(encoding="utf-8")
        st.markdown(f"<style>{css}</style>", unsafe_allow_html=True)
    except OSError as exc:
        st.warning(f"Could not load About page styles: {exc}")


def _section_heading(label: str, title: str, description: str | None = None) -> None:
    st.markdown(
        f"""
        <div class="about-section-heading">
            <span class="about-section-label">{label}</span>
            <h2>{title}</h2>
            {f'<p>{description}</p>' if description else ''}
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_about_page() -> None:
    """Render the About page for AI Video Assistant."""
    _load_about_css()
    render_topbar()

    # Hero
    st.markdown(
        """
        <section class="about-hero">
            <div class="about-eyebrow">AI-POWERED KNOWLEDGE ASSISTANT</div>
            <h1>Turn conversations into <span>knowledge.</span></h1>
            <p>
                AI Video Assistant transforms video and audio into searchable,
                structured information. Get transcripts, concise summaries,
                actionable insights, and answers grounded in your content.
            </p>
        </section>
        """,
        unsafe_allow_html=True,
    )

    # Overview
    _section_heading(
        "THE PROJECT",
        "Understand more. Search less.",
        "A modular Python application for turning long recordings into information "
        "you can review, use, and ask questions about.",
    )
    st.markdown(
        """
        <div class="about-copy">
            It accepts YouTube and other yt-dlp-supported URLs, as well as local
            audio and video files. The media is transcribed, analyzed by a language
            model, and indexed so you can explore the content without manually
            replaying the entire recording.
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Capabilities
    _section_heading("WHAT IT DOES", "Core capabilities")
    features = [
        ("01", "Speech transcription",
         "Convert audio and video into text using the selected Whisper or Sarvam engine."),
        ("02", "Meeting summaries",
         "Create concise summaries from transcript chunks using an LLM map-reduce workflow."),
        ("03", "Action items",
         "Extract tasks along with available owners and deadlines."),
        ("04", "Key decisions",
         "Identify decisions made during the conversation."),
        ("05", "Open questions",
         "Surface unresolved topics that may need follow-up."),
        ("06", "Transcript Q&A",
         "Ask natural-language questions and receive answers grounded in retrieved transcript context."),
    ]
    feature_cols = st.columns(3, gap="medium")
    for index, (number, title, description) in enumerate(features):
        with feature_cols[index % 3]:
            st.markdown(
                f"""
                <article class="about-feature">
                    <span class="about-card-number">{number}</span>
                    <h3>{title}</h3>
                    <p>{description}</p>
                </article>
                """,
                unsafe_allow_html=True,
            )

    # Workflow
    _section_heading(
        "THE WORKFLOW",
        "From media to meaningful insights",
        "Each stage has a focused responsibility, keeping the application modular.",
    )
    workflow = [
        ("01", "Media input",
         "Provide a supported video or audio URL, or upload a local media file."),
        ("02", "Audio preparation",
         "yt-dlp handles online media downloads; pydub prepares local media. Audio is converted to mono 16 kHz WAV."),
        ("03", "Transcription",
         "The selected Whisper or Sarvam engine processes audio chunks, and the resulting text is combined into a transcript."),
        ("04", "LLM analysis",
         "The configured language model generates a title and summary, then extracts action items, decisions, and open questions."),
        ("05", "RAG indexing",
         "Transcript chunks are embedded with all-MiniLM-L6-v2 and stored with metadata in ChromaDB."),
        ("06", "Question answering",
         "The retriever selects the four most relevant chunks and supplies them as context for the LLM response."),
    ]
    for number, title, description in workflow:
        st.markdown(
            f"""
            <div class="about-workflow">
                <div class="about-workflow-number">{number}</div>
                <div class="about-workflow-text">
                    <h3>{title}</h3>
                    <p>{description}</p>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    # RAG
    _section_heading(
        "UNDER THE HOOD",
        "How transcript search works",
        "Retrieval-Augmented Generation (RAG) gives the language model relevant "
        "transcript passages to work from when answering a question.",
    )
    rag_steps = [
        ("Chunk", "Split the transcript into 500-character segments with 50-character overlap."),
        ("Embed", "Convert each segment into a vector using all-MiniLM-L6-v2."),
        ("Store", "Save vectors and associated metadata in persistent ChromaDB storage."),
        ("Retrieve", "Find the four most semantically relevant transcript chunks for a question."),
        ("Answer", "Generate a response using the retrieved passages as context."),
    ]
    rag_cols = st.columns(5, gap="small")
    for col, (title, description) in zip(rag_cols, rag_steps):
        with col:
            st.markdown(
                f"""
                <div class="about-rag-step">
                    <h3>{title}</h3>
                    <p>{description}</p>
                </div>
                """,
                unsafe_allow_html=True,
            )

    # Technology stack
    _section_heading("TECHNOLOGY", "Built with Python and modern AI tooling")
    tech_stack = {
        "Language": ["Python 3.10+"],
        "Frontend": ["Streamlit", "Custom CSS"],
        "Backend": ["FastAPI", "Uvicorn", "Pydantic v2"],
        "Media processing": ["yt-dlp", "pydub", "FFmpeg"],
        "Speech recognition": ["OpenAI Whisper", "Sarvam AI"],
        "LLM providers": ["Groq", "Mistral AI", "OpenAI-compatible APIs"],
        "Orchestration": ["LangChain", "LCEL", "Text Splitters"],
        "Embeddings & storage": ["Sentence-Transformers", "ChromaDB"],
        "Utilities & testing": ["HTTPX", "Requests", "ReportLab", "python-dotenv", "pytest", "unittest"],
    }
    for category, technologies in tech_stack.items():
        tags = "".join(
            f'<span class="about-tech-tag">{technology}</span>'
            for technology in technologies
        )
        st.markdown(
            f"""
            <div class="about-tech-row">
                <div class="about-tech-category">{category}</div>
                <div class="about-tech-tags">{tags}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    # Architecture
    _section_heading(
        "APPLICATION STRUCTURE",
        "Separate layers. Clear responsibilities.",
        "The user interface communicates with the API, while the backend coordinates "
        "the processing pipeline and its supporting services.",
    )
    architecture = [
        ("Streamlit frontend",
         "Source input, file uploads, analysis results, history, settings, and chat."),
        ("FastAPI backend",
         "Versioned REST endpoints, request validation, and structured responses."),
        ("Core AI pipeline",
         "Audio processing, transcription, summarization, information extraction, and RAG."),
        ("AI services",
         "Speech recognition, language model providers, and embedding models."),
        ("ChromaDB",
         "Persistent vector storage for transcript chunks and metadata."),
    ]
    for title, description in architecture:
        st.markdown(
            f"""
            <div class="about-architecture-row">
                <span class="about-architecture-dot"></span>
                <div><h3>{title}</h3><p>{description}</p></div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    # Interfaces
    _section_heading("WAYS TO USE IT", "Three application interfaces")
    interface_cols = st.columns(3, gap="medium")
    interfaces = [
        ("Web application", "Streamlit",
         "An interactive interface for processing media, reviewing results, and chatting with transcripts."),
        ("REST API", "FastAPI",
         "Versioned endpoints for transcription, summarization, extraction, and RAG operations."),
        ("Command line", "CLI",
         "Run the processing pipeline directly without opening the web interface."),
    ]
    for col, (title, technology, description) in zip(interface_cols, interfaces):
        with col:
            st.markdown(
                f"""
                <article class="about-interface">
                    <span>{technology}</span>
                    <h3>{title}</h3>
                    <p>{description}</p>
                </article>
                """,
                unsafe_allow_html=True,
            )

    # Principles
    _section_heading("ENGINEERING APPROACH", "Designed around practical principles")
    principles = [
        ("Modularity", "Keep processing stages independent and easier to maintain."),
        ("Separation of concerns", "Keep UI responsibilities separate from backend AI logic."),
        ("Provider flexibility", "Support different transcription engines and LLM providers."),
        ("Context-grounded answers", "Retrieve transcript passages before generating an answer."),
        ("Persistent retrieval", "Store transcript embeddings and metadata in ChromaDB."),
    ]
    principle_cols = st.columns(2, gap="medium")
    for index, (title, description) in enumerate(principles):
        with principle_cols[index % 2]:
            st.markdown(
                f"""
                <div class="about-principle">
                    <h3>{title}</h3>
                    <p>{description}</p>
                </div>
                """,
                unsafe_allow_html=True,
            )

    # Footer
    st.markdown(
        """
        <footer class="about-footer">
            <h2>Built to make recorded information useful.</h2>
            <p>AI Video Assistant · Python · FastAPI · Streamlit · LangChain · RAG</p>
            <span>Designed &amp; developed by Anubhav</span>
        </footer>
        """,
        unsafe_allow_html=True,
    )
