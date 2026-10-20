"""
CareerKit AI - Document Parser Service
Handles safe, in-memory extraction of text from PDF, DOCX, and TXT files.
Enforces size boundaries, checks for encryption, detects unscanned image PDFs,
and provides clear OCR disclaimers.
"""

import io
import os
from typing import Tuple, Optional
from werkzeug.datastructures import FileStorage
from config import Config

# Maximum file size (10 MB in bytes)
MAX_FILE_SIZE = Config.MAX_CONTENT_LENGTH
ALLOWED_EXTENSIONS = Config.ALLOWED_EXTENSIONS


def is_allowed_file(filename: str) -> bool:
    """Verifies filename has an approved extension (.pdf, .docx, .txt)."""
    if not filename or "." not in filename:
        return False
    ext = filename.rsplit(".", 1)[1].lower()
    return ext in ALLOWED_EXTENSIONS


def extract_text_from_file(file_storage: FileStorage) -> Tuple[Optional[str], Optional[str], str]:
    """
    Safely extracts text from an uploaded file.
    
    Returns:
        (extracted_text, error_message, file_type)
    """
    if not file_storage or not file_storage.filename:
        return None, "No file provided for upload.", "unknown"

    filename = file_storage.filename.strip()
    if not is_allowed_file(filename):
        return None, f"Unsupported file type for '{filename}'. Only PDF (.pdf), Word (.docx), and plain text (.txt) files are supported.", "unsupported"

    ext = filename.rsplit(".", 1)[1].lower()

    # Read file content safely into memory
    file_bytes = file_storage.read()
    file_size = len(file_bytes)

    # 1. Check for empty files
    if file_size == 0:
        return None, f"The file '{filename}' is empty (0 bytes). Please upload a valid document.", ext

    # 2. Check for oversized files (guard against memory exhaustion)
    if file_size > MAX_FILE_SIZE:
        max_mb = MAX_FILE_SIZE // (1024 * 1024)
        return None, f"The file '{filename}' ({file_size / (1024*1024):.1f} MB) exceeds the maximum allowed upload limit of {max_mb} MB.", ext

    # Process by extension
    try:
        if ext == "txt":
            return _extract_from_txt(file_bytes, filename)
        elif ext == "docx":
            return _extract_from_docx(file_bytes, filename)
        elif ext == "pdf":
            return _extract_from_pdf(file_bytes, filename)
        else:
            return None, f"Unsupported file extension: .{ext}", ext
    except Exception as e:
        return None, f"Failed to parse '{filename}'. The file may be corrupted or malformed. (Details: {str(e)})", ext


def _extract_from_txt(file_bytes: bytes, filename: str) -> Tuple[Optional[str], Optional[str], str]:
    """Extracts text from plain text files with robust encoding fallback."""
    # Try common encodings
    for encoding in ["utf-8", "utf-8-sig", "latin-1", "cp1252"]:
        try:
            text = file_bytes.decode(encoding).strip()
            if not text:
                return None, f"The text file '{filename}' contains no readable characters.", "txt"
            return text, None, "txt"
        except UnicodeDecodeError:
            continue

    return None, f"Unable to decode text file '{filename}'. Please ensure it is saved in UTF-8 format.", "txt"


def _extract_from_docx(file_bytes: bytes, filename: str) -> Tuple[Optional[str], Optional[str], str]:
    """Extracts text paragraphs and table contents from a DOCX document."""
    try:
        from docx import Document
        doc_stream = io.BytesIO(file_bytes)
        doc = Document(doc_stream)

        extracted_lines = []

        # Extract standard paragraphs
        for para in doc.paragraphs:
            clean_text = para.text.strip()
            if clean_text:
                extracted_lines.append(clean_text)

        # Extract text embedded within tables
        for table in doc.tables:
            for row in table.rows:
                row_cells = [cell.text.strip() for cell in row.cells if cell.text.strip()]
                if row_cells:
                    extracted_lines.append(" | ".join(row_cells))

        full_text = "\n\n".join(extracted_lines).strip()

        if not full_text:
            return None, f"The Word document '{filename}' contains no readable paragraphs or table text.", "docx"

        return full_text, None, "docx"
    except Exception as e:
        return None, f"Error parsing Word document '{filename}': {str(e)}", "docx"


def _extract_from_pdf(file_bytes: bytes, filename: str) -> Tuple[Optional[str], Optional[str], str]:
    """
    Extracts text from PDF documents using pypdf.
    Identifies password encryption and detects non-extractable scanned PDFs.
    """
    try:
        from pypdf import PdfReader
        pdf_stream = io.BytesIO(file_bytes)
        reader = PdfReader(pdf_stream)

        # 1. Check for password-protected / encrypted PDFs
        if reader.is_encrypted:
            # Try decrypting with empty password
            try:
                decrypted = reader.decrypt("")
                if not decrypted:
                    return None, f"The PDF file '{filename}' is password-protected. Please remove the password before uploading.", "pdf"
            except Exception:
                return None, f"The PDF file '{filename}' is encrypted and password-protected. CareerKit AI cannot process locked documents.", "pdf"

        # 2. Extract text page by page
        page_texts = []
        for page_idx, page in enumerate(reader.pages):
            try:
                page_content = page.extract_text()
                if page_content and page_content.strip():
                    page_texts.append(page_content.strip())
            except Exception as pe:
                continue

        full_text = "\n\n".join(page_texts).strip()

        # 3. Handle scanned / image-only PDFs with explicit OCR disclaimer
        if not full_text:
            return (
                None,
                f"The PDF '{filename}' contains no digital text layers (likely a scanned image or rasterized print). "
                "CareerKit AI relies on direct text extraction for factual fidelity; scanned image OCR is not supported. "
                "Please upload a text-based PDF or paste your resume content manually.",
                "pdf"
            )

        return full_text, None, "pdf"
    except Exception as e:
        return None, f"Could not read PDF '{filename}'. File structure may be invalid or corrupted: {str(e)}", "pdf"
