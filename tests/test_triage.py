from nodes.triage import triage_node


def test_triage():
    test_cases = [
        (
            "My scheduled exports stopped after I changed my workspace timezone. What should I check?",
            "answerable",
        ),
        (
            "My export isn't working.",
            "clarification",
        ),
        (
            "Something is wrong with my dashboard.",
            "clarification",
        ),
        (
            "The export failed.",
            "clarification",
        ),
        (
            "Write a refund for my subscription.",
            "out_of_scope",
        ),
        (
            "Can you cancel my subscription?",
            "out_of_scope",
        ),
        (
            "Two consecutive runs show render_failed and all documented checks have already failed.",
            "escalation",
        ),
    ]

    for question, expected_classification in test_cases:
        state = {
            "question": question,
            "logs": [],
        }

        result = triage_node(state)

        assert result["classification"] == expected_classification
        assert "triage_node" in result["logs"]