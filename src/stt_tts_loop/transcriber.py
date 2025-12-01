from groq import Groq
from dotenv import load_dotenv
import os


# Load environment variables (including GROQ_API_KEY) from a .env file if present
load_dotenv()


def _get_groq_client() -> Groq:
    """Return a Groq client configured from the GROQ_API_KEY env var."""
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        raise RuntimeError("GROQ_API_KEY is not set. Please configure it in your .env file.")
    return Groq(api_key=api_key)


def transcribe_audio(audio_path: str) -> str:
    """
    Transcribes an audio file using Groq Whisper model.
    Returns transcribed text.
    """
    client = _get_groq_client()
    with open(audio_path, "rb") as audio_file:
        transcription = client.audio.transcriptions.create(
            model="whisper-large-v3",
            file=audio_file
        )
    return transcription.text
