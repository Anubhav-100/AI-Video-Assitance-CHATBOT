# AI Video Assistant — Streamlit UI

A minimalist Streamlit frontend inspired by the supplied dashboard reference. UI code is separated into reusable components and an external stylesheet.

## Files

```text
app.py                 # Streamlit page layout and application flow
ui/components.py       # Reusable HTML/Streamlit presentation components
ui/styles.py           # CSS loader and theme override
ui/styles.css          # Design system and responsive styling
requirements-ui.txt    # Minimum UI dependency
```

## Integrate into your existing project

Copy `app.py` and the entire `ui/` directory into the same project root as your existing `main.py`, `core/`, `schemas/`, and `utils/` folders. Do not replace your existing `main.py` or backend modules.

The app imports:

```python
from main import run_pipeline
from core.rag_engine import ask_question
```

It expects `run_pipeline(source, engine)` to return a dictionary containing the analysis fields and `rag_chain`, matching your current pipeline.

## Install and run

Activate your existing virtual environment, then run:

```powershell
python -m pip install -r requirements-ui.txt
python -m streamlit run app.py
```

If Streamlit is already installed, the additional installation is unnecessary.

## Important integration notes

- `MEDIA_TYPES` in `app.py` is a starter list. Match it to the actual formats supported by `core/audio_processor.py`.
- Uploaded media is written to a temporary app-controlled path, passed to `run_pipeline`, and removed after the synchronous pipeline call finishes.
- The active `rag_chain` stays in `st.session_state` and is never sent to the browser.
- The chat uses your existing `ask_question(rag_chain, question)` function.
- The pipeline currently does not expose structured per-stage progress callbacks. The app therefore displays a truthful overall processing status and marks the six timeline stages complete only after `run_pipeline` returns successfully. To show live stage-by-stage progress, add an optional callback or event mechanism to the backend while preserving the existing call signature for normal use.
- Session history lasts only for the current Streamlit browser session. Add a database if you need persistent history across sessions.
- The transcript's `st.code` viewer includes Streamlit's built-in copy control; the download button saves the transcript as TXT.

## Visual customization

Edit `ui/styles.css` for colors, dimensions, spacing, responsive behavior, and component styling. Edit `ui/components.py` for the reusable visual sections. Keep app orchestration and backend calls in `app.py`.
