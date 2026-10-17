import yt_dlp
import os
from typing import Any

from pydub import AudioSegment as _AudioSegment  # type: ignore[reportMissingTypeStubs]

AudioSegment: Any = _AudioSegment

# Configuration for Audio Processing
# ---------------------------------------------------------------------------------------------------------------------------------

DOWNLOAD_DIR = "downloads"
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

# Function to download audio from YouTube using yt-dlp
# ---------------------------------------------------------------------------------------------------------------------------------

def download_youtube_audio(url: str) -> str:
    output_path = os.path.join(DOWNLOAD_DIR, "%(title)s.%(ext)s")

    ydl_opts = {
        "format": "bestaudio/best",
        "outtmpl": output_path,
        "postprocessors": [{"key": "FFmpegExtractAudio", 
                            "preferredcodec": "wav", 
                            "preferredquality": "192"
                        }],
        "quiet": True,
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)

        filepath = ydl.prepare_filename(info)
        filepath = os.path.splitext(filepath)[0] + ".wav"

    return filepath


# Function to convert audio file to WAV format
# ---------------------------------------------------------------------------------------------------------------------------------

def convert_to_wav(input_path: str) -> str:
    """
    Converts an audio file to WAV format.
    Args:
        input_path (str): The path of the input audio file.
    Returns:
        str: The path where the WAV file is saved.
    """
    output_path = os.path.splitext(input_path)[0] + "_converted.wav"
    audio = AudioSegment.from_file(input_path)
    audio = audio.set_channels(1).set_frame_rate(16000)  # Convert to mono and set frame rate
    audio.export(output_path, format="wav")
    
    return output_path


# Function to chunk audio into smaller segments
# ---------------------------------------------------------------------------------------------------------------------------------

def chunk_audio(wav_path: str, chunk_secs: int = 300) -> list[str]:
    """
    Splits a WAV file into sequential chunks.
    Args:
        wav_path: Path to the input WAV file.
        chunk_secs: Chunk duration in seconds.
    Returns:
        List of paths to the generated WAV chunks.
    """

    audio = AudioSegment.from_wav(wav_path)

    chunk_ms = chunk_secs * 1000
    chunks: list[str] = []
    base_path = os.path.splitext(wav_path)[0]

    for i, start in enumerate(range(0, len(audio), chunk_ms)):
        chunk = audio[start:start + chunk_ms]
        chunk_filename = f"{base_path}_chunk_{i}.wav"
        chunk.export(chunk_filename, format="wav")
        chunks.append(chunk_filename)

    return chunks


# Function to process input (YouTube URL or local file) and return audio chunks
# ---------------------------------------------------------------------------------------------------------------------------------

def process_input(Source: str, engine: str) -> list[str]:
    """
    Processes a yt-dlp-supported video URL or a local audio/video file.
    Args:
        Source (str): A video URL or local audio/video file path.
        engine (str): The audio processing engine to use.
    Returns:
        list[str]: A list of paths to the processed audio files.
    """
    if Source.startswith("http://") or Source.startswith("https://"):
        print(f"Downloading audio from video URL: {Source}")
        wav_path = download_youtube_audio(Source)
    else:
        print(f"Processing local audio/video file: {Source}")
        wav_path = convert_to_wav(Source)
    
    print(f"Chunking audio file: {wav_path}")
    
    engine = engine.lower().strip()
   
    if engine == "whisper": 
        print("Using Whisper → 5-minute chunks") 
        chunks = chunk_audio(wav_path, chunk_secs=300)
         
    else: 
        print("Using Sarvam → 28-second chunks") 
        chunks = chunk_audio(wav_path, chunk_secs=28)
    
    return chunks
