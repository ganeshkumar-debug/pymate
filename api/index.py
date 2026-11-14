"""
PyMate v3 — Python AI Chatbot Backend
Server-side API key hardcoded. All users share it.
Supports all Gemini models with live model switching.
"""

import os
import json
import time
import traceback
from typing import List, Optional, Dict, Any
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

# Load .env for local development
try:
    from dotenv import load_dotenv
    load_dotenv(override=True)
except ImportError:
    pass

app = FastAPI(title="PyMate", version="3.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ══════════════════════════════════════════════════════════════════════════════
# 🔑 SERVER GEMINI API KEY (Shared by all users — upload/paste your key here)
# ══════════════════════════════════════════════════════════════════════════════
# You can paste your Gemini API key directly below, OR set GEMINI_API_KEY in .env
HARDCODED_API_KEY = "past your api key"

def get_api_key() -> str:
    """Returns the Gemini API key from file or environment."""
    # 1. Check HARDCODED_API_KEY first if user filled it
    if HARDCODED_API_KEY and not HARDCODED_API_KEY.startswith("YOUR_") and len(HARDCODED_API_KEY) > 15:
        # Check if environment overrides it
        env_key = os.environ.get("GEMINI_API_KEY", "").strip()
        if env_key and not env_key.startswith("PASTE") and len(env_key) > 15:
            return env_key
        return HARDCODED_API_KEY.strip()

    # 2. Check environment variable / .env
    try:
        from dotenv import load_dotenv
        load_dotenv(override=True)
    except Exception:
        pass
    env_key = os.environ.get("GEMINI_API_KEY", "").strip()
    return env_key

# Default model
DEFAULT_MODEL = os.environ.get("GEMINI_MODEL", "gemini-3.5-flash")

# ─── All available Gemini models ──────────────────────────────────────────
AVAILABLE_MODELS = [
    {"id": "gemini-3.5-flash",      "name": "Gemini 3.5 Flash",      "desc": "Fast, smart & reliable (recommended)", "tier": "fast"},
    {"id": "gemini-3.7-flash",      "name": "Gemini 3.7 Flash",      "desc": "Advanced reasoning & speed",           "tier": "fast"},
    {"id": "gemini-3.8-flash",      "name": "Gemini 3.8 Flash",      "desc": "Next-gen Flash model",                 "tier": "fast"},
    {"id": "gemini-3.6-flash",      "name": "Gemini 3.6 Flash",      "desc": "Balanced performance",                 "tier": "fast"},
    {"id": "gemini-3.5-flash-lite", "name": "Gemini 3.5 Flash Lite", "desc": "Lightweight & ultra quick",            "tier": "fast"},
    {"id": "gemini-3.1-flash-lite", "name": "Gemini 3.1 Flash Lite", "desc": "Small & quick",                       "tier": "fast"},
]
# ─── System Prompt (optimized for fast, concise Python answers) ───────────
SYSTEM_PROMPT = (
    "You are PyMate, a dedicated Python programming assistant. "
    "Answer ONLY Python-related questions. Be concise and direct. "
    "Jump straight to the solution with minimal preamble. "
    "Wrap code in ```python blocks. Keep answers short and focused. "
    "The user may write in broken English, slang, typos, or shorthand — "
    "silently understand the intent and answer correctly. "
    "Never correct their grammar. "
    "If a question is not about Python, politely say: "
    "'I specialize in Python! Please ask me a Python-related question.'"
)

# ─── Client cache ──────────────────────────────────────────────────────────
_client_cache: Dict[str, Any] = {}

def _get_client(api_key: str):
    if api_key not in _client_cache:
        from google import genai
        _client_cache[api_key] = genai.Client(api_key=api_key)
    return _client_cache[api_key]

# ─── Request / Response Models ─────────────────────────────────────────────
class Msg(BaseModel):
    role: str
    content: str

class ChatReq(BaseModel):
    messages: List[Msg]
    model: Optional[str] = None
    temperature: Optional[float] = 0.3

# ─── Endpoints ─────────────────────────────────────────────────────────────
@app.get("/api/health")
def health():
    key = get_api_key()
    is_valid = bool(key and len(key) > 15 and not key.startswith("YOUR_"))
    return {
        "status": "ok",
        "ready": is_valid,
        "model": DEFAULT_MODEL,
        "models": AVAILABLE_MODELS,
        "ts": time.time(),
    }

@app.get("/api/models")
def list_models():
    return {"models": AVAILABLE_MODELS, "default": DEFAULT_MODEL}

@app.post("/api/chat")
def chat(req: ChatReq):
    if not req.messages:
        raise HTTPException(400, "No messages")

    api_key = get_api_key()
    if not api_key or len(api_key) < 15 or api_key.startswith("YOUR_"):
        raise HTTPException(
            500,
            "Gemini API key missing on server! Please paste your API key inside api/index.py (at HARDCODED_API_KEY) or in .env."
        )

    model = req.model or DEFAULT_MODEL
    temp = max(0.0, min(1.0, req.temperature or 0.3))

    return StreamingResponse(
        _stream(api_key, model, req.messages, temp),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
            "Connection": "keep-alive",
        },
    )

# ─── Streaming Generator ──────────────────────────────────────────────────
def _stream(api_key: str, model: str, messages: List[Msg], temp: float):
    """SSE generator with automatic model fallback for speed."""
    try:
        from google.genai import types

        client = _get_client(api_key)

        contents = []
        for m in messages:
            role = "user" if m.role in ("user", "human") else "model"
            contents.append(
                types.Content(role=role, parts=[types.Part.from_text(text=m.content)])
            )

        cfg_kwargs: Dict[str, Any] = {
            "system_instruction": SYSTEM_PROMPT,
            "temperature": temp,
        }

        # Try primary model, fallback chain on failure
        fallback_chain = [model]
        for fb in ["gemini-3.5-flash", "gemini-3.7-flash", "gemini-3.5-flash-lite"]:
            if fb not in fallback_chain:
                fallback_chain.append(fb)

        last_err = None
        for target in fallback_chain:
            try:
                config = types.GenerateContentConfig(**cfg_kwargs)
                stream = client.models.generate_content_stream(
                    model=target, contents=contents, config=config
                )
                for chunk in stream:
                    txt = None
                    try:
                        txt = chunk.text
                    except (ValueError, AttributeError):
                        pass
                    if txt:
                        yield f"data: {json.dumps({'t': txt})}\n\n"
                # If we got here, success — break out of fallback chain
                yield "data: [DONE]\n\n"
                return
            except Exception as e:
                last_err = e
                err_str = str(e).lower()
                if "not found" in err_str or "404" in err_str or "unavailable" in err_str or "503" in err_str:
                    continue  # Try next fallback
                else:
                    raise e

        # All fallbacks failed
        if last_err:
            raise last_err

    except Exception as e:
        err = str(e)
        if "API_KEY_INVALID" in err or "API key not valid" in err:
            msg = "Invalid API Key. The server's API key needs to be updated."
        elif "RESOURCE_EXHAUSTED" in err or "429" in err:
            msg = "Rate limit reached. Please wait a moment and try again."
        elif "not found" in err.lower() or "404" in err:
            msg = f"Model not available. Try switching to a different model."
        elif "unavailable" in err.lower() or "503" in err:
            msg = "Model temporarily unavailable. Try a different model or wait a moment."
        else:
            msg = f"Error: {err[:300]}"

        yield f"data: {json.dumps({'e': msg})}\n\n"
        yield "data: [DONE]\n\n"

# ─── Static file serving (local dev) ──────────────────────────────────────
_pub = Path(__file__).parent.parent / "public"
if _pub.exists():
    app.mount("/assets", StaticFiles(directory=str(_pub / "assets")), name="assets")
    app.mount("/css", StaticFiles(directory=str(_pub / "css")), name="css")
    app.mount("/js", StaticFiles(directory=str(_pub / "js")), name="js")

    @app.get("/")
    def serve_index():
        return FileResponse(str(_pub / "index.html"))
