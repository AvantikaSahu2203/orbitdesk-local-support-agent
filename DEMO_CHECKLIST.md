# OrbitDesk Local Support Agent — Demo Checklist

This document acts as a step-by-step guide to verify the core capabilities of the OrbitDesk Local Support Agent: Query Triage, Semantic Retrieval, Answer Generation, and Deterministic Post-Generation Verification.

---

## 🚀 1. How to Run the Demo

To run the interactive CLI demo:
1. Activate your virtual environment:
   ```bash
   .\venv\Scripts\activate
   ```
2. Launch the application:
   ```bash
   python app.py
   ```
You will enter a chat prompt loop where you can input the queries described below.

---

## 🔍 2. Core Demo Test Cases

Input each query below to test the routing classifications and generation accuracy:

### Case A: Answerable Query (RAG Flow)
- **Input Query**: 
  `My scheduled exports stopped after I changed my workspace timezone. What should I check?`
- **Anticipated Classification**: `answerable`
- **Expected Behavior**:
  - The model retrieves chunks from `03_workspace_settings_and_timezones.md` and `04_scheduled_exports.md`.
  - The model generates a response instructing you to:
    1. Open the existing recurring schedule.
    2. Confirm/review the next-run time.
    3. Select **Save schedule** to apply the new timezone (clearing the `Timezone update pending` notice).
    4. Check the schedule state, run history, destination, and active connections.
  - The output must cite sources explicitly (e.g., `Source: 03_workspace_settings_and_timezones.md`, `Source: 04_scheduled_exports.md`).

### Case B: Clarification Query
- **Input Query**: 
  `My export isn't working.`
- **Anticipated Classification**: `clarification`
- **Expected Behavior**:
  - The graph bypasses retriever/generator completely.
  - The agent responds with a professional request asking for more details (e.g. format type, error code, symptoms).

### Case C: Out-of-Scope Query
- **Input Query**: 
  `Write a refund for my subscription.`
- **Anticipated Classification**: `out_of_scope`
- **Expected Behavior**:
  - Bypasses retriever/generator.
  - The agent states that billing adjustments and subscription refund requests are out of scope for the technical support assistant, guiding you to billing portals or support.

### Case D: Escalation Query
- **Input Query**: 
  `Two consecutive runs show render_failed and all documented checks have already failed.`
- **Anticipated Classification**: `escalation`
- **Expected Behavior**:
  - Bypasses retriever/generator.
  - The agent detects that standard documentation checks failed and routes to a human agent, confirming a service ticket has been created.

---

## 🛡️ 3. Verification & Grounding Rules Demo

The support agent enforces deterministic checks to filter out hallucinations/unauthorized instructions:
1. **Forbidden Terms**: Any generated response containing "contact IT support" or "try again" is blocked and revised unless those exact phrases exist in the retrieved evidence documents.
2. **UI Elements Checking**: If the model suggests a fake action or click (like select `'Resubmit'`), the verification node scans the evidence. If the button/menu item is not in the source text, verification fails and the agent attempts a revision.
3. **Invalid Sources**: If the model cites a document name not in the top retrieved evidence (e.g. `05_api_credentials.md`), the verification node fails it instantly.

---

## 🧪 4. Automated Test Verification

To run all automated unit and integration tests verifying the full flow:
1. Run `pytest`:
   ```bash
   .\venv\Scripts\python -m pytest tests -v
   ```
2. Verify that **19 tests** pass successfully, validating:
   - File chunking and loading logic.
   - Vector store and retriever implementation.
   - Evidence chunk deduplication logic.
   - Grounding validation rules.
   - Post-generation source validation.
   - Graph routing logic.
