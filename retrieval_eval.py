"""
Phase 4a: retrieval evaluation.

Runs every question in eval_questions.py through vector search, BM25, and
hybrid search, and reports Recall@5, MRR, and Precision@5 for each --
this is the "compare multiple retrieval approaches" rubric requirement.

Usage:
    python ingest.py          # make sure documents table is fresh first
    python retrieval_eval.py
"""

import os
import csv
import psycopg2
import psycopg2.extras

from eval_questions import EVAL_QUESTIONS
from retrieval import retrieve as retrieve_vector
from bm25_retrieval import retrieve_bm25
from hybrid_retrieval import retrieve_hybrid

DATABASE_URL = os.environ.get(
    "DATABASE_URL", "postgresql://postgres:postgres@localhost:5433/momentum"
)
TOP_K = 5


def resolve_expected_doc_ids(source_type: str, title_keyword: str) -> set[str]:
    """Finds the real document_id(s) matching a question's expected criteria."""
    conn = psycopg2.connect(DATABASE_URL)
    try:
        with conn.cursor() as cur:
            cur.execute(
                """SELECT id FROM documents
                   WHERE source_type = %s AND title ILIKE %s""",
                (source_type, f"%{title_keyword}%"),
            )
            return {str(row[0]) for row in cur.fetchall()}
    finally:
        conn.close()


def recall_at_k(retrieved_ids: list[str], expected_ids: set[str]) -> float:
    if not expected_ids:
        return None
    hit = any(doc_id in expected_ids for doc_id in retrieved_ids)
    return 1.0 if hit else 0.0


def mrr(retrieved_ids: list[str], expected_ids: set[str]) -> float:
    if not expected_ids:
        return None
    for rank, doc_id in enumerate(retrieved_ids, start=1):
        if doc_id in expected_ids:
            return 1.0 / rank
    return 0.0


def precision_at_k(retrieved_ids: list[str], expected_ids: set[str]) -> float:
    if not expected_ids or not retrieved_ids:
        return None
    hits = sum(1 for doc_id in retrieved_ids if doc_id in expected_ids)
    return hits / len(retrieved_ids)


METHODS = {
    "vector": lambda q: retrieve_vector(q, top_k=TOP_K),
    "bm25": lambda q: retrieve_bm25(q, top_k=TOP_K),
    "hybrid": lambda q: retrieve_hybrid(q, top_k=TOP_K),
}


def run_evaluation():
    results = {method: {"recall": [], "mrr": [], "precision": []} for method in METHODS}
    per_question_rows = []

    for item in EVAL_QUESTIONS:
        expected_ids = resolve_expected_doc_ids(item["expected_source_type"], item["title_keyword"])
        if not expected_ids:
            print(f"[skip] No matching document for: {item['question']!r} "
                  f"(expected {item['expected_source_type']} / {item['title_keyword']!r})")
            continue

        for method_name, retrieve_fn in METHODS.items():
            hits = retrieve_fn(item["question"])
            retrieved_ids = [h["document_id"] for h in hits]

            r = recall_at_k(retrieved_ids, expected_ids)
            m = mrr(retrieved_ids, expected_ids)
            p = precision_at_k(retrieved_ids, expected_ids)

            results[method_name]["recall"].append(r)
            results[method_name]["mrr"].append(m)
            results[method_name]["precision"].append(p)

            per_question_rows.append({
                "question": item["question"], "method": method_name,
                "recall": r, "mrr": m, "precision": p,
            })

    print(f"\n{'Method':<10} {'Recall@5':>10} {'MRR':>10} {'Precision@5':>14}")
    print("-" * 46)
    for method_name, metrics in results.items():
        avg_recall = sum(metrics["recall"]) / len(metrics["recall"]) if metrics["recall"] else 0
        avg_mrr = sum(metrics["mrr"]) / len(metrics["mrr"]) if metrics["mrr"] else 0
        avg_precision = sum(metrics["precision"]) / len(metrics["precision"]) if metrics["precision"] else 0
        print(f"{method_name:<10} {avg_recall:>10.3f} {avg_mrr:>10.3f} {avg_precision:>14.3f}")

    with open("retrieval_eval_results.csv", "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["question", "method", "recall", "mrr", "precision"])
        writer.writeheader()
        writer.writerows(per_question_rows)
    print("\nPer-question results written to retrieval_eval_results.csv")


if __name__ == "__main__":
    run_evaluation()