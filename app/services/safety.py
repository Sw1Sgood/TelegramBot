"""Распознавание вопросов, в которых есть признаки кризиса.

Такие вопросы бот не раскладывает, а отвечает с заботой и даёт контакты служб помощи.
"""

import re

_CRISIS_PATTERNS = (
    # ru
    r"суицид", r"самоубий", r"покончить с собой", r"убить себя", r"убью себя", r"не хочу жить",
    r"жить не хочу", r"не хочется жить", r"хочу умереть", r"лучше бы я умер", r"свести счеты с жизнью",
    r"(по)?резать себя", r"порезы на", r"самоповрежд", r"селфхарм", r"причиня\w* себе боль",
    r"меня бьет", r"меня избива", r"насил", r"домогает",
    # en
    r"suicid", r"kill myself", r"end my life", r"want to die", r"wanna die", r"self[- ]?harm",
    r"cut myself", r"hurt myself", r"abus(e|ing|ed) me", r"beats me", r"\brape",
)
_CRISIS_RE = re.compile("|".join(_CRISIS_PATTERNS), re.IGNORECASE)


def is_crisis(text: str) -> bool:
    return bool(_CRISIS_RE.search(text.lower().replace("ё", "е")))
