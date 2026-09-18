"""Browser app — a teammate uploads a Spanish clip and downloads the finished short.
No code: run start.bat (Windows) or start.command (Mac), then open the page.

    uvicorn webapp.app:app --host 0.0.0.0 --port 8000
"""
from __future__ import annotations
import io, threading, uuid
from contextlib import redirect_stdout
from pathlib import Path

try:
    from dotenv import load_dotenv; load_dotenv()
except Exception:
    pass

from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.responses import HTMLResponse, FileResponse, JSONResponse

from src.pipeline import generate
from src import styles

ROOT = Path(__file__).resolve().parent.parent
JOBS_DIR = ROOT / "webapp_jobs"; JOBS_DIR.mkdir(exist_ok=True)
INDEX = (Path(__file__).resolve().parent / "static" / "index.html").read_text(encoding="utf-8")

app = FastAPI(title="Lingopie Viral Shorts")
JOBS: dict[str, dict] = {}
_lock = threading.Lock()


class _Tee(io.StringIO):
    def __init__(self, job): super().__init__(); self.job = job
    def write(self, s):
        if s.strip(): self.job["log"].append(s.rstrip())
        return len(s)


def _worker(job_id, video_path, style, language, voice_id):
    job = JOBS[job_id]; outdir = JOBS_DIR / job_id / "output"
    try:
        with _lock:
            job["status"] = "running"
            with redirect_stdout(_Tee(job)):
                final = generate(str(video_path), style, str(outdir),
                                 language=language, voice_id=voice_id, verbose=True)
            job["outputs"] = [final.name]; job["status"] = "done"
    except Exception as e:  # noqa: BLE001
        job["status"] = "error"; job["error"] = f"{type(e).__name__}: {e}"
        job["log"].append("ERROR: " + job["error"])


@app.get("/", response_class=HTMLResponse)
def index() -> str:
    return INDEX


@app.get("/api/voices")
def api_voices():
    return {"voices": list(styles.VOICES.keys())}


@app.post("/api/generate")
async def api_generate(video: UploadFile = File(...), style: str = Form("s2"),
                       language: str = Form("es"), voice: str = Form("")):
    if not video.filename:
        raise HTTPException(400, "no file")
    voice_id = styles.VOICES.get(voice.lower(), voice) or None
    job_id = uuid.uuid4().hex[:12]; jdir = JOBS_DIR / job_id; jdir.mkdir(parents=True, exist_ok=True)
    dest = jdir / ("input" + Path(video.filename).suffix.lower())
    dest.write_bytes(await video.read())
    JOBS[job_id] = {"status": "queued", "log": [], "outputs": [], "error": None}
    threading.Thread(target=_worker, args=(job_id, dest, style, language, voice_id), daemon=True).start()
    return {"job_id": job_id}


@app.get("/api/status/{job_id}")
def api_status(job_id: str):
    job = JOBS.get(job_id)
    if not job: raise HTTPException(404, "unknown job")
    return JSONResponse({"status": job["status"], "log": job["log"][-50:],
                         "outputs": job["outputs"], "error": job["error"]})


@app.get("/api/download/{job_id}/{name}")
def api_download(job_id: str, name: str):
    f = JOBS_DIR / job_id / "output" / Path(name).name
    if not f.exists(): raise HTTPException(404, "not found")
    return FileResponse(str(f), media_type="video/mp4", filename=name)
