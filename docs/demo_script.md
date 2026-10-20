# Capstone Viva Presentation & Live Demo Script — CareerKit AI

**Target Audience:** Engineering Faculty Review Board, External Examiners, Technical Mentors  
**Presenter:** 3rd-Year Computer Science Undergraduate  
**Demonstration Duration:** 8–10 Minutes  

---

## 1. Opening Hook & Problem Statement (0:00 – 1:00)

> *"Good morning, respected professors and review committee members.*
>
> *Today, I am presenting my capstone project: **CareerKit AI — AI-Powered Job Application Kit with Dual-Layer Factuality Guards**.*
>
> *We all know that millions of students and job seekers now use generative AI to write their resumes and cover letters. But there is a critical problem: **Generative AI hallucinates.** When given a job description, commercial models routinely invent previous employers, unearned degrees, and fake performance numbers like 'boosted revenue by 300%' just to match recruiter keywords.*
>
> *When an engineering candidate reaches the live technical interview, these fabricated claims fall apart, destroying the candidate's credibility and institutional reputation.*
>
> *My project asks and answers a fundamental research question:*  
> **Can AI improve a candidate's resume, cover letter, and portfolio without fabrication, exaggeration, or deceptive claims?**
>
> *Let me demonstrate how CareerKit AI solves this."*

---

## 2. The Dashboard & Architecture (1:00 – 2:00)

*(Navigate to `/` — Dashboard)*

> *"Here on the Dashboard, you see a clean, accessible interface with our purple primary accent design system. All statistics displayed here—total candidates, resumes improved, cover letters generated, and claims requiring review—are dynamically queried from our embedded SQLite database using parameterized SQL.*
>
> *The system follows a clean modular architecture: a Python 3.14 Flask backend, SQLite persistence with foreign-key cascade deletions, a unified AI layer supporting both Google Gemini and Groq, and a ReportLab/python-docx export pipeline.*
>
> *Notice our recent activity feed on the right, which maintains an audit trail of all candidate actions for compliance and transparency."*

---

## 3. Candidate Ground Truth Store (2:00 – 3:15)

*(Navigate to `/candidates` and click **"Load Demo Profile"**)*

> *"In our system, every piece of generated content is bound to what we call the **Candidate Ground Truth**. This is stored in our database and represents the applicant's verified record.*
>
> *To demonstrate, I'll click **'Load Demo Profile'**, which seeds an authentic profile of a 3rd-year engineering student: **Aarav Sharma**, studying Computer Science at NIT with verified skills in Python, Flask, SQLite, and Git, and a genuine project called the 'Campus Placement Portal'.*
>
> *The Candidate Detail Hub acts as the command center, displaying all linked original documents, improved versions, cover letters, and portfolios. From here, we transition directly into the Resume Studio."*

---

## 4. Resume Studio & Ingestion (3:15 – 4:30)

*(Navigate to `/resume`)*

> *"In the Resume Studio, we support two ingestion pathways:*
> 1. *Direct file upload of text-based PDF, Word (.docx), or plain text (.txt) files.*
> 2. *Manual text pasting with live character and word counters.*
>
> *Our ingestion pipeline operates safely in memory using `pypdf` and `python-docx`. We enforce a strict 10 MB upload guard, graceful rejection of encrypted PDFs, and an explicit OCR notice informing users that scanned image-only documents require digital text.*
>
> *Below, the candidate inputs the target role—for example, 'Junior Full-Stack Engineer'—and pastes the target company's job description. Crucially, the job description is treated as a **reference benchmark**, never as ground truth."*

---

## 5. Responsible AI Improvement & Side-by-Side Review (4:30 – 6:00)

*(Click **"Improve Resume with AI"** after showing the Privacy Consent checkbox)*

> *"Before the AI runs, notice our **Mandatory Candidate Privacy Consent Gate**. We never transmit candidate data to external models without explicit user consent.*
>
> *Once authorized, the unified AI service dispatches the request to **Google Gemini 2.5 Flash** (with Groq LLaMA 3.3 as an alternative). We enforce two critical constraints:*
> 1. *We calibrate the model at **Temperature = 0.2**, suppressing exploratory token divergence.*
> 2. *Our system prompt strictly prohibits fabricating unlisted skills. Any missing requirement from the job description is surfaced explicitly as `[NEEDS CANDIDATE INPUT]`.*
>
> *Look at our **Side-by-Side Comparison**:*
> - *The original resume and improved resume are rendered side-by-side.*
> - *Our readability engine computes transparent metrics: word count difference, average sentence length (target 12–20 words), detected sections, and a keyword match percentage.*
> - *Notice we do NOT display a fake '98% ATS Pass Guarantee'. As computer scientists, we reject deceptive marketing scores in favor of transparent keyword and readability metrics."*

---

## 6. The Claim Verification Engine (6:00 – 7:30)

*(Navigate to `/verification`)*

> *"This is the centerpiece innovation of the project: our **Deterministic Claim Verification Engine**.*
>
> *Post-generation, our algorithm scans the document text and categorizes every factual assertion into a 4-tier audit taxonomy:*
> 1. **Green (Supported by supplied info):** *The degree (B.Tech) and declared skills (Python, Flask) match the profile.*
> 2. **Yellow (Needs candidate confirmation):** *A quantitative metric like '45% query reduction' or '500+ profiles' is flagged for candidate confirmation.*
> 3. **Blue (Unsupported):** *If the text mentions an unlisted skill like Kubernetes, it is flagged as unsupported.*
> 4. **Red (Contradiction detected):** *If a model were to claim a Ph.D. or an invalid graduation date, the system immediately flags a contradiction.*
>
> *Candidates can resolve each claim directly in the UI—confirming, editing inline, or removing it—ensuring complete human-in-the-loop accountability."*

---

## 7. Tailored Cover Letter, Portfolio & Video Script (7:30 – 8:45)

*(Navigate to `/cover-letter`, then `/portfolio`)*

> *"Next, in our **Cover Letter Studio**, the candidate generates a tailored letter. It connects their true projects to the employer's needs without inventing fake past employers.*
>
> *In our **One-Page Portfolio Builder**, we synthesize their verified credentials into a single-page web presentation with categorized skill badges, project cards, and verified contact links.*
>
> *Even more exciting is our **30–60 Second Video Script**:*
> - *Undergraduates frequently freeze when asked for a self-introduction during video screenings.*
> - *We generate a timed teleprompter script (~125 words, spoken at ~130 words per minute) divided into timed cue cards: `[0:00 - 0:10]` Hook, `[0:10 - 0:30]` Technical Project, `[0:30 - 0:50]` Engineering Mindset, and `[0:50 - 1:00]` Call to Action.*
> - *Every statement is grounded in the candidate's real profile."*

---

## 8. Multi-Format Exports & Automated Testing (8:45 – 9:30)

*(Show PDF & DOCX downloads, then show pytest terminal)*

> *"Finally, we provide one-click document exports:*
> - *ATS-ready **PDFs** generated programmatically via ReportLab.*
> - *Native Microsoft Word **.docx** documents generated via `python-docx`.*
> - *All download endpoints include path-traversal security guards preventing directory traversal attacks.*
>
> *To prove the software engineering robustness of our system, we built **35 automated unit and route tests** using pytest. All 35 tests pass cleanly in under 8 seconds, verifying candidate CRUD, document parsing, claim verification, consent gates, and exports.*
>
> *Thank you, professors. I am now ready for your questions."*

---

## 9. Anticipated Faculty Questions & Precise Technical Answers

### Q1: "Why did you use SQLite instead of a production database like PostgreSQL?"
> **Answer:** *"SQLite was chosen for local-first, zero-configuration portability, ensuring the application runs out of the box on any Windows laptop without requiring third-party database daemon processes or paid cloud instances. However, we implemented strict relational integrity—enabling `PRAGMA foreign_keys = ON;`, using parameterized queries against SQL injection, and adding indexes on all candidate foreign keys. The architecture uses standard SQL and can be migrated to PostgreSQL simply by swapping the connection layer in `services/database.py`."*

### Q2: "How do you guarantee the AI won't hallucinate a fake job experience?"
> **Answer:** *"We use a dual-layer strategy. First, at the LLM layer, we isolate candidate data under `[CANDIDATE FACTS (GROUND TRUTH)]`, set temperature to a very low $0.2$, and provide negative constraints. Second, at the application layer, our post-generation Claim Verification Engine scans the output with regular expressions. If an unlisted employer or degree is mentioned, it is flagged as 'Unsupported' or 'Contradiction Detected' in the audit dashboard."*

### Q3: "What happens if there is no internet or the API quota is exhausted during the viva?"
> **Answer:** *"We engineered a resilient Offline Mock Fallback in `services/ai_service.py`. If `GEMINI_API_KEY` is missing or an API call encounters a network failure, the application automatically falls back to a structured deterministic mock response. The user interface clearly displays an 'Offline Demonstration Mode' badge, ensuring zero downtime during an academic demonstration."*

### Q4: "Why don't you offer an 'ATS Score' like 95/100?"
> **Answer:** *"Because commercial ATS systems do not have a single standard algorithm—Workday, Lever, and Greenhouse all parse differently. Any tool offering a proprietary ATS score is using an arbitrary, unscientific number. We chose the honest, ethical approach: providing explainable keyword matching percentages and readability metrics (average sentence length, word count) that directly help human reviewers."*
