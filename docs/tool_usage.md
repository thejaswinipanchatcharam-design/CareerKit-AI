# Technology Stack & Tool Usage — CareerKit AI

This document provides a comprehensive justification and analysis of every tool, programming language, library, and framework employed in **CareerKit AI**.

---

## 1. Core Runtime & Backend

### Python 3.14
- **Purpose:** Primary application programming language.
- **Justification:** Python provides premier ecosystem support for text processing, regular expressions, document manipulation, and AI provider client SDKs. Its clean syntax enables 3rd-year engineering students to articulate and defend backend logic during technical viva reviews.

### Flask 3.1.2
- **Purpose:** Web framework and HTTP routing layer.
- **Justification:** Unlike heavy frameworks (e.g. Django) with extensive ORM abstractions and hidden administrative middleware, Flask provides transparent request dispatching, lightweight application factories (`create_app`), and explicit session handling. This makes every database transaction and route flow immediately explainable.

### Flask-WTF 1.2.2
- **Purpose:** Cross-Site Request Forgery (CSRF) protection.
- **Justification:** Protects application state-changing POST endpoints (document ingestions, profile deletions, AI triggers, claim resolutions) against CSRF attacks using encrypted tokens embedded in Jinja templates.

### python-dotenv 1.0.1
- **Purpose:** Environment variable management and secrets isolation.
- **Justification:** Keeps sensitive API keys (`GEMINI_API_KEY`, `GROQ_API_KEY`) and cryptographic session keys (`SECRET_KEY`) strictly outside source code and Git repositories.

---

## 2. Persistence Layer

### SQLite (Built-in `sqlite3`)
- **Purpose:** Relational database storage (`data/careerkit.db`).
- **Justification:**
  - **Zero Configuration:** Runs embedded directly on Windows/Linux without requiring external database server processes (e.g., PostgreSQL, MySQL).
  - **Relational Integrity:** Supports Foreign Key Cascade Deletions (`PRAGMA foreign_keys = ON;`), ensuring transactional cleanup of linked documents.
  - **Parameterized SQL:** Uses `?` query parameterization throughout `services/database.py` to prevent SQL Injection vulnerabilities.

---

## 3. Artificial Intelligence Services

### Google Gemini API via official `google-genai` SDK (v1.65.0)
- **Purpose:** Primary generative AI provider.
- **Model:** `gemini-2.5-flash`
- **Justification:** The official modern `google-genai` SDK replaces the legacy `google-generativeai` package. `gemini-2.5-flash` offers state-of-the-art semantic reasoning, high rate limits on the free tier, low token latency, and strong adherence to system instructions.

### Groq API via `groq` SDK (v1.0.0)
- **Purpose:** Configurable alternative high-speed LLM provider.
- **Model:** `llama-3.3-70b-versatile`
- **Justification:** Offers open-weights LLaMA model execution with near-instant inference speeds (300+ tokens/sec) on LPUs, providing architectural provider redundancy.

### Offline Deterministic Mock Provider
- **Purpose:** Local viva and offline demonstration reliability.
- **Justification:** Hardened fallback that activates automatically when API keys are absent or when internet access fails during an academic review, guaranteeing an uninterrupted live demonstration.

---

## 4. Multi-Format Document Processing

### `pypdf` (v5.3.0)
- **Purpose:** Text extraction from PDF resumes.
- **Justification:** Pure Python implementation that operates entirely in memory without requiring external C libraries (like Poppler or Tesseract). Gracefully detects encrypted documents and 0-byte streams.

### `python-docx` (v1.1.2)
- **Purpose:** DOCX resume ingestion and DOCX export generation.
- **Justification:** Direct XML-level manipulation of Microsoft Word packages. Parses both paragraphs and complex multi-column tables, and generates formatted Word documents with custom headings, margins, and typography.

### `ReportLab` (v4.4.10)
- **Purpose:** Programmatic PDF generation for resumes and cover letters.
- **Justification:** The definitive industry standard for Python PDF authoring. Uses flowable elements (`Paragraph`, `Spacer`, `HRFlowable`) and custom stylesheets to render publication-ready, ATS-compliant PDFs with exact purple brand styling (`#6366f1`).

---

## 5. Frontend & UI Design System

### HTML5 & Accessible Controls
- **Purpose:** Semantic document structure with accessible ARIA tags, labels, and keyboard navigability.

### Custom CSS3 (`static/css/style.css`)
- **Purpose:** Modern, lightweight responsive design system.
- **Theme:** Professional light theme with soft slate backgrounds (`#f8fafc`), white card surfaces, dark readable typography (`#1e293b`), and purple accent styling (`#6366f1`).
- **No Heavy CSS Frameworks:** Avoided bloated external dependencies (Bootstrap, Tailwind build steps) to ensure instantaneous loading and straightforward source inspection.

### Vanilla JavaScript (`static/js/app.js`)
- **Purpose:** Client-side interactivity.
- **Features:** Live word/character counting, automatic flash notification dismissal, tab switching, and one-click clipboard copying.

---

## 6. Testing & Quality Assurance

### `pytest` (v9.1.1)
- **Purpose:** Automated unit, route, and integration testing.
- **Justification:** Executes 35 automated tests in under 8 seconds. Leverages pytest fixtures (`tests/conftest.py`) to instantiate ephemeral temporary SQLite database files per test run, ensuring test isolation.
