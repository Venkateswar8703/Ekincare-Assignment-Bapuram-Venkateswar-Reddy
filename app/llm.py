"""
LLM Helper — thin wrapper around Google Generative AI (Gemini) via
langchain-google-genai.

Provides a single ``call_gemini`` function used by every agent.
"""

from __future__ import annotations

import json
import logging
import re
from typing import Any, Optional

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage

from app.config import GOOGLE_API_KEY, GEMINI_MODEL

logger = logging.getLogger(__name__)


def _get_model(temperature: float = 0.1) -> ChatGoogleGenerativeAI:
    """Instantiate the Gemini chat model."""
    return ChatGoogleGenerativeAI(
        model=GEMINI_MODEL,
        google_api_key=GOOGLE_API_KEY,
        temperature=temperature,
    )


def call_gemini(
    prompt: str,
    images_b64: Optional[list[str]] = None,
    response_json: bool = True,
    temperature: float = 0.1,
) -> dict[str, Any] | str:
    """
    Call Gemini with an optional set of base64 images.

    Parameters
    ----------
    prompt : str
        The text prompt (system + user combined).
    images_b64 : list[str] | None
        Base64-encoded PNG images to include as inline data.
    response_json : bool
        If True, attempt to parse the response as JSON.
    temperature : float
        Sampling temperature.

    Returns
    -------
    dict | str
        Parsed JSON dict, or raw text if ``response_json`` is False
        or parsing fails.
    """
    model = _get_model(temperature=temperature)

    # Build multimodal content parts
    content: list[dict[str, Any] | str] = []

    # Attach images first so the model "sees" them before the prompt
    if images_b64:
        for img_b64 in images_b64:
            content.append({
                "type": "image_url",
                "image_url": {"url": f"data:image/png;base64,{img_b64}"},
            })

    content.append({"type": "text", "text": prompt})

    message = HumanMessage(content=content)
    response = model.invoke([message])

    text = response.content.strip()

    if response_json:
        try:
            # Gemini sometimes wraps JSON in markdown code fences
            cleaned = _strip_code_fences(text)
            return json.loads(cleaned)
        except json.JSONDecodeError:
            logger.warning("Failed to parse Gemini response as JSON, returning raw text.")
            return text

    return text


def _strip_code_fences(text: str) -> str:
    """Remove markdown code fences (```json ... ```) if present."""
    pattern = r"```(?:json)?\s*\n?(.*?)\n?\s*```"
    match = re.search(pattern, text, re.DOTALL)
    if match:
        return match.group(1).strip()
    return text
