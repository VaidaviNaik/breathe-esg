# Tradeoffs — Three Things Deliberately Not Built

## 1. Authentication / Multi-user login
Not built. Would need JWT/OAuth, user roles (analyst vs auditor), and per-user audit trails. For a prototype reviewed internally, the overhead wasn't worth it. In production: Django REST + SimpleJWT, with roles controlling who can approve vs view-only.

## 2. Emission Factor Management UI
Hardcoded emission factors (IPCC/DEFRA/CEA values) rather than building a DB-backed factor library. A real system needs versioned factors, source citations, and the ability to update without code changes. Skipped because the model design already accommodates it (co2e_kg is computed at ingestion, could be recomputed).

## 3. PDF Bill Parsing for Utility Data
Utility bills as PDFs are the most realistic source but require OCR + layout parsing (pdfplumber/tesseract). Chose CSV portal export instead. A real deployment would need this. The ingestion pipeline is structured to add a new parser without changing the core model.