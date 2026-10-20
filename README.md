# CareerKit AI — AI Job Application Kit

[![Python 3.14](https://img.shields.io/badge/python-3.14-blue.svg)](https://www.python.org/downloads/)
[![Flask 3.1](https://img.shields.io/badge/flask-3.1-black.svg)](https://flask.palletsprojects.com/)
[![Tests Passing](https://img.shields.io/badge/tests-35%20passed-success.svg)](https://pytest.org/)
[![AI Models](https://img.shields.io/badge/AI-Gemini%202.5%20%7C%20Groq%20LLaMA%203.3-purple.svg)](https://aistudio.google.com/)
[![License: MIT](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

An explainable, ethically grounded, full-stack web application designed for engineering candidates to create, improve, and audit job application materials while preserving **uncompromising factual integrity, candidate privacy, and human control**.

---

## 🎯 Problem Statement & Research Objective

> **Can generative AI improve a candidate's resume, cover letter, and portfolio without fabrication, exaggeration, or deceptive claims?**

Commercial AI resume generators routinely hallucinate unearned degrees, invent past employers, extrapolate unstudied programming languages, and fabricate performance metrics to "beat" automated recruiter algorithms. When applicants reach live technical interviews, these fabrications collapse.

**CareerKit AI** enforces **dual-layer factual integrity**:
1. **Pre-Generation Constraint Binding:** LLMs are conditioned at low temperature ($T = 0.2$) with strict ground-truth isolation and negative prompts prohibiting fabrication. Missing job requirements are explicitly marked `[NEEDS CANDIDATE INPUT]`.
2. **Post-Generation Deterministic Auditing:** Document outputs are parsed by regular-expression heuristic engines that extract claims and cross-reference them against verified candidate database records into a transparent **4-Tier Verification Taxonomy**.

---

## 🚀 Key Modules & Capabilities

- 📊 **Real-Time Analytics Dashboard:** Live tracking of candidates, document versions, generated letters, and pending audit claims.
- 👥 **Candidate Profile Hub:** Ground-truth profile management with full CRUD, search filtering, and a 1-click viva sample profile seeder (*"Aarav Sharma — 3rd Year CSE"*).
- 📄 **AI Resume Studio:** Dual-pathway ingestion (File upload for PDF/DOCX/TXT with 10MB limits, or manual text paste), side-by-side visual diff, and transparent readability heuristics (word count, sentence length, keyword alignment).
- 🛡️ **Claim Verification Engine:** Categorizes assertions into **Supported**, **Needs Candidate Confirmation**, **Unsupported**, and **Contradiction Detected** with inline candidate resolution tools.
- ✉️ **Tailored Cover Letter Studio:** Generates professional letters aligned strictly with verified candidate skills and target company job descriptions.
- 🌐 **One-Page Portfolio Builder:** Clean, responsive web portfolio layout featuring skills matrix badges, project cards, and verified contact links.
- 🎬 **30–60s Video Script Teleprompter:** Speech-optimized introduction script with teleprompter timing markers (`[0:00 - 0:10]` to `[0:50 - 1:00]`) and pacing metrics (~130 words/minute).
- 📥 **Document Export Engine:** One-click exports to ATS-compliant **PDFs** (via `ReportLab`) and Microsoft Word **DOCX** (via `python-docx`) with path-traversal cybersecurity guards.
- 📑 **Capstone Report & Ethics View:** Integrated academic reflection explaining the methodology, prompt design, and viva defense guide.

---

## 📁 Project Directory Structure

```
CareerKit-AI/
│
├── app.py                      # Flask application factory, routes, and error handlers
├── config.py                   # Development, testing, and production configuration
├── requirements.txt            # Explicit dependency specifications
├── .env.example                # Environment variable template
├── .gitignore                  # Git exclusions for secrets, caches, and local DBs
├── README.md                   # Comprehensive project documentation
│
├── data/
│   ├── .gitkeep
│   └── careerkit.db            # SQLite database (auto-initialized at startup)
│
├── templates/
│   ├── base.html               # Master layout with purple accent design system
│   ├── index.html              # Real-time analytics dashboard
│   ├── profile.html            # Candidate directory with live search filter
│   ├── candidate_form.html     # Accessible candidate creation & edit form
│   ├── candidate_detail.html   # Candidate Hub with linked application materials
│   ├── resume.html             # Resume Studio with side-by-side diff & metrics
│   ├── cover_letter.html       # Cover Letter Studio with history & editor
│   ├── portfolio.html          # One-page portfolio & video teleprompter script
│   ├── verification.html       # 4-tier claim audit checklist & resolution
│   ├── report.html             # Capstone academic report & ethics view
│   ├── 404.html                # Branded 404 resource not found error page
│   └── 500.html                # Safe 500 internal server error page
│
├── static/
│   ├── css/
│   │   └── style.css           # Modern light theme with purple accents (#6366f1)
│   ├── js/
│   │   └── app.js              # Word counting, flash dismissal, tab switching
│   └── assets/
│
├── services/
│   ├── __init__.py
│   ├── database.py             # SQLite layer with foreign keys & parameterized queries
│   ├── resume_parser.py        # Safe in-memory PDF/DOCX/TXT parsing & validation
│   ├── ai_service.py           # Unified Google Gemini & Groq layer with offline mock
│   ├── resume_service.py       # Factuality-locked resume improvement pipeline
│   ├── readability_service.py  # Word count, sentence length & keyword match heuristics
│   ├── verification.py         # 4-tier claim verification and auditing service
│   ├── cover_letter_service.py # Job-tailored cover letter generator
│   ├── portfolio_service.py    # One-page portfolio & 30-60s video script generator
│   └── export_service.py       # ReportLab (PDF) & python-docx (DOCX) export engine
│
├── tests/
│   ├── conftest.py             # Pytest fixtures & isolated temporary SQLite DB per test
│   ├── test_candidates.py      # Candidate CRUD & validation tests (9 tests)
│   ├── test_resume.py          # Document parsers & ingestion tests (9 tests)
│   ├── test_routes.py          # Route dispatch & error handling tests (3 tests)
│   ├── test_verification.py    # Readability heuristics & claim audit tests (6 tests)
│   └── test_exports.py         # PDF/DOCX exports, letter, portfolio tests (8 tests)
│
└── docs/
    ├── architecture.md         # System architecture, ERD, and component diagrams
    ├── workflow.md             # End-to-end candidate lifecycle workflow
    ├── prompts.md              # Full system prompts, temperature, and regexes
    ├── tool_usage.md           # Rationale for all languages and frameworks
    ├── testing_report.md       # Complete 35-test execution log & edge cases
    ├── ethical_reflection.md   # Ethical analysis on AI career tools & ATS myths
    ├── project_report.md       # Formal academic capstone project report
    └── demo_script.md          # Step-by-step viva presentation walkthrough
```

---

## 🛠️ Installation & Setup (Windows PowerShell)

Follow these exact commands to set up and run CareerKit AI locally on Windows:

### 1. Open Windows PowerShell and navigate to the project directory:
```powershell
cd "H:\My Drive\projects\capstone_project\CareerKit-AI"
```

### 2. Create and activate a Python virtual environment:
```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```
*(If PowerShell restricts script execution, run: `Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass`)*

### 3. Install project dependencies:
```powershell
pip install -r requirements.txt
```

### 4. Configure environment variables:
Copy `.env.example` to `.env`:
```powershell
Copy-Item .env.example .env
```
Open `.env` in your text editor (e.g. Visual Studio Code) and add your free Google Gemini API key:
```env
SECRET_KEY=careerkit-ai-secure-random-key-2026
AI_PROVIDER=gemini
GEMINI_API_KEY=your_gemini_api_key_here
GEMINI_MODEL=gemini-2.5-flash
```
> *Note: If you do not have an API key right now, you can leave it blank! CareerKit AI includes a built-in **Offline Demonstration Mode** that generates structured sample responses automatically.*

### 5. Launch the application:
```powershell
python app.py
```
Open your web browser and visit: **`http://127.0.0.1:5000/`**

---

## 🧪 Running Automated Tests

CareerKit AI includes a comprehensive automated test suite with **35 unit, integration, and security tests**.

Execute all tests in PowerShell:
```powershell
python -m pytest tests -v
```

Execute a specific test module:
```powershell
python -m pytest tests/test_exports.py -v
```

Expected result:
```
============================= 35 passed in 7.79s ==============================
```

---

## 🎓 Capstone Viva Demonstration Guide

For students demonstrating this project to academic faculty:

1. **Dashboard (`/`):** Point out the live database statistics and explain the SQLite foreign-key architecture.
2. **Candidate Hub (`/candidates`):** Click **"Load Demo Profile"** to load *"Aarav Sharma — 3rd Year CSE Student"*. Explain that all AI outputs are strictly bound to this ground truth.
3. **Resume Studio (`/resume`):** Show multi-format upload or text paste. Highlight the **Mandatory Privacy Consent Gate**, the **Temperature = 0.2** constraint, and the **Side-by-Side Comparison** with transparent readability metrics.
4. **Claim Auditing (`/verification`):** Show how the 4-tier taxonomy flags unverified claims and allows the candidate to confirm, edit, or remove them.
5. **Cover Letter & Portfolio (`/cover-letter`, `/portfolio`):** Display the job-tailored letter and the **30–60s Video Script Teleprompter**.
6. **Exports:** Click **"Export PDF"** and **"Export DOCX"** to show instant, formatted downloads.
7. **Report (`/report`):** Present the integrated academic research report, prompt designs, and ethical reflection.

Refer to **[`docs/demo_script.md`](docs/demo_script.md)** for the full word-for-word viva presentation script and answers to faculty questions.

---

## ⚖️ Ethical Commitments & Disclaimers

- **Zero Hallucination Tolerance:** The system will never invent employers, degrees, metrics, or certifications.
- **No ATS Guarantees:** CareerKit AI does not claim proprietary "ATS scores" or guarantee job interviews. It provides honest, explainable heuristics.
- **Candidate Ownership:** All candidate data is stored locally. Users retain 100% control to review, edit, accept, or delete any generated material.

---

## 📄 License

This project is licensed under the MIT License — open-source, free-tier accessible, and educational.
#   C a r e e r K i t - A I  
 