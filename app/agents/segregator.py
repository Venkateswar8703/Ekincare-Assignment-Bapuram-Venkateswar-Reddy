"""
Segregator Agent — AI-powered PDF page classifier.

Takes the full PDF, renders each page to an image, and asks Gemini to
classify every page into one of the 9 recognised document types.
"""

from __future__ import annotations

import logging
from typing import Any

from app.config import DOCUMENT_TYPES
from app.llm import call_gemini
from app.models import PageClassification, SegregatorResult
from app.pdf_utils import get_total_pages, pdf_page_to_base64_image

logger = logging.getLogger(__name__)

# ── Prompt ────────────────────────────────────────────────────────────────

_SEGREGATOR_PROMPT_TEMPLATE = """You are an expert medical-claim document classifier.

You are given an image of **page {page_number}** (of {total_pages} total) from an
insurance claim PDF.

Analyse the visual content and classify this page into EXACTLY ONE of the
following document types:

{doc_types_list}

Rules:
1. Pick the single best-matching type.
2. If the page doesn't clearly fit any category, use "other".
3. Return ONLY valid JSON — no markdown fences, no extra text.

Return your answer as a JSON object with these fields:
{{
  "page_number": {page_number},
  "document_type": "<one of the types above>",
  "confidence": <float between 0.0 and 1.0>,
  "reasoning": "<one sentence explaining your choice>"
}}
"""


def _build_prompt(page_number: int, total_pages: int) -> str:
    doc_types_formatted = "\n".join(f"  - {dt}" for dt in DOCUMENT_TYPES)
    return _SEGREGATOR_PROMPT_TEMPLATE.format(
        page_number=page_number,
        total_pages=total_pages,
        doc_types_list=doc_types_formatted,
    )


# ── Agent Logic ───────────────────────────────────────────────────────────

def classify_page(pdf_path: str, page_number: int, total_pages: int) -> PageClassification:
    """Classify a single page using Gemini vision."""
    img_b64 = pdf_page_to_base64_image(pdf_path, page_number)
    prompt = _build_prompt(page_number, total_pages)

    result = call_gemini(prompt=prompt, images_b64=[img_b64], response_json=True)

    if isinstance(result, dict):
        doc_type = result.get("document_type", "other")
        # Validate against known types
        if doc_type not in DOCUMENT_TYPES:
            logger.warning(
                "Gemini returned unknown type '%s' for page %d — falling back to 'other'",
                doc_type, page_number,
            )
            doc_type = "other"
        return PageClassification(
            page_number=page_number,
            document_type=doc_type,
            confidence=float(result.get("confidence", 0.5)),
        )

    # Fallback when JSON parsing failed
    logger.warning("Non-JSON response for page %d — classifying as 'other'", page_number)
    return PageClassification(
        page_number=page_number,
        document_type="other",
        confidence=0.0,
    )


def run_segregator(pdf_path: str) -> SegregatorResult:
    """
    Run the Segregator Agent across all pages of a PDF.

    Returns a ``SegregatorResult`` with per-page classifications and
    a convenience ``page_groups`` dict mapping document_type → [page_numbers].
    """
    total_pages = get_total_pages(pdf_path)
    logger.info("Segregator: processing %d pages from %s", total_pages, pdf_path)

    classifications: list[PageClassification] = []
    for pn in range(1, total_pages + 1):
        try:
            cls = classify_page(pdf_path, pn, total_pages)
            classifications.append(cls)
            logger.info("  Page %d → %s (%.2f)", pn, cls.document_type, cls.confidence)
        except Exception as exc:
            logger.error("  Page %d classification failed: %s", pn, exc)
            classifications.append(
                PageClassification(page_number=pn, document_type="other", confidence=0.0)
            )

    # Build page_groups
    page_groups: dict[str, list[int]] = {}
    for cls in classifications:
        page_groups.setdefault(cls.document_type, []).append(cls.page_number)

    return SegregatorResult(classifications=classifications, page_groups=page_groups)
