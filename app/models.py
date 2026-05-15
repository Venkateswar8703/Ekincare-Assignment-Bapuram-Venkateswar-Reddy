"""
Claim Processing Pipeline - Pydantic Models.

Defines the data schemas flowing through the LangGraph pipeline and
the API response shape.
"""

from __future__ import annotations

from typing import Any, Optional
from pydantic import BaseModel, Field


# ── Segregator Output ─────────────────────────────────────────────────────

class PageClassification(BaseModel):
    """Classification result for a single PDF page."""
    page_number: int = Field(..., description="1-indexed page number")
    document_type: str = Field(..., description="One of the 9 document types")
    confidence: float = Field(0.0, ge=0.0, le=1.0, description="Confidence score")


class SegregatorResult(BaseModel):
    """Complete output from the Segregator Agent."""
    classifications: list[PageClassification] = Field(default_factory=list)
    page_groups: dict[str, list[int]] = Field(
        default_factory=dict,
        description="Mapping from document_type → list of page numbers",
    )


# ── Extraction Agent Outputs ─────────────────────────────────────────────

class IdentityInfo(BaseModel):
    """Data extracted by the ID Agent."""
    patient_name: Optional[str] = None
    date_of_birth: Optional[str] = None
    gender: Optional[str] = None
    id_type: Optional[str] = None
    id_number: Optional[str] = None
    policy_number: Optional[str] = None
    insurer_name: Optional[str] = None
    address: Optional[str] = None
    contact_number: Optional[str] = None
    additional_info: dict[str, Any] = Field(default_factory=dict)


class DischargeSummaryInfo(BaseModel):
    """Data extracted by the Discharge Summary Agent."""
    patient_name: Optional[str] = None
    admission_date: Optional[str] = None
    discharge_date: Optional[str] = None
    hospital_name: Optional[str] = None
    primary_diagnosis: Optional[str] = None
    secondary_diagnosis: Optional[str] = None
    treating_physician: Optional[str] = None
    procedures_performed: list[str] = Field(default_factory=list)
    medications_prescribed: list[str] = Field(default_factory=list)
    follow_up_instructions: Optional[str] = None
    additional_info: dict[str, Any] = Field(default_factory=dict)


class BillLineItem(BaseModel):
    """A single line item on an itemized bill."""
    description: str
    quantity: Optional[float] = None
    unit_price: Optional[float] = None
    amount: float


class ItemizedBillInfo(BaseModel):
    """Data extracted by the Itemized Bill Agent."""
    hospital_name: Optional[str] = None
    bill_number: Optional[str] = None
    bill_date: Optional[str] = None
    patient_name: Optional[str] = None
    items: list[BillLineItem] = Field(default_factory=list)
    subtotal: Optional[float] = None
    tax: Optional[float] = None
    discount: Optional[float] = None
    total_amount: Optional[float] = None
    additional_info: dict[str, Any] = Field(default_factory=dict)


# ── Pipeline State (LangGraph) ───────────────────────────────────────────

class PipelineState(BaseModel):
    """
    The shared state that flows through the LangGraph workflow.

    Every node reads and writes to this state object.
    """
    # Input
    claim_id: str = ""
    pdf_path: str = ""

    # Segregator
    segregator_result: Optional[SegregatorResult] = None

    # Extraction results
    identity_info: Optional[IdentityInfo] = None
    discharge_summary_info: Optional[DischargeSummaryInfo] = None
    itemized_bill_info: Optional[ItemizedBillInfo] = None

    # Aggregated output
    aggregated_result: dict[str, Any] = Field(default_factory=dict)

    # Errors encountered during processing
    errors: list[str] = Field(default_factory=list)


# ── API Response ──────────────────────────────────────────────────────────

class ProcessResponse(BaseModel):
    """Shape returned by POST /api/process."""
    claim_id: str
    status: str = "success"
    segregation: Optional[SegregatorResult] = None
    extracted_data: dict[str, Any] = Field(default_factory=dict)
    errors: list[str] = Field(default_factory=list)
