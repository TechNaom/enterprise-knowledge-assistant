# Sample Questions

These questions exercise different documents and retrieval behaviours against
the included **Aveltra Technologies** sample document pack.

## Single-turn factual
1. How many paid vacation days do I get, and can I carry them over?
2. What is the per diem for international travel?
3. How often must I change my password, and is MFA required?
4. What does the wellness stipend cover and how much is it?
5. What is the notice period if I resign as a manager?

## Exact-term / acronym (shows BM25 value)
6. What is the policy on VPN and split tunnelling?
7. How much is the PTO carry-over limit?
8. What is Policy ID IT-SEC-004 about?

## Multi-turn (shows conversation memory)
9. "How much parental leave is there?"
   → follow-up: "And how long for partners?"
   → follow-up: "What about adoption?"

## Out-of-scope (shows grounded refusal)
10. What is the company's stock price today?
    (Not in the documents — the assistant should decline and suggest a contact.)
