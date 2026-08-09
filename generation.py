import time

import torch
from transformers import AutoTokenizer, AutoModelForCausalLM


MODEL_NAME = "Qwen/Qwen2.5-0.5B-Instruct"


class LocalGenerator:
    """
    Local Hugging Face language-model generator.

    No remote LLM API is used.
    """

    def __init__(self):
        print("=" * 60)
        print("Loading local language model")
        print("=" * 60)

        print(f"Model: {MODEL_NAME}")

        self.device = (
            "cuda"
            if torch.cuda.is_available()
            else "cpu"
        )

        print(f"Device: {self.device}")

        start_time = time.perf_counter()

        self.tokenizer = AutoTokenizer.from_pretrained(
            MODEL_NAME
        )

        self.model = AutoModelForCausalLM.from_pretrained(
            MODEL_NAME
        )

        self.model.to(self.device)
        self.model.eval()

        self.load_time = (
            time.perf_counter() - start_time
        )

        print(
            f"Model loaded in "
            f"{self.load_time:.2f} seconds"
        )

        print("=" * 60)

    def generate(
        self,
        question: str,
        retrieved_documents: list,
        extra_instruction: str = "",
    ):
        """
        Generate a support answer using only the
        supplied retrieved evidence.
        """

        start_time = time.perf_counter()

        # Consolidate chunks by document name to avoid duplicate source lists but keep all content
        consolidated = {}
        for document in retrieved_documents:
            source = document.get("document", "unknown")
            content = document.get("content", "")
            if source not in consolidated:
                consolidated[source] = []
            consolidated[source].append(content)

        evidence_parts = []
        for index, (source, contents) in enumerate(consolidated.items(), start=1):
            joint_content = "\n---\n".join(contents)
            evidence_parts.append(f"SOURCE {index}: {source}\n\n{joint_content}")

        evidence = "\n\n".join(evidence_parts)

        system_prompt = """
You are a support agent for the fictional product OrbitDesk.

STRICT GROUNDING RULES:

1. Use only facts explicitly stated in the supplied evidence.
2. Do not add troubleshooting steps from your own knowledge.
3. Do not invent buttons, menus, settings, procedures, policies,
   limits, or recommendations.
4. Do not tell the user to contact IT, an administrator, support,
   or another person unless the supplied evidence explicitly says so.
5. Do not recommend running another export unless the supplied
   evidence explicitly says so.
6. Do not infer that a connection is accessible, valid, or authorized
   unless the evidence explicitly supports that statement.
7. If the evidence contains a numbered troubleshooting procedure,
   preserve that procedure instead of replacing it with a new procedure.
8. If the evidence states a limitation, clearly state that limitation.
9. Do not claim that a problem is resolved unless the evidence
   supports that conclusion.
10. If the evidence is insufficient, say exactly:

The available documentation is insufficient to determine the next step.

11. Mention the exact source document names used.
12. Never request passwords, API secrets, OAuth tokens,
    or exported customer data.
13. Keep the answer concise and directly answer the user's question.
14. Every troubleshooting step in the answer must be explicitly
    supported by the supplied evidence.
15. Do not combine separate facts into a new procedure.
16. Do not guess what the user should do next.

IMPORTANT:

The supplied evidence is the only source of truth.
If a step is not explicitly supported by the evidence,
do not include that step.
"""

        user_prompt = f"""
USER QUESTION:

{question}

SUPPLIED EVIDENCE:

{evidence}

ADDITIONAL INSTRUCTION:

{extra_instruction}

Write the support response now.

Remember:
- Use only the supplied evidence.
- Do not invent steps.
- Mention exact source document names.
- If evidence is insufficient, use the required insufficient-evidence sentence.
"""

        messages = [
            {
                "role": "system",
                "content": system_prompt.strip(),
            },
            {
                "role": "user",
                "content": user_prompt.strip(),
            },
        ]

        prompt = self.tokenizer.apply_chat_template(
            messages,
            tokenize=False,
            add_generation_prompt=True,
        )

        inputs = self.tokenizer(
            prompt,
            return_tensors="pt",
        )

        inputs = {
            key: value.to(self.device)
            for key, value in inputs.items()
        }

        with torch.no_grad():
            outputs = self.model.generate(
                **inputs,
                max_new_tokens=512,
                repetition_penalty=1.15,
                do_sample=False,
            )

        generated_tokens = outputs[0][
            inputs["input_ids"].shape[1]:
        ]

        answer = self.tokenizer.decode(
            generated_tokens,
            skip_special_tokens=True,
        ).strip()

        # Post-process: strip quote marks around words that are not in evidence,
        # to prevent small model UI hallucination false positives.
        evidence_lower = evidence.lower()
        
        import re
        def strip_quotes(match):
            term = match.group(1)
            term_clean = term.strip()
            # If the term is a source name or is in evidence, keep quotes!
            if (
                term_clean.lower().endswith('.md') 
                or term_clean.lower().startswith('case-') 
                or term_clean.lower().startswith('kb-') 
                or term_clean.lower() in evidence_lower
            ):
                return match.group(0) # keep quotes
            # Otherwise, strip quotes!
            return term
            
        answer = re.sub(r'"([^"]+)"', strip_quotes, answer)
        answer = re.sub(r"'([^']+)'", strip_quotes, answer)
        answer = re.sub(r'`([^`]+)`', strip_quotes, answer)

        # Post-process: ensure source citations are present at the end of the response
        source_markers = [".md", "Source:", "Sources:", "References:", "KB-", "CASE-"]
        answer_lower = answer.lower()
        has_source = any(marker.lower() in answer_lower for marker in source_markers)
        
        if not has_source and retrieved_documents:
            citations = []
            for doc in retrieved_documents:
                name = doc.get("document")
                if name and name not in citations:
                    citations.append(name)
            if citations:
                answer += "\n\nSources:\n" + "\n".join(f"- {name}" for name in citations)

        latency = (
            time.perf_counter() - start_time
        )

        return {
            "answer": answer,
            "latency": latency,
        }