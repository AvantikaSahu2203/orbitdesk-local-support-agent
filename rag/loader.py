from pathlib import Path
import json

DOCS_PATH = Path("data/docs")
CASES_PATH = Path("data/resolved_cases.json")


def load_markdown_documents():
    documents = []

    for file_path in DOCS_PATH.glob("*.md"):
        content = file_path.read_text(encoding="utf-8")

        documents.append(
            {
                "document": file_path.name,
                "content": content,
            }
        )

    return documents


def load_resolved_cases():
    """
    Load resolved support cases from JSON.
    Returns only the list of cases.
    """
    with open(CASES_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)

    return data["cases"]


def load_all_documents():
    docs = load_markdown_documents()
    cases = load_resolved_cases()

    case_documents = []

    for case in cases:

        # Skip historical cases
        if case["status"] == "superseded":
            continue

        text = f"""
Case ID:
{case.get("case_id", "")}

Status:
{case.get("status", "")}

Title:
{case.get("title", "")}

Symptoms:
{" ".join(case.get("symptoms", []))}

Resolution:
{" ".join(case.get("resolution", []))}

Important Limit:
{case.get("important_limit", "")}

Source Documents:
{", ".join(case.get("source_documents", []))}
"""

        case_documents.append(
            {
                "document": case["case_id"],
                "content": text,
            }
        )

    return docs + case_documents