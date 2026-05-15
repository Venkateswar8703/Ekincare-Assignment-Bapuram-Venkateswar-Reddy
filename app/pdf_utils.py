"""
PDF Utilities — page-level image extraction via PyMuPDF.

Converts individual PDF pages into base64-encoded PNG images so they
can be sent to the Gemini vision model for analysis.
"""

from __future__ import annotations

import base64
import io
from typing import Optional

import fitz  # PyMuPDF
from PIL import Image


def get_total_pages(pdf_path: str) -> int:
    """Return the total number of pages in a PDF."""
    doc = fitz.open(pdf_path)
    count = doc.page_count
    doc.close()
    return count


def pdf_page_to_base64_image(
    pdf_path: str,
    page_number: int,  # 1-indexed
    dpi: int = 200,
) -> str:
    """
    Render a single PDF page to a base64-encoded PNG string.

    Parameters
    ----------
    pdf_path : str
        Path to the PDF file on disk.
    page_number : int
        1-indexed page number.
    dpi : int
        Resolution for rendering.  200 is a good trade-off between
        quality and token cost when sending to a vision LLM.

    Returns
    -------
    str
        Base64-encoded PNG image.
    """
    doc = fitz.open(pdf_path)
    page = doc.load_page(page_number - 1)  # fitz is 0-indexed
    zoom = dpi / 72
    mat = fitz.Matrix(zoom, zoom)
    pix = page.get_pixmap(matrix=mat)

    img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)

    b64 = base64.b64encode(buf.read()).decode("utf-8")
    doc.close()
    return b64


def pdf_pages_to_base64_images(
    pdf_path: str,
    page_numbers: Optional[list[int]] = None,
    dpi: int = 200,
) -> dict[int, str]:
    """
    Convert multiple PDF pages to base64 images.

    Parameters
    ----------
    pdf_path : str
        Path to the PDF.
    page_numbers : list[int] | None
        1-indexed page numbers. ``None`` means *all* pages.
    dpi : int
        Rendering resolution.

    Returns
    -------
    dict[int, str]
        Mapping of page_number → base64 PNG string.
    """
    if page_numbers is None:
        total = get_total_pages(pdf_path)
        page_numbers = list(range(1, total + 1))

    return {pn: pdf_page_to_base64_image(pdf_path, pn, dpi) for pn in page_numbers}
