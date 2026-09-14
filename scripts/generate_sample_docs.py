#!/usr/bin/env python3
"""Generate a sample company-document pack for a fictional organisation.

Creates a realistic set of HR / IT / travel / benefits documents for
**Aveltra Technologies** (a fictional company) in two formats — Markdown and
PDF — so the ingestion pipeline can be exercised out of the box.

    python scripts/generate_sample_docs.py

Output goes to ``data/documents/``.
"""

from __future__ import annotations

from pathlib import Path

from fpdf import FPDF

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data" / "documents"

COMPANY = "Aveltra Technologies"

# --- Markdown documents ----------------------------------------------------

LEAVE_POLICY = f"""# {COMPANY} — Leave Policy

**Policy ID:** HR-LEA-001  **Effective:** 1 January 2025

## 1. Annual Leave (Paid Time Off)
Full-time employees accrue **20 days of paid annual leave (PTO)** per calendar
year, accruing at 1.67 days per completed month of service. New joiners accrue
from their start date. Up to **5 unused PTO days** may be carried over into the
next calendar year; any excess is forfeited on 31 January.

## 2. Sick Leave
Employees are entitled to **10 paid sick days** per year. A medical certificate
is required for any sick absence of **3 or more consecutive days**. Unused sick
leave does not carry over and is not paid out.

## 3. Parental Leave
- **Maternity leave:** 26 weeks, of which the first 16 weeks are fully paid.
- **Paternity/partner leave:** 4 weeks fully paid, to be taken within 6 months
  of the birth or adoption.
- **Adoption leave:** treated identically to maternity leave.

## 4. Applying for Leave
All leave must be requested through the HR portal at least **7 calendar days**
in advance for planned leave. Manager approval is required. Sick leave should be
reported to your manager by 9:30 AM on the first day of absence.

## 5. Unpaid Leave
Unpaid leave of up to 30 days per year may be granted at management discretion
once paid entitlements are exhausted.
"""

BENEFITS = f"""# {COMPANY} — Employee Benefits

**Policy ID:** HR-BEN-002  **Effective:** 1 January 2025

## Health Insurance
All full-time employees and their immediate dependents are covered under the
company **Gold health plan** from day one. The company pays 100% of the employee
premium and 70% of dependent premiums.

## Retirement / Provident Fund
The company matches employee retirement contributions up to **6% of base
salary**. Vesting is immediate.

## Wellness Stipend
Every employee receives an annual **wellness stipend of $500**, reimbursable
against gym memberships, mental-health apps, or ergonomic equipment.

## Learning & Development
Each employee has a **$1,500 annual learning budget** for courses, books and
conferences, subject to manager approval.

## Remote Work Allowance
Remote and hybrid employees receive a one-time **$400 home-office setup
allowance** and a **$40 monthly internet reimbursement**.

## Employee Assistance Program (EAP)
Confidential counselling and legal/financial advice is available 24/7 through
the EAP hotline listed on the HR portal.
"""

CODE_OF_CONDUCT = f"""# {COMPANY} — Code of Conduct

**Policy ID:** HR-COC-003

## Our Principles
We act with integrity, respect and accountability. Every employee is expected to
treat colleagues, customers and partners fairly and professionally.

## Anti-Harassment
Harassment, discrimination or bullying of any kind is strictly prohibited.
Reports can be made confidentially to HR or via the anonymous ethics hotline.
All reports are investigated within 10 business days.

## Conflicts of Interest
Employees must disclose any personal, financial or family interest that could
conflict with company interests to their manager and HR.

## Confidentiality
Employees must protect confidential company and customer information both during
and after employment. Sharing confidential data externally without authorisation
is grounds for disciplinary action.

## Gifts and Entertainment
Gifts valued above **$100** must be declared. Cash gifts may never be accepted.

## Disciplinary Process
Violations follow a documented process: verbal warning, written warning, final
warning, and termination, depending on severity.
"""

FAQ = f"""# {COMPANY} — Employee FAQ

**Q: How many paid vacation days do I get?**
Full-time employees get 20 days of paid annual leave (PTO) per year. See the
Leave Policy for accrual and carry-over rules.

**Q: How do I reset my company password?**
Use the self-service portal at password.aveltra.example, or contact the IT Help
Desk. Passwords must be changed every 90 days.

**Q: Can I work from home?**
Yes. Aveltra operates a hybrid model — most roles require a minimum of 2 days per
week in the office. Fully-remote arrangements need VP approval.

**Q: How do I claim travel expenses?**
Submit receipts through the expense portal within 30 days of travel. See the
Travel & Expense Policy for daily limits.

**Q: Who do I contact about payroll issues?**
Email payroll@aveltra.example or raise a ticket in the HR portal.

**Q: What is the notice period if I resign?**
The standard notice period is 30 days for individual contributors and 60 days
for managers and above.
"""

MARKDOWN_DOCS = {
    "leave-policy.md": LEAVE_POLICY,
    "benefits.md": BENEFITS,
    "code-of-conduct.md": CODE_OF_CONDUCT,
    "company-faq.md": FAQ,
}

# --- PDF documents ---------------------------------------------------------

IT_SECURITY = {
    "title": f"{COMPANY} — IT Security & Acceptable Use Policy",
    "meta": "Policy ID: IT-SEC-004   Effective: 1 January 2025",
    "sections": [
        ("1. Passwords & Authentication",
         "Passwords must be at least 12 characters and include letters, numbers "
         "and symbols. They must be changed every 90 days and never reused across "
         "systems. Multi-factor authentication (MFA) is mandatory for all email, "
         "VPN and cloud-console access."),
        ("2. VPN & Remote Access",
         "All access to internal systems from outside the office must go through "
         "the company VPN. Split tunnelling is disabled. VPN credentials must not "
         "be shared. Report a lost or stolen device to the IT Help Desk within 2 "
         "hours."),
        ("3. Acceptable Use",
         "Company devices are for business use. Installing unapproved software, "
         "disabling antivirus, or connecting personal USB storage to company "
         "laptops is prohibited. Personal use of email and internet must be "
         "reasonable and lawful."),
        ("4. Data Classification & Handling",
         "Data is classified as Public, Internal, Confidential or Restricted. "
         "Confidential and Restricted data must be encrypted at rest and in "
         "transit and may never be stored on personal devices or public cloud "
         "drives."),
        ("5. Phishing & Incident Reporting",
         "Do not click links or open attachments from unknown senders. Report "
         "suspected phishing using the 'Report Phish' button in the mail client. "
         "Any suspected security incident must be reported to security@aveltra."
         "example immediately."),
    ],
}

TRAVEL_POLICY = {
    "title": f"{COMPANY} — Travel & Expense Policy",
    "meta": "Policy ID: FIN-TRV-005   Effective: 1 January 2025",
    "sections": [
        ("1. Booking Travel",
         "All business travel must be pre-approved by your manager and booked "
         "through the company travel portal at least 14 days in advance where "
         "possible. Economy class is standard for flights under 6 hours; premium "
         "economy is permitted for flights over 6 hours."),
        ("2. Accommodation",
         "Hotel costs are capped at $180 per night in standard cities and $250 "
         "per night in designated high-cost cities (New York, London, Tokyo, "
         "San Francisco, Singapore). Book through the travel portal to receive "
         "corporate rates."),
        ("3. Daily Meal Allowance (Per Diem)",
         "The per diem for meals and incidentals is $60 per day domestic and $80 "
         "per day international. Alcohol is not reimbursable. Itemised receipts "
         "are required for any single expense above $25."),
        ("4. Ground Transport",
         "Use ride-share or public transport where practical. Car rental requires "
         "manager approval. Mileage for personal-vehicle business use is "
         "reimbursed at $0.55 per mile."),
        ("5. Submitting Expenses",
         "Submit all expenses with receipts through the expense portal within 30 "
         "days of the trip. Claims older than 60 days will not be reimbursed "
         "except in exceptional, manager-approved cases."),
    ],
}


def _latin1(text: str) -> str:
    """Replace Unicode punctuation the built-in PDF font can't render."""
    replacements = {"—": "-", "–": "-", "‘": "'", "’": "'",
                    "“": '"', "”": '"', "…": "...", "•": "-"}
    for uni, ascii_ in replacements.items():
        text = text.replace(uni, ascii_)
    return text.encode("latin-1", "replace").decode("latin-1")


def write_pdf(spec: dict, path: Path) -> None:
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()

    def block(text: str, size: int, style: str = "", height: float = 6) -> None:
        pdf.set_x(pdf.l_margin)  # always start at the left margin
        pdf.set_font("Helvetica", style, size)
        pdf.multi_cell(pdf.epw, height, _latin1(text))

    block(spec["title"], 15, "B", 9)
    pdf.set_text_color(90, 90, 90)
    block(spec["meta"], 10, "I", 7)
    pdf.set_text_color(0, 0, 0)
    pdf.ln(3)
    for heading, body in spec["sections"]:
        block(heading, 12, "B", 8)
        block(body, 11, "", 6)
        pdf.ln(2)
    pdf.output(str(path))


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    for name, content in MARKDOWN_DOCS.items():
        (OUT / name).write_text(content, encoding="utf-8")
        print(f"wrote {name}")
    write_pdf(IT_SECURITY, OUT / "it-security-policy.pdf")
    print("wrote it-security-policy.pdf")
    write_pdf(TRAVEL_POLICY, OUT / "travel-and-expense-policy.pdf")
    print("wrote travel-and-expense-policy.pdf")
    print(f"\nSample documents for {COMPANY} written to {OUT}")


if __name__ == "__main__":
    main()
