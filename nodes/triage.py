from state import SupportState


def triage_node(state: SupportState) -> SupportState:
    """
    Classify the incoming support request.

    This first version intentionally uses deterministic
    rules so that routing is predictable and auditable.
    """

    question = state["question"].lower()

    logs = state.get("logs", [])

    logs.append("triage_node")

    # --------------------------------------------------
    # Out-of-scope detection
    # --------------------------------------------------

    out_of_scope_terms = [
        "refund",
        "refund my",
        "cancel my subscription",
        "billing",
        "charge my card",
        "payment",
        "subscription",
    ]

    if any(term in question for term in out_of_scope_terms):

        return {
            **state,
            "classification": "out_of_scope",
            "requires_human": False,
            "confidence": 0.95,
            "reason": "The request concerns billing, cancelations, or refunds, which are outside the supplied knowledge base.",
            "logs": logs,
        }

    # --------------------------------------------------
    # Escalation detection
    # --------------------------------------------------

    escalation_terms = [
        "render_failed",
        "render failure",
        "already tried everything",
        "documented checks failed",
        "escalate",
    ]

    if any(term in question for term in escalation_terms):

        return {
            **state,
            "classification": "escalation",
            "requires_human": True,
            "confidence": 0.90,
            "reason": "The request indicates a documented failure scenario that may require escalation.",
            "logs": logs,
        }

    # --------------------------------------------------
    # Clarification detection
    # --------------------------------------------------

    clarification_terms = [
        "not working",
        "isn't working",
        "doesn't work",
        "broken",
        "failed",
        "stopped",
        "error",
        "wrong",
        "something is wrong",
        "problem",
        "issue",
    ]

    # Questions with vague failure descriptions need
    # additional context unless they contain strong
    # domain-specific information.

    specific_terms = [
        "timezone",
        "scheduled export",
        "api credential",
        "api credentials",
        "connection",
        "refresh",
        "destination",
        "run history",
        "render_failed",
        "viewer",
        "read-only",
        "audit",
    ]

    has_specific_context = any(
        term in question
        for term in specific_terms
    )

    has_vague_failure = any(
        term in question
        for term in clarification_terms
    )

    if has_vague_failure and not has_specific_context:

        return {
            **state,
            "classification": "clarification",
            "requires_human": False,
            "confidence": 0.90,
            "reason": "The request describes a problem but does not provide enough context to identify the relevant support procedure.",
            "logs": logs,
        }

    # --------------------------------------------------
    # Default
    # --------------------------------------------------

    return {
        **state,
        "classification": "answerable",
        "requires_human": False,
        "confidence": 0.70,
        "reason": "The request appears related to the supplied OrbitDesk support knowledge base.",
        "logs": logs,
    }