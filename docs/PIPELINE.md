# Pipeline

```
 clip.mp4
    │
    ▼
 1. TRANSCRIBE           src/transcribe.py  (faster-whisper small, int8, word timestamps)
    │  → word-level transcript (seconds)
    ▼
 2. PICK SCENE + WORDS   src/autopick.py  (Claude / ANTHROPIC_API_KEY)
    │  → { window:{start,end}, stops:[{word,en,tag,phrase,hl,word_in,word_out} ×3] }
    ▼
 3. CUT                  src/ffmpeg_ops.py
    │  window_start = firstWord_in − 0.4
    │  freeze_i     = word_out_i + 0.12         (freeze after each target word)
    │  seg1..seg4 = [start→f0, f0→f1, f1→f2, f2→end]  (1080×1920, 30fps, muted)
    │  frz-seg1..3.png = last frame of seg1..3   cold.png = first frame of seg1
    ▼
 4. VOICEOVER            src/elevenlabs_tts.py  (ElevenLabs REST, eleven_multilingual_v2)
    │  hook  = style hook line     words = "<spanish>, <english>!"  ×3     cta = style CTA line
    │  brand spoken as "Drama Riz" so it says rizz, not rice. Silence-trimmed to wav.
    │  INTRO (cold-open freeze length) = hook_vo duration + 0.9
    ▼
 5. BUILD                node/build_short.mjs  ← build.json (all data resolved in Python)
    │  writes public/index.html + ptimings.json
    │  timeline: [cold+hook] → seg1 → freeze/reveal(word0) → seg2 → reveal(word1)
    │            → seg3 → reveal(word2) → seg4 → CTA
    │  always-on caption track; s4 adds the 0/3→3/3 counter + recap CTA
    ▼
 6. RENDER               npx hyperframes@0.7.64 render public --workers 1   → silent.mp4  (VISUALS ONLY)
    ▼
 7. MIX                  src/pipeline.py::_mux  (ffmpeg)
    │  hook VO @0.3s · segment dialogue @ each seg start · word VO @ reveal+0.7s
    │  CTA VO @ cta_at · music bed ONLY under hook + CTA (never over dialogue) · loudnorm
    │  mux onto silent.mp4
    ▼
 <clipname>_<style>.mp4      (9:16, ~40s)
```

## Files
- `node/build_short.mjs` — the one renderer for all styles (data-driven).
- `node/assets/` — fonts, vendored GSAP, `music_bed.wav`.
- `src/pipeline.py` — orchestrates steps 3–7. `src/styles.py` — locked hook/CTA copy + voice map.
- `src/autopick.py` — Claude scene/word picker. `src/transcribe.py`, `src/ffmpeg_ops.py`, `src/elevenlabs_tts.py` — helpers.
- `webapp/` — the no-code browser app. `generate.py` — CLI.

## Notes / tuning
- Locked constants live at the top of `src/pipeline.py`: `LEAD, TAIL, HOLD, CTADUR`.
- To change a voice, use the web app's dropdown or `--voice`; add voices in `src/styles.py::VOICES`
  (values are real ElevenLabs `voice_id`s).
- To change hook/CTA wording, edit `src/styles.py`.
- The render/mux path is deterministic and offline; only steps 1–2 and 4 use the network.
- `ELEVENLABS_VOICE_ID` names an ElevenLabs library voice; the in-house test voice from the
  original session ("Holden"/Higgsfield) is not an ElevenLabs REST voice, so the repo defaults
  to ElevenLabs **Adam** (deep American male) — swap per taste.
```
