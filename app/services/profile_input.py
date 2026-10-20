"""Разбор и проверка того, что пользователь вводит в профиль."""

import re
from datetime import date, time

NAME_MAX_LEN = 50
CITY_MIN_LEN = 2
CITY_MAX_LEN = 100
MIN_BIRTH_YEAR = 1900


class InputError(ValueError):
    """Ошибка ввода; code — ключ локализации с текстом ошибки."""

    def __init__(self, code: str) -> None:
        super().__init__(code)
        self.code = code


_DATE_RE = re.compile(r"^(\d{1,2})[.\-/ ](\d{1,2})[.\-/ ](\d{4})$")
_TIME_RE = re.compile(r"^(\d{1,2})[:.\- ](\d{2})$")
_SPACES_RE = re.compile(r"\s+")


def parse_birth_date(text: str, today: date) -> date:
    match = _DATE_RE.match(text.strip())
    if not match:
        raise InputError("error-date-format")
    day, month, year = (int(group) for group in match.groups())
    try:
        value = date(year, month, day)
    except ValueError:
        raise InputError("error-date-invalid") from None
    if value > today:
        raise InputError("error-date-future")
    if year < MIN_BIRTH_YEAR:
        raise InputError("error-date-too-old")
    return value


def parse_time(text: str) -> time:
    match = _TIME_RE.match(text.strip())
    if not match:
        raise InputError("error-time-format")
    hour, minute = int(match.group(1)), int(match.group(2))
    if hour > 23 or minute > 59:
        raise InputError("error-time-format")
    return time(hour, minute)


def validate_name(text: str) -> str:
    value = _SPACES_RE.sub(" ", text).strip()
    if not value or len(value) > NAME_MAX_LEN or not any(char.isalpha() for char in value):
        raise InputError("error-name")
    return value


def validate_city(text: str) -> str:
    value = _SPACES_RE.sub(" ", text).strip()
    if not CITY_MIN_LEN <= len(value) <= CITY_MAX_LEN or not any(char.isalpha() for char in value):
        raise InputError("error-city")
    return value
