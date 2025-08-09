import json
import os
import re
from typing import List
from pydub import AudioSegment


def extract_json_block(text: str):
    match = re.search(r"\{.*\}", text, re.DOTALL)
    if match:
        try:
            return json.loads(match.group())
        except json.JSONDecodeError as e:
            print("❌ JSON decoding failed:", e)
            print("OpenAI response:", text)
            raise
    print("❌ No JSON found in OpenAI response.")
    print("Raw output:", text)
    raise ValueError("Response did not contain valid JSON.")


def split_audio_file(
    audio_path: str,
    max_size_bytes: int = 25 * 1024 * 1024,
    fixed_chunk_ms: int = 15 * 60 * 1000,
) -> List[str]:
    if os.path.getsize(audio_path) <= max_size_bytes:
        return [audio_path]

    audio = AudioSegment.from_file(audio_path)
    duration_ms = len(audio)
    base_name = os.path.splitext(audio_path)[0]

    chunks: List[str] = []
    for start_ms in range(0, duration_ms, fixed_chunk_ms):
        chunk = audio[start_ms : start_ms + fixed_chunk_ms]
        chunk_path = f"{base_name}_part{start_ms // fixed_chunk_ms}.m4a"
        chunk.export(chunk_path, format="mp4")
        chunks.append(chunk_path)

    print(f"🔪 Split {audio_path} into {len(chunks)} chunks of {fixed_chunk_ms // 1000} seconds each.")
    return chunks