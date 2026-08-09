from typing import TypedDict, Literal, List, Dict, Any


Classification = Literal[
    "answerable",
    "clarification",
    "escalation",
    "out_of_scope",
]


class SupportState(TypedDict, total=False):

    # Original user request
    question: str

    # Triage result
    classification: Classification

    # Retrieved evidence
    retrieved_documents: List[Dict[str, Any]]

    # Generated answer
    # Generated answer
    answer: str
    # Generation performance
    generation_latency: float
    model_load_time: float

    # Local model information
    generation_latency: float
    model_name: str

    # Verification information
    verification_passed: bool
    verification_reason: str

    # Number of generation/revision attempts
    revision_count: int

    # Final output
    confidence: float
    requires_human: bool
    reason: str

    # Execution trace
    logs: List[str]