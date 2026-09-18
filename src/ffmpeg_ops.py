"""Thin wrappers around ffmpeg / ffprobe for cutting clips, extracting audio,
grabbing freeze frames and measuring durations. These reproduce exactly the
ffmpeg commands the original hand-built pipeline used."""
from __future__ import annotations
import json
import shutil
import subprocess
from pathlib import Path

FFMPEG = shutil.which("ffmpeg") or "ffmpeg"
FFPROBE = shutil.which("ffprobe") or "ffprobe"


def _run(cmd: list[str]) -> None:
    subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)


def duration(path: str | Path) -> float:
    out = subprocess.run(
        [FFPROBE, "-v", "error", "-show_entries", "format=duration",
         "-of", "default=nw=1:nk=1", str(path)],
        check=True, capture_output=True, text=True,
    ).stdout.strip()
    return float(out)


def cut_scene(src: str, t_in: float, t_out: float, out_mp4: Path,
              width: int, height: int, fps: int) -> float:
    """Cut [t_in,t_out] from src, normalise to WxH@fps, keep audio. Returns duration."""
    out_mp4.parent.mkdir(parents=True, exist_ok=True)
    _run([FFMPEG, "-y", "-ss", str(t_in), "-to", str(t_out), "-i", src,
          "-vf", f"scale={width}:{height}:force_original_aspect_ratio=increase,"
                 f"crop={width}:{height},fps={fps}",
          "-c:v", "libx264", "-crf", "18", "-preset", "veryfast",
          "-c:a", "aac", "-b:a", "192k", str(out_mp4)])
    return duration(out_mp4)


def extract_audio(src_mp4: Path, out_wav: Path) -> None:
    out_wav.parent.mkdir(parents=True, exist_ok=True)
    _run([FFMPEG, "-y", "-i", str(src_mp4), "-vn", "-ac", "2", "-ar", "44100", str(out_wav)])


def last_frame(src_mp4: Path, out_png: Path) -> None:
    out_png.parent.mkdir(parents=True, exist_ok=True)
    _run([FFMPEG, "-y", "-sseof", "-0.08", "-i", str(src_mp4), "-update", "1",
          "-frames:v", "1", str(out_png)])


def frame_at(src: str, t: float, out_png: Path, width: int, height: int) -> None:
    out_png.parent.mkdir(parents=True, exist_ok=True)
    _run([FFMPEG, "-y", "-ss", str(t), "-i", src, "-frames:v", "1",
          "-vf", f"scale={width}:{height}", str(out_png)])


def extract_wav_16k_mono(src: str, out_wav: Path) -> None:
    """16k mono wav for transcription."""
    out_wav.parent.mkdir(parents=True, exist_ok=True)
    _run([FFMPEG, "-y", "-i", src, "-vn", "-ac", "1", "-ar", "16000", str(out_wav)])
