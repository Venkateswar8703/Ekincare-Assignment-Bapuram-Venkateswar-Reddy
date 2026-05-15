"""
Discharge Summary Agent — extracts clinical summary data.

Processes only the pages classified as ``discharge_summary``.
"""

from __future__ import annotations

import logging
from typing import Any

from app.llm import call_gemini
from app.models import DischargeSummaryInfo
from app.pdf_utils import pdf_pages_to_base64_images

logger = logging.getLogger(__name__)

_DISCHARGE_PROMPT = """You are an expert medical document data-extraction agent.

You are given images of pages from an insurance claim document that contain a
hospital discharge summary.

Extract ALL available clinical and administrative information. Return ONLY a
JSON object with the following fields (use null for any field not found):

{{
  "patient_name": "<full name>",
  "admission_date": "<YYYY-MM-DD or as written>",
  "discharge_date": "<YYYY-MM-DD or as written>",
  "hospital_name": "<name of hospital>",
  "primary_diagnosis": "<main diagnosis>",
  "secondary_diagnosis": "<secondary diagnosis if any>",
  "treating_physician": "<doctor name>",
  "procedures_performed": ["<procedure 1>", "<procedure 2>"],
  "medications_prescribed": ["<medication 1>", "<medication 2>"],
  "follow_up_instructions": "<follow-up details>",
  "additional_info": {{ "<key>": "<value>" }}
}}

Important:
- Be thorough — capture every clinical detail visible.
- Return ONLY valid JSON — no markdown fences, no commentary.
"""


def run_discharge_agent(pdf_path: str, page_numbers: list[int]) -> DischargeSummaryInfo:
    """
    Extract discharge summary information from the specified pages.

    Parameters
    ----------
    pdf_path : str
        Path to the claim PDF.
    page_numbers : list[int]
        1-indexed pages assigned by the Segregator.

    Returns
    -------
    DischargeSummaryInfo
    """
    if not page_numbers:
        logger.info("Discharge Summary Agent: no pages assigned — returning empty result.")
        return DischargeSummaryInfo()

    logger.info("Discharge Summary Agent: processing pages %s", page_numbers)

    images = pdf_pages_to_base64_images(pdf_path, page_numbers)
    images_b64 = [images[pn] for pn in sorted(images)]

    page_list = ", ".join(str(p) for p in page_numbers)
    prompt = (
        f"The following {len(images_b64)} image(s) are pages [{page_list}] "
        f"from a medical insurance claim PDF.\n\n{_DISCHARGE_PROMPT}"
    )

    result = call_gemini(prompt=prompt, images_b64=images_b64, response_json=True)

    if isinstance(result, dict):
        return DischargeSummaryInfo(
            **{k: v for k, v in result.items() if k in DischargeSummaryInfo.model_fields}
        )

    logger.warning("Discharge Summary Agent: could not parse LLM response — returning empty result.")
    return DischargeSummaryInfo()
