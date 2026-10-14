import os
import asyncio
from typing import Optional

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field
from huggingface_hub import InferenceClient

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
HF_TOKEN = os.getenv("HF_TOKEN", "").strip()
HF_MODEL = os.getenv("HF_MODEL", "Wan-AI/Wan2.2-TI2V-5B").strip()
HF_PROVIDER = os.getenv("HF_PROVIDER", "fal-ai").strip()

app = FastAPI(title="FrameForge API", version="2.0.0")

class GenerateRequest(BaseModel):
    prompt: str = Field(min_length=5, max_length=8000)
    project: Optional[str] = Field(default="Untitled Film Project", max_length=120)
    aspect_ratio: Optional[str] = Field(default="16:9", pattern=r"^(16:9|9:16|1:1)$")

@app.get("/api/health")
def health():
    return {
        "ok": True,
        "provider": "Hugging Face Inference Providers",
        "provider_configured": bool(HF_TOKEN),
        "provider_name": HF_PROVIDER,
        "model": HF_MODEL,
    }

@app.post("/api/generate")
async def generate(req: GenerateRequest):
    if not HF_TOKEN:
        raise HTTPException(
            status_code=503,
            detail="Video provider is not configured. Set HF_TOKEN as a server environment variable, then restart/redeploy FrameForge."
        )
    # The API key stays on the server. A synchronous model call is run in a worker
    # thread so the FastAPI event loop can continue handling other requests.
    try:
        client = InferenceClient(
            provider=HF_PROVIDER,
            api_key=HF_TOKEN,
            timeout=540,
        )
        video_bytes = await asyncio.to_thread(
            client.text_to_video,
            req.prompt,
            model=HF_MODEL,
        )
        if not video_bytes:
            raise RuntimeError("The provider returned an empty response.")
        # Some providers may return bytes or a file-like object; normalize to bytes.
        if hasattr(video_bytes, "read"):
            video_bytes = video_bytes.read()
        if not isinstance(video_bytes, (bytes, bytearray)):
            raise RuntimeError(
                "Unexpected output type from provider. Check the model's text-to-video support and provider compatibility."
            )
        return StreamingResponse(
            iter([bytes(video_bytes)]),
            media_type="video/mp4",
            headers={"Content-Disposition": 'inline; filename="frameforge-clip.mp4"'},
        )
    except HTTPException:
        raise
    except Exception as exc:
        # Do not return secrets or raw request headers. Error text is for troubleshooting.
        message = str(exc)
        if "401" in message or "Unauthorized" in message:
            detail = "The provider rejected HF_TOKEN. Verify the token and that it has permission to use Inference Providers."
        elif "402" in message or "payment" in message.lower() or "credit" in message.lower():
            detail = "The provider reports insufficient credits or billing access. Check your Hugging Face Inference Providers usage and model pricing."
        elif "404" in message or "not found" in message.lower():
            detail = f"The configured model/provider route was not found. Check HF_MODEL ({HF_MODEL}) and HF_PROVIDER ({HF_PROVIDER}) against the current text-to-video docs."
        else:
            detail = f"Video generation failed: {message[:700]}"
        raise HTTPException(status_code=502, detail=detail) from exc

@app.get("/")
def home():
    return FileResponse(os.path.join(BASE_DIR, "index.html"))

# Keep API routes above the static mount.
