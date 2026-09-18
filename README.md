# Lingopie Viral Shorts

Turn a Spanish drama clip into a viral 9:16 language-learning short — automatically.
Upload a clip, and the tool finds a gripping scene, teaches **3 beginner words** with a
tap-to-reveal translation bubble, always-on Spanish captions, a spoken **hook** and a
**"learn Spanish while you binge the drama" CTA**. Three viral styles included.

| Style | What it is |
|-------|------------|
| **s2 — POV hook** | Cold-open freeze + *"POV: you learn Spanish from telenovelas"* |
| **s3 — Challenge** | *"Can you catch 3 Spanish words in this scene?"* |
| **s4 — Word counter** | Live `0/3 → 3/3` counter + *"you just learned 3 words"* payoff |

Every style: American voiceover (ElevenLabs), narrator says each Spanish word, always-on
captions, light music under the hook + CTA, DramaRizz outro.

---

## For teammates — no code needed

1. Install **Python 3.11+** ([python.org](https://python.org)) and **Node 18+** ([nodejs.org](https://nodejs.org)) once.
2. **Windows:** double-click **`start.bat`**.  **Mac:** double-click **`start.command`**.
3. First run: it creates a `.env` and opens it — paste the two API keys (below), save, run again.
4. Your browser opens at **http://localhost:8000**. Drag a clip, pick a style + voice, click **Generate**, download the short.

That's it. One person sets up the keys once; everyone else just uses the page.

## Keys (set once, by whoever deploys it)

Put these in `.env` (copy from `.env.example`):

- `ELEVENLABS_API_KEY` — voiceover ([elevenlabs.io](https://elevenlabs.io) → API Keys)
- `ANTHROPIC_API_KEY` — Claude picks the scene + the 3 words ([console.anthropic.com](https://console.anthropic.com))
- `ELEVENLABS_VOICE_ID` — default narrator (Adam, deep American male, pre-filled)

## Command line (optional)

```bash
python generate.py --input clip.mp4 --style s2 --output out
python generate.py -i clip.mp4 -s s4 -v "brian (m, american narrator)"
```

## How it works

`docs/PIPELINE.md` has the full flow. In short:
`transcribe (faster-whisper) → Claude picks scene + 3 A1 words → ffmpeg cuts
segments/freezes/cold frame → ElevenLabs voiceover → HyperFrames builds + renders the
9:16 composition → ffmpeg mixes dialogue + voice + music → MP4`.

Requires `ffmpeg` on PATH. The renderer (`hyperframes`) installs via `npm install`.
