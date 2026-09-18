"""Let Claude pick a gripping ~15-20s scene + 3 beginner (A1) words from a clip.

Given a word-level transcript (faster-whisper) it returns a plan:
  { "window": {"start": <sec>, "end": <sec>},
    "stops": [ {"word","en","tag","phrase":[tok,tok],"hl":<idx>,"word_in","word_out"}, x3 ] }

Requires ANTHROPIC_API_KEY. Model via ANTHROPIC_MODEL (default claude-opus-4-8).
"""
from __future__ import annotations
import json
import os
import re
import requests

ANTHROPIC_URL = "https://api.anthropic.com/v1/messages"
DEFAULT_MODEL = os.environ.get("ANTHROPIC_MODEL", "claude-opus-4-8")

PROMPT = """You are choosing a short vertical language-learning clip from a TV drama.

Below is a word-level transcript (seconds) in {lang}. Pick ONE gripping, self-contained
window 15-20 seconds long that is funny / flirty / tense / a cliffhanger — something that
stops the scroll. Inside that window pick exactly THREE beginner (A1/A2) vocabulary words
that a learner would want: concrete, common, useful (nouns/adjectives/verbs), spread out
across the window (not all in the same 2 seconds), each clearly audible.

Return ONLY JSON, no prose:
{{
  "window": {{"start": <sec>, "end": <sec>}},
  "stops": [
    {{"word":"<exact spanish word as heard>", "en":"<english>", "tag":"<short grammar tag e.g. 'noun · el' | 'adjective' | 'verb'>",
      "phrase":["<one word before>","<the target word>"], "hl":1,
      "word_in":<sec>, "word_out":<sec>}}
  ]
}}
Rules: 3 stops, in time order. word_in/word_out are that word's timestamps from the transcript.
phrase is 2 short tokens ending with the target; hl is the index (0 or 1) of the target in phrase.
The window must fully contain all three words with ~0.4s before the first and ~2s after the last.
Transcript:
{transcript}
"""


def pick(transcript: list[dict], language: str = "es") -> dict:
    api_key = os.environ.get("ANTHROPIC_API_KEY", "").strip()
    if not api_key:
        raise RuntimeError("ANTHROPIC_API_KEY not set (needed to auto-pick the scene/words).")
    # compact the transcript to keep the prompt small
    compact = []
    for s in transcript:
        compact.append({"t": s["start"], "text": s["text"],
                        "w": [[w["w"], w["s"], w["e"]] for w in s.get("words", [])]})
    body = {
        "model": DEFAULT_MODEL, "max_tokens": 1500,
        "messages": [{"role": "user", "content": PROMPT.format(
            lang=language, transcript=json.dumps(compact, ensure_ascii=False))}],
    }
    r = requests.post(ANTHROPIC_URL, headers={
        "x-api-key": api_key, "anthropic-version": "2023-06-01", "content-type": "application/json",
    }, json=body, timeout=120)
    r.raise_for_status()
    text = "".join(b.get("text", "") for b in r.json().get("content", []))
    m = re.search(r"\{.*\}", text, re.S)
    if not m:
        raise RuntimeError(f"auto-pick: no JSON in model reply:\n{text[:400]}")
    plan = json.loads(m.group(0))
    if len(plan.get("stops", [])) != 3:
        raise RuntimeError("auto-pick: expected exactly 3 stops")
    plan["stops"].sort(key=lambda s: s["word_in"])
    return plan
