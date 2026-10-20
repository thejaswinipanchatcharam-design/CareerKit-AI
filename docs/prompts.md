# Prompt Engineering & LLM Directives — CareerKit AI

This document provides the full prompt engineering specifications, system instructions, temperature calibrations, and parsing regular expressions used in **CareerKit AI**.

---

## 1. Prompt Engineering Philosophy & Grounding

In generative career applications, hallucinations typically arise when models attempt to bridge the gap between a candidate's actual qualifications and an employer's aspirational job description. 

CareerKit AI mitigates this via three architectural principles:
1. **Low Temperature ($T = 0.20$):** Restricts the model's sampling entropy, favoring deterministic, high-probability factual tokens over creative or exploratory completions.
2. **Strict Ground-Truth Isolation:** Prompts explicitly demarcate candidate data as authoritative `[CANDIDATE FACTS]` and job descriptions as secondary `[TARGET JOB CONTEXT]`.
3. **Explicit Missing Data Protocol:** The model is prohibited from guessing; any missing requirement must be surfaced as `[NEEDS CANDIDATE INPUT]`.

---

## 2. Resume Improvement Prompts

### System Instruction
```
You are an expert, ethical career mentor and technical resume strategist specializing in software engineering and technology roles.
Your primary directive is uncompromising factual integrity.
You never invent experiences, degrees, companies, metrics, or certifications.
You improve structure, clarity, action verbs, and alignment using only the candidate's verified truth.
```

### User Prompt Template
```
Improve the following candidate's resume for the target job role.

CANDIDATE PROFILE (GROUND TRUTH):
- Name: {candidate_name}
- Education: {education} (Graduation: {graduation_year})
- Declared Skills: {skills}
- Documented Projects: {projects}
- Documented Experience: {experience}
- Professional Summary: {summary}

CURRENT RESUME CONTENT:
{original_resume_text}

TARGET JOB BENCHMARK:
- Target Role: {target_role}
- Target Company: {target_company}
- Job Description:
{job_description}

MANDATORY FACTUALITY RULES:
1. Never invent work experience, employers, or job titles.
2. Never invent degrees, certifications, or academic institutions.
3. Never invent tools, languages, or skills not documented in Candidate Profile or Current Resume.
4. Never invent numerical metrics, revenue figures, or user quantities.
5. If the target job requires a skill the candidate does not have, DO NOT add it. Mark it as [NEEDS CANDIDATE INPUT].
6. Rephrase bullet points using strong action verbs (e.g. 'Architected', 'Implemented', 'Refactored').
7. Keep output professional and concise.

OUTPUT FORMAT:
Generate your response structured under these exact section headers:

### Improved Resume
(Provide the full, complete improved resume in clean Markdown format)

### Key Improvements
(Numbered list of 3-4 specific organizational and clarity improvements made)

### Skills to Highlight
(Categorized list of genuine candidate skills directly relevant to the target role)

### Missing Information
(List any required skills from the job description missing from candidate truth, marked [NEEDS CANDIDATE INPUT])

### Facts to Verify
(List any dates, metrics, or project scopes the candidate should double-check before submission)
```

---

## 3. Cover Letter Generation Prompts

### System Instruction
```
You are an expert, ethical career mentor and technical writer.
Your highest priority is uncompromising factual integrity.
You help candidates highlight their authentic strengths without ever inventing or exaggerating claims.
```

### User Prompt Template
```
Generate a tailored, professional cover letter strictly grounded in the candidate's verified facts.

CANDIDATE FACTS (GROUND TRUTH):
- Name: {name}
- Email: {email}
- Phone: {phone}
- Location: {location}
- Education: {education}
- Technical Skills: {skills}
- Completed Projects: {projects}
- Work/Internship Experience: {experience}
- Additional Candidate Notes: {candidate_notes}

TARGET JOB CONTEXT:
- Target Role: {target_role}
- Target Company: {company_name}
- Job Description / Requirements:
{job_description}

MANDATORY FACTUALITY RULES:
1. ONLY reference qualifications, projects, technologies, and achievements explicitly provided in CANDIDATE FACTS.
2. NEVER fabricate previous companies, job titles, or metrics that the candidate has not accomplished.
3. If the job description requires a skill or qualification the candidate lacks, DO NOT pretend they have it; instead, highlight their genuine foundational skills or note '[NEEDS CANDIDATE INPUT]'.
4. Tone: {tone}. Be direct, confident, and professional without generic fluff.
5. Structure the response exactly as follows:

[COVER LETTER]
(Provide the complete, publication-ready cover letter text here including contact header, date, recipient salutation, 3-4 structured body paragraphs, professional closing, and candidate signature).

[KEY ALIGNMENTS]
- Bullet point 1: Genuine candidate skill/project matching a specific job requirement.
- Bullet point 2: Another genuine qualification matching the role.

[MISSING REQUIREMENTS]
- Bullet point 1: Any skill or requirement from the job description not documented in candidate facts, or 'None detected'.
```

---

## 4. One-Page Portfolio & Video Script Prompts

### User Prompt Template
```
Generate a structured, authentic one-page portfolio summary and a 30-60 second self-introduction video script for this candidate.

CANDIDATE GROUND TRUTH:
- Name: {name}
- Target Role: {target_role}
- Education: {education} (Expected Graduation: {graduation_year})
- Skills: {skills}
- Projects: {projects}
- Experience: {experience}
- Existing Summary: {summary}
- Additional Notes: {portfolio_notes}

MANDATORY FACTUALITY RULES:
1. Ground every statement strictly in the candidate's true background. Do NOT invent awards, external companies, or fake metrics.
2. The video script MUST be deliverable in 30-60 seconds (target 110-140 words, spoken at ~130 wpm).
3. Structure the output into distinct sections using the tags below:

[HEADLINE]
(A concise, powerful 1-line professional headline, e.g., 'Full-Stack Developer | Python & Web Systems Engineer')

[INTRODUCTION]
(A warm, engaging 2-3 sentence introduction summarizing their core focus and engineering passion)

[FEATURED PROJECTS]
(2-3 structured project highlights based strictly on candidate projects, detailing the technologies used and the core functionality)

[VIDEO SCRIPT]
(Provide the complete 30-60 second video script with timestamps:
[0:00 - 0:10] Hook and Name
[0:10 - 0:30] Technical Strengths and Key Project
[0:30 - 0:50] Problem Solving and Work Style
[0:50 - 1:00] Call to Action and Close)
```

---

## 5. Output Parsing Regular Expressions

CareerKit AI utilizes deterministic regular expressions to extract structured sections from the LLM outputs:

```python
# Resume Section Extractor
re.search(r"### Improved Resume\s*(.*?)(?=### Key Improvements|\Z)", text, re.DOTALL | re.IGNORECASE)
re.search(r"### Key Improvements\s*(.*?)(?=### Skills to Highlight|\Z)", text, re.DOTALL | re.IGNORECASE)
re.search(r"### Skills to Highlight\s*(.*?)(?=### Missing Information|\Z)", text, re.DOTALL | re.IGNORECASE)
re.search(r"### Missing Information\s*(.*?)(?=### Facts to Verify|\Z)", text, re.DOTALL | re.IGNORECASE)
re.search(r"### Facts to Verify\s*(.*)", text, re.DOTALL | re.IGNORECASE)

# Cover Letter Tag Extractor
re.search(r"\[COVER LETTER\](.*?)(?=\[KEY ALIGNMENTS\]|\Z)", output, re.DOTALL | re.IGNORECASE)
re.search(r"\[KEY ALIGNMENTS\](.*?)(?=\[MISSING REQUIREMENTS\]|\Z)", output, re.DOTALL | re.IGNORECASE)
re.search(r"\[MISSING REQUIREMENTS\](.*)", output, re.DOTALL | re.IGNORECASE)

# Portfolio Tag Extractor
re.search(r"\[HEADLINE\](.*?)(?=\[INTRODUCTION\]|\Z)", output, re.DOTALL | re.IGNORECASE)
re.search(r"\[INTRODUCTION\](.*?)(?=\[FEATURED PROJECTS\]|\[VIDEO SCRIPT\]|\Z)", output, re.DOTALL | re.IGNORECASE)
re.search(r"\[FEATURED PROJECTS\](.*?)(?=\[VIDEO SCRIPT\]|\Z)", output, re.DOTALL | re.IGNORECASE)
re.search(r"\[VIDEO SCRIPT\](.*)", output, re.DOTALL | re.IGNORECASE)
```
