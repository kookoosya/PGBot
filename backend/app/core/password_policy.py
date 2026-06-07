import re

WEAK_PASSWORDS = {
    "password", "123456", "12345678", "admin123", "qwerty", "пароль",
    "password123", "111111", "1234567890", "admin", "letmein",
}


def validate_password(password: str) -> tuple[bool, str]:
    if len(password) < 10:
        return False, "Пароль минимум 10 символов"
    if len(password) > 128:
        return False, "Пароль слишком длинный"
    if password.lower() in WEAK_PASSWORDS:
        return False, "Слишком простой пароль"
    if not re.search(r"[a-zа-яё]", password.lower()):
        return False, "Нужна строчная буква"
    if not re.search(r"[A-ZА-ЯЁ]", password):
        return False, "Нужна заглавная буква"
    if not re.search(r"\d", password):
        return False, "Нужна цифра"
    return True, ""
