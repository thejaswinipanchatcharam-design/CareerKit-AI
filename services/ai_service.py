"""
CareerKit AI - Unified AI Service Layer
Provides a provider-agnostic interface for Google Gemini and Groq.
Enforces low temperature for factual fidelity, scrubs private resume data
and secrets from server logs, and handles rate limits, timeouts, and quota exhaustion safely.
"""

import os
import time
import logging
from typing import Dict, Any, Optional
from config import Config

logger = logging.getLogger("CareerKitAI.AIService")


def generate_ai_response(
    prompt: str,
    system_instruction: str = "",
    temperature: float = 0.2,
    allow_mock_fallback: bool = True
) -> Dict[str, Any]:
    """
    Unified entry point for AI text generation.
    Dispatches to the active provider (Gemini or Groq) configured in .env.
    
    Returns:
        Dict with keys:
            success (bool): Whether the call succeeded
            content (str): The generated response text
            provider (str): Provider used ('gemini', 'groq', or 'mock')
            model (str): Model name used
            error (str or None): Safe, user-friendly error message
            error_type (str or None): Categorized error code
            is_mock (bool): True if generated via offline fallback
    """
    provider = Config.AI_PROVIDER.lower().strip()

    if not prompt or not prompt.strip():
        return {
            "success": False,
            "content": "",
            "provider": provider,
            "model": "none",
            "error": "The input prompt cannot be empty.",
            "error_type": "EMPTY_PROMPT",
            "is_mock": False
        }

    # Scrub log: Record length only, NEVER private resume text or API keys
    logger.info(
        f"AI Request: provider='{provider}', prompt_length={len(prompt)} chars, "
        f"has_system_instruction={bool(system_instruction)}"
    )

    start_time = time.time()

    # Route to selected provider
    if provider == "gemini":
        result = _call_gemini(prompt, system_instruction, temperature, allow_mock_fallback)
    elif provider == "groq":
        result = _call_groq(prompt, system_instruction, temperature, allow_mock_fallback)
    else:
        logger.warning(f"Unsupported AI_PROVIDER '{provider}'. Falling back to mock demo.")
        result = _generate_mock_response(prompt, reason=f"Unsupported provider: '{provider}'")

    latency = time.time() - start_time
    logger.info(
        f"AI Response: success={result['success']}, provider='{result['provider']}', "
        f"model='{result['model']}', latency={latency:.2f}s, is_mock={result['is_mock']}"
    )

    return result


def _call_gemini(
    prompt: str,
    system_instruction: str,
    temperature: float,
    allow_mock_fallback: bool
) -> Dict[str, Any]:
    """Invokes Google Gemini API via official google-genai SDK."""
    api_key = Config.GEMINI_API_KEY
    model_name = Config.GEMINI_MODEL or "gemini-2.5-flash"

    # Handle missing API key
    if not api_key:
        if allow_mock_fallback:
            logger.info("No GEMINI_API_KEY found in .env. Using structured offline demonstration response.")
            return _generate_mock_response(
                prompt,
                reason="Google Gemini API key not configured in .env. Using offline viva demonstration mode."
            )
        return {
            "success": False,
            "content": "",
            "provider": "gemini",
            "model": model_name,
            "error": "Google Gemini API key is missing. Please add GEMINI_API_KEY to your .env file.",
            "error_type": "MISSING_API_KEY",
            "is_mock": False
        }

    try:
        from google import genai
        from google.genai import types

        client = genai.Client(api_key=api_key)

        # Build configuration with system instructions and factuality temperature
        config_params = {
            "temperature": max(0.0, min(temperature, 1.0))
        }
        if system_instruction:
            config_params["system_instruction"] = system_instruction

        config = types.GenerateContentConfig(**config_params)

        response = client.models.generate_content(
            model=model_name,
            contents=prompt,
            config=config
        )

        if not response or not response.text:
            return {
                "success": False,
                "content": "",
                "provider": "gemini",
                "model": model_name,
                "error": "Gemini returned an empty response. The content may have triggered safety filters.",
                "error_type": "EMPTY_RESPONSE",
                "is_mock": False
            }

        return {
            "success": True,
            "content": response.text.strip(),
            "provider": "gemini",
            "model": model_name,
            "error": None,
            "error_type": None,
            "is_mock": False
        }

    except Exception as e:
        error_str = str(e)
        logger.error(f"Gemini API invocation failure: {error_str}")

        # Classify user-friendly error messages
        if "API_KEY_INVALID" in error_str or "401" in error_str:
            err_msg = "Invalid Gemini API key. Please check your GEMINI_API_KEY in .env."
            err_type = "AUTH_FAILURE"
        elif "RESOURCE_EXHAUSTED" in error_str or "429" in error_str:
            err_msg = "Gemini API rate limit or quota exceeded. Please retry in a few moments."
            err_type = "RATE_LIMIT"
        elif "NOT_FOUND" in error_str or "404" in error_str:
            err_msg = f"The specified Gemini model '{model_name}' was not found. Please verify the model name in .env."
            err_type = "MODEL_NOT_FOUND"
        else:
            err_msg = f"Gemini API request failed: {error_str}"
            err_type = "PROVIDER_ERROR"

        if allow_mock_fallback:
            logger.info("Falling back to offline demonstration mode due to API error.")
            mock_res = _generate_mock_response(prompt, reason=f"Gemini error: {err_msg}")
            mock_res["error"] = f"{err_msg} (Offline demonstration content loaded)."
            return mock_res

        return {
            "success": False,
            "content": "",
            "provider": "gemini",
            "model": model_name,
            "error": err_msg,
            "error_type": err_type,
            "is_mock": False
        }


def _call_groq(
    prompt: str,
    system_instruction: str,
    temperature: float,
    allow_mock_fallback: bool
) -> Dict[str, Any]:
    """Invokes Groq API via official groq SDK."""
    api_key = Config.GROQ_API_KEY
    model_name = Config.GROQ_MODEL or "llama-3.3-70b-versatile"

    if not api_key:
        if allow_mock_fallback:
            logger.info("No GROQ_API_KEY found in .env. Using structured offline demonstration response.")
            return _generate_mock_response(
                prompt,
                reason="Groq API key not configured in .env. Using offline viva demonstration mode."
            )
        return {
            "success": False,
            "content": "",
            "provider": "groq",
            "model": model_name,
            "error": "Groq API key is missing. Please add GROQ_API_KEY to your .env file.",
            "error_type": "MISSING_API_KEY",
            "is_mock": False
        }

    try:
        from groq import Groq

        client = Groq(api_key=api_key)

        messages = []
        if system_instruction:
            messages.append({"role": "system", "content": system_instruction})
        messages.append({"role": "user", "content": prompt})

        chat_completion = client.chat.completions.create(
            messages=messages,
            model=model_name,
            temperature=max(0.0, min(temperature, 1.0))
        )

        content = chat_completion.choices[0].message.content or ""
        if not content.strip():
            return {
                "success": False,
                "content": "",
                "provider": "groq",
                "model": model_name,
                "error": "Groq returned an empty response.",
                "error_type": "EMPTY_RESPONSE",
                "is_mock": False
            }

        return {
            "success": True,
            "content": content.strip(),
            "provider": "groq",
            "model": model_name,
            "error": None,
            "error_type": None,
            "is_mock": False
        }

    except Exception as e:
        error_str = str(e)
        logger.error(f"Groq API invocation failure: {error_str}")

        if "401" in error_str or "invalid_api_key" in error_str:
            err_msg = "Invalid Groq API key. Please check your GROQ_API_KEY in .env."
            err_type = "AUTH_FAILURE"
        elif "429" in error_str or "rate_limit" in error_str:
            err_msg = "Groq rate limit or quota exceeded. Please retry in a few moments."
            err_type = "RATE_LIMIT"
        else:
            err_msg = f"Groq API request failed: {error_str}"
            err_type = "PROVIDER_ERROR"

        if allow_mock_fallback:
            mock_res = _generate_mock_response(prompt, reason=f"Groq error: {err_msg}")
            mock_res["error"] = f"{err_msg} (Offline demonstration content loaded)."
            return mock_res

        return {
            "success": False,
            "content": "",
            "provider": "groq",
            "model": model_name,
            "error": err_msg,
            "error_type": err_type,
            "is_mock": False
        }


def _generate_mock_response(prompt: str, reason: str = "") -> Dict[str, Any]:
    """
    Generates a structured, factuality-compliant mock response for offline testing
    and college viva reviews when internet or API keys are unavailable.
    """
    mock_content = f"""### Improved Document (Offline Demonstration Mode)
*Note: {reason}*

#### Professional Summary
Dedicated and detail-oriented candidate with a solid foundation in computer science and software development. Experienced in building responsive web applications using Python, Flask, and relational databases. Committed to writing maintainable code and following software engineering best practices.

#### Key Improvements
1. Restructured technical skills into distinct categories (Languages, Frameworks, Developer Tools) for improved ATS readability.
2. Transformed passive project descriptions into action-oriented bullet points emphasizing architecture and testing.
3. Preserved all original qualifications and metrics without fabricating unverified claims.

#### Skills to Highlight
- Python & Flask web development
- Relational database management (SQLite, PostgreSQL)
- Version control with Git & GitHub
- Unit testing with pytest

#### Missing Information
- Specific deployment environments (e.g. AWS, Render, Docker) [NEEDS CANDIDATE INPUT]
- Recent certifications or coursework completion dates [NEEDS CANDIDATE INPUT]

#### Facts to Verify
- Confirm accuracy of project scope and metrics in the candidate profile.
- Verify internship duration dates with employer documentation.
"""
    return {
        "success": True,
        "content": mock_content.strip(),
        "provider": "mock",
        "model": "offline-demonstration",
        "error": None,
        "error_type": None,
        "is_mock": True
    }
