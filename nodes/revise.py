def revision_node(state):
    """
    Prepare the state for one controlled regeneration attempt.
    """

    logs = list(state.get("logs", []))
    logs.append("revision_node")

    revision_count = state.get(
        "revision_count",
        0,
    )

    revision_count += 1

    verification_reason = state.get(
        "verification_reason",
        "",
    )

    revision_instruction = f"""
The previous answer failed deterministic verification.

Verification result:
{verification_reason}

Regenerate the answer.

IMPORTANT:
- Remove unsupported claims.
- Remove unsupported troubleshooting steps.
- Use only facts explicitly stated in the retrieved evidence.
- Preserve documented numbered procedures when present.
- Mention the exact retrieved source document names.
- Do not invent buttons, menus, settings, procedures, policies,
  recommendations, or escalation instructions.
- If the evidence is insufficient, say exactly:

The available documentation is insufficient to determine the next step.
"""

    return {
        **state,
        "revision_count": revision_count,
        "revision_instruction": revision_instruction,
        "logs": logs,
    }