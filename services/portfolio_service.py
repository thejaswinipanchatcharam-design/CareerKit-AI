"""
CareerKit AI - One-Page Portfolio & Video Script Service
Generates structured single-page web portfolio data and a concise 30-60 second
self-introduction video script strictly grounded in verified candidate facts.
"""

import re
from typing import Dict, Any, Optional
from services.ai_service import generate_ai_response


def generate_portfolio_and_script(
    candidate: Dict[str, Any],
    theme: str = "clean-purple",
    portfolio_notes: str = ""
) -> Dict[str, Any]:
    """
    Generates a structured one-page portfolio and a timed 30-60s self-introduction video script.

    Returns:
        Dict with headline, introduction, education_section, skills_section,
        projects_section, experience_section, contact_section, video_script,
        script_metrics, success, error.
    """
    if not candidate:
        return {
            "success": False,
            "error": "Candidate profile is required to generate a portfolio.",
            "headline": "",
            "video_script": ""
        }

    c_name = candidate.get("name", "Candidate")
    c_role = candidate.get("target_role", "Software Engineer")
    c_edu = candidate.get("education", "Computer Science")
    c_grad = candidate.get("graduation_year", "")
    c_skills = candidate.get("skills", "")
    c_projects = candidate.get("projects", "")
    c_exp = candidate.get("experience", "")
    c_email = candidate.get("email", "")
    c_phone = candidate.get("phone", "")
    c_loc = candidate.get("location", "")
    c_summary = candidate.get("summary", "")

    prompt = f"""Generate a structured, authentic one-page portfolio summary and a 30-60 second self-introduction video script for this candidate.

CANDIDATE GROUND TRUTH:
- Name: {c_name}
- Target Role: {c_role}
- Education: {c_edu} (Expected Graduation: {c_grad or 'N/A'})
- Skills: {c_skills}
- Projects: {c_projects or 'Academic and course projects'}
- Experience: {c_exp or 'Hands-on practical development'}
- Existing Summary: {c_summary or 'Aspiring engineer dedicated to high-quality code'}
- Additional Notes: {portfolio_notes or 'None'}

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
"""

    system_instruction = (
        "You are an expert technical portfolio coach and speech mentor. "
        "Create concise, authentic, and engaging presentation materials strictly grounded in genuine facts."
    )

    ai_res = generate_ai_response(
        prompt=prompt,
        system_instruction=system_instruction,
        temperature=0.25
    )

    if not ai_res.get("success"):
        # Fallback to local deterministic generator
        return _generate_fallback_portfolio(candidate)

    raw_output = ai_res.get("content", "")
    parsed = _parse_portfolio_output(raw_output, candidate)
    parsed["success"] = True
    parsed["provider"] = ai_res.get("provider")
    parsed["model"] = ai_res.get("model")
    parsed["is_mock"] = ai_res.get("is_mock", False)
    return parsed


def _parse_portfolio_output(output: str, candidate: Dict[str, Any]) -> Dict[str, Any]:
    """Extracts headline, introduction, projects, and script from AI response."""
    headline = ""
    introduction = ""
    projects_section = ""
    video_script = ""

    # Headline
    h_match = re.search(r"\[HEADLINE\](.*?)(?=\[INTRODUCTION\]|\Z)", output, re.DOTALL | re.IGNORECASE)
    if h_match:
        headline = h_match.group(1).strip()
    else:
        headline = f"{candidate.get('target_role', 'Software Developer')} | {candidate.get('education', 'Engineering')}"

    # Introduction
    intro_match = re.search(r"\[INTRODUCTION\](.*?)(?=\[FEATURED PROJECTS\]|\[VIDEO SCRIPT\]|\Z)", output, re.DOTALL | re.IGNORECASE)
    if intro_match:
        introduction = intro_match.group(1).strip()
    else:
        introduction = candidate.get("summary") or f"Passionate {candidate.get('target_role')} focusing on clean architecture and practical problem solving."

    # Projects
    proj_match = re.search(r"\[FEATURED PROJECTS\](.*?)(?=\[VIDEO SCRIPT\]|\Z)", output, re.DOTALL | re.IGNORECASE)
    if proj_match:
        projects_section = proj_match.group(1).strip()
    else:
        projects_section = candidate.get("projects") or "Featured academic software projects."

    # Video Script
    script_match = re.search(r"\[VIDEO SCRIPT\](.*)", output, re.DOTALL | re.IGNORECASE)
    if script_match:
        video_script = script_match.group(1).strip()
    else:
        video_script = _generate_fallback_script(candidate)

    # Calculate metrics
    # Strip timestamp headers to get pure spoken words count
    spoken_text = re.sub(r"\[\d+:\d+\s*-\s*\d+:\d+[^\]]*\]", "", video_script)
    words = spoken_text.split()
    word_count = len(words)
    # Estimate seconds based on standard conversational rate of 130 words per minute (~2.17 words/sec)
    estimated_seconds = max(20, round(word_count / 2.15))

    return {
        "headline": headline,
        "introduction": introduction,
        "education_section": f"{candidate.get('education', '')} (Graduation: {candidate.get('graduation_year', 'In Progress')})",
        "skills_section": candidate.get("skills", ""),
        "projects_section": projects_section,
        "experience_section": candidate.get("experience") or "Practical project experience and technical development.",
        "contact_section": f"Email: {candidate.get('email', 'Available on request')} | Phone: {candidate.get('phone', 'Available on request')} | Location: {candidate.get('location', 'Global')}",
        "video_script": video_script,
        "script_metrics": {
            "word_count": word_count,
            "estimated_seconds": estimated_seconds,
            "pace_rating": "Optimal (30–60s)" if 30 <= estimated_seconds <= 65 else ("Slightly Long" if estimated_seconds > 65 else "Short")
        }
    }


def _generate_fallback_portfolio(candidate: Dict[str, Any]) -> Dict[str, Any]:
    """Generates a complete deterministic portfolio and video script without external API."""
    name = candidate.get("name", "Candidate")
    role = candidate.get("target_role", "Software Engineer")
    edu = candidate.get("education", "Computer Science")
    skills = candidate.get("skills", "Python, SQL, Web Development")
    projects = candidate.get("projects", "Placement and portfolio automation systems")
    exp = candidate.get("experience", "")

    headline = f"{role} | Specializing in {skills.split(',')[0].strip() if skills else 'Software Engineering'}"
    introduction = (
        f"I am {name}, an aspiring {role} with a strong academic foundation in {edu}. "
        f"I enjoy building responsive, reliable applications using {skills}."
    )

    script = _generate_fallback_script(candidate)
    spoken_text = re.sub(r"\[\d+:\d+\s*-\s*\d+:\d+[^\]]*\]", "", script)
    words = spoken_text.split()
    word_count = len(words)
    estimated_seconds = round(word_count / 2.15)

    return {
        "success": True,
        "headline": headline,
        "introduction": introduction,
        "education_section": f"{edu} (Graduation: {candidate.get('graduation_year', 'In Progress')})",
        "skills_section": skills,
        "projects_section": projects,
        "experience_section": exp or "Hands-on engineering projects and academic coursework.",
        "contact_section": f"Email: {candidate.get('email', 'N/A')} | Location: {candidate.get('location', 'N/A')}",
        "video_script": script,
        "script_metrics": {
            "word_count": word_count,
            "estimated_seconds": estimated_seconds,
            "pace_rating": "Optimal (30–60s)"
        },
        "is_mock": True
    }


def _generate_fallback_script(candidate: Dict[str, Any]) -> str:
    """Generates an authentic 30-60s script with timing markers."""
    name = candidate.get("name", "Aarav Sharma")
    role = candidate.get("target_role", "Software Engineer")
    edu = candidate.get("education", "Computer Science")
    skills = candidate.get("skills", "Python, Flask, and relational databases")
    first_skills = ", ".join([s.strip() for s in skills.split(",")[:3]])

    return f"""[0:00 - 0:10 | Introduction & Hook]
"Hello, my name is {name}. I'm an aspiring {role} with a background in {edu}."

[0:10 - 0:30 | Technical Foundation & Projects]
"My primary engineering strengths lie in {first_skills}. Through my project work, I've focused on building scalable, well-tested applications with clean architecture and reliable data workflows."

[0:30 - 0:50 | Problem-Solving & Mindset]
"I believe in disciplined software engineering—emphasizing automated testing, transparent documentation, and continuous learning to solve real-world problems effectively."

[0:50 - 1:00 | Call to Action]
"I'm eager to contribute to an engineering team that values code quality and practical innovation. Thank you for your time, and I look forward to connecting!"
"""
