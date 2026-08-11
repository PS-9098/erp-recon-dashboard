# ERP Reconciliation Mini-Dashboard

**A lightweight full-stack proof-of-concept for automated AP reconciliation and aging analysis.**

---

## 1. Executive Summary

Manual reconciliation of vendor invoices against general ledger entries is time-consuming and error-prone in many finance departments. This project demonstrates a simple, end-to-end solution that:

- Ingests mock financial data (GL entries & vendor invoices) into a SQL database.
- Exposes key reconciliation metrics via a REST API.
- Presents an interactive dashboard showing **outstanding invoices**, **flagged discrepancies**, and **aging summaries**.

The tool is built with minimal dependencies (vanilla HTML/CSS/JS, Python Flask, SQLite) to prove that core reconciliation logic can be delivered quickly and iteratively—a common need in consulting and audit technology engagements.

---

## 2. Features

- **Outstanding Invoices Table** – All open vendor invoices with vendor name, invoice number, amount, due date, and days overdue.
- **Discrepancy Flags** – Automatic detection of:
  - Invoices without a matching GL entry.
  - Amount mismatches between an invoice and its linked GL entry.
- **Aging Summary** – Count of outstanding invoices grouped into classic buckets: 0–30, 31–60, 61–90, and 90+ days overdue.
- **One-click Refresh** – Re-fetches the latest data from the backend.
- **Mock Data Generator** – Reproducible script that creates a realistic dataset with pre-seeded discrepancies.

---

## 3. Tech Stack

| Layer | Technology |
| :--- | :--- |
| **Frontend** | HTML5, CSS3, Vanilla JavaScript (ES6) |
| **Backend** | Python 3.x, Flask |
| **Database** | SQLite (file-based, zero-config) |
| **Data Gen** | Python script (uses `sqlite3` standard library) |
| **Versioning** | Git with incremental commits |

---

## 4. Project Structure

```text
erp-recon-dashboard/
├── README.md
├── .gitignore
├── requirements.txt
├── scripts/
│   └── generate_data.py          # creates tables & mock data
├── backend/
│   └── app.py                    # Flask server + API routes
└── frontend/
    ├── index.html
    ├── style.css
    └── dashboard.js
