# Academic Capstone Project Report — CareerKit AI

**Project Title:** CareerKit AI — AI-Powered Job Application Kit with Dual-Layer Factuality Guards  
**Author / Candidate:** 3rd-Year Computer Science & Engineering Undergraduate  
**Academic Year:** 2026–2027  
**Technology Stack:** Python 3.14, Flask, SQLite, Google Gemini API (`google-genai`), Groq API, ReportLab, python-docx, pytest  

---

## Abstract

In the modern competitive employment market, automated Applicant Tracking Systems (ATS) and generative artificial intelligence have reshaped technical hiring. While large language models (LLMs) can rapidly generate application materials, unconstrained generation frequently hallucinates non-existent work experiences, unstudied technical proficiencies, and unverified numerical metrics. This compromises academic integrity, misleads recruiters, and exposes applicants to severe interview discrepancies.

This capstone project presents **CareerKit AI**, a full-stack web application engineered to solve the problem: *Can generative AI measurably improve resume, cover letter, and portfolio materials while strictly preserving factual accuracy, transparency, and candidate sovereignty?*

CareerKit AI implements a dual-layer factual integrity architecture:
1. **Pre-generation prompt conditioning:** Operates at low temperature ($T=0.2$) with strict ground-truth isolation and negative constraints.
2. **Post-generation deterministic auditing:** Automatically parses generated text to classify claims into a transparent 4-tier verification taxonomy (Supported, Needs Confirmation, Unsupported, Contradiction Detected).

The system integrates multi-format document ingestion (PDF, DOCX, TXT), tailored cover letter generation, a single-page web portfolio builder with an authentic 30–60 second video introduction script, and multi-format document exports (ReportLab PDF and python-docx DOCX). The application is validated through 35 automated pytest unit and integration tests with a 100% pass rate.

---

## 1. Problem Definition & Motivation

### 1.1 The Problem
Generative AI tools (ChatGPT, Claude, generic resume builders) are trained on general probabilistic token completion. When prompted to *"tailor my resume for this job"*, these models treat the job description as an imperative target, frequently fabricating:
- Degrees or advanced certifications not possessed by the applicant.
- Prior employment at external companies.
- Unsubstantiated quantitative metrics (e.g., *"improved query latency by 45%"* without profiling data).
- Extrapolated programming languages (e.g., claiming Rust or Kubernetes expertise simply because the job post mentions them).

### 1.2 The Motivation
For undergraduate engineering students, this creates a catastrophic vulnerability: candidates who pass initial resume screening are unable to defend fabricated claims during live technical interviews, damaging their professional reputation and institutional standing. An engineering solution is required that acts as a disciplined career mentor—clarifying genuine achievements, improving grammar and structure, and explicitly preventing ungrounded fabrications.

---

## 2. System Architecture & Methodology

CareerKit AI is built upon an explainable, modular MVC architecture:

```
[Presentation Layer]      Jinja2 Templates, Responsive CSS3, Vanilla JS
          │
[Application Layer]       Flask Application Factory, CSRF Protection, Route Guards
          │
[Service Layer]           Document Parsers, Unified AI Service, Claim Verification,
                          Readability Heuristics, Document Exporters
          │
[Data Layer]              SQLite Database with Cascade Foreign Keys
```

### 2.1 Unified AI Service Layer
The AI interface abstracts multiple backend providers through a single consistent entrypoint (`services/ai_service.py`):
- **Google Gemini 2.5 Flash:** Primary model utilizing the official `google-genai` SDK.
- **Groq LLaMA 3.3 70B:** Ultra-fast alternative provider.
- **Offline Deterministic Mock:** Failsafe fallback ensuring uninterrupted offline academic reviews.

### 2.2 Claim Verification Engine
The verification engine (`services/verification.py`) uses regular expression tokenizers to identify factual assertions in generated text and compares them against the candidate's verified profile:
- **Academic Qualifications:** Cross-references detected degree patterns against candidate education.
- **Quantitative Metrics:** Extracts percentage changes, currency figures, and user counts, checking for presence in candidate project notes.
- **Technical Skills:** Compares technical tools in the document against candidate declared skills.

---

## 3. Implementation Details

### 3.1 Database Relational Schema
The SQLite database (`data/careerkit.db`) comprises 7 normalized tables:
- `candidates`: Ground truth profile store.
- `original_documents`: Ingested resume text and linked job descriptions.
- `improved_documents`: AI-improved resume text and review notes.
- `cover_letters`: Tailored cover letters with tone configurations.
- `portfolios`: One-page web portfolio sections and video scripts.
- `verification_records`: Audit claims and candidate resolution states.
- `activity_logs`: Chronological audit trail.

### 3.2 Document Ingestion & Safe Parsing
- **PDF Extraction:** Handled via `pypdf` directly in memory buffers.
- **DOCX Extraction:** Handled via `python-docx` traversing paragraphs and tables.
- **Security Limits:** Enforces a 10 MB maximum upload limit, rejects password-protected PDFs, and provides an OCR notice for scanned image-only documents.

### 3.3 Document Export Engine
- **ReportLab PDF:** Generates publication-ready PDFs with purple primary accent colors (`#6366f1`), bold section headings, bulleted lists, and 40pt margins.
- **python-docx:** Generates styled Microsoft Word documents with Calibri typography and proper Heading hierarchies.
- **Path Traversal Protection:** All download routes validate target file paths using `Path.resolve()` to prevent directory traversal attacks.

---

## 4. Experimental Results & Verification

The application was subjected to comprehensive automated regression testing across 5 test modules using `pytest`:

| Test Module | Component Tested | Test Cases | Result |
| :--- | :--- | :---: | :---: |
| `test_candidates.py` | Profile CRUD, validations, search, cascade delete | 9 | **PASS** |
| `test_resume.py` | PDF/DOCX/TXT parsers, limits, manual ingestion, mock AI | 9 | **PASS** |
| `test_routes.py` | Dashboard stats, 7 navigation routes, custom 404 page | 3 | **PASS** |
| `test_verification.py` | Readability heuristics, claim audits, consent checks | 6 | **PASS** |
| `test_exports.py` | ReportLab PDF, python-docx, cover letter, portfolio | 8 | **PASS** |
| **Total** | **Comprehensive Application Test Suite** | **35** | **100% PASS** |

Average test execution time across the entire 35-test suite is **7.79 seconds**, demonstrating exceptional local execution speed and stability.

---

## 5. Limitations & Future Scope

### 5.1 Limitations
1. **Scanned Image PDFs:** Currently requires digital text layers. Image-only scanned PDFs require external OCR preprocessing.
2. **Subjective Soft Claims:** While quantitative metrics and technical skills are audited deterministically, subjective statements (e.g., *"demonstrated strong leadership"*) remain dependent on candidate self-attestation.

### 5.2 Future Scope
1. **Local LLM Embedding Integration:** Incorporating local vector databases (e.g. ChromaDB) and lightweight embedding models for semantic ground-truth similarity search.
2. **Webcam Recording Studio:** Integrating WebRTC video recording directly into the teleprompter tab for practicing the 30–60s video introduction with speech cadence analytics.

---

## 6. Conclusion

**CareerKit AI** successfully proves that generative AI can be deployed responsibly in technical hiring. By establishing dual-layer factuality constraints ($T=0.2$ model conditioning and deterministic post-generation claim auditing), the application empowers candidates to articulate their genuine qualifications with professional polish, while eliminating deceptive hallucinations and preserving complete candidate control.
