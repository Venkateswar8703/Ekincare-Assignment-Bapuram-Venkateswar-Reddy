"""
Claim Processing Pipeline — FastAPI Application.

Exposes POST /api/process which accepts a claim_id and a PDF file,
runs the LangGraph pipeline, and returns structured JSON.
"""

from __future__ import annotations

import logging
import os
import uuid

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.config import UPLOAD_DIR, MAX_FILE_SIZE_MB
from app.workflow import claim_pipeline

# ── Logging ───────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s │ %(name)-30s │ %(levelname)-7s │ %(message)s",
)
logger = logging.getLogger(__name__)

# ── FastAPI App ───────────────────────────────────────────────────────────

app = FastAPI(
    title="Claim Processing Pipeline",
    description=(
        "AI-powered claim document processing service. "
        "Accepts a PDF claim, segregates pages by document type using "
        "an LLM, routes pages to specialised extraction agents, and "
        "returns structured JSON with all extracted data."
    ),
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Health Check ──────────────────────────────────────────────────────────

@app.get("/", tags=["health"])
async def root():
    """Health check endpoint."""
    return {
        "service": "Claim Processing Pipeline",
        "version": "1.0.0",
        "status": "healthy",
    }


@app.get("/health", tags=["health"])
async def health():
    """Detailed health check."""
    return {"status": "ok"}


# ── Core Endpoint ─────────────────────────────────────────────────────────

@app.post("/api/process", tags=["processing"])
async def process_claim(
    claim_id: str = Form(..., description="Unique claim identifier"),
    file: UploadFile = File(..., description="PDF claim document"),
):
    """
    Process a PDF claim document through the AI pipeline.

    1. Validates & saves the uploaded PDF.
    2. Runs the LangGraph workflow (segregator → extractors → aggregator).
    3. Returns structured JSON with all extracted data.
    """
    # ── Validate ──────────────────────────────────────────────────────
    if not file.filename or not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are accepted.")

    content = await file.read()
    size_mb = len(content) / (1024 * 1024)
    if size_mb > MAX_FILE_SIZE_MB:
        raise HTTPException(
            status_code=400,
            detail=f"File too large ({size_mb:.1f} MB). Maximum is {MAX_FILE_SIZE_MB} MB.",
        )

    # ── Save to disk ──────────────────────────────────────────────────
    unique_name = f"{claim_id}_{uuid.uuid4().hex[:8]}.pdf"
    save_path = os.path.join(UPLOAD_DIR, unique_name)
    os.makedirs(UPLOAD_DIR, exist_ok=True)

    with open(save_path, "wb") as f:
        f.write(content)

    logger.info("Saved uploaded PDF → %s (%.2f MB)", save_path, size_mb)

    # ── Run LangGraph Pipeline ────────────────────────────────────────
    try:
        initial_state = {
            "claim_id": claim_id,
            "pdf_path": save_path,
            "errors": [],
        }

        logger.info("Starting LangGraph pipeline for claim_id=%s", claim_id)
        final_state = claim_pipeline.invoke(initial_state)
        logger.info("Pipeline completed for claim_id=%s", claim_id)

        # Build response
        aggregated = final_state.get("aggregated_result", {})
        errors = final_state.get("errors", [])

        response = {
            "claim_id": claim_id,
            "status": "success" if not errors else "partial_success",
            "segregation": aggregated.get("segregation_summary", {}),
            "extracted_data": aggregated.get("extracted_data", {}),
            "errors": errors,
        }

        return JSONResponse(content=response)

    except Exception as exc:
        logger.exception("Pipeline failed for claim_id=%s", claim_id)
        raise HTTPException(
            status_code=500,
            detail=f"Pipeline processing failed: {str(exc)}",
        )

    finally:
        # Clean up uploaded file
        try:
            os.remove(save_path)
            logger.info("Cleaned up %s", save_path)
        except OSError:
            pass
