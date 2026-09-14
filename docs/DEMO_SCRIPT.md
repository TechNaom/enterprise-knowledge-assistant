# Demo Video Script (~3 minutes)

A tight walkthrough for the capstone demo/walkthrough video. Record your screen
(OBS Studio, Loom, or Windows Game Bar `Win+G`) and narrate.

---

### 0:00 – Intro (20s)
> "Hi, I'm Manohar. This is my capstone — an **Enterprise Knowledge Assistant**,
> a production-oriented **advanced RAG** app that answers employee questions
> from company documents like HR, IT, travel and benefits policies. It's more
> than chat-with-PDF: it uses hybrid retrieval, re-ranking, conversation memory
> and cites its sources."

### 0:20 – The documents & architecture (25s)
- Show `data/documents/` — point out **PDF and Markdown** files.
- Show the README architecture diagram briefly.
> "Documents are chunked, embedded, and stored in a local ChromaDB vector
> database plus a BM25 keyword index."

### 0:45 – Launch the app (15s)
- `streamlit run app.py` (or open the live URL).
- Show the sidebar: backend, index ready, document list.

### 1:00 – Single-turn question with citations (35s)
- Ask: **"How many paid vacation days do I get, and can I carry them over?"**
> "It answers 20 days PTO with up to 5 carried over — and cites the leave
> policy."
- Expand **Sources** and **Retrieval trace**.
> "You can see the expanded queries, the dense and sparse hits, and that
> re-ranking ran — the advanced pipeline in action."

### 1:35 – Exact-term question (20s)
- Ask: **"What's the policy on VPN and split tunnelling?"**
> "This shows BM25 keyword retrieval catching an exact acronym from a PDF."

### 1:55 – Multi-turn memory (35s)
- Ask: **"How much parental leave is there?"**
- Then follow up: **"And how long for partners?"**
> "Notice it understood 'partners' in context — the retrieval trace shows the
> follow-up was rewritten into a standalone question. That's conversation
> memory."

### 2:30 – Grounded refusal (20s)
- Ask: **"What is the company's stock price today?"**
> "It doesn't hallucinate — it says the documents don't cover this and suggests
> who to contact. That's what makes it trustworthy."

### 2:50 – Close (15s)
> "The code is modular Python, runs locally on open-source Ollama or deploys to
> the cloud with Gemini. The repo, README, and sample data are on GitHub.
> Thanks for watching."

---

**Recording tips**
- Pre-build the index before recording (`python ingest.py`) so answers are fast.
- Use the Gemini provider for snappy responses on camera.
- Keep the browser zoom at ~110% so text is readable.
