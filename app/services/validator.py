import re

# Список запрещенных слов (в нижнем регистре)
# Сюда можно добавить мат, оскорбления и служебные слова
BAD_WORDS = [
    # --- Системные и служебные слова ---
    "admin", "administrator", "moderator", "support", "bot", "robot", "root",
    "manager", "director", "president", "yuksalish", "system",

    # --- "Мусор" и тесты ---
    "test", "demo", "null", "undefined", "qwerty", "asdf", "zxcv",
    "bla", "blabla", "xxx", "123", "noname",

    # --- Русский мат и оскорбления (корни) ---
    "хуй", "хер", "пизд", "ебал", "ебан", "бля", "блят",
    "мудак", "говно", "жопа", "сука", "манда", "залупа",
    "пидор", "педик", "гандон", "гондон", "чмо", "лох",
    "шлюха", "проститутка", "дроч", "сперма", "тварь",

    # --- Узбекский мат и оскорбления ---
    "jalab", "qotoq", "sik", "sike", "skay",
    "gandon", "yop tvoy", "dalbayob", "dalboyob",
    "haromi", "fohisha", "foxisha", "qanjiq",
    "ombir", "onangni", "eshshak", "mol", "hayvon",
    "koting", "kotini"  # Специфичные формы, чтобы случайно не забанить обычные слова
]


def validate_fullname(text: str) -> dict:
    """
    Проверяет имя на адекватность.
    Возвращает: {'valid': True/False, 'error': 'код_ошибки'}
    """
    cleaned_text = text.strip()

    # 1. Проверка длины
    if len(cleaned_text) < 3:
        return {"valid": False, "error": "short"}

    if len(cleaned_text) > 50:
        return {"valid": False, "error": "long"}

    # 2. Проверка на символы (Разрешаем: Буквы (любые), пробел, дефис, апостроф)
    # Регулярка захватывает: Латиницу, Кириллицу, ЎўҚқҒғҲҳ (узб), апострофы '`’
    pattern = r"^[a-zA-Zа-яА-ЯёЁўЎқҚғҒҳҲ\s\-\'\`’]+$"

    if not re.match(pattern, cleaned_text):
        return {"valid": False, "error": "symbols"}

    # 3. Проверка на стоп-слова
    text_lower = cleaned_text.lower()

    # Проверяем каждое слово в имени
    for word in text_lower.split():
        for bad in BAD_WORDS:
            # Если плохое слово есть внутри введенного слова
            if bad in word:
                return {"valid": False, "error": "bad_word"}

    return {"valid": True, "clean_name": cleaned_text.title()}