"""
Test script — sends the test PDF to the /api/process endpoint
and prints the structured JSON response.

Usage:
    1. Start the server:  uvicorn app.main:app --port 8000
    2. Run this script:   python test_api.py
"""

import requests
import json
import sys


def test_process_endpoint(
    base_url: str = "http://localhost:8000",
    pdf_path: str = "test_claim.pdf",
    claim_id: str = "CLM-2024-789456",
):
    url = f"{base_url}/api/process"

    print(f"Sending POST {url}")
    print(f"  claim_id : {claim_id}")
    print(f"  file     : {pdf_path}")
    print()

    with open(pdf_path, "rb") as f:
        resp = requests.post(
            url,
            data={"claim_id": claim_id},
            files={"file": (pdf_path, f, "application/pdf")},
            timeout=300,
        )

    print(f"Status: {resp.status_code}")
    print()

    if resp.status_code == 200:
        data = resp.json()
        print(json.dumps(data, indent=2, default=str))
    else:
        print(f"Error: {resp.text}")

    return resp


if __name__ == "__main__":
    pdf = sys.argv[1] if len(sys.argv) > 1 else "test_claim.pdf"
    test_process_endpoint(pdf_path=pdf)
