"""
LangGraph Workflow — Claim Processing Pipeline.

Defines the graph:

    START → segregator_node → [id_node, discharge_node, bill_node] → aggregator_node → END

The three extraction agents run in parallel after the segregator
routes pages to them.
"""

from __future__ import annotations

import logging
from typing import Any, TypedDict

from langgraph.graph import StateGraph, START, END

from app.agents.segregator import run_segregator
from app.agents.id_agent import run_id_agent
from app.agents.discharge_agent import run_discharge_agent
from app.agents.bill_agent import run_bill_agent

logger = logging.getLogger(__name__)


# ── State schema for LangGraph ────────────────────────────────────────────
# Using TypedDict instead of Pydantic for LangGraph state compatibility.

class GraphState(TypedDict, total=False):
    claim_id: str
    pdf_path: str

    # Segregator output
    segregator_result: dict[str, Any]

    # Extraction outputs
    identity_info: dict[str, Any]
    discharge_summary_info: dict[str, Any]
    itemized_bill_info: dict[str, Any]

    # Final
    aggregated_result: dict[str, Any]
    errors: list[str]


# ── Node Functions ────────────────────────────────────────────────────────

def segregator_node(state: GraphState) -> dict[str, Any]:
    """Classify every page of the PDF into document types."""
    logger.info("═══ Segregator Node ═══")
    pdf_path = state["pdf_path"]

    try:
        result = run_segregator(pdf_path)
        return {"segregator_result": result.model_dump()}
    except Exception as exc:
        logger.error("Segregator failed: %s", exc)
        errors = state.get("errors", [])
        errors.append(f"Segregator error: {str(exc)}")
        return {
            "segregator_result": {"classifications": [], "page_groups": {}},
            "errors": errors,
        }


def id_node(state: GraphState) -> dict[str, Any]:
    """Extract identity information from relevant pages."""
    logger.info("═══ ID Agent Node ═══")
    pdf_path = state["pdf_path"]
    seg = state.get("segregator_result", {})
    page_groups = seg.get("page_groups", {})

    # Collect pages for ID agent: identity_document + claim_forms
    pages = page_groups.get("identity_document", []) + page_groups.get("claim_forms", [])

    try:
        result = run_id_agent(pdf_path, pages)
        return {"identity_info": result.model_dump()}
    except Exception as exc:
        logger.error("ID Agent failed: %s", exc)
        errors = state.get("errors", [])
        errors.append(f"ID Agent error: {str(exc)}")
        return {"identity_info": {}, "errors": errors}


def discharge_node(state: GraphState) -> dict[str, Any]:
    """Extract discharge summary information from relevant pages."""
    logger.info("═══ Discharge Summary Agent Node ═══")
    pdf_path = state["pdf_path"]
    seg = state.get("segregator_result", {})
    page_groups = seg.get("page_groups", {})

    pages = page_groups.get("discharge_summary", [])

    try:
        result = run_discharge_agent(pdf_path, pages)
        return {"discharge_summary_info": result.model_dump()}
    except Exception as exc:
        logger.error("Discharge Agent failed: %s", exc)
        errors = state.get("errors", [])
        errors.append(f"Discharge Agent error: {str(exc)}")
        return {"discharge_summary_info": {}, "errors": errors}


def bill_node(state: GraphState) -> dict[str, Any]:
    """Extract itemized bill information from relevant pages."""
    logger.info("═══ Itemized Bill Agent Node ═══")
    pdf_path = state["pdf_path"]
    seg = state.get("segregator_result", {})
    page_groups = seg.get("page_groups", {})

    pages = page_groups.get("itemized_bill", [])

    try:
        result = run_bill_agent(pdf_path, pages)
        return {"itemized_bill_info": result.model_dump()}
    except Exception as exc:
        logger.error("Bill Agent failed: %s", exc)
        errors = state.get("errors", [])
        errors.append(f"Bill Agent error: {str(exc)}")
        return {"itemized_bill_info": {}, "errors": errors}


def aggregator_node(state: GraphState) -> dict[str, Any]:
    """Combine all extraction results into a final output."""
    logger.info("═══ Aggregator Node ═══")

    seg = state.get("segregator_result", {})
    identity = state.get("identity_info", {})
    discharge = state.get("discharge_summary_info", {})
    bill = state.get("itemized_bill_info", {})

    aggregated = {
        "claim_id": state.get("claim_id", ""),
        "segregation_summary": {
            "total_pages": len(seg.get("classifications", [])),
            "page_groups": seg.get("page_groups", {}),
            "classifications": seg.get("classifications", []),
        },
        "extracted_data": {
            "identity_information": identity,
            "discharge_summary": discharge,
            "itemized_bill": bill,
        },
    }

    return {"aggregated_result": aggregated}


# ── Build the Graph ───────────────────────────────────────────────────────

def build_graph() -> StateGraph:
    """
    Construct and compile the LangGraph workflow.

    Flow:
        START → segregator → [id, discharge, bill] (parallel) → aggregator → END
    """
    graph = StateGraph(GraphState)

    # Add nodes
    graph.add_node("segregator", segregator_node)
    graph.add_node("id_agent", id_node)
    graph.add_node("discharge_agent", discharge_node)
    graph.add_node("bill_agent", bill_node)
    graph.add_node("aggregator", aggregator_node)

    # Edges: START → segregator
    graph.add_edge(START, "segregator")

    # Segregator fans out to all three extraction agents
    graph.add_edge("segregator", "id_agent")
    graph.add_edge("segregator", "discharge_agent")
    graph.add_edge("segregator", "bill_agent")

    # All three extraction agents converge at the aggregator
    graph.add_edge("id_agent", "aggregator")
    graph.add_edge("discharge_agent", "aggregator")
    graph.add_edge("bill_agent", "aggregator")

    # Aggregator → END
    graph.add_edge("aggregator", END)

    return graph.compile()


# Module-level compiled graph (singleton)
claim_pipeline = build_graph()
