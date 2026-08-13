#!/usr/bin/env python
"""
Optional ElevenLabs voiceover generator.
Requires ELEVENLABS_API_KEY and ELEVENLABS_VOICE_ID.
The generated audio is a presentation asset, never part of scientific evidence.
"""
import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()
api_key = os.getenv("ELEVENLABS_API_KEY")
voice_id = os.getenv("ELEVENLABS_VOICE_ID")
if not api_key or not voice_id:
    raise SystemExit("Set ELEVENLABS_API_KEY and ELEVENLABS_VOICE_ID.")

from elevenlabs.client import ElevenLabs
client = ElevenLabs(api_key=api_key)

script = Path("docs/video_voiceover.txt").read_text(encoding="utf-8")
audio = client.text_to_speech.convert(
    text=script,
    voice_id=voice_id,
    model_id="eleven_v3",
    output_format="mp3_44100_128",
)
out = Path("runs/local/voiceover.mp3")
out.parent.mkdir(parents=True, exist_ok=True)
with out.open("wb") as f:
    for chunk in audio:
        f.write(chunk)
print(out)
