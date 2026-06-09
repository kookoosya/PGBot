"""VK chat moderation thresholds and profanity patterns."""

MAX_VIOLATION_WARNINGS = 5
BAN_DURATION_DAYS = 7
SPAM_REPEAT_WINDOW_SECONDS = 90
SPAM_MAX_IDENTICAL_MESSAGES = 3
SPAM_MAX_URLS = 3
SPAM_MIN_LENGTH_FOR_CAPS = 20
SPAM_CAPS_RATIO = 0.85

# Obscene roots / patterns (partial match, case-insensitive).
PROFANITY_PATTERNS: tuple[str, ...] = (
    r"\bхуй",
    r"\bпизд",
    r"\bеба[тл]",
    r"\bёба[тл]",
    r"\bбля",
    r"\bсука\b",
    r"\bмудак",
    r"\bпидор",
    r"\bпедик",
    r"\bгандон",
)
