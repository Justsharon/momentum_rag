"""
Phase 4b: LLM (prompt) evaluation.

Generates an answer for each eval question under each prompt variant
(prompts.py), then uses Groq itself as a judge to score each answer on
groundedness, relevance, and helpfulness (1-5). Averages per prompt.

Paced deliberately to stay under Groq's free-tier limits (30 requests/min
as of writing) -- with 10 questions x 3 prompts x 2 calls (generate +
judge) that's 60 calls, so this WILL take a couple of minutes to run
and may need retries. Reduce EVAL_SUBSET_SIZE below if you hit 429s
repeatedly.

Usage:
    export GROQ_API_KEY="gsk_..."
    python llm_eval.py
"""

import os
import re
import time
import json
import csv
from groq import Groq

from eval_questions import EVAL_QUESTIONS
from prompts import PROMPTS
from hybrid_retrieval import retrieve_hybrid
from llm import build_prompt

GROQ_API_KEY = os.environ["GROQ_API_KEY"]
MODEL_NAME = os.environ.get("GROQ_MODEL", "llama-3.3-70b-versatile")
client = Groq(api_key=GROQ_API_KEY)

EVAL_SUBSET_SIZE = 8          # keep small to respect free-tier rate limits
SECONDS_BETWEEN_CALLS = 2.5   # ~24 req/min, under the 30 RPM free-tier cap

JUDGE_SYSTEM_PROMPT = """You are grading an AI assistant's answer to a \
personal-knowledge question. You will see the retrieved context, the \
question, and the answer. Score the answer from 1-5 on each of:
- groundedness: does it only use facts present in the context?
- relevance: does it actually address the question asked?
- helpfulness: would this genuinely help the person plan their next step?

Respond with ONLY a JSON object, no other text:
{"groundedness": <1-5>, "relevance": <1-5>, "helpfulness": <1-5>}"""


def call_groq(system: str, user: str) -> str:
    response = client.chat.completions.create(
        model=MODEL_NAME,
        messages=[{"role": "system", "content": system}, {"role": "user", "content": user}],
        temperature=0.3,
    )
    return response.choices[0].message.content


def judge_answer(context: str, question: str, answer: str) -> dict:
    user_msg = f"Context:\n{context}\n\nQuestion: {question}\n\nAnswer: {answer}"
    raw = call_groq(JUDGE_SYSTEM_PROMPT, user_msg)
    match = re.search(r"\{.*\}", raw, re.DOTALL)
    try:
        return json.loads(match.group(0)) if match else {}
    except json.JSONDecodeError:
        return {}


def run_evaluation():
    subset = EVAL_QUESTIONS[:EVAL_SUBSET_SIZE]
    rows = []

    for item in subset:
        question = item["question"]
        retrieved = retrieve_hybrid(question, top_k=5)
        if not retrieved:
            print(f"[skip] Nothing retrieved for: {question!r}")
            continue

        context = "\n\n".join(f"[{r['source_type']} | {r['title']}]\n{r['text']}" for r in retrieved)
        user_prompt = build_prompt(question, retrieved)

        for prompt_name, system_prompt in PROMPTS.items():
            answer = call_groq(system_prompt, user_prompt)
            time.sleep(SECONDS_BETWEEN_CALLS)

            scores = judge_answer(context, question, answer)
            time.sleep(SECONDS_BETWEEN_CALLS)

            rows.append({
                "question": question, "prompt": prompt_name, "answer": answer,
                "groundedness": scores.get("groundedness"),
                "relevance": scores.get("relevance"),
                "helpfulness": scores.get("helpfulness"),
            })
            print(f"[{prompt_name}] {question[:40]!r} -> {scores}")

    print(f"\n{'Prompt':<14} {'Groundedness':>13} {'Relevance':>11} {'Helpfulness':>12}")
    print("-" * 54)
    for prompt_name in PROMPTS:
        prompt_rows = [r for r in rows if r["prompt"] == prompt_name]
        g = [r["groundedness"] for r in prompt_rows if r["groundedness"] is not None]
        rel = [r["relevance"] for r in prompt_rows if r["relevance"] is not None]
        h = [r["helpfulness"] for r in prompt_rows if r["helpfulness"] is not None]
        avg = lambda xs: sum(xs) / len(xs) if xs else 0
        print(f"{prompt_name:<14} {avg(g):>13.2f} {avg(rel):>11.2f} {avg(h):>12.2f}")

    with open("llm_eval_results.csv", "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["question", "prompt", "answer", "groundedness", "relevance", "helpfulness"])
        writer.writeheader()
        writer.writerows(rows)
    print("\nFull results written to llm_eval_results.csv")


if __name__ == "__main__":
    run_evaluation()