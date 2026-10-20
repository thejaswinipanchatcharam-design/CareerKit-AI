# Automated Testing Report & Quality Assurance — CareerKit AI

This document provides the full test plan, execution log, coverage analysis, and edge-case validation for **CareerKit AI**.

---

## 1. Test Architecture & Isolation Strategy

CareerKit AI utilizes `pytest` with a dedicated fixture architecture in `tests/conftest.py`:
- **Isolated SQLite Storage:** Rather than running in-memory databases (`:memory:`) which discard state between multi-connection HTTP transactions, each test run instantiates an isolated temporary disk file using `tempfile.mkstemp(suffix=".db")`.
- **Automatic Schema Initialization:** Each test runs `init_db(db_path)` to establish foreign keys and tables.
- **Teardown Cleanup:** Upon test completion, `os.remove(db_path)` purges the temporary database file, preventing cross-test pollution.
- **Mock Fallback Verification:** Automated tests execute without requiring live external internet connections or paid API keys by evaluating deterministic mock provider behaviors.

---

## 2. Test Execution Summary

```
============================= test session starts =============================
platform win32 -- Python 3.14.2, pytest-9.1.1, pluggy-1.6.0
rootdir: H:\My Drive\projects\capstone_project\CareerKit-AI
plugins: anyio-4.14.2
collected 35 items

tests/test_candidates.py::test_create_candidate_success PASSED           [  2%]
tests/test_candidates.py::test_create_candidate_missing_required_fields PASSED [  5%]
tests/test_candidates.py::test_view_candidate_detail PASSED              [  8%]
tests/test_candidates.py::test_view_nonexistent_candidate_returns_404 PASSED [ 11%]
tests/test_candidates.py::test_edit_candidate PASSED                     [ 14%]
tests/test_candidates.py::test_delete_candidate PASSED                   [ 17%]
tests/test_candidates.py::test_search_candidates PASSED                  [ 20%]
tests/test_candidates.py::test_seed_sample_candidate_route PASSED        [ 22%]
tests/test_candidates.py::test_candidate_documents_summary_service PASSED [ 25%]
tests/test_exports.py::test_pdf_export_generation PASSED                 [ 28%]
tests/test_exports.py::test_docx_export_generation PASSED                [ 31%]
tests/test_exports.py::test_cover_letter_service_generation PASSED       [ 34%]
tests/test_exports.py::test_portfolio_and_script_service PASSED          [ 37%]
tests/test_exports.py::test_cover_letter_routes_and_consent PASSED       [ 40%]
tests/test_exports.py::test_portfolio_routes_and_consent PASSED          [ 42%]
tests/test_exports.py::test_export_download_routes PASSED                [ 45%]
tests/test_exports.py::test_export_security_format_validation PASSED     [ 48%]
tests/test_resume.py::test_is_allowed_file PASSED                        [ 51%]
tests/test_resume.py::test_txt_parsing PASSED                            [ 54%]
tests/test_resume.py::test_docx_parsing PASSED                           [ 57%]
tests/test_resume.py::test_pdf_parsing PASSED                            [ 60%]
tests/test_resume.py::test_empty_file_rejected PASSED                    [ 62%]
tests/test_resume.py::test_unsupported_file_rejected PASSED              [ 65%]
tests/test_resume.py::test_manual_resume_ingest_route PASSED             [ 68%]
tests/test_resume.py::test_file_upload_resume_ingest_route PASSED        [ 71%]
tests/test_resume.py::test_ai_service_unified_interface PASSED           [ 74%]
tests/test_routes.py::test_dashboard_route PASSED                        [ 77%]
tests/test_routes.py::test_navigation_routes PASSED                      [ 80%]
tests/test_routes.py::test_404_error_page PASSED                         [ 82%]
tests/test_verification.py::test_readability_metrics PASSED              [ 85%]
tests/test_verification.py::test_claim_verification_supported_vs_contradiction PASSED [ 88%]
tests/test_verification.py::test_claim_verification_unsupported_skills PASSED [ 91%]
tests/test_verification.py::test_resume_improve_route_with_consent PASSED [ 94%]
tests/test_verification.py::test_claim_resolution_workflow PASSED        [ 97%]
tests/test_verification.py::test_update_improved_resume_edits PASSED     [100%]

============================= 35 passed in 7.79s ==============================
```

---

## 3. Detailed Module Breakdown

### 1. `tests/test_candidates.py` (9 Tests)
- **`test_create_candidate_success`**: Validates candidate profile creation with all required and optional attributes.
- **`test_create_candidate_missing_required_fields`**: Confirms that submitting forms with missing required fields (Name, Target Role, Education, Skills) triggers validation warnings.
- **`test_view_candidate_detail`**: Verifies retrieval and rendering of candidate details in the Candidate Hub.
- **`test_view_nonexistent_candidate_returns_404`**: Verifies that requesting invalid candidate IDs aborts with HTTP 404.
- **`test_edit_candidate`**: Validates updating existing profile attributes with instant SQLite persistence.
- **`test_delete_candidate`**: Confirms profile deletion and verifies that linked foreign-key records cascade properly.
- **`test_search_candidates`**: Tests the search filter against candidate names, skills, and target roles.
- **`test_seed_sample_candidate_route`**: Validates the 1-click viva sample profile seeder ("Aarav Sharma").
- **`test_candidate_documents_summary_service`**: Verifies document counts aggregated across resumes, cover letters, and portfolios.

### 2. `tests/test_resume.py` (9 Tests)
- **`test_is_allowed_file`**: Validates allowed extensions (`.pdf`, `.docx`, `.txt`) and rejection of unapproved extensions (`.py`, `.exe`, `.png`).
- **`test_txt_parsing`**: Verifies UTF-8 text extraction from plain text documents.
- **`test_docx_parsing`**: Generates in-memory Word documents with tables and paragraphs to test `python-docx` extraction.
- **`test_pdf_parsing`**: Generates in-memory text-based PDFs via ReportLab and validates extraction via `pypdf`.
- **`test_empty_file_rejected`**: Ensures 0-byte uploaded files are caught and rejected gracefully.
- **`test_unsupported_file_rejected`**: Confirms malicious binaries (`payload.exe`) are rejected before parsing.
- **`test_manual_resume_ingest_route`**: Tests manual text paste ingestion.
- **`test_file_upload_resume_ingest_route`**: Tests multipart file upload ingestion.
- **`test_ai_service_unified_interface`**: Verifies empty prompt rejection and structured mock generation fallback.

### 3. `tests/test_routes.py` (3 Tests)
- **`test_dashboard_route`**: Validates HTTP 200 and real-time statistics rendering on the dashboard.
- **`test_navigation_routes`**: Asserts that all 7 primary sidebar links load successfully without broken routes.
- **`test_404_error_page`**: Confirms invalid URLs render the custom branded 404 template.

### 4. `tests/test_verification.py` (6 Tests)
- **`test_readability_metrics`**: Validates word count, sentence length, section detection, and keyword matching algorithms.
- **`test_claim_verification_supported_vs_contradiction`**: Verifies matching degrees (B.Tech) are classified as Supported and conflicting degrees (Ph.D.) trigger Contradiction Detected.
- **`test_claim_verification_unsupported_skills`**: Verifies that unlisted technical skills (Rust, Kubernetes) are flagged as Unsupported.
- **`test_resume_improve_route_with_consent`**: Validates the privacy consent gate; asserts requests without consent are rejected.
- **`test_claim_resolution_workflow`**: Tests candidate resolution of audited claims (`confirmed`, `edited`, `removed`).
- **`test_update_improved_resume_edits`**: Tests candidate manual editing and version acceptance (`accepted`, `rejected`).

### 5. `tests/test_exports.py` (8 Tests)
- **`test_pdf_export_generation`**: Asserts ReportLab generates valid PDFs starting with binary magic bytes `%PDF`.
- **`test_docx_export_generation`**: Asserts python-docx generates openable `.docx` files containing candidate text.
- **`test_cover_letter_service_generation`**: Validates tailored cover letter generation and structured key alignments.
- **`test_portfolio_and_script_service`**: Validates one-page portfolio data and 30-60s video script timing metrics.
- **`test_cover_letter_routes_and_consent`**: Tests cover letter web workflow, consent check, and manual editing.
- **`test_portfolio_routes_and_consent`**: Tests portfolio generation with consent and manual section updating.
- **`test_export_download_routes`**: Validates HTTP 200, Content-Type headers, and attachment downloads for PDF and DOCX.
- **`test_export_security_format_validation`**: Asserts unsupported export formats (e.g. `.exe`) return HTTP 400.

---

## 4. How to Execute Tests

Execute the entire test suite in PowerShell:
```powershell
python -m pytest tests -v
```

Execute a specific test module:
```powershell
python -m pytest tests/test_verification.py -v
```
