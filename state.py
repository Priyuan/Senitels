from dataclasses import dataclass
from typing import TypedDict, List, Optional

@dataclass
class VerificationReport:
    """Structured report from Agent Alpha (Investigator)."""
    claim: str
    verdict: str   # TRUE / FALSE / INSUFFICIENT_EVIDENCE
    confidence: float
    evidence_summary: str
    sources: List[str]

class GraphState(TypedDict):
    """State passed between agents in the LangGraph workflow."""
    original_claim: str
    verification_report: Optional[VerificationReport]
    db_action: str   # INSERT / FLAG / DISCARD
    human_review_needed: bool
    error_message: Optional[str]