"""Prompt templates used across the RAG pipeline.

Keeping prompts in one module makes them easy to read, review and tune
without touching pipeline logic.
"""

from __future__ import annotations

# Rewrites a follow-up question into a standalone one using chat history,
# so retrieval works on multi-turn conversations ("what about for managers?").
CONDENSE_QUESTION_PROMPT = """Given the conversation history and a follow-up \
question, rewrite the follow-up question as a standalone question that can be \
understood without the history. Keep it concise and preserve the user's intent. \
Do not answer it. If the follow-up is already standalone, return it unchanged.

Conversation history:
{history}

Follow-up question: {question}

Standalone question:"""


# Generates alternative phrasings of a query to widen recall (multi-query).
MULTI_QUERY_PROMPT = """You are helping a search system retrieve relevant \
company-policy passages. Generate {n} alternative phrasings of the question \
below. Vary the wording and vocabulary (synonyms, formal/informal, expanded \
acronyms) but keep the same meaning. Return one phrasing per line with no \
numbering or extra text.

Question: {question}

Alternative phrasings:"""


# The grounded-answer prompt.  Instructs the model to answer ONLY from context
# and to cite the numbered sources, which keeps the assistant faithful.
ANSWER_SYSTEM_PROMPT = """You are the Enterprise Knowledge Assistant for a \
company. You answer employee questions using ONLY the company documents \
provided as context. Follow these rules strictly:

1. Base your answer only on the provided context. Do not use outside knowledge.
2. If the context does not contain the answer, say so plainly and suggest who \
the employee might contact. Never invent policy details.
3. Cite the sources you used with bracketed numbers like [1], [2] that match \
the numbered context blocks.
4. Be concise, clear and professional. Use short paragraphs or bullet points.
"""


ANSWER_USER_PROMPT = """Context documents:
{context}

Question: {question}

Answer (cite sources as [n]):"""


# LLM re-ranking prompt: score ALL candidate passages in a single call.
# The model returns one "index:score" pair per line, which keeps re-ranking to
# one round-trip instead of one call per passage (critical on CPU inference).
RERANK_PROMPT = """You are ranking passages by how well each one helps answer \
the question. For every passage below, output a line ``index:score`` where \
score is an integer 0-10 (10 = directly answers the question, 0 = irrelevant). \
Output only those lines, one per passage, nothing else.

Question: {question}

Passages:
{passages}

Scores (one 'index:score' per line):"""
