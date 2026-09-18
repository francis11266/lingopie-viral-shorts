# Get Started (for the whole team)

Make viral Spanish learning shorts on your own computer. No coding.
Follow this once; after that it's just "double-click → drag clip → download".

Works on **Windows** and **Mac**.

---

## 1. Install two free programs (one time)

| Program | Link | Notes |
|---------|------|-------|
| **Python 3.11+** | https://python.org/downloads | Windows: on the first install screen tick **“Add Python to PATH”**. |
| **Node.js 18+** | https://nodejs.org (the “LTS” button) | Just click through the installer. |
| **ffmpeg** | Win: https://www.gyan.dev/ffmpeg/builds/ (get “release full”, unzip, add its `bin` folder to PATH). Mac: install Homebrew then `brew install ffmpeg`. | Needed for video/audio. |

> Not sure if you have them? Open Terminal (Mac) / Command Prompt (Windows) and type `python --version`, `node --version`, `ffmpeg -version`. Each should print a version.

## 2. Get the code

Open the GitHub repo your team shared → green **Code** button → **Download ZIP** →
unzip it somewhere easy, e.g. your Desktop. You'll have a folder `lingopie-viral-shorts`.

## 3. Get two API keys (one time)

The tool uses two paid services. Each teammate can use their own keys, or the team can
share one set.

- **ElevenLabs** (the voice): https://elevenlabs.io → sign in → profile → **API Keys** → copy.
- **Anthropic / Claude** (picks the scene + the 3 words): https://console.anthropic.com → **API Keys** → create → copy.

## 4. First launch

- **Windows:** double-click **`start.bat`**
- **Mac:** double-click **`start.command`**
  (If Mac blocks it: right-click → Open → Open. Or run `chmod +x start.command` once.)

The first launch installs the tool (a few minutes), then creates a file called **`.env`**
and opens it. Paste your two keys so it looks like:

```
ELEVENLABS_API_KEY=sk_...paste here...
ELEVENLABS_VOICE_ID=pNInz6obpgDQGcFmaJgB
ANTHROPIC_API_KEY=sk-ant-...paste here...
ANTHROPIC_MODEL=claude-opus-4-8
```

**Save the file**, then double-click `start.bat` / `start.command` **again**.

## 5. Make a short

Your browser opens at **http://localhost:8000**.

1. **Drag a Spanish drama clip** onto the box (any length; it finds the best ~20s scene).
2. Pick a **style**: POV hook · Challenge · Word counter.
3. Pick a **voice** (Adam = deep American male, default).
4. Click **Generate**. The log shows: transcribe → scene → cut → voice → render → mix.
   The very first run also downloads the speech model, so give it a few minutes.
5. When it's done, the finished 9:16 short appears — click **⬇ download**.

Make as many as you like. To stop the tool, just close the black window / terminal.

---

## Tips & fixes

- **“python/node/ffmpeg is not recognized”** → that program isn't installed or not on PATH. Redo step 1 (Windows: reinstall Python with “Add to PATH” ticked).
- **It says a key is missing** → open `.env`, check both keys are pasted with no spaces, save, relaunch.
- **Nothing opens in the browser** → go to http://localhost:8000 manually.
- **Want a different narrator** → change the **Voice** dropdown before Generate.
- **Best clips** = a clear, gripping dialogue scene (flirty / tense / funny). Talking-head drama works best; avoid loud background music in the source.

You never touch code. One teammate can also host it once on a shared machine/server so
others just open the URL — ask whoever set it up.
