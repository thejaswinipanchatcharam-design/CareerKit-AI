"""
CareerKit AI - Database Service Layer
Manages SQLite connection lifecycle, schema initialization, parameterized queries,
data integrity with foreign keys, and activity audit logging.
"""

import sqlite3
import os
from pathlib import Path
from typing import Optional, List, Dict, Any
from config import Config


def get_db(db_path: Optional[str] = None) -> sqlite3.Connection:
    """
    Opens and configures a SQLite connection.
    Enforces foreign key constraints and dictionary-like row access.
    """
    path = db_path or Config.DATABASE_PATH
    if path != ":memory:":
        Path(path).parent.mkdir(parents=True, exist_ok=True)

    conn = sqlite3.connect(path, timeout=20.0)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn


def close_db(e=None) -> None:
    """Safe teardown handler."""
    pass


def init_db(db_path: Optional[str] = None) -> None:
    """
    Initializes the database schema if tables do not already exist.
    Preserves all existing data across normal server restarts.
    """
    conn = get_db(db_path)
    cursor = conn.cursor()

    # 1. Candidates Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS candidates (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        email TEXT,
        phone TEXT,
        location TEXT,
        education TEXT NOT NULL,
        graduation_year TEXT,
        skills TEXT NOT NULL,
        projects TEXT,
        experience TEXT,
        target_role TEXT NOT NULL,
        summary TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)

    # 2. Original Documents (Resumes uploaded or manually entered)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS original_documents (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        candidate_id INTEGER NOT NULL,
        doc_type TEXT NOT NULL DEFAULT 'resume',
        source_method TEXT NOT NULL, -- 'manual' or 'upload'
        filename TEXT,
        file_type TEXT,              -- 'pdf', 'docx', 'txt', 'manual'
        raw_text TEXT NOT NULL,
        target_job_title TEXT,
        target_company TEXT,
        job_description TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (candidate_id) REFERENCES candidates(id) ON DELETE CASCADE
    );
    """)

    # 3. Improved Documents (AI-enhanced resumes & fact-checking notes)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS improved_documents (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        original_doc_id INTEGER NOT NULL,
        candidate_id INTEGER NOT NULL,
        improved_text TEXT NOT NULL,
        key_improvements TEXT,
        skills_to_highlight TEXT,
        missing_information TEXT,
        facts_to_verify TEXT,
        status TEXT DEFAULT 'pending_review', -- 'pending_review', 'accepted', 'rejected'
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (original_doc_id) REFERENCES original_documents(id) ON DELETE CASCADE,
        FOREIGN KEY (candidate_id) REFERENCES candidates(id) ON DELETE CASCADE
    );
    """)

    # 4. Cover Letters Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS cover_letters (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        candidate_id INTEGER NOT NULL,
        target_role TEXT NOT NULL,
        company_name TEXT NOT NULL,
        job_description TEXT,
        tone TEXT DEFAULT 'professional',
        greeting TEXT,
        opening TEXT,
        qualifications TEXT,
        examples TEXT,
        closing TEXT,
        full_content TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (candidate_id) REFERENCES candidates(id) ON DELETE CASCADE
    );
    """)

    # 5. One-Page Portfolios Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS portfolios (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        candidate_id INTEGER NOT NULL,
        headline TEXT,
        introduction TEXT,
        education_section TEXT,
        skills_section TEXT,
        projects_section TEXT,
        experience_section TEXT,
        contact_section TEXT,
        video_script TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (candidate_id) REFERENCES candidates(id) ON DELETE CASCADE
    );
    """)

    # 6. Verification Records (Claims extracted and audited for truthfulness)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS verification_records (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        candidate_id INTEGER NOT NULL,
        document_type TEXT NOT NULL, -- 'resume', 'cover_letter', 'portfolio'
        claim_text TEXT NOT NULL,
        status TEXT NOT NULL,        -- 'Supported by supplied info', 'Needs candidate confirmation', 'Unsupported', 'Contradiction detected'
        reason TEXT,
        supporting_info TEXT,
        suggested_action TEXT,
        candidate_resolution TEXT DEFAULT 'pending', -- 'pending', 'confirmed', 'edited', 'removed'
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (candidate_id) REFERENCES candidates(id) ON DELETE CASCADE
    );
    """)

    # 7. Activity Logs (Audit trail for dashboard and compliance)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS activity_logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        candidate_id INTEGER,
        action TEXT NOT NULL,
        details TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (candidate_id) REFERENCES candidates(id) ON DELETE SET NULL
    );
    """)

    # Create Indexes for Query Performance
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_orig_docs_candidate ON original_documents(candidate_id);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_imp_docs_candidate ON improved_documents(candidate_id);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_cover_letters_candidate ON cover_letters(candidate_id);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_portfolios_candidate ON portfolios(candidate_id);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_verif_candidate ON verification_records(candidate_id);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_activity_logs_created ON activity_logs(created_at DESC);")

    conn.commit()
    conn.close()


def log_activity(action: str, details: Optional[str] = None, candidate_id: Optional[int] = None, db_path: Optional[str] = None) -> None:
    """Records an activity event into the audit log."""
    try:
        conn = get_db(db_path)
        with conn:
            conn.execute(
                "INSERT INTO activity_logs (candidate_id, action, details) VALUES (?, ?, ?);",
                (candidate_id, action, details)
            )
        conn.close()
    except Exception as e:
        # Logging should never crash main application flow
        print(f"[ActivityLog Error] Failed to log activity '{action}': {e}")


def get_dashboard_stats(db_path: Optional[str] = None) -> Dict[str, Any]:
    """Retrieves real-time statistics directly from database records."""
    conn = get_db(db_path)
    cursor = conn.cursor()

    total_candidates = cursor.execute("SELECT COUNT(*) FROM candidates;").fetchone()[0]
    resumes_improved = cursor.execute("SELECT COUNT(*) FROM improved_documents;").fetchone()[0]
    cover_letters_generated = cursor.execute("SELECT COUNT(*) FROM cover_letters;").fetchone()[0]
    portfolios_created = cursor.execute("SELECT COUNT(*) FROM portfolios;").fetchone()[0]
    
    claims_requiring_review = cursor.execute("""
        SELECT COUNT(*) FROM verification_records 
        WHERE status IN ('Needs candidate confirmation', 'Unsupported', 'Contradiction detected')
        AND candidate_resolution = 'pending';
    """).fetchone()[0]

    recent_activities = cursor.execute("""
        SELECT a.id, a.action, a.details, a.created_at, c.name as candidate_name
        FROM activity_logs a
        LEFT JOIN candidates c ON a.candidate_id = c.id
        ORDER BY a.created_at DESC
        LIMIT 8;
    """).fetchall()

    recent_candidates = cursor.execute("""
        SELECT id, name, target_role, education, created_at
        FROM candidates
        ORDER BY created_at DESC
        LIMIT 5;
    """).fetchall()

    conn.close()

    return {
        "total_candidates": total_candidates,
        "resumes_improved": resumes_improved,
        "cover_letters_generated": cover_letters_generated,
        "portfolios_created": portfolios_created,
        "claims_requiring_review": claims_requiring_review,
        "recent_activities": [dict(r) for r in recent_activities],
        "recent_candidates": [dict(r) for r in recent_candidates]
    }


# ==============================================================================
# CANDIDATE PROFILE CRUD FUNCTIONS (PARAMETERIZED)
# ==============================================================================

def create_candidate(data: Dict[str, Any], db_path: Optional[str] = None) -> int:
    """Inserts a new candidate profile and returns the new candidate ID."""
    conn = get_db(db_path)
    with conn:
        cursor = conn.execute("""
            INSERT INTO candidates (
                name, email, phone, location, education, graduation_year,
                skills, projects, experience, target_role, summary
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
        """, (
            data.get("name", "").strip(),
            data.get("email", "").strip() or None,
            data.get("phone", "").strip() or None,
            data.get("location", "").strip() or None,
            data.get("education", "").strip(),
            data.get("graduation_year", "").strip() or None,
            data.get("skills", "").strip(),
            data.get("projects", "").strip() or None,
            data.get("experience", "").strip() or None,
            data.get("target_role", "").strip(),
            data.get("summary", "").strip() or None
        ))
        new_id = cursor.lastrowid
    conn.close()

    log_activity(
        action="Candidate Profile Created",
        details=f"Created profile for {data.get('name')} (Target: {data.get('target_role')})",
        candidate_id=new_id,
        db_path=db_path
    )
    return new_id


def get_all_candidates(db_path: Optional[str] = None) -> List[Dict[str, Any]]:
    """Returns all candidates ordered by newest first."""
    conn = get_db(db_path)
    cursor = conn.cursor()
    rows = cursor.execute("SELECT * FROM candidates ORDER BY created_at DESC;").fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_candidate_by_id(candidate_id: int, db_path: Optional[str] = None) -> Optional[Dict[str, Any]]:
    """Returns candidate by ID or None if not found."""
    conn = get_db(db_path)
    cursor = conn.cursor()
    row = cursor.execute("SELECT * FROM candidates WHERE id = ?;", (candidate_id,)).fetchone()
    conn.close()
    return dict(row) if row else None


def update_candidate(candidate_id: int, data: Dict[str, Any], db_path: Optional[str] = None) -> bool:
    """Updates candidate profile fields with timestamp refresh."""
    conn = get_db(db_path)
    with conn:
        cursor = conn.execute("""
            UPDATE candidates SET
                name = ?,
                email = ?,
                phone = ?,
                location = ?,
                education = ?,
                graduation_year = ?,
                skills = ?,
                projects = ?,
                experience = ?,
                target_role = ?,
                summary = ?,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = ?;
        """, (
            data.get("name", "").strip(),
            data.get("email", "").strip() or None,
            data.get("phone", "").strip() or None,
            data.get("location", "").strip() or None,
            data.get("education", "").strip(),
            data.get("graduation_year", "").strip() or None,
            data.get("skills", "").strip(),
            data.get("projects", "").strip() or None,
            data.get("experience", "").strip() or None,
            data.get("target_role", "").strip(),
            data.get("summary", "").strip() or None,
            candidate_id
        ))
        success = cursor.rowcount > 0
    conn.close()

    if success:
        log_activity(
            action="Candidate Profile Updated",
            details=f"Updated details for candidate ID {candidate_id}",
            candidate_id=candidate_id,
            db_path=db_path
        )
    return success


def delete_candidate(candidate_id: int, db_path: Optional[str] = None) -> bool:
    """Deletes candidate and cascades to all linked documents and verification records."""
    candidate = get_candidate_by_id(candidate_id, db_path)
    if not candidate:
        return False

    name = candidate.get("name", "Unknown")
    conn = get_db(db_path)
    with conn:
        cursor = conn.execute("DELETE FROM candidates WHERE id = ?;", (candidate_id,))
        success = cursor.rowcount > 0
    conn.close()

    if success:
        log_activity(
            action="Candidate Profile Deleted",
            details=f"Deleted candidate profile for {name} (ID {candidate_id})",
            candidate_id=None,
            db_path=db_path
        )
    return success


def search_candidates(query: str, db_path: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    Searches candidates by name, target role, education, or skills
    using safe parameterized SQL pattern matching.
    """
    clean_query = f"%{query.strip()}%"
    conn = get_db(db_path)
    cursor = conn.cursor()
    rows = cursor.execute("""
        SELECT * FROM candidates 
        WHERE name LIKE ? OR target_role LIKE ? OR education LIKE ? OR skills LIKE ?
        ORDER BY created_at DESC;
    """, (clean_query, clean_query, clean_query, clean_query)).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_candidate_documents_summary(candidate_id: int, db_path: Optional[str] = None) -> Dict[str, Any]:
    """
    Fetches all application documents and claim audit records tied to a specific candidate.
    """
    conn = get_db(db_path)
    cursor = conn.cursor()

    orig_docs = cursor.execute(
        "SELECT * FROM original_documents WHERE candidate_id = ? ORDER BY created_at DESC;",
        (candidate_id,)
    ).fetchall()

    imp_docs = cursor.execute(
        "SELECT * FROM improved_documents WHERE candidate_id = ? ORDER BY created_at DESC;",
        (candidate_id,)
    ).fetchall()

    cover_letters = cursor.execute(
        "SELECT * FROM cover_letters WHERE candidate_id = ? ORDER BY created_at DESC;",
        (candidate_id,)
    ).fetchall()

    portfolios = cursor.execute(
        "SELECT * FROM portfolios WHERE candidate_id = ? ORDER BY created_at DESC;",
        (candidate_id,)
    ).fetchall()

    claims = cursor.execute(
        "SELECT * FROM verification_records WHERE candidate_id = ? ORDER BY created_at DESC;",
        (candidate_id,)
    ).fetchall()

    claims_list = [dict(c) for c in claims]
    claim_counts = {
        "supported": sum(1 for c in claims_list if c["status"] == "Supported by supplied info"),
        "needs_confirmation": sum(1 for c in claims_list if c["status"] == "Needs candidate confirmation"),
        "unsupported": sum(1 for c in claims_list if c["status"] == "Unsupported"),
        "contradiction": sum(1 for c in claims_list if c["status"] == "Contradiction detected"),
    }

    conn.close()

    return {
        "original_documents": [dict(d) for d in orig_docs],
        "improved_documents": [dict(d) for d in imp_docs],
        "cover_letters": [dict(l) for l in cover_letters],
        "portfolios": [dict(p) for p in portfolios],
        "claims": claims_list,
        "claim_counts": claim_counts
    }


def seed_sample_candidate(db_path: Optional[str] = None) -> int:
    """
    Seeds a realistic, fictional 3rd-year engineering student candidate profile
    for capstone live demonstration and testing.
    """
    sample_data = {
        "name": "Aarav Sharma",
        "email": "aarav.sharma.demo@example.com",
        "phone": "+91 98765 43210",
        "location": "Bengaluru, India",
        "education": "B.Tech in Computer Science and Engineering, National Institute of Technology",
        "graduation_year": "2026",
        "skills": "Python, Flask, JavaScript, SQLite, PostgreSQL, HTML5/CSS3, Git, REST APIs, Docker, Linux",
        "projects": (
            "1. Campus Placement Management System: Built a Flask-based portal with SQLite database "
            "allowing students to submit resumes and track applications; integrated automated validation for 500+ student profiles.\n"
            "2. Automated Job Match Heuristic: Python script that matches resume skills against job description "
            "keywords using TF-IDF and regex without hallucinating qualifications."
        ),
        "experience": (
            "Software Engineering Intern at CloudVibe Solutions (May 2025 - July 2025): "
            "Developed modular RESTful endpoints in Python/Flask, wrote 40+ unit tests in pytest, "
            "and optimized SQL queries reducing latency by 25%."
        ),
        "target_role": "Junior Full-Stack Engineer",
        "summary": (
            "Third-year Computer Science undergraduate with hands-on experience developing full-stack web applications "
            "in Python and Flask. Passionate about building transparent, reliable software systems with clean architecture."
        )
    }

    candidate_id = create_candidate(sample_data, db_path)
    log_activity(
        action="Sample Candidate Loaded",
        details="Loaded realistic anonymized 3rd-year engineering student profile (Aarav Sharma) for viva demo",
        candidate_id=candidate_id,
        db_path=db_path
    )
    return candidate_id


# ==============================================================================
# ORIGINAL & IMPROVED DOCUMENT PERSISTENCE (RESUME STUDIO)
# ==============================================================================

def save_original_document(data: Dict[str, Any], db_path: Optional[str] = None) -> int:
    """Saves raw/parsed resume content and target job metadata."""
    conn = get_db(db_path)
    with conn:
        cursor = conn.execute("""
            INSERT INTO original_documents (
                candidate_id, doc_type, source_method, filename, file_type,
                raw_text, target_job_title, target_company, job_description
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?);
        """, (
            data.get("candidate_id"),
            data.get("doc_type", "resume"),
            data.get("source_method", "manual"),
            data.get("filename"),
            data.get("file_type", "txt"),
            data.get("raw_text", "").strip(),
            data.get("target_job_title", "").strip() or None,
            data.get("target_company", "").strip() or None,
            data.get("job_description", "").strip() or None
        ))
        new_id = cursor.lastrowid
    conn.close()

    log_activity(
        action="Resume Ingested",
        details=f"Ingested {data.get('file_type', 'manual').upper()} resume ({data.get('source_method')})",
        candidate_id=data.get("candidate_id"),
        db_path=db_path
    )
    return new_id


def get_original_document_by_id(doc_id: int, db_path: Optional[str] = None) -> Optional[Dict[str, Any]]:
    """Retrieves an original document by its ID."""
    conn = get_db(db_path)
    cursor = conn.cursor()
    row = cursor.execute("SELECT * FROM original_documents WHERE id = ?;", (doc_id,)).fetchone()
    conn.close()
    return dict(row) if row else None


def get_original_documents_by_candidate(candidate_id: int, db_path: Optional[str] = None) -> List[Dict[str, Any]]:
    """Retrieves all original documents for a specific candidate."""
    conn = get_db(db_path)
    cursor = conn.cursor()
    rows = cursor.execute(
        "SELECT * FROM original_documents WHERE candidate_id = ? ORDER BY created_at DESC;",
        (candidate_id,)
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def save_improved_document(data: Dict[str, Any], db_path: Optional[str] = None) -> int:
    """Saves AI-improved resume text and review flags."""
    conn = get_db(db_path)
    with conn:
        cursor = conn.execute("""
            INSERT INTO improved_documents (
                original_doc_id, candidate_id, improved_text, key_improvements,
                skills_to_highlight, missing_information, facts_to_verify, status
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?);
        """, (
            data.get("original_doc_id"),
            data.get("candidate_id"),
            data.get("improved_text", "").strip(),
            data.get("key_improvements", "").strip() or None,
            data.get("skills_to_highlight", "").strip() or None,
            data.get("missing_information", "").strip() or None,
            data.get("facts_to_verify", "").strip() or None,
            data.get("status", "pending_review")
        ))
        new_id = cursor.lastrowid
    conn.close()

    log_activity(
        action="Resume Improved by AI",
        details=f"Generated improved resume version #{new_id}",
        candidate_id=data.get("candidate_id"),
        db_path=db_path
    )
    return new_id


def get_improved_document_by_id(doc_id: int, db_path: Optional[str] = None) -> Optional[Dict[str, Any]]:
    """Retrieves an improved document by its ID."""
    conn = get_db(db_path)
    cursor = conn.cursor()
    row = cursor.execute("SELECT * FROM improved_documents WHERE id = ?;", (doc_id,)).fetchone()
    conn.close()
    return dict(row) if row else None


def get_improved_documents_by_candidate(candidate_id: int, db_path: Optional[str] = None) -> List[Dict[str, Any]]:
    """Retrieves all improved documents for a specific candidate."""
    conn = get_db(db_path)
    cursor = conn.cursor()
    rows = cursor.execute(
        "SELECT * FROM improved_documents WHERE candidate_id = ? ORDER BY created_at DESC;",
        (candidate_id,)
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def update_improved_document_status(doc_id: int, status: str, db_path: Optional[str] = None) -> bool:
    """Updates candidate acceptance/rejection status of an improved document."""
    conn = get_db(db_path)
    with conn:
        cursor = conn.execute(
            "UPDATE improved_documents SET status = ? WHERE id = ?;",
            (status, doc_id)
        )
        success = cursor.rowcount > 0
    conn.close()
    return success


# ==============================================================================
# VERIFICATION RECORDS (CLAIM AUDITING)
# ==============================================================================

def save_verification_record(data: Dict[str, Any], db_path: Optional[str] = None) -> int:
    """Stores a fact-checked statement with supporting evidence and suggested action."""
    conn = get_db(db_path)
    with conn:
        cursor = conn.execute("""
            INSERT INTO verification_records (
                candidate_id, document_type, claim_text, status,
                reason, supporting_info, suggested_action, candidate_resolution
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?);
        """, (
            data.get("candidate_id"),
            data.get("document_type", "resume"),
            data.get("claim_text", "").strip(),
            data.get("status", "Needs candidate confirmation"),
            data.get("reason", "").strip() or None,
            data.get("supporting_info", "").strip() or None,
            data.get("suggested_action", "Confirm statement").strip() or None,
            data.get("candidate_resolution", "pending")
        ))
        new_id = cursor.lastrowid
    conn.close()
    return new_id


def get_verification_records_by_candidate(candidate_id: int, db_path: Optional[str] = None) -> List[Dict[str, Any]]:
    """Fetches all verification claims audited for a specific candidate."""
    conn = get_db(db_path)
    cursor = conn.cursor()
    rows = cursor.execute("""
        SELECT * FROM verification_records 
        WHERE candidate_id = ? 
        ORDER BY 
            CASE status
                WHEN 'Contradiction detected' THEN 1
                WHEN 'Unsupported' THEN 2
                WHEN 'Needs candidate confirmation' THEN 3
                ELSE 4
            END,
            created_at DESC;
    """, (candidate_id,)).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_verification_record_by_id(record_id: int, db_path: Optional[str] = None) -> Optional[Dict[str, Any]]:
    """Fetches a single verification record by ID."""
    conn = get_db(db_path)
    cursor = conn.cursor()
    row = cursor.execute("SELECT * FROM verification_records WHERE id = ?;", (record_id,)).fetchone()
    conn.close()
    return dict(row) if row else None


def update_verification_resolution(record_id: int, resolution: str, db_path: Optional[str] = None) -> bool:
    """Updates candidate resolution status ('confirmed', 'edited', 'removed')."""
    conn = get_db(db_path)
    with conn:
        cursor = conn.execute(
            "UPDATE verification_records SET candidate_resolution = ? WHERE id = ?;",
            (resolution, record_id)
        )
        success = cursor.rowcount > 0
    conn.close()

    if success:
        log_activity(
            action="Claim Resolution Updated",
            details=f"Candidate resolved audit claim #{record_id} as '{resolution}'",
            candidate_id=None,
            db_path=db_path
        )
    return success


# ==============================================================================
# COVER LETTERS PERSISTENCE
# ==============================================================================

def save_cover_letter(data: Dict[str, Any], db_path: Optional[str] = None) -> int:
    """Stores a tailored cover letter and its generation metadata."""
    conn = get_db(db_path)
    with conn:
        cursor = conn.execute("""
            INSERT INTO cover_letters (
                candidate_id, target_role, company_name, job_description,
                tone, greeting, opening, qualifications, examples, closing, full_content
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
        """, (
            data.get("candidate_id"),
            data.get("target_role", "").strip(),
            data.get("company_name", "").strip(),
            data.get("job_description", "").strip() or None,
            data.get("tone", "professional").strip(),
            data.get("greeting", "").strip() or None,
            data.get("opening", "").strip() or None,
            data.get("qualifications", "").strip() or None,
            data.get("examples", "").strip() or None,
            data.get("closing", "").strip() or None,
            data.get("full_content", "").strip()
        ))
        new_id = cursor.lastrowid
    conn.close()

    log_activity(
        action="Cover Letter Generated",
        details=f"Generated cover letter for {data.get('company_name')} ({data.get('target_role')})",
        candidate_id=data.get("candidate_id"),
        db_path=db_path
    )
    return new_id


def get_cover_letters_by_candidate(candidate_id: int, db_path: Optional[str] = None) -> List[Dict[str, Any]]:
    """Retrieves all cover letters generated for a candidate."""
    conn = get_db(db_path)
    cursor = conn.cursor()
    rows = cursor.execute(
        "SELECT * FROM cover_letters WHERE candidate_id = ? ORDER BY created_at DESC;",
        (candidate_id,)
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_cover_letter_by_id(letter_id: int, db_path: Optional[str] = None) -> Optional[Dict[str, Any]]:
    """Retrieves a single cover letter by ID."""
    conn = get_db(db_path)
    cursor = conn.cursor()
    row = cursor.execute("SELECT * FROM cover_letters WHERE id = ?;", (letter_id,)).fetchone()
    conn.close()
    return dict(row) if row else None


def update_cover_letter_content(letter_id: int, full_content: str, db_path: Optional[str] = None) -> bool:
    """Updates candidate manual edits to a cover letter."""
    conn = get_db(db_path)
    with conn:
        cursor = conn.execute(
            "UPDATE cover_letters SET full_content = ? WHERE id = ?;",
            (full_content.strip(), letter_id)
        )
        success = cursor.rowcount > 0
    conn.close()
    return success


# ==============================================================================
# PORTFOLIOS PERSISTENCE
# ==============================================================================

def save_portfolio(data: Dict[str, Any], db_path: Optional[str] = None) -> int:
    """Stores or updates a candidate's one-page portfolio and video script."""
    conn = get_db(db_path)
    candidate_id = data.get("candidate_id")
    with conn:
        existing = conn.execute(
            "SELECT id FROM portfolios WHERE candidate_id = ?;", (candidate_id,)
        ).fetchone()

        if existing:
            conn.execute("""
                UPDATE portfolios SET
                    headline = ?,
                    introduction = ?,
                    education_section = ?,
                    skills_section = ?,
                    projects_section = ?,
                    experience_section = ?,
                    contact_section = ?,
                    video_script = ?,
                    updated_at = CURRENT_TIMESTAMP
                WHERE candidate_id = ?;
            """, (
                data.get("headline", "").strip() or None,
                data.get("introduction", "").strip() or None,
                data.get("education_section", "").strip() or None,
                data.get("skills_section", "").strip() or None,
                data.get("projects_section", "").strip() or None,
                data.get("experience_section", "").strip() or None,
                data.get("contact_section", "").strip() or None,
                data.get("video_script", "").strip() or None,
                candidate_id
            ))
            new_id = existing[0]
        else:
            cursor = conn.execute("""
                INSERT INTO portfolios (
                    candidate_id, headline, introduction, education_section,
                    skills_section, projects_section, experience_section,
                    contact_section, video_script
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?);
            """, (
                candidate_id,
                data.get("headline", "").strip() or None,
                data.get("introduction", "").strip() or None,
                data.get("education_section", "").strip() or None,
                data.get("skills_section", "").strip() or None,
                data.get("projects_section", "").strip() or None,
                data.get("experience_section", "").strip() or None,
                data.get("contact_section", "").strip() or None,
                data.get("video_script", "").strip() or None
            ))
            new_id = cursor.lastrowid
    conn.close()

    log_activity(
        action="Portfolio Updated",
        details=f"Created or updated one-page portfolio and video script for candidate #{candidate_id}",
        candidate_id=candidate_id,
        db_path=db_path
    )
    return new_id


def get_portfolio_by_candidate(candidate_id: int, db_path: Optional[str] = None) -> Optional[Dict[str, Any]]:
    """Retrieves portfolio details and video script for a specific candidate."""
    conn = get_db(db_path)
    cursor = conn.cursor()
    row = cursor.execute("SELECT * FROM portfolios WHERE candidate_id = ?;", (candidate_id,)).fetchone()
    conn.close()
    return dict(row) if row else None


def get_portfolio_by_id(portfolio_id: int, db_path: Optional[str] = None) -> Optional[Dict[str, Any]]:
    """Retrieves portfolio by its primary key ID."""
    conn = get_db(db_path)
    cursor = conn.cursor()
    row = cursor.execute("SELECT * FROM portfolios WHERE id = ?;", (portfolio_id,)).fetchone()
    conn.close()
    return dict(row) if row else None




