import tempfile
import os
from fastapi import FastAPI, Form, HTTPException, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
import yt_dlp

app = FastAPI()

# Enable CORS for all origins (for GitHub Pages frontend)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/api/info")
async def get_video_info(url: str = Form(...)):
    try:
        ydl_opts = {"quiet": True, "skip_download": True, "extract_flat": False}
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
        return {
            "title": info.get("title"),
            "thumbnail": info.get("thumbnail"),
            "uploader": info.get("uploader"),
            "duration": info.get("duration"),
            "formats": [
                {"format_id": f["format_id"], "ext": f["ext"], "format_note": f.get("format_note", ""), "filesize": f.get("filesize")}
                for f in info.get("formats", [])
                if f.get("ext") in ["mp4", "m4a", "webm", "mp3"]
            ],
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/api/download")
async def download_video(
    url: str = Form(...),
    format_id: str = Form(...)
):
    try:
        with tempfile.TemporaryDirectory() as tmpdir:
            ydl_opts = {
                "outtmpl": os.path.join(tmpdir, "%(title)s.%(ext)s"),
                "format": format_id,
                "quiet": True,
            }
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)
                filename = ydl.prepare_filename(info)
            if not os.path.exists(filename):
                raise HTTPException(status_code=404, detail="File not found after download.")
            ext = filename.split('.')[-1]
            return FileResponse(
                filename,
                media_type="video/mp4" if ext == "mp4" else "audio/mpeg",
                filename=os.path.basename(filename),
                headers={
                    "Cache-Control": "no-cache",
                    "Content-Disposition": f'attachment; filename="{os.path.basename(filename)}"'
                }
            )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
