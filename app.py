"""
CareerKit AI - Flask Application Entrypoint
Initializes Flask app, CSRF protection, SQLite database, custom error handlers,
and foundational routes for candidate management and dashboard analytics.
"""

import os
import re
import logging
from pathlib import Path
from flask import (
    Flask, render_template, request, redirect, url_for, flash, abort, jsonify, send_file
)
from flask_wtf.csrf import CSRFProtect, CSRFError
from werkzeug.utils import secure_filename
from config import Config
from services.database import (
    get_db, init_db, get_dashboard_stats, get_all_candidates, get_candidate_by_id,
    create_candidate, update_candidate, delete_candidate, log_activity,
    search_candidates, get_candidate_documents_summary, seed_sample_candidate,
    save_original_document, get_original_document_by_id,
    get_original_documents_by_candidate, save_improved_document,
    get_improved_document_by_id, get_improved_documents_by_candidate,
    update_improved_document_status, save_verification_record,
    get_verification_records_by_candidate, get_verification_record_by_id,
    update_verification_resolution, save_cover_letter, get_cover_letters_by_candidate,
    get_cover_letter_by_id, update_cover_letter_content, save_portfolio,
    get_portfolio_by_candidate, get_portfolio_by_id
)
from services.resume_parser import extract_text_from_file
from services.ai_service import generate_ai_response
from services.resume_service import improve_resume_content
from services.readability_service import analyze_text_readability
from services.verification import audit_and_save_document_claims
from services.cover_letter_service import generate_cover_letter
from services.portfolio_service import generate_portfolio_and_script
from services.export_service import (
    export_resume_to_pdf, export_resume_to_docx,
    export_cover_letter_to_pdf, export_cover_letter_to_docx
)

# Configure logging: Diagnostic info logged to console without private resume dumps
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("CareerKitAI")


def create_app(config_class=Config) -> Flask:
    """Application factory for CareerKit AI."""
    app = Flask(__name__)
    app.config.from_object(config_class)

    # Initialize CSRF Protection
    csrf = CSRFProtect(app)

    # Ensure csrf_token is callable in Jinja templates even if CSRF is disabled during testing
    if not app.config.get("WTF_CSRF_ENABLED", True):
        app.jinja_env.globals["csrf_token"] = lambda: ""

    # Teardown database connection at the end of each request
    @app.teardown_appcontext
    def close_database(error):
        from services.database import close_db
        close_db(error)

    # Ensure required runtime storage directories exist
    for folder in [app.config.get("UPLOAD_FOLDER"), app.config.get("EXPORT_FOLDER")]:
        if folder:
            Path(folder).mkdir(parents=True, exist_ok=True)

    # Auto-initialize SQLite database schema on startup
    with app.app_context():
        init_db(app.config.get("DATABASE_PATH"))
        logger.info(f"Database initialized at: {app.config.get('DATABASE_PATH')}")

    # Inject Provider Diagnostic Status into all Jinja templates
    @app.context_processor
    def inject_provider_info():
        return {
            "provider_info": Config.get_active_provider_info()
        }

    # ==========================================================================
    # ERROR HANDLERS
    # ==========================================================================

    @app.errorhandler(404)
    def page_not_found(e):
        return render_template("404.html", active_page=""), 404

    @app.errorhandler(500)
    def internal_server_error(e):
        logger.error(f"Internal server error: {e}", exc_info=True)
        return render_template("500.html", active_page=""), 500

    @app.errorhandler(CSRFError)
    def handle_csrf_error(e):
        logger.warning(f"CSRF validation failed: {e.description}")
        flash("Your session or security token expired. Please try submitting the form again.", "danger")
        return redirect(request.referrer or url_for("dashboard"))

    @app.errorhandler(413)
    def request_entity_too_large(e):
        flash("Uploaded file exceeds the maximum allowed limit of 10 MB.", "danger")
        return redirect(request.referrer or url_for("resume_studio"))

    # ==========================================================================
    # DASHBOARD & CORE ROUTES
    # ==========================================================================

    @app.route("/")
    def dashboard():
        """Home page: Real-time statistics, recent candidates, and activity feed."""
        stats = get_dashboard_stats(app.config.get("DATABASE_PATH"))
        return render_template("index.html", active_page="dashboard", stats=stats)

    @app.route("/candidates")
    def list_candidates():
        """Lists all registered candidate profiles with optional search/filtering."""
        query = request.args.get("q", "").strip()
        db_path = app.config.get("DATABASE_PATH")
        if query:
            candidates = search_candidates(query, db_path)
        else:
            candidates = get_all_candidates(db_path)
        return render_template("profile.html", active_page="candidates", candidates=candidates, search_query=query)

    @app.route("/candidates/seed-sample", methods=["POST"])
    def seed_sample():
        """Seeds a realistic fictional candidate profile for demonstration purposes."""
        try:
            candidate_id = seed_sample_candidate(app.config.get("DATABASE_PATH"))
            flash("Realistic sample candidate profile (Aarav Sharma - 3rd Year CSE) loaded successfully for demo!", "success")
            return redirect(url_for("view_candidate", candidate_id=candidate_id))
        except Exception as e:
            logger.error(f"Error seeding sample candidate: {e}")
            flash("Could not load sample candidate profile.", "danger")
            return redirect(url_for("list_candidates"))

    @app.route("/candidates/new", methods=["GET", "POST"])
    def new_candidate():
        """Create a new candidate profile with grounded factual information."""
        if request.method == "POST":
            name = request.form.get("name", "").strip()
            education = request.form.get("education", "").strip()
            skills = request.form.get("skills", "").strip()
            target_role = request.form.get("target_role", "").strip()

            # Backend Validation
            if not name or not education or not skills or not target_role:
                flash("Please fill in all required fields (Name, Target Role, Education, and Skills).", "warning")
                return render_template("candidate_form.html", candidate=request.form, active_page="candidates")

            candidate_data = {
                "name": name,
                "email": request.form.get("email", "").strip(),
                "phone": request.form.get("phone", "").strip(),
                "location": request.form.get("location", "").strip(),
                "education": education,
                "graduation_year": request.form.get("graduation_year", "").strip(),
                "skills": skills,
                "projects": request.form.get("projects", "").strip(),
                "experience": request.form.get("experience", "").strip(),
                "target_role": target_role,
                "summary": request.form.get("summary", "").strip()
            }

            try:
                candidate_id = create_candidate(candidate_data, app.config.get("DATABASE_PATH"))
                flash(f"Profile created successfully for {name}!", "success")
                return redirect(url_for("view_candidate", candidate_id=candidate_id))
            except Exception as e:
                logger.error(f"Error creating candidate profile: {e}")
                flash("An error occurred while saving the profile. Please try again.", "danger")
                return render_template("candidate_form.html", candidate=request.form, active_page="candidates")

        return render_template("candidate_form.html", candidate=None, active_page="candidates")

    @app.route("/candidates/<int:candidate_id>")
    def view_candidate(candidate_id: int):
        """Displays complete candidate profile and linked application materials."""
        db_path = app.config.get("DATABASE_PATH")
        candidate = get_candidate_by_id(candidate_id, db_path)
        if not candidate:
            abort(404)
        summary = get_candidate_documents_summary(candidate_id, db_path)
        return render_template("candidate_detail.html", active_page="candidates", candidate=candidate, summary=summary)

    @app.route("/candidates/<int:candidate_id>/edit", methods=["GET", "POST"])
    def edit_candidate(candidate_id: int):
        """Edits an existing candidate profile."""
        candidate = get_candidate_by_id(candidate_id, app.config.get("DATABASE_PATH"))
        if not candidate:
            abort(404)

        if request.method == "POST":
            name = request.form.get("name", "").strip()
            education = request.form.get("education", "").strip()
            skills = request.form.get("skills", "").strip()
            target_role = request.form.get("target_role", "").strip()

            if not name or not education or not skills or not target_role:
                flash("Please fill in all required fields.", "warning")
                return render_template("candidate_form.html", candidate=request.form, active_page="candidates")

            updated_data = {
                "name": name,
                "email": request.form.get("email", "").strip(),
                "phone": request.form.get("phone", "").strip(),
                "location": request.form.get("location", "").strip(),
                "education": education,
                "graduation_year": request.form.get("graduation_year", "").strip(),
                "skills": skills,
                "projects": request.form.get("projects", "").strip(),
                "experience": request.form.get("experience", "").strip(),
                "target_role": target_role,
                "summary": request.form.get("summary", "").strip()
            }

            try:
                update_candidate(candidate_id, updated_data, app.config.get("DATABASE_PATH"))
                flash(f"Profile for {name} updated successfully!", "success")
                return redirect(url_for("view_candidate", candidate_id=candidate_id))
            except Exception as e:
                logger.error(f"Error updating candidate profile #{candidate_id}: {e}")
                flash("An error occurred while updating the profile.", "danger")

        return render_template("candidate_form.html", candidate=candidate, active_page="candidates")

    @app.route("/candidates/<int:candidate_id>/delete", methods=["POST"])
    def delete_candidate_route(candidate_id: int):
        """Deletes candidate and cascades deletion to linked documents and audit claims."""
        success = delete_candidate(candidate_id, app.config.get("DATABASE_PATH"))
        if success:
            flash("Candidate profile and all associated documents were deleted.", "info")
        else:
            flash("Candidate not found or could not be deleted.", "warning")
        return redirect(url_for("list_candidates"))

    # ==========================================================================
    # NAVIGATION TABS (PHASE 1 STARTERS)
    # ==========================================================================

    @app.route("/resume")
    def resume_studio():
        """Resume Studio entrypoint: candidate selection, document history, and preview."""
        db_path = app.config.get("DATABASE_PATH")
        candidates = get_all_candidates(db_path)
        candidate_id = request.args.get("candidate_id", type=int)
        doc_id = request.args.get("doc_id", type=int)
        improved_id = request.args.get("improved_id", type=int)

        selected_candidate = None
        if candidate_id:
            selected_candidate = get_candidate_by_id(candidate_id, db_path)
        elif candidates:
            selected_candidate = candidates[0]
            candidate_id = selected_candidate["id"]

        selected_doc = None
        if doc_id:
            selected_doc = get_original_document_by_id(doc_id, db_path)

        candidate_docs = []
        improved_docs = []
        if candidate_id:
            candidate_docs = get_original_documents_by_candidate(candidate_id, db_path)
            improved_docs = get_improved_documents_by_candidate(candidate_id, db_path)

        # If no specific doc requested, select the most recent original doc
        if not selected_doc and candidate_docs:
            selected_doc = candidate_docs[0]

        selected_improved = None
        if improved_id:
            selected_improved = get_improved_document_by_id(improved_id, db_path)
        elif improved_docs:
            # Default to most recent improved version for this original doc if available
            if selected_doc:
                matching = [imp for imp in improved_docs if imp["original_doc_id"] == selected_doc["id"]]
                selected_improved = matching[0] if matching else improved_docs[0]
            else:
                selected_improved = improved_docs[0]

        # Readability & structural comparison metrics
        orig_readability = None
        imp_readability = None
        if selected_doc:
            orig_readability = analyze_text_readability(
                selected_doc["raw_text"],
                selected_doc.get("job_description") or ""
            )

        if selected_improved:
            imp_readability = analyze_text_readability(
                selected_improved["improved_text"],
                selected_doc.get("job_description") if selected_doc else ""
            )

        return render_template(
            "resume.html",
            active_page="resume",
            candidates=candidates,
            selected_candidate=selected_candidate,
            selected_doc=selected_doc,
            selected_improved=selected_improved,
            candidate_docs=candidate_docs,
            improved_docs=improved_docs,
            orig_readability=orig_readability,
            imp_readability=imp_readability
        )

    @app.route("/resume/ingest", methods=["POST"])
    def ingest_resume():
        """Ingests resume content via file upload (PDF/DOCX/TXT) or manual text entry."""
        db_path = app.config.get("DATABASE_PATH")
        candidate_id = request.form.get("candidate_id", type=int)
        if not candidate_id:
            flash("Please select a candidate profile first.", "warning")
            return redirect(url_for("resume_studio"))

        candidate = get_candidate_by_id(candidate_id, db_path)
        if not candidate:
            flash("Candidate profile not found.", "danger")
            return redirect(url_for("resume_studio"))

        input_method = request.form.get("input_method", "upload")
        raw_text = ""
        filename = None
        file_type = "txt"

        target_job_title = request.form.get("target_job_title", "").strip() or candidate.get("target_role")
        target_company = request.form.get("target_company", "").strip()
        job_description = request.form.get("job_description", "").strip()

        if input_method == "upload":
            if "resume_file" not in request.files:
                flash("No file was uploaded. Please choose a file.", "warning")
                return redirect(url_for("resume_studio", candidate_id=candidate_id))

            file = request.files["resume_file"]
            if not file or not file.filename:
                flash("No file was selected for upload.", "warning")
                return redirect(url_for("resume_studio", candidate_id=candidate_id))

            text, err, detected_type = extract_text_from_file(file)
            if err:
                flash(f"Resume upload error: {err}", "danger")
                return redirect(url_for("resume_studio", candidate_id=candidate_id))

            raw_text = text
            filename = file.filename
            file_type = detected_type
        else:
            # Manual text submission
            manual_text = request.form.get("manual_resume_text", "").strip()
            if not manual_text:
                flash("Please enter or paste your resume content.", "warning")
                return redirect(url_for("resume_studio", candidate_id=candidate_id))

            raw_text = manual_text
            filename = None
            file_type = "txt"

        # Save original document into SQLite database
        doc_id = save_original_document({
            "candidate_id": candidate_id,
            "filename": filename,
            "file_type": file_type,
            "raw_text": raw_text,
            "target_job_title": target_job_title,
            "target_company": target_company,
            "job_description": job_description
        }, db_path)

        flash("Resume document successfully ingested! You can now review or proceed to AI Improvement.", "success")
        return redirect(url_for("resume_studio", candidate_id=candidate_id, doc_id=doc_id))

    @app.route("/resume/improve", methods=["POST"])
    def improve_resume():
        """Generates AI-enhanced resume content and audits factual claims."""
        db_path = app.config.get("DATABASE_PATH")
        candidate_id = request.form.get("candidate_id", type=int)
        doc_id = request.form.get("doc_id", type=int)

        if not candidate_id or not doc_id:
            flash("Candidate and original resume document must both be selected.", "warning")
            return redirect(url_for("resume_studio"))

        candidate = get_candidate_by_id(candidate_id, db_path)
        orig_doc = get_original_document_by_id(doc_id, db_path)
        if not candidate or not orig_doc:
            flash("Specified candidate profile or original resume could not be found.", "danger")
            return redirect(url_for("resume_studio"))

        # AI Consent Verification Gate
        user_consent = request.form.get("user_consent")
        if not user_consent:
            flash("Candidate privacy consent is required before processing resume data with AI.", "warning")
            return redirect(url_for("resume_studio", candidate_id=candidate_id, doc_id=doc_id))

        target_role = request.form.get("target_job_title", "").strip() or orig_doc.get("target_job_title") or candidate.get("target_role")
        target_company = request.form.get("target_company", "").strip() or orig_doc.get("target_company") or ""
        job_description = request.form.get("job_description", "").strip() or orig_doc.get("job_description") or ""

        # Invoke factuality-locked resume improvement service
        ai_res = improve_resume_content(
            candidate=candidate,
            original_text=orig_doc["raw_text"],
            target_role=target_role,
            target_company=target_company,
            job_description=job_description
        )

        if not ai_res["success"]:
            flash(f"Resume Improvement Notice: {ai_res['error']}", "warning")
            return redirect(url_for("resume_studio", candidate_id=candidate_id, doc_id=doc_id))

        # Save improved document into database
        improved_id = save_improved_document({
            "original_doc_id": orig_doc["id"],
            "candidate_id": candidate_id,
            "improved_text": ai_res["improved_text"],
            "key_improvements": ai_res["key_improvements"],
            "skills_to_highlight": ai_res["skills_to_highlight"],
            "missing_information": ai_res["missing_information"],
            "facts_to_verify": ai_res["facts_to_verify"],
            "status": "pending_review"
        }, db_path)

        # Run automated claim verification on the improved resume text
        audit_and_save_document_claims(
            candidate=candidate,
            document_text=ai_res["improved_text"],
            document_type="resume",
            db_path=db_path
        )

        if ai_res.get("is_mock"):
            flash("AI Improvement complete (Offline Demonstration Mode). Review claims and edit below.", "info")
        else:
            flash(f"Resume improved via {ai_res.get('provider', 'AI').title()}! Claims have been extracted for audit.", "success")

        return redirect(url_for("resume_studio", candidate_id=candidate_id, doc_id=doc_id, improved_id=improved_id))

    @app.route("/resume/improve/update", methods=["POST"])
    def update_improved_resume():
        """Saves candidate manual edits or updates document acceptance status."""
        db_path = app.config.get("DATABASE_PATH")
        improved_id = request.form.get("improved_id", type=int)
        candidate_id = request.form.get("candidate_id", type=int)
        doc_id = request.form.get("doc_id", type=int)
        action_type = request.form.get("action_type", "save").strip().lower()
        improved_text = request.form.get("improved_text", "").strip()

        imp_doc = get_improved_document_by_id(improved_id, db_path)
        if not imp_doc:
            flash("Improved document not found.", "danger")
            return redirect(url_for("resume_studio"))

        conn = get_db(db_path)
        with conn:
            if action_type == "accept":
                conn.execute("UPDATE improved_documents SET status = 'accepted' WHERE id = ?;", (improved_id,))
                flash("Improved resume version accepted!", "success")
            elif action_type == "reject":
                conn.execute("UPDATE improved_documents SET status = 'rejected' WHERE id = ?;", (improved_id,))
                flash("Improved resume version rejected.", "info")
            else:
                if improved_text:
                    conn.execute(
                        "UPDATE improved_documents SET improved_text = ?, status = 'pending_review' WHERE id = ?;",
                        (improved_text, improved_id)
                    )
                    flash("Resume edits saved successfully!", "success")
        conn.close()

        return redirect(url_for("resume_studio", candidate_id=candidate_id, doc_id=doc_id, improved_id=improved_id))

    @app.route("/verification")
    def verification():
        """Claim Verification and Factuality Audit Dashboard."""
        db_path = app.config.get("DATABASE_PATH")
        candidates = get_all_candidates(db_path)
        candidate_id = request.args.get("candidate_id", type=int)
        status_filter = request.args.get("status", "").strip()

        selected_candidate = None
        if candidate_id:
            selected_candidate = get_candidate_by_id(candidate_id, db_path)
        elif candidates:
            selected_candidate = candidates[0]
            candidate_id = selected_candidate["id"]

        all_claims = []
        if candidate_id:
            all_claims = get_verification_records_by_candidate(candidate_id, db_path)

        # Calculate counts
        counts = {
            "total": len(all_claims),
            "supported": sum(1 for c in all_claims if c["status"] == "Supported by supplied info"),
            "needs_confirmation": sum(1 for c in all_claims if c["status"] == "Needs candidate confirmation"),
            "unsupported": sum(1 for c in all_claims if c["status"] == "Unsupported"),
            "contradiction": sum(1 for c in all_claims if c["status"] == "Contradiction detected"),
        }

        # Apply status filter if selected
        filtered_claims = all_claims
        if status_filter:
            filtered_claims = [c for c in all_claims if c["status"].lower() == status_filter.lower()]

        return render_template(
            "verification.html",
            active_page="verification",
            candidates=candidates,
            selected_candidate=selected_candidate,
            claims=filtered_claims,
            counts=counts,
            active_status_filter=status_filter
        )

    @app.route("/verification/<int:record_id>/resolve", methods=["POST"])
    def resolve_claim(record_id: int):
        """Allows candidate to resolve, confirm, edit, or remove an audited claim."""
        db_path = app.config.get("DATABASE_PATH")
        resolution = request.form.get("resolution", "confirmed").strip().lower()
        candidate_id = request.form.get("candidate_id", type=int)
        edited_claim = request.form.get("claim_text", "").strip()

        record = get_verification_record_by_id(record_id, db_path)
        if not record:
            flash("Verification record not found.", "warning")
            return redirect(url_for("verification", candidate_id=candidate_id))

        conn = get_db(db_path)
        with conn:
            if resolution == "edited" and edited_claim:
                conn.execute(
                    "UPDATE verification_records SET candidate_resolution = ?, claim_text = ? WHERE id = ?;",
                    (resolution, edited_claim, record_id)
                )
            else:
                conn.execute(
                    "UPDATE verification_records SET candidate_resolution = ? WHERE id = ?;",
                    (resolution, record_id)
                )
        conn.close()

        flash(f"Claim #{record_id} resolution marked as '{resolution}'.", "info")
        return redirect(url_for("verification", candidate_id=candidate_id))

    # ==========================================================================
    # COVER LETTER GENERATOR (PHASE 5)
    # ==========================================================================

    @app.route("/cover-letter")
    def cover_letter():
        """Cover Letter generator entrypoint: candidate selection, job matching, and preview."""
        db_path = app.config.get("DATABASE_PATH")
        candidates = get_all_candidates(db_path)
        candidate_id = request.args.get("candidate_id", type=int)
        letter_id = request.args.get("letter_id", type=int)

        selected_candidate = None
        if candidate_id:
            selected_candidate = get_candidate_by_id(candidate_id, db_path)
        elif candidates:
            selected_candidate = candidates[0]
            candidate_id = selected_candidate["id"]

        letters = []
        selected_letter = None
        if candidate_id:
            letters = get_cover_letters_by_candidate(candidate_id, db_path)
            if letter_id:
                selected_letter = get_cover_letter_by_id(letter_id, db_path)
            elif letters:
                selected_letter = letters[0]

        return render_template(
            "cover_letter.html",
            active_page="cover_letter",
            candidates=candidates,
            selected_candidate=selected_candidate,
            letters=letters,
            selected_letter=selected_letter
        )

    @app.route("/cover-letter/generate", methods=["POST"])
    def generate_cover_letter_route():
        """Generates targeted cover letter strictly grounded in candidate facts."""
        db_path = app.config.get("DATABASE_PATH")
        candidate_id = request.form.get("candidate_id", type=int)
        if not candidate_id:
            flash("Please select a candidate profile first.", "warning")
            return redirect(url_for("cover_letter"))

        candidate = get_candidate_by_id(candidate_id, db_path)
        if not candidate:
            flash("Candidate profile not found.", "danger")
            return redirect(url_for("cover_letter"))

        user_consent = request.form.get("user_consent")
        if not user_consent:
            flash("Candidate privacy consent is required before generating a cover letter with AI.", "warning")
            return redirect(url_for("cover_letter", candidate_id=candidate_id))

        target_role = request.form.get("target_role", "").strip() or candidate.get("target_role")
        company_name = request.form.get("company_name", "").strip() or "Hiring Organization"
        job_description = request.form.get("job_description", "").strip()
        tone = request.form.get("tone", "professional").strip()
        candidate_notes = request.form.get("candidate_notes", "").strip()

        ai_res = generate_cover_letter(
            candidate=candidate,
            target_role=target_role,
            company_name=company_name,
            job_description=job_description,
            tone=tone,
            candidate_notes=candidate_notes
        )

        if not ai_res.get("success"):
            flash(f"Cover Letter Generation Notice: {ai_res.get('error')}", "warning")
            return redirect(url_for("cover_letter", candidate_id=candidate_id))

        letter_id = save_cover_letter({
            "candidate_id": candidate_id,
            "target_role": target_role,
            "company_name": company_name,
            "job_description": job_description,
            "tone": tone,
            "full_content": ai_res["full_content"]
        }, db_path)

        # Audit generated cover letter claims against ground truth
        audit_and_save_document_claims(
            candidate=candidate,
            document_text=ai_res["full_content"],
            document_type="cover_letter",
            db_path=db_path
        )

        if ai_res.get("is_mock"):
            flash("Cover letter generated (Offline Demonstration Mode). Review and edit below.", "info")
        else:
            flash(f"Tailored cover letter for {company_name} generated successfully!", "success")

        return redirect(url_for("cover_letter", candidate_id=candidate_id, letter_id=letter_id))

    @app.route("/cover-letter/<int:letter_id>/edit", methods=["POST"])
    def edit_cover_letter_route(letter_id: int):
        """Saves candidate manual edits to an existing cover letter."""
        db_path = app.config.get("DATABASE_PATH")
        candidate_id = request.form.get("candidate_id", type=int)
        full_content = request.form.get("full_content", "").strip()

        letter = get_cover_letter_by_id(letter_id, db_path)
        if not letter:
            flash("Cover letter record not found.", "danger")
            return redirect(url_for("cover_letter"))

        if full_content:
            update_cover_letter_content(letter_id, full_content, db_path)
            flash("Cover letter edits saved successfully!", "success")

        return redirect(url_for("cover_letter", candidate_id=candidate_id, letter_id=letter_id))

    # ==========================================================================
    # PORTFOLIO BUILDER & SCRIPT GENERATOR (PHASE 5)
    # ==========================================================================

    @app.route("/portfolio")
    def portfolio():
        """One-page portfolio and 30-60s self-introduction video script builder."""
        db_path = app.config.get("DATABASE_PATH")
        candidates = get_all_candidates(db_path)
        candidate_id = request.args.get("candidate_id", type=int)

        selected_candidate = None
        if candidate_id:
            selected_candidate = get_candidate_by_id(candidate_id, db_path)
        elif candidates:
            selected_candidate = candidates[0]
            candidate_id = selected_candidate["id"]

        portfolio_data = None
        if candidate_id:
            portfolio_data = get_portfolio_by_candidate(candidate_id, db_path)

        return render_template(
            "portfolio.html",
            active_page="portfolio",
            candidates=candidates,
            selected_candidate=selected_candidate,
            portfolio=portfolio_data
        )

    @app.route("/portfolio/generate", methods=["POST"])
    def generate_portfolio_route():
        """Generates one-page portfolio layout and timed self-introduction script."""
        db_path = app.config.get("DATABASE_PATH")
        candidate_id = request.form.get("candidate_id", type=int)
        if not candidate_id:
            flash("Please select a candidate profile first.", "warning")
            return redirect(url_for("portfolio"))

        candidate = get_candidate_by_id(candidate_id, db_path)
        if not candidate:
            flash("Candidate profile not found.", "danger")
            return redirect(url_for("portfolio"))

        user_consent = request.form.get("user_consent")
        if not user_consent:
            flash("Candidate privacy consent is required before generating portfolio content with AI.", "warning")
            return redirect(url_for("portfolio", candidate_id=candidate_id))

        theme = request.form.get("theme", "clean-purple").strip()
        portfolio_notes = request.form.get("portfolio_notes", "").strip()

        ai_res = generate_portfolio_and_script(
            candidate=candidate,
            theme=theme,
            portfolio_notes=portfolio_notes
        )

        if not ai_res.get("success"):
            flash(f"Portfolio generation error: {ai_res.get('error')}", "warning")
            return redirect(url_for("portfolio", candidate_id=candidate_id))

        save_portfolio({
            "candidate_id": candidate_id,
            "headline": ai_res.get("headline"),
            "introduction": ai_res.get("introduction"),
            "education_section": ai_res.get("education_section"),
            "skills_section": ai_res.get("skills_section"),
            "projects_section": ai_res.get("projects_section"),
            "experience_section": ai_res.get("experience_section"),
            "contact_section": ai_res.get("contact_section"),
            "video_script": ai_res.get("video_script")
        }, db_path)

        if ai_res.get("is_mock"):
            flash("One-page portfolio and video script created (Offline Demonstration Mode)!", "info")
        else:
            flash("One-page portfolio and 30–60s video script generated successfully!", "success")

        return redirect(url_for("portfolio", candidate_id=candidate_id))

    @app.route("/portfolio/<int:portfolio_id>/edit", methods=["POST"])
    def edit_portfolio_route(portfolio_id: int):
        """Saves candidate manual updates to portfolio sections or video script."""
        db_path = app.config.get("DATABASE_PATH")
        candidate_id = request.form.get("candidate_id", type=int)

        portfolio_record = get_portfolio_by_id(portfolio_id, db_path)
        if not portfolio_record:
            flash("Portfolio record not found.", "danger")
            return redirect(url_for("portfolio"))

        save_portfolio({
            "candidate_id": candidate_id,
            "headline": request.form.get("headline", "").strip(),
            "introduction": request.form.get("introduction", "").strip(),
            "education_section": request.form.get("education_section", "").strip(),
            "skills_section": request.form.get("skills_section", "").strip(),
            "projects_section": request.form.get("projects_section", "").strip(),
            "experience_section": request.form.get("experience_section", "").strip(),
            "contact_section": request.form.get("contact_section", "").strip(),
            "video_script": request.form.get("video_script", "").strip()
        }, db_path)

        flash("Portfolio details and video script updated successfully!", "success")
        return redirect(url_for("portfolio", candidate_id=candidate_id))

    # ==========================================================================
    # DOCUMENT EXPORT DOWNLOADS (PDF & DOCX)
    # ==========================================================================

    @app.route("/export/resume/<int:doc_id>/<file_format>")
    def export_resume(doc_id: int, file_format: str):
        """Exports improved resume to PDF or DOCX with path traversal safeguards."""
        db_path = app.config.get("DATABASE_PATH")
        file_format = file_format.lower()
        if file_format not in ["pdf", "docx"]:
            abort(400, description="Unsupported export format. Supported formats: pdf, docx.")

        imp_doc = get_improved_document_by_id(doc_id, db_path)
        if not imp_doc:
            abort(404, description="Improved resume document not found.")

        candidate = get_candidate_by_id(imp_doc["candidate_id"], db_path)
        if not candidate:
            abort(404, description="Candidate record not found.")

        export_dir = Path(app.config.get("EXPORT_FOLDER", "data/exports")).resolve()
        export_dir.mkdir(parents=True, exist_ok=True)

        clean_name = re.sub(r"[^\w\-]", "_", candidate.get("name", "Candidate"))
        download_filename = f"{clean_name}_Improved_Resume.{file_format}"
        safe_filename = secure_filename(f"resume_{doc_id}_{clean_name}.{file_format}")
        target_path = (export_dir / safe_filename).resolve()

        # Path Traversal Guard: Ensure target path is strictly within the export folder
        if not str(target_path).startswith(str(export_dir)):
            abort(403, description="Access denied: Invalid export file destination.")

        try:
            if file_format == "pdf":
                export_resume_to_pdf(candidate, imp_doc["improved_text"], str(target_path))
                mimetype = "application/pdf"
            else:
                export_resume_to_docx(candidate, imp_doc["improved_text"], str(target_path))
                mimetype = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"

            log_activity(
                action=f"Resume Exported ({file_format.upper()})",
                details=f"Exported improved resume #{doc_id} as {file_format.upper()}",
                candidate_id=candidate["id"],
                db_path=db_path
            )

            return send_file(
                target_path,
                as_attachment=True,
                download_name=download_filename,
                mimetype=mimetype
            )
        except Exception as e:
            logger.error(f"Error generating {file_format.upper()} resume export: {e}")
            flash(f"Could not generate {file_format.upper()} export: {e}", "danger")
            return redirect(url_for("resume_studio", candidate_id=candidate["id"], improved_id=doc_id))

    @app.route("/export/cover-letter/<int:letter_id>/<file_format>")
    def export_cover_letter(letter_id: int, file_format: str):
        """Exports tailored cover letter to PDF or DOCX with path traversal safeguards."""
        db_path = app.config.get("DATABASE_PATH")
        file_format = file_format.lower()
        if file_format not in ["pdf", "docx"]:
            abort(400, description="Unsupported export format. Supported formats: pdf, docx.")

        letter = get_cover_letter_by_id(letter_id, db_path)
        if not letter:
            abort(404, description="Cover letter record not found.")

        candidate = get_candidate_by_id(letter["candidate_id"], db_path)
        if not candidate:
            abort(404, description="Candidate record not found.")

        export_dir = Path(app.config.get("EXPORT_FOLDER", "data/exports")).resolve()
        export_dir.mkdir(parents=True, exist_ok=True)

        clean_name = re.sub(r"[^\w\-]", "_", candidate.get("name", "Candidate"))
        clean_company = re.sub(r"[^\w\-]", "_", letter.get("company_name", "Company"))
        download_filename = f"{clean_name}_{clean_company}_Cover_Letter.{file_format}"
        safe_filename = secure_filename(f"coverletter_{letter_id}_{clean_name}_{clean_company}.{file_format}")
        target_path = (export_dir / safe_filename).resolve()

        if not str(target_path).startswith(str(export_dir)):
            abort(403, description="Access denied: Invalid export file destination.")

        try:
            if file_format == "pdf":
                export_cover_letter_to_pdf(
                    candidate=candidate,
                    letter_text=letter["full_content"],
                    output_path=str(target_path),
                    company=letter.get("company_name", ""),
                    target_role=letter.get("target_role", "")
                )
                mimetype = "application/pdf"
            else:
                export_cover_letter_to_docx(
                    candidate=candidate,
                    letter_text=letter["full_content"],
                    output_path=str(target_path),
                    company=letter.get("company_name", ""),
                    target_role=letter.get("target_role", "")
                )
                mimetype = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"

            log_activity(
                action=f"Cover Letter Exported ({file_format.upper()})",
                details=f"Exported cover letter #{letter_id} for {letter.get('company_name')} as {file_format.upper()}",
                candidate_id=candidate["id"],
                db_path=db_path
            )

            return send_file(
                target_path,
                as_attachment=True,
                download_name=download_filename,
                mimetype=mimetype
            )
        except Exception as e:
            logger.error(f"Error generating {file_format.upper()} cover letter export: {e}")
            flash(f"Could not generate {file_format.upper()} export: {e}", "danger")
            return redirect(url_for("cover_letter", candidate_id=candidate["id"], letter_id=letter_id))

    @app.route("/report")
    def project_report():
        """Capstone project report & ethics view."""
        return render_template("report.html", active_page="report")

    return app


# Standard WSGI Application Instance
app = create_app()

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=Config.DEBUG)
