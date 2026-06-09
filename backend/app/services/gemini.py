import json
import logging
import re

import google.generativeai as genai

from app.config import get_settings
from app.models.enums import IssueCategory, Priority

logger = logging.getLogger(__name__)
settings = get_settings()

CATEGORIES = [c.value for c in IssueCategory]

ANALYSIS_PROMPT = """Ты — аналитик обращений жителей поселка Пушкинские Горы.
Проанализируй обращение и верни ТОЛЬКО JSON без markdown:

{
  "is_valid": true/false,
  "category": "одна из категорий",
  "priority": "low/medium/high/critical",
  "summary": "краткое описание проблемы",
  "duplicate_probability": 0.0-1.0,
  "suggested_department": "название отдела"
}

Категории: {categories}

Отклоняй (is_valid=false) если:
- реклама или спам
- бессмысленный текст
- оскорбления
- только ссылки без описания проблемы

Обращение жителя:
{text}

{context}
"""


def _configure_gemini() -> None:
    if settings.GEMINI_API_KEY:
        genai.configure(api_key=settings.GEMINI_API_KEY)


def _parse_json_response(text: str) -> dict:
    cleaned = text.strip()
    if cleaned.startswith("```"):
        cleaned = re.sub(r"^```(?:json)?\n?", "", cleaned)
        cleaned = re.sub(r"\n?```$", "", cleaned)
    return json.loads(cleaned)


def _fallback_analysis(text: str) -> dict:
    """Rule-based fallback when Gemini is unavailable."""
    text_lower = text.lower()
    spam_patterns = [
        r"http[s]?://",
        r"купи|скидк|акци[яи]|реклам",
        r"^[.\s!?]+$",
    ]
    is_spam = any(re.search(p, text_lower) for p in spam_patterns) or len(text.strip()) < 10

    category = IssueCategory.OTHER.value
    category_keywords = {
        IssueCategory.ROADS: ["дорог", "яма", "асфальт", "тротуар"],
        IssueCategory.LIGHTING: ["фонар", "освещ", "свет"],
        IssueCategory.GARBAGE: ["мусор", "свалк", "контейнер"],
        IssueCategory.WATER: ["вод", "кран", "труб"],
        IssueCategory.SEWERAGE: ["канализ", "сток"],
        IssueCategory.UTILITIES: ["жкх", "отоплен", "газ"],
        IssueCategory.LANDSCAPING: ["благоустрой", "сквер", "парк", "дерев"],
        IssueCategory.PUBLIC_TRANSPORT: ["автобус", "маршрут", "остановк"],
        IssueCategory.SAFETY: ["безопасн", "преступ", "драк"],
        IssueCategory.STRAY_ANIMALS: ["собак", "кошк", "животн"],
        IssueCategory.SOCIAL_HELP: ["помощ", "социальн", "пенси"],
        IssueCategory.ECOLOGY: ["эколог", "загрязн", "выброс"],
    }
    for cat, keywords in category_keywords.items():
        if any(kw in text_lower for kw in keywords):
            category = cat.value
            break

    priority = Priority.MEDIUM.value
    if any(w in text_lower for w in ["срочно", "авария", "опасно", "угроза"]):
        priority = Priority.HIGH.value

    return {
        "is_valid": not is_spam,
        "category": category,
        "priority": priority,
        "summary": text[:200],
        "duplicate_probability": 0.0,
        "suggested_department": "ЖКХ" if category in [IssueCategory.UTILITIES.value, IssueCategory.WATER.value] else "Администрация",
    }


class GeminiAnalysisError(Exception):
    """Gemini API call failed (transient or permanent)."""


async def request_gemini_analysis(text: str, existing_issues_context: str = "") -> dict:
    """Call Gemini when configured; raises GeminiAnalysisError on API failure."""
    context = ""
    if existing_issues_context:
        context = f"Существующие похожие обращения:\n{existing_issues_context}"

    if not settings.GEMINI_API_KEY:
        logger.warning("Gemini API key not set, using fallback analysis")
        return _fallback_analysis(text)

    try:
        _configure_gemini()
        model = genai.GenerativeModel(settings.GEMINI_MODEL)
        prompt = ANALYSIS_PROMPT.format(
            categories=", ".join(CATEGORIES),
            text=text,
            context=context,
        )
        response = model.generate_content(prompt)
        result = _parse_json_response(response.text)

        if result.get("category") not in CATEGORIES:
            result["category"] = IssueCategory.OTHER.value
        if result.get("priority") not in [p.value for p in Priority]:
            result["priority"] = Priority.MEDIUM.value

        return result
    except Exception as exc:
        raise GeminiAnalysisError(str(exc)) from exc


async def analyze_issue(text: str, existing_issues_context: str = "") -> dict:
    try:
        return await request_gemini_analysis(text, existing_issues_context)
    except GeminiAnalysisError as exc:
        logger.error("Gemini analysis failed: %s", exc)
        return _fallback_analysis(text)
