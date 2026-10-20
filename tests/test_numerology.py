from datetime import date

import pytest

from app.services.numerology import life_path_number, reduce_number


@pytest.mark.parametrize(("value", "expected"), [(7, 7), (10, 1), (19, 1), (28, 1), (99, 9), (11, 11), (22, 22), (33, 33), (29, 11)])
def test_reduce_number_keeps_master_numbers(value: int, expected: int) -> None:
    assert reduce_number(value) == expected


def test_reduce_number_without_master() -> None:
    assert reduce_number(11, keep_master=False) == 2
    assert reduce_number(29, keep_master=False) == 2


@pytest.mark.parametrize(
    ("birth_date", "expected"),
    [
        (date(1995, 3, 25), 7),  # 7 + 3 + (1995 → 24 → 6) = 16 → 7
        (date(1979, 11, 18), 1),  # 9 + 11 + (1979 → 26 → 8) = 28 → 10 → 1
        (date(1990, 3, 25), 11),  # 7 + 3 + 1 = 11 — мастер-число
        (date(2000, 1, 1), 4),  # 1 + 1 + 2
    ],
)
def test_life_path_number(birth_date: date, expected: int) -> None:
    assert life_path_number(birth_date) == expected


def test_life_path_range() -> None:
    allowed = set(range(1, 10)) | {11, 22, 33}
    start = date(1900, 1, 1).toordinal()
    for offset in range(0, 365 * 120, 7):
        assert life_path_number(date.fromordinal(start + offset)) in allowed
