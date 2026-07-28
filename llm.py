"""
Wraps calls to Groq. Kept separate from api.py so Phase 4 can swap prompts
in and out for evaluation without touching the API layer.
"""

import os
import time
from groq import Groq

GROQ_API_KEY = os.environ["GROQ_API_KEY"]  # export this before running
MODEL_NAME = os.environ.get("GROQ_MODEL", "llama-3.3-70b-versatile")

client = Groq(api_key=GROQ_API_KEY)

# This is "Prompt B" from the project doc -- structured, grounded, refuses
# to guess. Swap this out in Phase 4 when comparing prompt variants.
SYSTEM_PROMPT = """You are MomentumRAG, a personal assistant that answers \
questions using ONLY the retrieved context below, which comes from the \
user's own goals, projects, reflections, and daily check-ins.

Rules:
- Base your answer only on the retrieved context. Do not invent details.
- If the context doesn't contain enough information to answer, say so \
plainly instead of guessing.
- Where relevant, point out patterns across multiple entries (e.g. \
recurring blockers, mood trends) rather than just restating one entry.
- Be direct and concise. This is a tool for self-reflection, not a \
motivational speech."""


def build_prompt(question: str, retrieved: list[dict]) -> str:
    context = "\n\n".join(
        f"[{r['source_type']} | {r['title']}]\n{r['text']}" for r in retrieved
    )
    return f"Context:\n{context}\n\nQuestion: {question}"


def ask_llm(question: str, retrieved: list[dict]) -> dict:
    """Returns {answer, latency_ms, total_tokens}"""
    prompt = build_prompt(question, retrieved)

    start = time.time()
    response = client.chat.completions.create(
        model=MODEL_NAME,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": prompt},
        ],
        temperature=0.3,
    )
    latency_ms = int((time.time() - start) * 1000)

    return {
        "answer": response.choices[0].message.content,
        "latency_ms": latency_ms,
        "total_tokens": response.usage.total_tokens,
    }