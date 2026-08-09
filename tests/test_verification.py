from nodes.verification import verify_answer


def test_verification_passes_with_valid_answer():
    state = {
        "classification": "answerable",
        "answer": (
            "Follow the documented troubleshooting steps. "
            "Source: 04_scheduled_exports.md"
        ),
        "retrieved_documents": [
            {
                "document": "04_scheduled_exports.md",
                "content": "Troubleshooting a missed export.",
            }
        ],
        "revision_count": 0,
    }

    result = verify_answer(state)

    assert result["verification_passed"] is True


def test_verification_fails_without_evidence():
    state = {
        "classification": "answerable",
        "answer": "Source: 04_scheduled_exports.md",
        "retrieved_documents": [],
        "revision_count": 0,
    }

    result = verify_answer(state)

    assert result["verification_passed"] is False
    assert "No retrieved evidence" in result["verification_reason"]


def test_verification_fails_without_source():
    state = {
        "classification": "answerable",
        "answer": "Follow the documented troubleshooting steps.",
        "retrieved_documents": [
            {
                "document": "04_scheduled_exports.md",
                "content": "Troubleshooting a missed export.",
            }
        ],
        "revision_count": 0,
    }

    result = verify_answer(state)

    assert result["verification_passed"] is False
    assert "source reference" in result["verification_reason"]


def test_verification_fails_after_revision_limit():
    state = {
        "classification": "answerable",
        "answer": "Source: 04_scheduled_exports.md",
        "retrieved_documents": [
            {
                "document": "04_scheduled_exports.md",
                "content": "Troubleshooting a missed export.",
            }
        ],
        "revision_count": 2,
    }

    result = verify_answer(state)

    assert result["verification_passed"] is False
    assert "Maximum revision limit" in result["verification_reason"]


def test_verification_fails_with_invalid_source():
    state = {
        "classification": "answerable",
        "answer": "Refer to documentation. Source: 05_api_credentials.md",
        "retrieved_documents": [
            {
                "document": "04_scheduled_exports.md",
                "content": "Troubleshooting a missed export.",
            }
        ],
        "revision_count": 0,
    }

    result = verify_answer(state)

    assert result["verification_passed"] is False
    assert "source that was not retrieved" in result["verification_reason"]


def test_verification_passes_with_multiple_sources():
    state = {
        "classification": "answerable",
        "answer": "Refer to 04_scheduled_exports.md and 03_workspace_settings_and_timezones.md.",
        "retrieved_documents": [
            {
                "document": "04_scheduled_exports.md",
                "content": "Troubleshooting a missed export.",
            },
            {
                "document": "03_workspace_settings_and_timezones.md",
                "content": "Workspace settings options.",
            }
        ],
        "revision_count": 0,
    }

    result = verify_answer(state)

    assert result["verification_passed"] is True


def test_verification_fails_with_unsupported_contact_it():
    state = {
        "classification": "answerable",
        "answer": "You should contact IT support. Source: 04_scheduled_exports.md",
        "retrieved_documents": [
            {
                "document": "04_scheduled_exports.md",
                "content": "Troubleshooting a missed export.",
            }
        ],
        "revision_count": 0,
    }

    result = verify_answer(state)

    assert result["verification_passed"] is False
    assert "recommends unsupported instruction" in result["verification_reason"]


def test_verification_passes_with_supported_contact_it():
    state = {
        "classification": "answerable",
        "answer": "You should contact IT. Source: 04_scheduled_exports.md",
        "retrieved_documents": [
            {
                "document": "04_scheduled_exports.md",
                "content": "If problems persist, contact IT support immediately.",
            }
        ],
        "revision_count": 0,
    }

    result = verify_answer(state)

    assert result["verification_passed"] is True


def test_verification_fails_with_unsupported_ui_element():
    state = {
        "classification": "answerable",
        "answer": "Click on 'Resubmit Export' button. Source: 04_scheduled_exports.md",
        "retrieved_documents": [
            {
                "document": "04_scheduled_exports.md",
                "content": "Troubleshooting a missed export.",
            }
        ],
        "revision_count": 0,
    }

    result = verify_answer(state)

    assert result["verification_passed"] is False
    assert "references unsupported UI element" in result["verification_reason"]