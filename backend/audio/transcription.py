import openai
from config import OPENAI_KEY, WHISPER_MODEL

# Set the OpenAI API key
openai.api_key = OPENAI_KEY


def transcribe_audio(audio_path: str) -> str:
    """
    Transcribe/translate an audio file to English text using Whisper API.
    (Flow unchanged.)
    """
    print("🎙️ Transcribing with OpenAI Whisper API...")
    with open(audio_path, "rb") as audio_file:
        response = openai.Audio.transcribe(
            model=WHISPER_MODEL,
            file=audio_file,
            response_format="text",
            task="translate",  # auto-translate non-English audio to English
        )
        return response.strip()
