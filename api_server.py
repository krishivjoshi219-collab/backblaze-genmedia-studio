import os
import sys
import time
import uuid
import logging
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field

try:
    from fastapi import FastAPI, HTTPException, Header, UploadFile, File, BackgroundTasks
    from fastapi.middleware.cors import CORSMiddleware
    from fastapi.responses import JSONResponse, FileResponse
    HAS_FASTAPI = True
except ImportError:
    HAS_FASTAPI = False

# Import modular services
from services.manga import compile_manga_panel, colorize_manga_panel
from services.novel import write_japanese_novel_scene, translate_novel_text
from services.whisper import transcribe_audio, export_multiformat_subtitles
from services.vault import test_b2_connection, archive_to_b2, get_b2_vault_gallery, get_presigned_streaming_url
from services.orchestrator import CentralOrchestrator, MODEL_CATALOG

# Setup Logger
logger = logging.getLogger("GenMediaAPIServer")

app = FastAPI(
    title="Backblaze GenMedia Studio REST API",
    description="Production-Grade Multi-Modal Generative AI & Backblaze B2 Storage API Backend",
    version="2.5.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Enable CORS for external API integrations
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Request Models
class MangaGenerateRequest(BaseModel):
    prompt: str = Field(..., example="A cyberpunk samurai navigating neon-lit Neo Tokyo")
    style_preset: str = Field("Cyberpunk Neon", example="Cyberpunk Neon")
    model_id: Optional[str] = Field(None, example="gemini-2.5-flash-image")

class NovelGenerateRequest(BaseModel):
    title: str = Field("運命のコンパイル", example="Destiny Compile")
    concept: str = Field(..., example="A programmer reincarnated as a wizard whose spells use a compiler")
    genre: str = Field("Isekai (Otherworld Fantasy)", example="Isekai")
    tone: str = Field("Expressive & Standard", example="Epic & Grandiose")
    model_id: Optional[str] = Field("Qwen/Qwen2.5-7B-Instruct", example="Qwen/Qwen2.5-7B-Instruct")

class TranslationRequest(BaseModel):
    source_text: str = Field(..., example="「――エラーだと？ 馬鹿な、そんなはずはない！」")
    direction: str = Field("Japanese ➔ English", example="Japanese ➔ English")
    model_id: Optional[str] = Field("Qwen/Qwen2.5-7B-Instruct")

class VaultGalleryRequest(BaseModel):
    b2_id: str = Field(...)
    b2_key: str = Field(...)
    b2_bucket: str = Field(...)
    limit: int = Field(50, ge=1, le=200)

# Helper function to resolve auth token
def get_auth_token(authorization: Optional[str] = Header(None), x_api_key: Optional[str] = Header(None)) -> str:
    if authorization:
        if authorization.startswith("Bearer "):
            return authorization[7:].strip()
        return authorization.strip()
    if x_api_key:
        return x_api_key.strip()
    return os.environ.get("GEMINI_API_KEY", "") or os.environ.get("HF_TOKEN", "")

@app.get("/")
def root_endpoint():
    return {
        "status": "online",
        "service": "Backblaze GenMedia Studio REST API Backend",
        "version": "2.5.0",
        "documentation": "/docs",
        "timestamp": time.time()
    }

@app.get("/api/v1/health")
def health_check():
    return {
        "status": "healthy",
        "models_supported": MODEL_CATALOG,
        "services": ["manga", "novel", "whisper", "vault", "orchestrator"],
        "server_time": time.strftime("%Y-%m-%d %H:%M:%S GMT", time.gmtime())
    }

@app.post("/api/v1/manga/generate")
def generate_manga(req: MangaGenerateRequest, authorization: Optional[str] = Header(None), x_api_key: Optional[str] = Header(None)):
    token = get_auth_token(authorization, x_api_key)
    full_prompt = f"{req.prompt}, {req.style_preset} style, masterpiece"
    ok, res_path = compile_manga_panel(token, full_prompt, model_id=req.model_id)
    
    if not ok:
        raise HTTPException(status_code=500, detail=f"Manga generation failed: {res_path}")
        
    return {
        "success": True,
        "image_path": res_path,
        "prompt": full_prompt,
        "model_used": req.model_id or MODEL_CATALOG["image"],
        "timestamp": time.time()
    }

@app.post("/api/v1/novel/generate")
def generate_novel(req: NovelGenerateRequest, authorization: Optional[str] = Header(None), x_api_key: Optional[str] = Header(None)):
    token = get_auth_token(authorization, x_api_key)
    prompt_instructions = (
        f"Title: {req.title}\nConcept: {req.concept}\nGenre: {req.genre}\nTone: {req.tone}\n"
        f"Format output as an engaging Light Novel chapter."
    )
    ok, jp_text, en_text = write_japanese_novel_scene(token, prompt_instructions, model_id=req.model_id)
    if not ok:
        raise HTTPException(status_code=500, detail=f"Novel generation failed: {jp_text}")
        
    return {
        "success": True,
        "title": req.title,
        "japanese_prose": jp_text,
        "english_prose": en_text,
        "model_used": req.model_id,
        "timestamp": time.time()
    }

@app.post("/api/v1/translate")
def translate_text(req: TranslationRequest, authorization: Optional[str] = Header(None), x_api_key: Optional[str] = Header(None)):
    token = get_auth_token(authorization, x_api_key)
    prompt = f"Translate from {req.direction}:\n\n{req.source_text}"
    ok, translated = translate_novel_text(token, prompt, model_id=req.model_id)
    if not ok:
        raise HTTPException(status_code=500, detail=f"Translation failed: {translated}")
        
    return {
        "success": True,
        "source_text": req.source_text,
        "translated_text": translated,
        "direction": req.direction
    }

@app.post("/api/v1/vault/gallery")
def fetch_vault_gallery(req: VaultGalleryRequest):
    ok, msg, items = get_b2_vault_gallery(req.b2_id, req.b2_key, req.b2_bucket, limit=req.limit)
    if not ok:
        raise HTTPException(status_code=400, detail=f"B2 Vault error: {msg}")
    return {
        "success": True,
        "message": msg,
        "asset_count": len(items),
        "assets": items
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
