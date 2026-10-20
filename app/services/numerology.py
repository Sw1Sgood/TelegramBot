from datetime import date

MASTER_NUMBERS = frozenset({11, 22, 33})


def reduce_number(value: int, keep_master: bool = True) -> int:
    """Складывает цифры числа, пока не останется одна цифра (или мастер-число)."""
    while value > 9 and not (keep_master and value in MASTER_NUMBERS):
        value = sum(int(digit) for digit in str(value))
    return value


def life_path_number(birth_date: date) -> int:
    """Число жизненного пути: день, месяц и год сводятся по отдельности, затем суммируются.

    Мастер-числа 11, 22 и 33 сохраняются.
    """
    total = reduce_number(birth_date.day) + reduce_number(birth_date.month) + reduce_number(birth_date.year)
    return reduce_number(total)


# Пифагорейская таблица: буква → число 1–9.
_LETTER_VALUES: dict[str, int] = {}
for _alphabet in ("абвгдеёжзийклмнопрстуфхцчшщъыьэюя", "abcdefghijklmnopqrstuvwxyz"):
    for _index, _letter in enumerate(_alphabet):
        _LETTER_VALUES[_letter] = _index % 9 + 1
_VOWELS = frozenset("аеёиоуыэюяaeiou")


def _letters(name: str) -> list[str]:
    return [char for char in name.lower() if char in _LETTER_VALUES]


def has_letters(name: str) -> bool:
    return bool(_letters(name))


def expression_number(name: str) -> int:
    """Число судьбы (выражения) — сумма всех букв имени."""
    return reduce_number(sum(_LETTER_VALUES[c] for c in _letters(name)))


def soul_number(name: str) -> int:
    """Число души — сумма гласных."""
    return reduce_number(sum(_LETTER_VALUES[c] for c in _letters(name) if c in _VOWELS))


def personality_number(name: str) -> int:
    """Число личности — сумма согласных."""
    return reduce_number(sum(_LETTER_VALUES[c] for c in _letters(name) if c not in _VOWELS))


def birthday_number(birth_date: date) -> int:
    return reduce_number(birth_date.day)


def personal_year(birth_date: date, year: int) -> int:
    return reduce_number(birth_date.day + birth_date.month + year, keep_master=False)
