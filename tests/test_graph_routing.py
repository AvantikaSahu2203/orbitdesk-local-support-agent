from nodes.triage import triage_node
from graph import route_after_triage


def test_graph_routing():
    test_cases = [
        (
            "My scheduled exports stopped after I changed my workspace timezone. What should I check?",
            "answerable",
            "retrieval",
        ),
        (
            "My export isn't working.",
            "clarification",
            "clarification",
        ),
        (
            "Write a refund for my subscription.",
            "out_of_scope",
            "out_of_scope",
        ),
        (
            "Two consecutive runs show render_failed and all documented checks have already failed.",
            "escalation",
            "escalation",
        ),
    ]

    for question, expected_classification, expected_route in test_cases:
        state = triage_node(
            {
                "question": question,
                "logs": [],
            }
        )

        assert state["classification"] == expected_classification

        route = route_after_triage(state)

        assert route == expected_route