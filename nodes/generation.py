from generation import LocalGenerator


# Lazy load the generator to avoid loading it on import
_generator = None

def get_generator():
    global _generator
    if _generator is None:
        _generator = LocalGenerator()
    return _generator


def generation_node(state):
    """
    Generate an answer using only the retrieved evidence.
    """

    logs = list(state.get("logs", []))
    logs.append("generation_node")

    question = state["question"]

    retrieved_documents = state.get(
        "retrieved_documents",
        [],
    )

    extra_instruction = state.get(
        "revision_instruction",
        "",
    )

    result = get_generator().generate(
        question=question,
        retrieved_documents=retrieved_documents,
        extra_instruction=extra_instruction,
    )

    return {
        **state,
        "answer": result["answer"],
        "generation_latency": result["latency"],
        "logs": logs,
    }