#!/usr/bin/env python3
"""FastAPI backend for Soccer Practice Excel Generator."""

import tempfile
import os
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from dotenv import load_dotenv

from src.agent import PracticeMenuAgent

# Load environment variables
load_dotenv()

app = FastAPI(
    title="Soccer Practice Menu Generator",
    description="サッカー練習メニューをExcelファイルで生成するAPI",
    version="1.0.0",
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class PracticeRequest(BaseModel):
    """Request model for practice menu generation."""

    challenge: str

    class Config:
        json_schema_extra = {"example": {"challenge": "4人でのパス練習"}}


@app.get("/", response_class=HTMLResponse)
async def root():
    """Serve the frontend HTML page."""
    html_path = Path(__file__).parent / "static" / "index.html"
    if html_path.exists():
        return HTMLResponse(content=html_path.read_text(encoding="utf-8"))
    return HTMLResponse(content="<h1>Soccer Practice Menu Generator</h1><p>Frontend not found</p>")


@app.post("/api/generate")
async def generate_practice_menu(request: PracticeRequest):
    """Generate a practice menu Excel file.

    Args:
        request: Practice request containing the challenge description.

    Returns:
        Excel file as download.
    """
    if not request.challenge.strip():
        raise HTTPException(status_code=400, detail="練習課題を入力してください")

    # Check API key (either OpenRouter or Azure)
    has_openrouter = bool(os.getenv("OPENROUTER_API_KEY"))
    has_azure = bool(os.getenv("AZURE_OPENAI_API_KEY") and os.getenv("AZURE_OPENAI_ENDPOINT"))
    if not has_openrouter and not has_azure:
        raise HTTPException(
            status_code=500,
            detail="APIキーが設定されていません。OPENROUTER_API_KEY または AZURE_OPENAI_API_KEY/AZURE_OPENAI_ENDPOINT を設定してください",
        )

    try:
        # Create temp file for output
        temp_dir = tempfile.mkdtemp()
        output_path = os.path.join(temp_dir, "practice_menu.xlsx")

        # Generate practice menu
        agent = PracticeMenuAgent()
        agent.generate_practice_menu(request.challenge, output_path)

        # Return file
        return FileResponse(
            path=output_path,
            filename="practice_menu.xlsx",
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"生成エラー: {str(e)}")


@app.get("/api/health")
async def health_check():
    """Health check endpoint."""
    has_openrouter = bool(os.getenv("OPENROUTER_API_KEY"))
    has_azure = bool(os.getenv("AZURE_OPENAI_API_KEY") and os.getenv("AZURE_OPENAI_ENDPOINT"))

    # Detect which provider will be used
    if has_azure:
        provider = "Azure OpenAI"
    elif has_openrouter:
        provider = "OpenRouter"
    else:
        provider = None

    return {
        "status": "ok",
        "api_key_configured": has_openrouter or has_azure,
        "provider": provider,
    }


# Mount static files
static_dir = Path(__file__).parent / "static"
if static_dir.exists():
    app.mount("/static", StaticFiles(directory=static_dir), name="static")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
