from datetime import date, time

import pytest

from app.services.profile_input import InputError, parse_birth_date, parse_time, validate_city, validate_name

TODAY = date(2026, 10, 20)


@pytest.mark.parametrize("text", ["25.03.1995", " 25.03.1995 ", "25/03/1995", "25-3-1995", "25 03 1995"])
def test_parse_birth_date_formats(text: str) -> None:
    assert parse_birth_date(text, TODAY) == date(1995, 3, 25)


def test_children_are_allowed() -> None:
    assert parse_birth_date("01.01.2020", TODAY) == date(2020, 1, 1)
    assert parse_birth_date("20.10.2026", TODAY) == TODAY


@pytest.mark.parametrize(
    ("text", "code"),
    [
        ("1995-03-25", "error-date-format"),
        ("завтра", "error-date-format"),
        ("31.02.1995", "error-date-invalid"),
        ("21.10.2026", "error-date-future"),
        ("01.01.1850", "error-date-too-old"),
    ],
)
def test_parse_birth_date_errors(text: str, code: str) -> None:
    with pytest.raises(InputError) as error:
        parse_birth_date(text, TODAY)
    assert error.value.code == code


@pytest.mark.parametrize(("text", "expected"), [("14:30", time(14, 30)), ("9:05", time(9, 5)), ("09.00", time(9, 0))])
def test_parse_time(text: str, expected: time) -> None:
    assert parse_time(text) == expected


@pytest.mark.parametrize("text", ["24:00", "12:60", "полдень", "1430"])
def test_parse_time_errors(text: str) -> None:
    with pytest.raises(InputError):
        parse_time(text)


def test_validate_name() -> None:
    assert validate_name("  Анна   Мария ") == "Анна Мария"
    for bad in ["", "   ", "123", "а" * 51]:
        with pytest.raises(InputError):
            validate_name(bad)


def test_validate_city() -> None:
    assert validate_city("Санкт-Петербург") == "Санкт-Петербург"
    for bad in ["М", "12345"]:
        with pytest.raises(InputError):
            validate_city(bad)
