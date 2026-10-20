"""
CareerKit AI - Readability & Heuristic Text Analysis Service
Calculates transparent text metrics: word count, sentence length,
detected resume sections, keyword alignment with job descriptions,
and overused vocabulary. Transparent formulas; no fake 'ATS scores'.
"""

import re
from typing import Dict, Any, List, Set


# Common standard resume section headings
STANDARD_SECTIONS = [
    "education",
    "experience",
    "work experience",
    "projects",
    "technical skills",
    "skills",
    "summary",
    "professional summary",
    "certifications",
    "publications",
    "achievements",
    "contact"
]

# Common English stop words to filter out when analyzing keywords
STOP_WORDS = {
    "a", "about", "above", "after", "again", "against", "all", "am", "an", "and",
    "any", "are", "aren't", "as", "at", "be", "because", "been", "before", "being",
    "below", "between", "both", "but", "by", "can", "cannot", "could", "couldn't",
    "did", "didn't", "do", "does", "doesn't", "doing", "don't", "down", "during",
    "each", "few", "for", "from", "further", "had", "hadn't", "has", "hasn't",
    "have", "haven't", "having", "he", "he'd", "he'll", "he's", "her", "here",
    "here's", "hers", "herself", "him", "himself", "his", "how", "how's", "i",
    "i'd", "i'll", "i'm", "i've", "if", "in", "into", "is", "isn't", "it", "it's",
    "its", "itself", "let's", "me", "more", "most", "mustn't", "my", "myself",
    "no", "nor", "not", "of", "off", "on", "once", "only", "or", "other", "ought",
    "our", "ours", "ourselves", "out", "over", "own", "same", "shan't", "she",
    "she'd", "she'll", "she's", "should", "shouldn't", "so", "some", "such",
    "than", "that", "that's", "the", "their", "theirs", "them", "themselves",
    "then", "there", "there's", "these", "they", "they'd", "they'll", "they're",
    "they've", "this", "those", "through", "to", "too", "under", "until", "up",
    "very", "was", "wasn't", "we", "we'd", "we'll", "we're", "we've", "were",
    "weren't", "what", "what's", "when", "when's", "where", "where's", "which",
    "while", "who", "who's", "whom", "why", "why's", "with", "won't", "would",
    "wouldn't", "you", "you'd", "you'll", "you're", "you've", "your", "yours",
    "yourself", "yourselves"
}


def analyze_text_readability(text: str, job_description: str = "") -> Dict[str, Any]:
    """
    Computes transparent structural and readability metrics for a resume.
    
    Returns:
        Dict with metrics, sections detected, long sentences, and keyword match analysis.
    """
    if not text or not text.strip():
        return {
            "word_count": 0,
            "char_count": 0,
            "sentence_count": 0,
            "avg_sentence_length": 0.0,
            "long_sentences": [],
            "detected_sections": [],
            "missing_sections": ["Education", "Experience", "Skills", "Projects"],
            "matched_keywords": [],
            "missing_keywords": [],
            "keyword_match_percentage": 0.0,
            "repeated_words": []
        }

    clean_text = text.strip()
    words = re.findall(r"\b[A-Za-z0-9+#.-]+\b", clean_text)
    word_count = len(words)
    char_count = len(clean_text)

    # Split into sentences using punctuation (. ! ?)
    raw_sentences = re.split(r"[.!?]+(?:\s+|\n+)", clean_text)
    sentences = [s.strip() for s in raw_sentences if len(s.strip()) > 3]
    sentence_count = len(sentences)

    # Identify long sentences (> 25 words) that can hurt visual scanning
    long_sentences = []
    total_sentence_words = 0
    for s in sentences:
        s_words = len(s.split())
        total_sentence_words += s_words
        if s_words > 25:
            long_sentences.append({
                "sentence": s[:120] + "..." if len(s) > 120 else s,
                "word_count": s_words
            })

    avg_sentence_length = round(total_sentence_words / max(sentence_count, 1), 1)

    # Section detection
    lower_text = clean_text.lower()
    detected_sections = set()
    for sec in STANDARD_SECTIONS:
        # Match section as a standalone line or header, allowing optional leading whitespace and markdown hashes
        if re.search(rf"(?:^|\n)\s*#*\s*{re.escape(sec)}\b", lower_text):
            title_sec = sec.title()
            detected_sections.add(title_sec)
            if "skills" in sec:
                detected_sections.add("Skills")
            if "experience" in sec:
                detected_sections.add("Experience")

    detected_sections_list = sorted(list(detected_sections))

    # Check for core missing sections
    core_sections = ["Education", "Experience", "Skills", "Projects"]
    missing_sections = [
        cs for cs in core_sections
        if not any(cs.lower() in ds.lower() for ds in detected_sections_list)
    ]

    # Repeated words analysis (excluding common stop words)
    word_freq = {}
    for w in words:
        wl = w.lower()
        if len(wl) > 3 and wl not in STOP_WORDS:
            word_freq[wl] = word_freq.get(wl, 0) + 1

    repeated_words = [
        {"word": w, "count": count}
        for w, count in sorted(word_freq.items(), key=lambda item: item[1], reverse=True)
        if count >= 4
    ][:8]

    # Keyword alignment against target job description
    matched_keywords = []
    missing_keywords = []
    keyword_match_percentage = 0.0

    if job_description and job_description.strip():
        jd_words = re.findall(r"\b[A-Za-z0-9+#.-]+\b", job_description.lower())
        jd_keywords = set(w for w in jd_words if len(w) > 3 and w not in STOP_WORDS)
        resume_words_set = set(w.lower() for w in words)

        matched_keywords = sorted(list(jd_keywords.intersection(resume_words_set)))
        missing_keywords = sorted(list(jd_keywords.difference(resume_words_set)))[:12]

        if jd_keywords:
            keyword_match_percentage = round((len(matched_keywords) / len(jd_keywords)) * 100, 1)

    return {
        "word_count": word_count,
        "char_count": char_count,
        "sentence_count": sentence_count,
        "avg_sentence_length": avg_sentence_length,
        "long_sentences": long_sentences[:5],
        "detected_sections": detected_sections_list,
        "missing_sections": missing_sections,
        "matched_keywords": matched_keywords[:12],
        "missing_keywords": missing_keywords,
        "keyword_match_percentage": keyword_match_percentage,
        "repeated_words": repeated_words
    }
