"""
AI Video Assistant — Main Pipeline
Run:  python main.py
"""

import os
import sys
import uuid
from dotenv import load_dotenv

load_dotenv()

from core.audio_processor import process_input
from core.transcriber import transcribe_all
from core.summarizer import summarize_transcript, generate_title
from core.extractor import extract_action_items, extract_key_decisions, extract_questions
from core.rag_engine import build_rag_chain, ask_question
from utils.llm import get_llm
from schemas.pipeline import PipelineInput
from schemas.analysis import MeetingAnalysisResult


def run_pipeline(source: str, engine: str = "whisper") -> dict:
    """
    Full pipeline: audio → transcript → summary → extraction → RAG.

    Returns a dict with all results and the rag_chain for Q&A.
    """
    pipeline_input = PipelineInput(source=source, engine=engine)
    source = pipeline_input.source
    engine = pipeline_input.engine

    # 1. Process audio
    print(f"\n[1/6] Processing audio from: {source}")
    chunks = process_input(source, engine)
    print(f"{len(chunks)} chunk(s) created")

    # 2. Transcribe
    print("[2/6] Transcribing ...")
    transcript = transcribe_all(chunks, engine)
    print(f"{len(transcript.split()):,} words transcribed")

    # 3. Init LLM
    print("[3/6] Initializing LLM ...")
    llm = get_llm()

    # 4. Title + Summary
    print("[4/6] Generating title & summary ...")
    title = generate_title(transcript, llm)
    summary = summarize_transcript(transcript, llm)

    # 5. Extraction
    print("[5/6] Extracting action items, decisions & questions ...")
    action_items = extract_action_items(transcript, llm)
    key_decisions = extract_key_decisions(transcript, llm)
    open_questions = extract_questions(transcript, llm)

    # 6. RAG index
    print("[6/6] Building RAG index ...")
    video_id = os.path.splitext(os.path.basename(source))[0] if not source.startswith("http") else uuid.uuid4().hex[:8]
    session_id = uuid.uuid4().hex[:12]

    rag_chain = build_rag_chain(
        llm=llm,
        transcript=transcript,
        video_id=video_id,
        video_title=title,
        session_id=session_id,
    )

    # Cleanup temp chunks
    for c in chunks:
        try:
            os.remove(c)
        except OSError:
            pass

    # Print results
    print("\n" + "=" * 60)
    print(f"  Title: {title}")
    print("=" * 60)
    print(f"\n--- Summary ---\n{summary}")
    print(f"\n--- Action Items ---\n{action_items}")
    print(f"\n--- Key Decisions ---\n{key_decisions}")
    print(f"\n--- Open Questions ---\n{open_questions}")
    print()

    analysis = MeetingAnalysisResult(
        title=title,
        transcript=transcript,
        summary=summary,
        action_items=action_items,
        key_decisions=key_decisions,
        open_questions=open_questions,
        video_id=video_id,
        session_id=session_id,
    )
    analysis_data = analysis.model_dump() if hasattr(analysis, "model_dump") else analysis.dict()

    return {
        **analysis_data,
        "rag_chain": rag_chain,
    }


def qa_loop(rag_chain):
    """Interactive Q&A over the meeting. Type 'q' to quit."""

    print("\n--- Ask questions about the meeting (type 'q' to quit) ---\n")

    while True:
        try:
            question = input("You: ").strip()
        except (EOFError, KeyboardInterrupt):
            break

        if not question or question.lower() in {"q", "quit", "exit"}:
            break

        answer = ask_question(rag_chain, question)
        print(f"Assistant: {answer}\n")


def main():
    source = input("Enter video URL or local file path: ").strip()
    if not source:
        print("No source provided.")
        sys.exit(1)

    engine_choice = input("Engine — 1) Whisper  2) Sarvam  [1]: ").strip()
    engine = "sarvam" if engine_choice == "2" else "whisper"

    results = run_pipeline(source, engine)
    qa_loop(results["rag_chain"])


if __name__ == "__main__":
    main()
