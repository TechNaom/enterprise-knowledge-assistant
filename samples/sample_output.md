# Sample Output

Generated against the **Aveltra Technologies** sample documents using provider `gemini`.

## Single-turn questions

### Q: How many paid vacation days do I get, and can I carry them over?

Based on the company documents:

* **Paid Vacation Days:** Full-time employees receive **20 days of paid annual leave (PTO)** per calendar year [1, 2].
* **Carry-over Rules:** You may carry over up to **5 unused PTO days** into the next calendar year, while any excess is forfeited on 31 January [1].

**Sources:** leave-policy.md (chunk 0), company-faq.md (chunk 0), travel-and-expense-policy.pdf (chunk 1), benefits.md (chunk 1)

---

### Q: How often must I change my password, and is MFA required?

Based on the provided documents:

* **Password Change Frequency:** You must change your password every 90 days [1, 2].
* **Multi-Factor Authentication (MFA):** MFA is mandatory for all email, VPN, and cloud-console access [1].

**Sources:** it-security-policy.pdf (chunk 0), company-faq.md (chunk 0), travel-and-expense-policy.pdf (chunk 1), code-of-conduct.md (chunk 1)

---

### Q: What is the per diem for international travel, and is alcohol reimbursable?

Based on the company travel and expense policy:

* The per diem for international travel is **$80 per day** [1].
* **Alcohol is not reimbursable** [1].

**Sources:** travel-and-expense-policy.pdf (chunk 1), code-of-conduct.md (chunk 0), benefits.md (chunk 1), leave-policy.md (chunk 1)

---

## Multi-turn conversation (memory)

### Q: How much parental leave is there?
*(resolved to: “How much parental leave is there?”)*

Based on the company leave policy, parental leave is structured as follows:

* **Maternity leave:** 26 weeks, with the first 16 weeks fully paid [1].
* **Paternity/partner leave:** 4 weeks fully paid, to be taken within 6 months of the birth or adoption [1].
* **Adoption leave:** Treated identically to maternity leave [1].

**Sources:** leave-policy.md (chunk 1), it-security-policy.pdf (chunk 0), code-of-conduct.md (chunk 1), benefits.md (chunk 1)

---

### Q: And how long for partners?
*(resolved to: “How much paternity or partner leave does the company provide?”)*

The company provides **4 weeks fully paid** paternity or partner leave, which must be taken within 6 months of the birth or adoption [1].

**Sources:** leave-policy.md (chunk 1), it-security-policy.pdf (chunk 0), code-of-conduct.md (chunk 1), benefits.md (chunk 1)

---

## Out-of-scope (grounded refusal)

### Q: What is the company's stock price today?

The provided documents do not contain information about the company's stock price today. 

Please consult the finance department or your manager for assistance with financial information [1, 2, 3, 4].

**Sources:** company-faq.md (chunk 1), code-of-conduct.md (chunk 1), benefits.md (chunk 1), it-security-policy.pdf (chunk 0)

---
