from rag.loader import load_all_documents
from rag.chunker import chunk_documents
from rag.embeddings import EmbeddingModel
from rag.retriever import Retriever
from typing import Literal

from langgraph.graph import StateGraph, START, END

from state import SupportState
from nodes.triage import triage_node


# ============================================================
# Initialize RAG components once
# ============================================================

print("Initializing local RAG system...")

documents = load_all_documents()

chunks = chunk_documents(documents)

embedding_model = EmbeddingModel()

embeddings = embedding_model.encode(
    [chunk["content"] for chunk in chunks]
)

retriever = Retriever(
    embedding_model=embedding_model,
    chunks=chunks,
    embeddings=embeddings,
)

print(
    f"RAG system ready: {len(chunks)} chunks indexed."
)


# ============================================================
# Routing
# ============================================================

def route_after_triage(
    state: SupportState,
) -> Literal[
    "retrieval",
    "clarification",
    "escalation",
    "out_of_scope",
]:

    classification = state["classification"]

    if classification == "answerable":
        return "retrieval"

    if classification == "clarification":
        return "clarification"

    if classification == "escalation":
        return "escalation"

    if classification == "out_of_scope":
        return "out_of_scope"

    raise ValueError(
        f"Unknown classification: {classification}"
    )


# ============================================================
# Terminal response nodes
# ============================================================

def clarification_node(state: SupportState) -> SupportState:

    logs = state.get("logs", [])
    logs.append("clarification_node")

    return {
        **state,
        "answer": (
            "I need a little more information before I can "
            "identify the correct troubleshooting procedure. "
            "Please provide the specific feature, what you "
            "expected to happen, what happened instead, and "
            "any visible error code or status."
        ),
        "requires_human": False,
        "reason": (
            "The request does not contain enough information "
            "to identify the relevant support procedure."
        ),
        "logs": logs,
    }


def escalation_node(state: SupportState) -> SupportState:

    logs = state.get("logs", [])
    logs.append("escalation_node")

    return {
        **state,
        "answer": (
            "This issue appears to require escalation after "
            "the documented troubleshooting checks have been "
            "exhausted. Please collect the relevant workspace "
            "ID, dashboard ID, schedule ID, run IDs, "
            "timestamps, and error information. Do not attach "
            "exported customer data or secrets."
        ),
        "requires_human": True,
        "reason": (
            "The request matches a documented escalation "
            "scenario."
        ),
        "logs": logs,
    }


def out_of_scope_node(state: SupportState) -> SupportState:

    logs = state.get("logs", [])
    logs.append("out_of_scope_node")

    return {
        **state,
        "answer": (
            "I can't provide a supported answer for this "
            "request because it is outside the supplied "
            "OrbitDesk knowledge base."
        ),
        "requires_human": False,
        "reason": (
            "The requested information is outside the "
            "provided product knowledge base."
        ),
        "logs": logs,
    }


# ============================================================
# Temporary retrieval node
# ============================================================

def retrieval_node(state: SupportState) -> SupportState:
    """
    Retrieve the most relevant evidence from the
    local knowledge base and resolved cases.
    """

    logs = state.get("logs", [])
    logs.append("retrieval_node")

    question = state["question"]

    print("\n[RETRIEVAL]")
    print(f"Query: {question}")

    results = retriever.retrieve(
        query=question,
        top_k=5,
    )

    print(f"Retrieved {len(results)} chunks.")

    for i, result in enumerate(results, start=1):

        print(
            f"\nResult {i}: "
            f"{result.get('document', 'unknown')} "
            f"(score={result.get('score', 0):.4f})"
        )

    return {
        **state,
        "retrieved_documents": results,
        "logs": logs,
    }


# ============================================================
# Build Graph
# ============================================================

def build_graph():

    workflow = StateGraph(SupportState)

    # --------------------------------------------------------
    # Add nodes
    # --------------------------------------------------------

    workflow.add_node(
        "triage",
        triage_node,
    )

    workflow.add_node(
        "retrieval",
        retrieval_node,
    )

    workflow.add_node(
        "clarification",
        clarification_node,
    )

    workflow.add_node(
        "escalation",
        escalation_node,
    )

    workflow.add_node(
        "out_of_scope",
        out_of_scope_node,
    )

    # --------------------------------------------------------
    # Start
    # --------------------------------------------------------

    workflow.add_edge(
        START,
        "triage",
    )

    # --------------------------------------------------------
    # Conditional routing after triage
    # --------------------------------------------------------

    workflow.add_conditional_edges(
        "triage",
        route_after_triage,
        {
            "retrieval": "retrieval",
            "clarification": "clarification",
            "escalation": "escalation",
            "out_of_scope": "out_of_scope",
        },
    )

    # --------------------------------------------------------
    # Terminal edges
    # --------------------------------------------------------

    workflow.add_edge(
        "retrieval",
        END,
    )

    workflow.add_edge(
        "clarification",
        END,
    )

    workflow.add_edge(
        "escalation",
        END,
    )

    workflow.add_edge(
        "out_of_scope",
        END,
    )

    # --------------------------------------------------------
    # Compile
    # --------------------------------------------------------

    return workflow.compile()


# Build graph once when imported
graph = build_graph()