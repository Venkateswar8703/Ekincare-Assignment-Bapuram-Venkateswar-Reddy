"""
Itemized Bill Agent — extracts billing line items and totals.

Processes only the pages classified as ``itemized_bill``.
"""

from __future__ import annotations

import logging
from typing import Any

from app.llm import call_gemini
from app.models import BillLineItem, ItemizedBillInfo
from app.pdf_utils import pdf_pages_to_base64_images

logger = logging.getLogger(__name__)

_BILL_PROMPT = """You are an expert medical document data-extraction agent.

You are given images of pages from an insurance claim document that contain an
itemized hospital / medical bill.

Extract ALL line items and billing information. Return ONLY a JSON object with
the following fields (use null for any field not found):

{{
  "hospital_name": "<name of hospital or provider>",
  "bill_number": "<bill / invoice number>",
  "bill_date": "<YYYY-MM-DD or as written>",
  "patient_name": "<patient name on the bill>",
  "items": [
    {{
      "description": "<service or item description>",
      "quantity": <number or null>,
      "unit_price": <number or null>,
      "amount": <number>
    }}
  ],
  "subtotal": <number or null>,
  "tax": <number or null>,
  "discount": <number or null>,
  "total_amount": <number or null>,
  "additional_info": {{ "<key>": "<value>" }}
}}

Important:
- Capture EVERY line item visible in the bill.
- Calculate or verify the total_amount by summing item amounts if possible.
- All monetary values should be numbers (not strings).
- Return ONLY valid JSON — no markdown fences, no commentary.
"""


def run_bill_agent(pdf_path: str, page_numbers: list[int]) -> ItemizedBillInfo:
    """
    Extract itemized bill information from the specified pages.

    Parameters
    ----------
    pdf_path : str
        Path to the claim PDF.
    page_numbers : list[int]
        1-indexed pages assigned by the Segregator.

    Returns
    -------
    ItemizedBillInfo
    """
    if not page_numbers:
        logger.info("Itemized Bill Agent: no pages assigned — returning empty result.")
        return ItemizedBillInfo()

    logger.info("Itemized Bill Agent: processing pages %s", page_numbers)

    images = pdf_pages_to_base64_images(pdf_path, page_numbers)
    images_b64 = [images[pn] for pn in sorted(images)]

    page_list = ", ".join(str(p) for p in page_numbers)
    prompt = (
        f"The following {len(images_b64)} image(s) are pages [{page_list}] "
        f"from a medical insurance claim PDF.\n\n{_BILL_PROMPT}"
    )

    result = call_gemini(prompt=prompt, images_b64=images_b64, response_json=True)

    if isinstance(result, dict):
        # Parse line items
        raw_items = result.pop("items", [])
        items = []
        for item in raw_items:
            try:
                items.append(BillLineItem(**item))
            except Exception:
                logger.warning("Skipping malformed bill line item: %s", item)

        # Calculate total if not provided
        info = ItemizedBillInfo(
            **{k: v for k, v in result.items() if k in ItemizedBillInfo.model_fields},
            items=items,
        )

        if info.total_amount is None and items:
            info.total_amount = sum(item.amount for item in items)
            logger.info("Calculated total_amount from line items: %.2f", info.total_amount)

        return info

    logger.warning("Itemized Bill Agent: could not parse LLM response — returning empty result.")
    return ItemizedBillInfo()
