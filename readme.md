Here is a cleaned-up, emoji-free, professional, plain-text version.
I removed emojis, removed decorative lines, simplified headings, and made it look like you typed it normally.

---

# Invoice QC Service

A complete invoice extraction and quality control system that extracts structured data from PDF invoices and validates them against business rules.

Overview

This project implements an end-to-end invoice processing pipeline:

1. Extraction: Reads PDF invoices and extracts structured data
2. Validation: Validates data against business rules
3. Interfaces: Provides both CLI and REST API access
4. Reporting: Generates validation reports

Completed Components

* PDF Extraction Module
* Validation Engine
* Command-Line Interface
* HTTP REST API
* Web UI (not implemented due to time)

Schema and Validation Design

Invoice Schema

The system extracts 13 core invoice-level fields:

Identifiers

* invoice_number
* external_reference

Seller Information

* seller_name
* seller_address
* seller_tax_id

Buyer Information

* buyer_name
* buyer_address
* buyer_tax_id

Dates

* invoice_date
* due_date

Financial Information

* currency
* net_total
* tax_amount
* tax_rate
* gross_total

Additional

* payment_terms
* line_items (description, quantity, unit_price, line_total)

Line items are included to support reconciliation, verification of totals, and product-level analysis.

Validation Rules

Completeness Rules

1. invoice_number_required
2. invoice_date_required
3. seller_name_required and buyer_name_required
4. gross_total_required

Business Rules
5. date_order
6. totals_consistency
7. line_items_sum
8. non_negative_amounts

Anomaly Rules
9. duplicate_invoice
10. reasonable_date_range
11. valid_currency

Architecture

Folder Structure

invoice-qc-service/
├── invoice_qc/
│   ├── schemas.py
│   ├── extractor.py
│   ├── validator.py
│   └── cli.py
├── api/
│   └── main.py
├── tests/
├── pdfs/
├── output/
├── requirements.txt
└── README.md

Component Flow

PDF Files → PDF Extractor → Structured JSON → Validator Engine → Validation Report
CLI and HTTP API both consume the validator.

Extraction Pipeline

1. PDF reading using pdfplumber
2. Text parsing with regex
3. Seller/buyer detection using keyword sections
4. Amount extraction
5. Table detection for line items
6. Output is converted into Pydantic Invoice models

Validation Core

1. Batch validation
2. Per-invoice rule execution
3. Error collection
4. Duplicate detection
5. Summary generation

Setup and Installation

Prerequisites: Python 3.9+ and pip

Clone repository:

```
git clone <repository-url>
cd invoice-qc-service
```

Create virtual environment:

```
python -m venv venv
source venv/bin/activate
```

Install dependencies:

```
pip install --upgrade pip
pip install -r requirements.txt
```

Place sample PDFs in the pdfs/ directory.

Usage

CLI

Extract only:

```
python -m invoice_qc.cli extract --pdf-dir pdfs --output extracted.json
```

Validate only:

```
python -m invoice_qc.cli validate --input extracted.json --report report.json
```

Adjust tolerance:

```
python -m invoice_qc.cli validate --input extracted.json --report report.json --tolerance 0.05
```

Full run:

```
python -m invoice_qc.cli full-run --pdf-dir pdfs --report validation_report.json
```

Save extracted data:

```
python -m invoice_qc.cli full-run --pdf-dir pdfs --report validation_report.json --save-extracted extracted.json
```

HTTP API

Start server:

```
uvicorn api.main:app --reload --host 0.0.0.0 --port 8000
```

Endpoints:

Health check:

```
GET /health
```

Validate JSON:

```
POST /validate-json
```

Extract and validate PDFs:

```
POST /extract-and-validate-pdfs
```

Interactive docs available at /docs and /redoc.

AI Usage Notes

Tools Used

* ChatGPT
* GitHub Copilot

Helpful AI contributions: regex patterns, FastAPI scaffolding, Pydantic models, documentation, error messages.

Incorrect AI suggestions and fixes:

* Table extraction (raw lists vs header detection)
* Float usage for money (switched to Decimal)
* Single date format (added multiple fallback formats)
* Strict equality for totals (added tolerance)

Assumptions and Limitations

Assumptions

* Invoices follow standard layouts
* Mostly English invoices
* Text-based PDFs
* Single currency per invoice

Limitations

* No OCR
* Complex layouts may fail
* Multi-page invoice line items may be incomplete
* Limited language support
* No multi-tax support
* Basic table detection

Edge cases

* Invoices with no tables
* Unusual date formats
* Mixed currency symbols
* Merged cells
* Credit notes not supported

Future Improvements

* OCR
* ML-based extraction
* More language support
* Better table detection
* Credit note handling
* Database integration
* Webhook support
* Performance improvements

