from typing import Literal

from langgraph.graph import StateGraph, START, END

from state import SupportState

from rag.loader import load_all_documents
from rag.chunker import chunk_documents
from rag.embeddings import EmbeddingModel
from rag.retriever import Retriever

from nodes.triage import triage_node
from nodes.generation import generation_node
from nodes.verification import verify_answer


# ============================================================
# INITIALIZE RAG SYSTEM
# ============================================================

_retriever = None

def get_retriever():
    global _retriever
    if _retriever is None:
        print("Initializing local RAG system...")
        documents = load_all_documents()
        chunks = chunk_documents(documents)
        embedding_model = EmbeddingModel()
        embeddings = embedding_model.encode(
            [chunk["content"] for chunk in chunks]
        )
        _retriever = Retriever(
            embedding_model=embedding_model,
            chunks=chunks,
            embeddings=embeddings,
        )
        print(
            f"RAG system ready: {len(chunks)} chunks indexed."
        )
    return _retriever



# ============================================================
# ROUTING AFTER TRIAGE
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
# RETRIEVAL NODE
# ============================================================

def retrieval_node(
    state: SupportState,
) -> SupportState:

    logs = state.get("logs", [])
    logs.append("retrieval_node")

    question = state["question"]

    print("\n[RETRIEVAL]")
    print(f"Query: {question}")

    results = get_retriever().retrieve(
        query=question,
        top_k=5,
    )

    print(
        f"Retrieved {len(results)} chunks."
    )

    for i, result in enumerate(
        results,
        start=1,
    ):

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
# CLARIFICATION NODE
# ============================================================

def clarification_node(
    state: SupportState,
) -> SupportState:

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


# ============================================================
# ESCALATION NODE
# ============================================================

def escalation_node(
    state: SupportState,
) -> SupportState:

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


# ============================================================
# OUT OF SCOPE NODE
# ============================================================

def out_of_scope_node(
    state: SupportState,
) -> SupportState:

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
# GENERATION NODE
# ============================================================

def run_generation(
    state: SupportState,
) -> SupportState:

    logs = state.get("logs", [])
    logs.append("generation_node")

    return generation_node(state)


# ============================================================
# VERIFICATION NODE
# ============================================================

def verification_node(
    state: SupportState,
) -> SupportState:

    logs = state.get("logs", [])
    logs.append("verification_node")

    result = verify_answer(state)

    return {
        **state,
        "verification_passed": result["verification_passed"],
        "verification_reason": result["verification_reason"],
        "logs": logs,
    }


# ============================================================
# FINAL RESPONSE NODES
# ============================================================

def finalize_node(
    state: SupportState,
) -> SupportState:

    logs = state.get("logs", [])
    logs.append("finalize_node")

    classification = state.get("classification")
    verification_passed = state.get("verification_passed", True)

    answer = state.get("answer", "")
    if classification == "answerable" and not verification_passed:
        answer = "The available documentation is insufficient to determine the next step."

    return {
        **state,
        "answer": answer,
        "logs": logs,
    }


# ============================================================
# REVISION ROUTING
# ============================================================

def route_after_verification(
    state: SupportState,
) -> Literal["finalize", "revision"]:

    verification_passed = state.get(
        "verification_passed",
        False,
    )

    revision_count = state.get(
        "revision_count",
        0,
    )

    # Maximum number of revisions allowed.
    MAX_REVISIONS = 1

    # Verification passed -> final answer.
    if verification_passed:
        return "finalize"

    # Verification failed, but we still have one
    # revision available.
    if revision_count < MAX_REVISIONS:
        return "revision"

    # Revision limit reached.
    return "finalize"


# ============================================================
# REVISION NODE
# ============================================================

def run_revision(
    state: SupportState,
) -> SupportState:

    from nodes.revise import revision_node

    return revision_node(state)


# ============================================================
# BUILD GRAPH
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
        "generation",
        run_generation,
    )

    workflow.add_node(
        "verification",
        verification_node,
    )

    workflow.add_node(
        "revision",
        run_revision,
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

    workflow.add_node(
        "finalize",
        finalize_node,
    )

    # --------------------------------------------------------
    # START -> TRIAGE
    # --------------------------------------------------------

    workflow.add_edge(
        START,
        "triage",
    )

    # --------------------------------------------------------
    # TRIAGE -> ROUTE
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
    # RETRIEVAL -> GENERATION
    # --------------------------------------------------------

    workflow.add_edge(
        "retrieval",
        "generation",
    )

    # --------------------------------------------------------
    # GENERATION -> VERIFICATION
    # --------------------------------------------------------

    workflow.add_edge(
        "generation",
        "verification",
    )

    # --------------------------------------------------------
    # VERIFICATION -> FINALIZE OR REVISION
    # --------------------------------------------------------

    workflow.add_conditional_edges(
        "verification",
        route_after_verification,
        {
            "finalize": "finalize",
            "revision": "revision",
        },
    )

    # --------------------------------------------------------
    # REVISION -> GENERATION
    # --------------------------------------------------------

    workflow.add_edge(
        "revision",
        "generation",
    )

    # --------------------------------------------------------
    # Other routes -> FINALIZE
    # --------------------------------------------------------

    workflow.add_edge(
        "clarification",
        "finalize",
    )

    workflow.add_edge(
        "escalation",
        "finalize",
    )

    workflow.add_edge(
        "out_of_scope",
        "finalize",
    )

    # --------------------------------------------------------
    # FINALIZE -> END
    # --------------------------------------------------------

    workflow.add_edge(
        "finalize",
        END,
    )

    # --------------------------------------------------------
    # Compile
    # --------------------------------------------------------

    return workflow.compile()


# ============================================================
# BUILD GRAPH ON IMPORT
# ============================================================

graph = build_graph()