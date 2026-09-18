"""End-to-end pipeline: raw Spanish clip -> finished viral pause-&-reveal short.

  transcribe -> Claude picks scene + 3 A1 words -> cut segments/freezes/cold frame
  -> ElevenLabs voiceover (hook, the 3 words, CTA) -> build HyperFrames HTML
  -> render (visuals) -> mux (dialogue + VO + light BGM) -> MP4.

Deterministic render/mux use ffmpeg + Node + HyperFrames. The two API calls
(transcribe is local; Claude auto-pick + ElevenLabs VO) need keys in the env.
"""
from __future__ import annotations
import json
import shutil
import subprocess
from pathlib import Path

from . import ffmpeg_ops, autopick, styles
from .elevenlabs_tts import synth

ROOT = Path(__file__).resolve().parent.parent
NODE_BUILDER = ROOT / "node" / "build_short.mjs"
ASSETS = ROOT / "node" / "assets"
BGM = ASSETS / "music_bed.wav"
HF = "hyperframes@0.7.64"
LEAD, TAIL, HOLD, CTADUR = 0.4, 3.0, 3.8, 6.6


def _run(cmd, cwd=None):
    subprocess.run(cmd, cwd=cwd and str(cwd), check=True,
                   stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)


def _dur(p): return ffmpeg_ops.duration(p)


def generate(video: str, style: str, output_dir: str, *, language: str = "es",
             voice_id: str | None = None, plan: dict | None = None, verbose: bool = True) -> Path:
    import os
    style = style if style in styles.STYLES else "s2"
    preset = styles.STYLES[style]
    voice_id = voice_id or os.environ.get("ELEVENLABS_VOICE_ID") or styles.DEFAULT_VOICE
    api_key = os.environ.get("ELEVENLABS_API_KEY", "").strip()
    out = Path(output_dir); out.mkdir(parents=True, exist_ok=True)
    work = out / ".work"; pub = work / "public"; vo = work / "vo"
    for d in (pub / "fonts", pub / "vendor", vo):
        d.mkdir(parents=True, exist_ok=True)
    for f in (ASSETS / "fonts").glob("*.woff2"):
        shutil.copy(f, pub / "fonts" / f.name)
    shutil.copy(ASSETS / "vendor" / "gsap.min.js", pub / "vendor" / "gsap.min.js")

    def log(m):
        if verbose: print(m, flush=True)

    # 1) transcript + scene/word plan --------------------------------------
    if plan is None:
        log("· transcribing (faster-whisper)…")
        from .transcribe import transcribe
        transcript = transcribe(video, language=language)
        log("· asking Claude for the scene + 3 A1 words…")
        plan = autopick.pick(transcript, language=language)
    else:
        transcript = plan.get("_transcript", [])
    stops = sorted(plan["stops"], key=lambda s: s["word_in"])
    win = plan["window"]

    # 2) cut points ---------------------------------------------------------
    win_start = max(float(win["start"]), stops[0]["word_in"] - LEAD)
    fz = [s["word_out"] + 0.12 for s in stops]
    win_end = max(float(win.get("end", 0)), fz[2] + TAIL)
    bounds = [(win_start, fz[0]), (fz[0], fz[1]), (fz[1], fz[2]), (fz[2], win_end)]
    seg_src = [b[0] for b in bounds]

    # 3) cut segments (video, muted) + freezes + cold frame ----------------
    log("· cutting segments + freeze frames…")
    for i, (a, b) in enumerate(bounds, 1):
        ffmpeg_ops.cut_scene(video, a, b, pub / f"seg{i}.mp4", width=1080, height=1920, fps=30)
    seg_dur = [_dur(pub / f"seg{i}.mp4") for i in range(1, 5)]
    for i in range(3):
        ffmpeg_ops.last_frame(pub / f"seg{i+1}.mp4", pub / f"frz-seg{i+1}.png")
    # cold-open freeze = first frame of seg1
    _run(["ffmpeg", "-y", "-i", str(pub / "seg1.mp4"), "-frames:v", "1", str(pub / "cold.png")])

    # 4) voiceover (hook, 3 words, CTA) ------------------------------------
    log("· generating voiceover (ElevenLabs)…")
    hook_wav = vo / "hook.wav"
    synth(preset["hook_vo"], hook_wav, voice_id=voice_id, api_key=api_key)
    word_wavs = []
    for i, s in enumerate(stops):
        w = vo / f"w{i}.wav"
        synth(f"{s['word']}, {s['en']}!", w, voice_id=voice_id, api_key=api_key)
        word_wavs.append(w)
    cta_wav = vo / "cta.wav"
    synth(preset["cta_vo"], cta_wav, voice_id=voice_id, api_key=api_key)
    intro = max(3.2, _dur(hook_wav) + 0.9)

    # 5) caption lines from transcript within the window -------------------
    lines = [[float(seg["start"]), seg["text"]] for seg in transcript
             if win_start <= float(seg["start"]) < win_end and seg.get("text")]
    if not lines:  # manual plan may carry its own
        lines = plan.get("lines", [])

    # 6) build HTML via node ------------------------------------------------
    build = {
        "style": style, "publicDir": str(pub), "timingsPath": str(work / "ptimings.json"),
        "fps": 30, "w": 1080, "h": 1920, "accent": "#FF8243",
        "hold": HOLD, "intro": round(intro, 3), "ctadur": CTADUR,
        "segDurs": seg_dur, "segSrc": seg_src,
        "stops": [{"id": f"w{i}", "word": s["word"], "en": s["en"], "tag": s.get("tag", ""),
                   "phrase": s.get("phrase", [s["word"]]), "hl": s.get("hl", len(s.get("phrase", [""])) - 1)}
                  for i, s in enumerate(stops)],
        "lines": lines,
        "hook": preset["hook"], "cta": preset["cta"],
    }
    (work / "build.json").write_text(json.dumps(build, ensure_ascii=False, indent=1), encoding="utf-8")
    log("· building composition…")
    _run(["node", str(NODE_BUILDER), str(work / "build.json")])

    # 7) render visuals -----------------------------------------------------
    log("· rendering (HyperFrames)…")
    silent = work / "silent.mp4"
    _run(["npx", HF, "render", str(pub), "--workers", "1", "-o", str(silent)])

    # 8) mux dialogue + VO + light BGM -------------------------------------
    log("· mixing audio…")
    final = out / f"{Path(video).stem}_{style}.mp4"
    _mux(video, seg_src, seg_dur, work, work / "ptimings.json", cta_wav, hook_wav, word_wavs, silent, final)
    log(f"✓ done → {final}")
    return final


def _mux(video, seg_src, seg_dur, work, timings_path, cta_wav, hook_wav, word_wavs, silent, final):
    tj = json.loads(Path(timings_path).read_text(encoding="utf-8"))
    intro, cta_at, dur = tj["intro"], tj["cta_at"], tj["dur"]
    seg_at = [tj["seg"][f"seg{i}"]["at"] for i in range(1, 5)]
    stop_at = [s["at"] for s in tj["stops"]]
    # per-segment source dialogue
    aud = []
    for i in range(4):
        a = work / f"a_seg{i+1}.wav"
        subprocess.run(["ffmpeg", "-y", "-v", "error", "-ss", f"{seg_src[i]:.3f}",
                        "-to", f"{seg_src[i]+seg_dur[i]:.3f}", "-i", str(video),
                        "-ac", "2", "-ar", "48000", str(a)], check=True)
        aud.append(a)
    ms = lambda x: int(round(x * 1000))
    ctalen = dur - cta_at
    inputs = ["-i", str(hook_wav)] + sum([["-i", str(a)] for a in aud], []) + \
             sum([["-i", str(w)] for w in word_wavs], []) + ["-i", str(cta_wav)]
    bgm_ok = BGM.exists()
    if bgm_ok:
        inputs += ["-i", str(BGM)]
    f = [f"[0]adelay=300|300,volume=1.0[hk]"]
    for i in range(4):
        f.append(f"[{1+i}]adelay={ms(seg_at[i])}|{ms(seg_at[i])},volume=1.0[d{i}]")
    for i in range(3):
        at = ms(stop_at[i] + 0.7)
        f.append(f"[{5+i}]adelay={at}|{at},volume=1.15[r{i}]")
    f.append(f"[8]adelay={ms(cta_at+0.15)}|{ms(cta_at+0.15)},volume=1.05[ct]")
    labels = "[hk][d0][d1][d2][d3][r0][r1][r2][ct]"
    n = 9
    if bgm_ok:
        f.append(f"[9]asplit=2[mA][mB]")
        f.append(f"[mA]atrim=0:{intro:.3f},asetpts=N/SR/TB,afade=t=in:st=0:d=0.25,"
                 f"afade=t=out:st={max(0,intro-0.5):.3f}:d=0.5,volume=0.17[bh]")
        f.append(f"[mB]atrim=8:{8+ctalen:.3f},asetpts=N/SR/TB,afade=t=in:st=0:d=0.4,"
                 f"afade=t=out:st={max(0,ctalen-0.7):.3f}:d=0.7,volume=0.18,adelay={ms(cta_at)}|{ms(cta_at)}[bc]")
        labels += "[bh][bc]"; n = 11
    f.append(f"{labels}amix=inputs={n}:normalize=0:dropout_transition=0[mix]")
    f.append("[mix]loudnorm=I=-14:TP=-1.5:LRA=11[a]")
    full = work / "full.wav"
    subprocess.run(["ffmpeg", "-y", "-v", "error", *inputs, "-filter_complex", ";".join(f),
                    "-map", "[a]", "-ar", "48000", "-ac", "2", str(full)], check=True)
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", str(silent), "-i", str(full),
                    "-map", "0:v:0", "-map", "1:a:0", "-c:v", "copy", "-c:a", "aac", "-b:a", "192k",
                    str(final)], check=True)
