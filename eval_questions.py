"""
Evaluation questions for retrieval.

Because your actual documents (and their UUIDs) depend on what's in your
Postgres instance, each question doesn't hardcode a document_id. Instead
it specifies `expected_source_type` + `title_keyword`, and
retrieval_eval.py resolves that to real document_id(s) from the
`documents` table at run time. Add more of these as you add real data --
this file should grow alongside your seed.py / daily check-ins.
"""

EVAL_QUESTIONS = [
    {"question": "What is my current project?",
     "expected_source_type": "project", "title_keyword": "MomentumRAG"},
    {"question": "What should I focus on next in the RAG project?",
     "expected_source_type": "project", "title_keyword": "MomentumRAG"},
    {"question": "What are my main goals right now?",
     "expected_source_type": "goal", "title_keyword": "Zoomcamp"},
    {"question": "Why am I struggling to keep a daily routine?",
     "expected_source_type": "goal", "title_keyword": "routine"},
    {"question": "What blocked me from working on my project recently?",
     "expected_source_type": "reflection", "title_keyword": "Reflection"},
    {"question": "How was my mood a couple of days ago?",
     "expected_source_type": "reflection", "title_keyword": "Reflection"},
    {"question": "Did I reinstall social media recently?",
     "expected_source_type": "checkin", "title_keyword": "Check-in"},
    {"question": "How motivated have I felt this week?",
     "expected_source_type": "checkin", "title_keyword": "Check-in"},
    {"question": "Did I complete my planned tasks yesterday?",
     "expected_source_type": "checkin", "title_keyword": "Check-in"},
    {"question": "What technologies am I using for the Zoomcamp project?",
     "expected_source_type": "project", "title_keyword": "MomentumRAG"},
]