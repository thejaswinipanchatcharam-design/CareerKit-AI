# Candidate Lifecycle Workflow — CareerKit AI

This document details the complete end-to-end operational workflow of **CareerKit AI**, from candidate profile initialization to multi-format document export and viva examination demonstration.

---

## Complete Workflow Diagram

```
[Candidate Profile] ──> [Resume Ingestion] ──> [AI Improvement] ──> [Claim Verification]
 (Ground Truth)          (PDF/DOCX/TXT)         (T=0.2 Guards)       (4-Tier Audit)
                                                       │                     │
                                                       v                     v
                                                [Side-by-Side]       [Candidate Review]
                                                (Diff & Heuristics)  (Confirm/Edit/Remove)
                                                       │                     │
                                                       v                     v
[Document Exports] <── [One-Page Portfolio] <── [Cover Letter] <─────────────┘
  (PDF & DOCX)          (& Video Script)        (Tailored Match)
```

---

## Step 1: Candidate Profile Grounding (Ground Truth Store)

1. **Profile Creation:**
   - The user creates or updates a candidate profile via `/candidates/new`.
   - Required fields: Name, Target Role, Education, and Technical Skills.
   - Optional fields: Email, Phone, Location, Graduation Year, Projects, Experience, and Summary.
2. **Viva Quick-Seed Demonstration:**
   - For rapid academic demonstrations without tedious manual typing, users can click **"Load Demo Profile"** (`POST /candidates/seed-sample`).
   - Seeds an authentic 3rd-year engineering profile: *"Aarav Sharma — 3rd Year CSE Student at National Institute of Technology"*.

---

## Step 2: Resume Ingestion & Validation

1. **Ingestion Methods:**
   - **Method A (File Upload):** Accepts text-based PDF, Word (.docx), or plain text (.txt). Files are processed safely in-memory using `pypdf` and `python-docx` without writing raw binaries to disk.
   - **Method B (Manual Text Paste):** Users paste raw resume text directly into an accessible textarea with a live client-side word counter.
2. **Safety & OCR Guards:**
   - 10 MB maximum file size limit.
   - Rejects encrypted/password-protected PDFs gracefully.
   - Clearly flags scanned image-only PDFs with an informative OCR notice, advising users to paste text directly if text extraction returns 0 readable characters.
3. **Target Job Context:**
   - Candidates provide the target job title, company name, and job description. These serve as reference benchmarks for relevance alignment, but never override candidate ground truth.

---

## Step 3: Responsible Resume Improvement

1. **Mandatory Privacy Consent Gate:**
   - The candidate must explicitly check the privacy consent box prior to triggering AI improvement. If unchecked, the server rejects the request with an explanatory flash alert.
2. **Inference with Factuality Locks:**
   - Unified AI service routes the prompt to Google Gemini 2.5 Flash (or Groq LLaMA 3.3).
   - Constrained with **Temperature = 0.2** and strict negative prompts prohibiting fabricated employers, unverified metrics, or extrapolated degrees.
   - Missing job requirements are strictly demarcated as `[NEEDS CANDIDATE INPUT]`.
3. **Side-by-Side Comparison & Heuristic Metrics:**
   - Original and improved resumes are rendered side-by-side in synchronized columns.
   - Live metrics track:
     - Word count change ($\Delta$ words).
     - Average sentence length (target: 12–20 words/sentence).
     - Detected resume sections (Education, Skills, Experience, Projects).
     - Job description keyword alignment percentage with transparent matched/unmatched lists.

---

## Step 4: Claim Verification & Audit Resolution

1. **Automated Claim Extraction:**
   - Regex-based parser scans the improved text for:
     - Academic degrees (B.Tech, B.S., M.Tech, Ph.D.).
     - Graduation years and historical dates.
     - Quantified performance metrics (e.g., "25%", "$10,000", "500+ users").
     - Technical tools and programming languages.
2. **4-Tier Classification:**
   - **Supported by supplied info:** Stored in profile (Green badge).
   - **Needs candidate confirmation:** Unindexed metric requiring student verification (Yellow badge).
   - **Unsupported:** Tool or framework not listed in profile (Blue badge).
   - **Contradiction detected:** Degree or qualification conflicting with ground truth (Red badge).
3. **Interactive Candidate Resolution:**
   - Candidates can resolve claims directly in the UI:
     - **Confirm:** Verified as truthful by candidate.
     - **Edit Claim:** Inline text adjustment to align with actual experience.
     - **Remove:** Flagged for deletion from the application materials.

---

## Step 5: Tailored Cover Letter Generation

1. **Fact-Grounded Alignment:**
   - Generates a 3-4 paragraph professional cover letter targeted at a specific company and role.
   - Connects the candidate's actual projects and coursework directly to employer requirements.
   - Tone selection: Professional, Confident, or Early Career / Academic.
2. **Review & Inline Editing:**
   - Full markdown editor allows candidates to refine greetings, body paragraphs, and sign-offs before export.

---

## Step 6: One-Page Portfolio & Video Script

1. **One-Page Web Portfolio:**
   - Synthesizes candidate qualifications into a single-page responsive presentation:
     - Hero Header with candidate initials avatar.
     - Professional biography.
     - Categorized skills matrix with rounded badge pills.
     - Featured projects cards detailing architecture and technologies.
     - Academic credentials and verified contact information.
2. **30–60 Second Self-Introduction Video Script:**
   - Tuned for ~130 words per minute conversational delivery (~110–135 words).
   - Segmented into teleprompter cue cards:
     - `[0:00 - 0:10]` Hook & Name.
     - `[0:10 - 0:30]` Technical Foundation & Key Project.
     - `[0:30 - 0:50]` Problem Solving & Engineering Mindset.
     - `[0:50 - 1:00]` Call to Action & Professional Sign-off.
   - One-click "Copy Script" button for teleprompter apps.

---

## Step 7: Document Export & Viva Demonstration

1. **Multi-Format Document Export:**
   - One-click export to **PDF** (ReportLab) and **DOCX** (python-docx) for both resumes and cover letters.
   - Generates publication-ready documents with consistent purple brand accent styling.
2. **Offline Demonstration Reliability:**
   - If internet access or API quota is unavailable during an academic review, CareerKit AI automatically switches to a deterministic offline mock response, ensuring a flawless live presentation.
