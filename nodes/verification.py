import re
from typing import Dict, Any, List


REQUIRED_CLASSIFICATIONS = {
    "answerable",
    "clarification",
    "escalation",
    "out_of_scope",
}


def _contains_source_reference(answer: str) -> bool:
    """
    Check whether the answer contains a recognizable
    source/document reference.
    """

    if not answer:
        return False

    source_markers = [
        ".md",
        "KB-",
        "CASE-",
        "Source:",
        "Sources:",
        "References:",
    ]

    answer_lower = answer.lower()

    return any(
        marker.lower() in answer_lower
        for marker in source_markers
    )


def _referenced_documents_are_retrieved(
    answer: str,
    retrieved_documents: List[Dict[str, Any]],
) -> bool:
    """
    Verify that ALL explicit document/source references
    in the answer correspond to retrieved evidence.

    This is intentionally deterministic.
    """

    if not retrieved_documents:
        return False

    retrieved_names = {
        document.get("document", "").strip().lower()
        for document in retrieved_documents
        if document.get("document")
    }

    # Extract all document-like references from the answer:
    # 1. Any word ending in .md (e.g. 04_scheduled_exports.md)
    # 2. Any case ID starting with CASE- or KB- (e.g. CASE-1041, KB-1002)
    referenced_docs = set(re.findall(r'\b[\w-]+\.md\b|\bcase-\w+\b|\bkb-\w+\b', answer, re.IGNORECASE))

    # If no explicit references are found, check if at least one retrieved document name is in the answer
    if not referenced_docs:
        for name in retrieved_names:
            if name in answer.lower():
                return True
        return False

    # Check if ALL extracted references are in retrieved_names
    for name in referenced_docs:
        if name.lower() not in retrieved_names:
            return False

    return True


def _evidence_text(
    retrieved_documents: List[Dict[str, Any]],
) -> str:
    """
    Combine retrieved evidence into one lowercase string.
    """

    parts = []

    for document in retrieved_documents:
        source = document.get(
            "document",
            "",
        )

        content = document.get(
            "content",
            "",
        )

        parts.append(
            str(source)
        )

        parts.append(
            str(content)
        )

    return "\n".join(parts).lower()


def _answer_contains_unsupported_source(
    answer: str,
    retrieved_documents: List[Dict[str, Any]],
) -> bool:
    """
    Detect if the answer mentions a specific document name or case ID
    that is not present in the retrieved evidence.
    """

    retrieved_names = {
        document.get("document", "").strip().lower()
        for document in retrieved_documents
        if document.get("document")
    }

    referenced_docs = set(re.findall(r'\b[\w-]+\.md\b|\bcase-\w+\b|\bkb-\w+\b', answer, re.IGNORECASE))

    for name in referenced_docs:
        if name.lower() not in retrieved_names:
            return True

    return False


def verify_answer(
    state: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Deterministic verification node.

    Checks:

    1. Valid classification
    2. Generated answer exists
    3. Retrieved evidence exists for answerable requests
    4. Source references exist
    5. Source references come from retrieved evidence
    6. Grounding-related validation checks (no unsupported lists/actions)
    7. Revision limit is respected
    """

    classification = state.get(
        "classification"
    )

    answer = state.get(
        "answer",
        "",
    )

    retrieved_documents = state.get(
        "retrieved_documents",
        [],
    )

    revision_count = state.get(
        "revision_count",
        0,
    )

    failures = []

    # ---------------------------------------------------------
    # 1. Classification validation
    # ---------------------------------------------------------

    if classification not in REQUIRED_CLASSIFICATIONS:
        failures.append(
            "Invalid classification."
        )

    # ---------------------------------------------------------
    # 2. Answer validation
    # ---------------------------------------------------------

    if not answer or not answer.strip():
        failures.append(
            "Generated answer is empty."
        )

    # ---------------------------------------------------------
    # 3. Evidence validation
    # ---------------------------------------------------------

    if classification == "answerable":

        if not retrieved_documents:
            failures.append(
                "No retrieved evidence is available."
            )

    # ---------------------------------------------------------
    # 4. Source validation
    # ---------------------------------------------------------

    if classification == "answerable":

        if not _contains_source_reference(
            answer
        ):
            failures.append(
                "Answer does not contain a source reference."
            )

    # ---------------------------------------------------------
    # 5. Source provenance validation
    # ---------------------------------------------------------

    if classification == "answerable":

        if retrieved_documents:

            if not _referenced_documents_are_retrieved(
                answer,
                retrieved_documents,
            ):
                failures.append(
                    "Answer does not reference a retrieved source document."
                )

            if _answer_contains_unsupported_source(
                answer,
                retrieved_documents,
            ):
                failures.append(
                    "Answer appears to reference a source that was not retrieved."
                )

    # ---------------------------------------------------------
    # 6. Grounding-related validation checks
    # ---------------------------------------------------------

    if classification == "answerable" and answer:
        evidence_lower = _evidence_text(retrieved_documents)
        answer_lower = answer.lower()

        # Grounding check for instructions or phrases that must be explicitly present in retrieved evidence
        forbidden_unsupported = [
            "contact IT",
            "contact support",
            "contact your administrator",
            "contact an administrator",
            "try again",
            "run another export",
            "resubmit the export",
            "try rescheduling",
        ]

        for term in forbidden_unsupported:
            if term.lower() in answer_lower:
                if term.lower() not in evidence_lower:
                    failures.append(
                        f"Answer recommends unsupported instruction: '{term}'."
                    )

        # Check for UI elements or terms in quotes/brackets/backticks
        ui_elements = re.findall(r'["\'\[`]([^"\'\]`]+)["\'\]`]', answer)
        for element in ui_elements:
            elem_clean = element.strip()
            # Ignore empty/short, source names, numbers, or general small words
            if (
                len(elem_clean) > 2
                and not elem_clean.lower().endswith('.md')
                and not elem_clean.lower().startswith('case-')
                and not elem_clean.lower().startswith('kb-')
            ):
                if elem_clean.lower() not in evidence_lower:
                    failures.append(
                        f"Answer references unsupported UI element or term: '{elem_clean}'."
                    )

    # ---------------------------------------------------------
    # 7. Revision limit
    # ---------------------------------------------------------

    MAX_REVISIONS = 1

    if revision_count > MAX_REVISIONS:
        failures.append(
            "Maximum revision limit exceeded."
        )

    # ---------------------------------------------------------
    # Final result
    # ---------------------------------------------------------

    passed = len(failures) == 0

    if passed:
        reason = (
            "Answer passed deterministic verification: "
            "required fields, evidence and source checks passed."
        )
    else:
        reason = " ".join(failures)

    return {
        "verification_passed": passed,
        "verification_reason": reason,
    }