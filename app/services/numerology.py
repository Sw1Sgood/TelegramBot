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
