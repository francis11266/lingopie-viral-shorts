#!/usr/bin/env python3
"""Lingopie viral pause-&-reveal short — command line.

  python generate.py --input clip.mp4 --style s2 --output out

Styles: s2 = POV hook · s3 = challenge hook · s4 = word-counter.
Needs ANTHROPIC_API_KEY (auto-pick) + ELEVENLABS_API_KEY (voiceover) in .env.
Most teammates should use the web app instead (run start.bat / start.command).
"""
from __future__ import annotations
import argparse, sys
from pathlib import Path

try:
    from dotenv import load_dotenv; load_dotenv()
except Exception:
    pass

from src.pipeline import generate
from src import styles


def main() -> int:
    ap = argparse.ArgumentParser(prog="generate.py")
    ap.add_argument("--input", "-i", required=True, help="source clip (Spanish drama, any size)")
    ap.add_argument("--style", "-s", default="s2", choices=["s2", "s3", "s4"])
    ap.add_argument("--language", "-l", default="es")
    ap.add_argument("--voice", "-v", default=None, help="ElevenLabs voice_id or a name from styles.VOICES")
    ap.add_argument("--output", "-o", default="output")
    args = ap.parse_args()
    if not Path(args.input).exists():
        print(f"error: not found: {args.input}", file=sys.stderr); return 2
    voice = styles.VOICES.get((args.voice or "").lower(), args.voice)
    final = generate(args.input, args.style, args.output, language=args.language, voice_id=voice)
    print(f"\nDone: {final}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
