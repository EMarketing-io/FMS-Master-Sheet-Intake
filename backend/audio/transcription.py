import os
import tempfile
from pydub import AudioSegment
import openai
from config.config import OPENAI_KEY, WHISPER_MODEL

openai.api_key = OPENAI_KEY

MAX_FILE_MB = 25
CHUNK_LENGTH_MS = 15 * 60 * 1000 


def split_audio_if_needed(file_path):
    file_size_mb = os.path.getsize(file_path) / (1024 * 1024)
    if file_size_mb <= MAX_FILE_MB:
        return [file_path]  

    print(f"⚠️ Audio is {file_size_mb:.2f} MB — splitting into 15 min chunks...")
    audio = AudioSegment.from_file(file_path)
    chunks = []
    for i in range(0, len(audio), CHUNK_LENGTH_MS):
        chunk = audio[i : i + CHUNK_LENGTH_MS]
        tmp_chunk_path = tempfile.NamedTemporaryFile(suffix=".mp3", delete=False).name
        chunk.export(tmp_chunk_path, format="mp3")
        chunks.append(tmp_chunk_path)
    return chunks


def transcribe_audio(file_path):
    all_chunks = split_audio_if_needed(file_path)
    full_transcript = ""

    for idx, chunk_path in enumerate(all_chunks, start=1):
        print(f"🎙️ Transcribing chunk {idx}/{len(all_chunks)}...")
        with open(chunk_path, "rb") as audio_file:
            try:
                transcript = openai.Audio.transcribe(
                    model=WHISPER_MODEL, file=audio_file
                )
                full_transcript += transcript["text"].strip() + "\n\n"
            except Exception as e:
                raise RuntimeError(f"❌ Whisper API failed for chunk {idx}: {e}")

    return full_transcript.strip()