"""
ID Agent — extracts identity & policy information.

Processes only the pages classified as ``identity_document`` (and optionally
``claim_forms`` which often contain patient/policy details).
"""

from __future__ import annotations

import logging
from typing import Any

from app.llm import call_gemini
from app.models import IdentityInfo
from app.pdf_utils import pdf_pages_to_base64_images

logger = logging.getLogger(__name__)

_ID_PROMPT = """You are an expert medical document data-extraction agent.

You are given images of pages from an insurance claim document that contain
identity-related information (ID cards, claim forms, policy documents, etc.).

Extract ALL available identity and policy information. Return ONLY a JSON
object with the following fields (use null for any field not found):

{{
  "patient_name": "<full name>",
  "date_of_birth": "<YYYY-MM-DD or as written>",
  "gender": "<Male/Female/Other>",
  "id_type": "<type of ID document, e.g. Aadhaar, PAN, Passport>",
  "id_number": "<ID document number>",
  "policy_number": "<insurance policy number>",
  "insurer_name": "<name of insurance company>",
  "address": "<full address>",
  "contact_number": "<phone number>",
  "additional_info": {{ "<key>": "<value>" }}
}}

Important:
- Extract every piece of information visible in the documents.
- If multiple IDs are present, pick the primary / most complete one and
  put the rest in additional_info.
- Return ONLY valid JSON — no markdown fences, no commentary.
"""


def run_id_agent(pdf_path: str, page_numbers: list[int]) -> IdentityInfo:
    """
    Extract identity information from the specified pages.

    Parameters
    ----------
    pdf_path : str
        Path to the claim PDF.
    page_numbers : list[int]
        1-indexed pages assigned by the Segregator.

    Returns
    -------
    IdentityInfo
    """
    if not page_numbers:
        logger.info("ID Agent: no pages assigned — returning empty result.")
        return IdentityInfo()

    logger.info("ID Agent: processing pages %s", page_numbers)

    images = pdf_pages_to_base64_images(pdf_path, page_numbers)
    images_b64 = [images[pn] for pn in sorted(images)]

    page_list = ", ".join(str(p) for p in page_numbers)
    prompt = (
        f"The following {len(images_b64)} image(s) are pages [{page_list}] "
        f"from a medical insurance claim PDF.\n\n{_ID_PROMPT}"
    )

    result = call_gemini(prompt=prompt, images_b64=images_b64, response_json=True)

    if isinstance(result, dict):
        return IdentityInfo(**{k: v for k, v in result.items() if k in IdentityInfo.model_fields})

    logger.warning("ID Agent: could not parse LLM response — returning empty result.")
    return IdentityInfo()
