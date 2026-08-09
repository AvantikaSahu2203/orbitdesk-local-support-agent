import sys
from pathlib import Path

sys.path.insert(
    0,
    str(Path(__file__).resolve().parents[1])
)

from generation import LocalGenerator

# Lazy load generator to prevent loading during test collection
_generator = None

def get_generator():
    global _generator
    if _generator is None:
        _generator = LocalGenerator()
    return _generator



def test_generation_basic():
    question = (
        "My scheduled exports stopped after I changed "
        "my workspace timezone. What should I check?"
    )

    evidence = [
        {
            "document": "03_workspace_settings_and_timezones.md",
            "content": """
Changing the workspace timezone does not immediately
rewrite existing recurring export schedules.

To apply the new workspace timezone to an existing
recurring schedule:

1. Open the schedule.
2. Review the displayed next-run time.
3. Select Save schedule.
4. Confirm that the Timezone update pending notice disappears.

Resaving changes future run times only.
It does not create a replacement run for an export
that was already missed.
""",
        },
        {
            "document": "04_scheduled_exports.md",
            "content": """
For a missed export:

1. Confirm the schedule state and next-run time.
2. Open Schedule > Run history.
3. Note the latest run status and error code.
4. Confirm required connections are active.
5. Confirm the destination is verified and enabled.
""",
        },
    ]

    result = get_generator().generate(
        question=question,
        retrieved_documents=evidence,
    )

    print()
    print("=" * 60)
    print("GENERATED ANSWER")
    print("=" * 60)
    print(result["answer"])

    print()
    print(
        f"Generation latency: "
        f"{result['latency']:.2f} seconds"
    )

    assert result["answer"] is not None
    assert len(result["answer"]) > 0