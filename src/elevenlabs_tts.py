"""ElevenLabs text-to-speech client.

The original pipeline generated voiceover with the ElevenLabs 'Juno' voice via a
Claude MCP tool. That tool does not exist outside the Claude session, so this
module calls the ElevenLabs REST API directly (the faithful external service).

Each line is: synthesized -> mp3 -> silence-trimmed to wav (ffmpeg silenceremove,
same params the original used). Results are cached by filename so re-runs and the
offline test path are cheap; if a matching <name>.wav already exists it is reused
and no API call is made.
"""
from __future__ import annotations
import os
import shutil
import subprocess
from pathlib import Path

import requests

API_ROOT = "https://api.elevenlabs.io/v1/text-to-speech"
FFMPEG = shutil.which("ffmpeg") or "ffmpeg"

# The original silence-trim used with every VO line.
_TRIM_AF = (
    "silenceremove=start_periods=1:start_silence=0.05:start_threshold=-45dB:"
    "stop_periods=-1:stop_silence=0.25:stop_threshold=-45dB,apad=pad_dur=0.05"
)


class ElevenLabsError(RuntimeError):
    pass


def _trim_to_wav(mp3: Path, wav: Path) -> None:
    subprocess.run(
        [FFMPEG, "-y", "-i", str(mp3), "-af", _TRIM_AF, "-ar", "44100", "-ac", "1", str(wav)],
        check=True, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE,
    )


def synth(text: str, out_wav: Path, *, voice_id: str, api_key: str,
          model_id: str = "eleven_multilingual_v2",
          stability: float = 0.4, similarity: float = 0.75) -> Path:
    """Synthesize `text` to `out_wav` (silence-trimmed). Cached by existence."""
    out_wav = Path(out_wav)
    if out_wav.exists():                       # cache hit / offline-supplied VO
        return out_wav
    if not api_key:
        raise ElevenLabsError(
            f"ELEVENLABS_API_KEY not set and no cached VO for {out_wav.name}. "
            "Set the key in .env, or supply the .wav yourself."
        )
    out_wav.parent.mkdir(parents=True, exist_ok=True)
    mp3 = out_wav.with_suffix(".mp3")
    resp = requests.post(
        f"{API_ROOT}/{voice_id}",
        headers={"xi-api-key": api_key, "accept": "audio/mpeg", "content-type": "application/json"},
        json={"text": text, "model_id": model_id,
              "voice_settings": {"stability": stability, "similarity_boost": similarity}},
        timeout=120,
    )
    if resp.status_code != 200:
        raise ElevenLabsError(f"ElevenLabs {resp.status_code}: {resp.text[:300]}")
    mp3.write_bytes(resp.content)
    _trim_to_wav(mp3, out_wav)
    return out_wav


def api_key_from_env() -> str:
    return os.environ.get("ELEVENLABS_API_KEY", "").strip()
