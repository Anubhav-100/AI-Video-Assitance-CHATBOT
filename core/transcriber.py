import os
import requests
import whisper
from dotenv import load_dotenv

load_dotenv()


# Configuration
#---------------------------------------------------------------------------------------------------------------------------------

WHISPER_MODEL = os.getenv("WHISPER_MODEL", "small")

SARVAM_API_KEY = os.getenv("SARVAM_API_KEY")
SARVAM_STT_TRANSLATE_URL = ("https://api.sarvam.ai/speech-to-text-translate")
SARVAM_MODEL = os.getenv("SARVAM_STT_MODEL", "saaras:v2.5")

# Retry configuration for temporary network failures
MAX_RETRIES = 3
RETRY_DELAY_SECONDS = 2

_model = None


# Load Whisper model once and reuse it
#---------------------------------------------------------------------------------------------------------------------------------

def load_model():
    """Load the Whisper model once and reuse it."""

    global _model
    if _model is None:
        print(f"Loading Whisper model: {WHISPER_MODEL} ...")
        _model = whisper.load_model(WHISPER_MODEL)
        print("Whisper model loaded.")

    return _model


# Transcribe Audio Chunk using Whisper
#---------------------------------------------------------------------------------------------------------------------------------

def transcribe_chunk_whisper(chunk_path: str) -> str:
    """
    Transcribe one pre-created audio chunk using Whisper.
    Args:
        chunk_path: Path to the audio chunk.
    Returns:
        Transcribed text in the spoken language.
    """
    
    model = load_model()
    result = model.transcribe(chunk_path, task="transcribe")

    return result["text"].strip()


# Transcribe Audio Chunk using Sarvam
#---------------------------------------------------------------------------------------------------------------------------------

def transcribe_chunk_sarvam(chunk_path: str) -> str:
    """Translate one pre-created audio chunk into English using Sarvam."""

    if not SARVAM_API_KEY:
        raise RuntimeError("SARVAM_API_KEY is not set in environment / .env")

    headers = {"api-subscription-key": SARVAM_API_KEY}
    data = {
        "model": SARVAM_MODEL,
        "with_diarization": "false",
    }

    with open(chunk_path, "rb") as audio_file:
        files = {"file":
            (
                os.path.basename(chunk_path),
                audio_file,
                "audio/wav",
            )
        }

        response = requests.post(
            SARVAM_STT_TRANSLATE_URL,
            headers=headers,
            files=files,
            data=data,
            timeout=120,
        )

    response.raise_for_status()

    result = response.json()
    return result.get("transcript", "").strip()


# Function for transcribing a single chunk based on the selected engine
#---------------------------------------------------------------------------------------------------------------------------------

def transcribe_chunk(chunk_path: str, engine: str) -> str:
    """
    Route a single audio chunk to the selected STT engine.
    Args:
        chunk_path: Path to the audio chunk.
        engine: "whisper" or "sarvam".
    Returns:
        Transcribed text.
    """

    engine = engine.lower().strip()

    if engine == "whisper":
        return transcribe_chunk_whisper(chunk_path)

    if engine == "sarvam":
        return transcribe_chunk_sarvam(chunk_path)

    raise ValueError("Invalid engine. Choose 'whisper' or 'sarvam'.")


# Transcribe All Audio Chunks
# ---------------------------------------------------------------------------------------------------------------------------------

def transcribe_all(chunks: list[str], engine: str) -> str:
    """
    Transcribe all pre-created audio chunks.
    Args:
        chunks: Audio chunk paths created by process_input().
        engine: "whisper" or "sarvam".
    Returns:
        Complete transcript as a single string.
    """

    engine = engine.lower().strip()

    if engine not in {"whisper", "sarvam"}:
        raise ValueError("Invalid engine. Choose 'whisper' or 'sarvam'.")

    if not chunks:
        raise ValueError("No audio chunks provided. Check process_input().")

    engine_name = ("Whisper" if engine == "whisper" else "Sarvam AI")
    print(f"Using {engine_name} for transcription.")
    transcripts: list[str] = []

    for i, chunk in enumerate(chunks, start=1):
        print(f"Transcribing chunk {i}/{len(chunks)}...")

        text = transcribe_chunk(chunk_path=chunk, engine=engine)

        if text:
            transcripts.append(text.strip())

    print("Transcription complete.")

    return " ".join(transcripts)