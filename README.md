# AI Video Assistant

Convert a local audio/video file or a supported video URL into a transcript,
meeting summary, action items, decisions, open questions, and a searchable
local transcript index.

## Structure

- `utils/` contains reusable configuration, validation, LLM, and audio helpers.
- `core/` contains individual pipeline stages plus `pipeline.py`, the high-level
  workflow.
- `tests/` contains offline tests that do not call APIs or download models.

## Setup

Install dependencies into a Python 3.10+ virtual environment:

```powershell
pip install -r requirements.txt
```

Create `.env` with the keys required by the engines you use:

```env
MISTRAL_API_KEY=...
SARVAM_API_KEY=...
WHISPER_MODEL=small
SARVAM_STT_MODEL=saaras:v2.5
TRANSCRIPTION_WORKERS=2
```

`MISTRAL_API_KEY` is needed for summaries, extraction, and RAG answers.
`SARVAM_API_KEY` is needed only when `engine="sarvam"`; Whisper runs locally.
Set `DOWNLOAD_DIR` or `CHROMA_DIR` to move generated files outside the project.

## Use the pipeline

```python
from core.pipeline import analyze_meeting
from core.rag_engine import answer_question
from core.vector_store import load_vector_store

analysis = analyze_meeting("path/to/meeting.mp4", engine="whisper")
print(analysis.summary)
print(analysis.action_items)

store = load_vector_store()
print(answer_question(store, "What deadline did the team agree to?"))
```

## Run the Application

### 1. Web Interface (Streamlit)
Launch the modern web UI:

```powershell
streamlit run app.py
```

### 2. Command-Line Interface (CLI)
Run the pipeline directly from your terminal:

```powershell
python main.py
```

## Testing

Run the offline checks with:

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
```

