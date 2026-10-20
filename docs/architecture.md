# System Architecture — CareerKit AI

## 1. Overview & Architectural Philosophy

**CareerKit AI** is architected as an explainable, factuality-constrained, and privacy-preserving job application suite. Unlike conventional black-box AI resume generators that hallucinate ungrounded achievements to "game" recruiter algorithms, CareerKit AI enforces **dual-layer factual integrity**:

1. **Pre-Generation Constraint Binding:** LLM prompts are conditioned at low temperature ($T=0.2$) with strict system instructions and isolated ground-truth candidate facts.
2. **Post-Generation Deterministic Auditing:** Document outputs are parsed by regular-expression heuristic engines that extract claims (degrees, technical skills, metrics, graduation years) and cross-reference them against verified candidate database records.

---

## 2. High-Level Modular Architecture

```
+----------------------------------------------------------------------------+
|                             Presentation Layer                             |
|       Jinja2 Templates (HTML5, Responsive CSS3, Vanilla JavaScript)        |
|  - Dashboard      - Candidate Hub      - Resume Studio    - Cover Letter   |
|  - Claim Audits   - Portfolio Builder  - Video Teleprompter- Project Report|
+----------------------------------------------------------------------------+
                                      │
                                      ▼  HTTP / CSRF Protected Form Data
+----------------------------------------------------------------------------+
|                          Application / Route Layer                         |
|                               Flask (app.py)                               |
|   - Authentication & CSRF Middleware (Flask-WTF)                           |
|   - Request Sanitization & Path Traversal Guards                           |
|   - Error Handlers (404, 500) & Activity Logging Audit Trail               |
+----------------------------------------------------------------------------+
                                      │
                                      ▼  Service Invocations
+----------------------------------------------------------------------------+
|                               Service Layer                                |
|  ├─ Resume Parser (`resume_parser.py`): pypdf, python-docx, txt safe stream|
|  ├─ AI Service (`ai_service.py`): Google Gemini / Groq / Offline Mock      |
|  ├─ Resume Service (`resume_service.py`): Low-T Factuality Improvement     |
|  ├─ Cover Letter Service (`cover_letter_service.py`): Tailored Matching   |
|  ├─ Portfolio & Script (`portfolio_service.py`): 30-60s Timed Script       |
|  ├─ Readability Engine (`readability_service.py`): Length & Keywords       |
|  ├─ Claim Verification (`verification.py`): 4-Tier Audit Taxonomy          |
|  └─ Export Service (`export_service.py`): ReportLab (PDF) & python-docx    |
+----------------------------------------------------------------------------+
                                      │
                                      ▼  Parameterized SQL (`?` Bindings)
+----------------------------------------------------------------------------+
|                              Persistence Layer                             |
|                        SQLite (`data/careerkit.db`)                        |
|   - Foreign Key Cascade Constraints (`PRAGMA foreign_keys = ON`)           |
|   - 7 Normalized Tables & Search Indexes                                   |
+----------------------------------------------------------------------------+
```

---

## 3. Database Schema & Entity Relationships

The relational persistence layer uses SQLite with strict foreign key integrity, ensuring that deleting a candidate profile automatically cascades and cleans up all associated original documents, improved versions, cover letters, portfolios, and audit records.

```
       +-----------------------+
       |       candidates      |
       +-----------------------+
       | id (PK)               |
       | name                  |<-----------------+-----------------+
       | education             |                  |                 |
       | skills                |                  |                 |
       | target_role           |                  |                 |
       +-----------------------+                  |                 |
         |         |         |                    |                 |
    1:N  |    1:N  |    1:1  |               1:N  |            1:N  |
         v         v         v                    v                 v
+------------------+  +------------------+  +-------------+  +---------------+  +---------------+
|original_documents|  |  cover_letters   |  | portfolios  |  | verification  |  | activity_logs |
+------------------+  +------------------+  +-------------+  +---------------+  +---------------+
| id (PK)          |  | id (PK)          |  | id (PK)     |  | id (PK)       |  | id (PK)       |
| candidate_id (FK)|  | candidate_id (FK)|  |candidate_id |  | candidate_id  |  | candidate_id  |
| raw_text         |  | target_role      |  | headline    |  | document_type |  | action         |
| job_description  |  | company_name     |  | video_script|  | claim_text    |  | details        |
+------------------+  | full_content     |  +-------------+  | status        |  +---------------+
         |            +------------------+                   | resolution    |
    1:N  v                                                   +---------------+
+------------------+
|improved_documents|
+------------------+
| id (PK)          |
| original_doc_id  |
| candidate_id (FK)|
| improved_text    |
| status           |
+------------------+
```

### Table Definitions:

1. **`candidates`**: Ground-truth profile store (name, email, phone, location, education, graduation year, skills, projects, experience, target role, summary).
2. **`original_documents`**: Raw ingested resumes uploaded as PDF/DOCX/TXT or entered manually, linked to target job descriptions.
3. **`improved_documents`**: AI-improved resume text, structural recommendations, missing info flags, and acceptance states (`pending_review`, `accepted`, `rejected`).
4. **`cover_letters`**: Job-tailored cover letters, company targets, tone configurations, and full editable content.
5. **`portfolios`**: One-page web portfolio sections and 30–60 second timed video introduction scripts.
6. **`verification_records`**: Extracted factual claims, audit classification (Supported, Needs Confirmation, Unsupported, Contradiction), and candidate resolutions (`confirmed`, `edited`, `removed`).
7. **`activity_logs`**: System audit trail tracking document ingestions, AI improvements, claim resolutions, and exports.

---

## 4. Security & Privacy Architecture

- **Application Default Security:** Implements CSRF protection across all HTTP POST endpoints via `flask_wtf.csrf.CSRFProtect`.
- **Zero-Storage Logging Policy:** Application logging (`logging.getLogger("CareerKitAI")`) prints request execution times, prompt token lengths, and diagnostic status without dumping candidate personal data or raw resume text.
- **In-Memory File Processing:** Uploaded resumes (PDF, DOCX, TXT) are read into memory buffers (`io.BytesIO`), validated for length (10 MB maximum), checked for encryption, and parsed without saving intermediate binary payload files to web-accessible directories.
- **Strict Path Traversal Guards:** File export endpoints (`/export/resume/<id>/<format>` and `/export/cover-letter/<id>/<format>`) validate output file paths using `os.path.abspath` and verify that the canonical destination is strictly confined to `data/exports/`.
- **Secret Isolation:** API keys (`GEMINI_API_KEY`, `GROQ_API_KEY`, `SECRET_KEY`) reside exclusively in `.env` and are never exposed to JavaScript, Jinja templates, or version control.

---

## 5. Document Generation & Export Engine

- **PDF Engine (`ReportLab`):** Builds publication-ready, ATS-compliant PDFs using `SimpleDocTemplate`, `ParagraphStyle`, and `HRFlowable`. Generates standardized font sizes (20pt title, 12pt bold section headers, 9.5pt body with 13.5pt leading) and purple brand accent styling (`#6366f1`).
- **DOCX Engine (`python-docx`):** Produces native Word documents with standardized 0.75-inch margins, formatted bullet lists, and typography in Calibri font.
