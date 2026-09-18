"""faster-whisper transcription helper (the same model/params the original used).

Used two ways:
  * `transcribe()` -> word-level transcript (list of segments) for authoring configs.
  * as a library from suggest_words.py to list candidate target words.

This is optional at render time: a finished config already carries the word/cue
timings, so the deterministic render path never needs whisper. It is only used to
help a human author a new config.
"""
from __future__ import annotations
from pathlib import Path

from . import ffmpeg_ops


def transcribe(src: str, language: str = "es", model_size: str = "small") -> list[dict]:
    from faster_whisper import WhisperModel  # imported lazily; heavy dependency

    scratch = Path(src).with_suffix(".16k.wav")
    ffmpeg_ops.extract_wav_16k_mono(src, scratch)
    model = WhisperModel(model_size, device="cpu", compute_type="int8")
    segments, _info = model.transcribe(
        str(scratch), language=language, word_timestamps=True, vad_filter=False
    )
    out: list[dict] = []
    for s in segments:
        out.append({
            "start": round(s.start, 2), "end": round(s.end, 2), "text": s.text.strip(),
            "words": [{"w": w.word.strip(), "s": round(w.start, 2), "e": round(w.end, 2)}
                      for w in (s.words or [])],
        })
    try:
        scratch.unlink()
    except OSError:
        pass
    return out
