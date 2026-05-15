"""
Claim Processing Pipeline - Configuration Module.

Centralises all environment variables and application settings.
"""

import os
from dotenv import load_dotenv

load_dotenv()

# ── Google Gemini ──────────────────────────────────────────────────────────
GOOGLE_API_KEY: str = os.getenv("GOOGLE_API_KEY", "")
GEMINI_MODEL: str = os.getenv("GEMINI_MODEL", "gemini-2.0-flash")

# ── Application ───────────────────────────────────────────────────────────
UPLOAD_DIR: str = os.getenv("UPLOAD_DIR", "uploads")
MAX_FILE_SIZE_MB: int = int(os.getenv("MAX_FILE_SIZE_MB", "50"))

# ── Document types recognised by the Segregator Agent ─────────────────────
DOCUMENT_TYPES: list[str] = [
    "claim_forms",
    "cheque_or_bank_details",
    "identity_document",
    "itemized_bill",
    "discharge_summary",
    "prescription",
    "investigation_report",
    "cash_receipt",
    "other",
]

# Ensure upload directory exists
os.makedirs(UPLOAD_DIR, exist_ok=True)
