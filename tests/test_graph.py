import sys
from pathlib import Path

sys.path.append(
    str(Path(__file__).resolve().parent.parent)
)

from graph import graph


def run_test(question):

    print("\n")
    print("=" * 70)
    print("QUESTION")
    print(question)

    result = graph.invoke(
        {
            "question": question,
            "logs": [],
        }
    )

    print("\nCLASSIFICATION")
    print(result["classification"])

    print("\nANSWER")
    print(result.get("answer", ""))

    print("\nLOGS")
    for log in result["logs"]:
        print(" ->", log)

    return result


def test_graph_flows():
    # Answerable
    result = run_test(
        "My scheduled exports stopped after I changed "
        "my workspace timezone. What should I check?"
    )

    assert result["classification"] == "answerable"
    assert "triage_node" in result["logs"]
    assert "retrieval_node" in result["logs"]
    assert len(result["retrieved_documents"]) > 0

    documents = [
        item["document"]
        for item in result["retrieved_documents"]
    ]

    print("\nRetrieved documents:")
    for document in documents:
        print(" -", document)

    # Clarification
    result = run_test(
        "My export isn't working."
    )

    assert result["classification"] == "clarification"
    assert "clarification_node" in result["logs"]
    assert "retrieval_node" not in result["logs"]

    # Out of scope
    result = run_test(
        "Write a refund for my subscription."
    )

    assert result["classification"] == "out_of_scope"
    assert "out_of_scope_node" in result["logs"]
    assert "retrieval_node" not in result["logs"]

    # Escalation
    result = run_test(
        "Two consecutive runs show render_failed "
        "and all documented checks have already failed."
    )

    assert result["classification"] == "escalation"
    assert "escalation_node" in result["logs"]
    assert "retrieval_node" not in result["logs"]

    print("\n")
    print("=" * 70)
    print("ALL GRAPH TESTS PASSED")
    print("=" * 70)