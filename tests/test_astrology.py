from datetime import date

import pytest

from app.services.astrology import ZodiacSign, zodiac_sign


@pytest.mark.parametrize(
    ("birth_date", "expected"),
    [
        (date(2000, 1, 1), ZodiacSign.CAPRICORN),
        (date(2000, 1, 19), ZodiacSign.CAPRICORN),
        (date(2000, 1, 20), ZodiacSign.AQUARIUS),
        (date(2000, 2, 18), ZodiacSign.AQUARIUS),
        (date(2000, 2, 19), ZodiacSign.PISCES),
        (date(2000, 2, 29), ZodiacSign.PISCES),
        (date(2000, 3, 20), ZodiacSign.PISCES),
        (date(2000, 3, 21), ZodiacSign.ARIES),
        (date(2000, 4, 19), ZodiacSign.ARIES),
        (date(2000, 4, 20), ZodiacSign.TAURUS),
        (date(2000, 5, 21), ZodiacSign.GEMINI),
        (date(2000, 6, 20), ZodiacSign.GEMINI),
        (date(2000, 6, 21), ZodiacSign.CANCER),
        (date(2000, 7, 22), ZodiacSign.CANCER),
        (date(2000, 7, 23), ZodiacSign.LEO),
        (date(2000, 8, 23), ZodiacSign.VIRGO),
        (date(2000, 9, 22), ZodiacSign.VIRGO),
        (date(2000, 9, 23), ZodiacSign.LIBRA),
        (date(2000, 10, 23), ZodiacSign.SCORPIO),
        (date(2000, 11, 21), ZodiacSign.SCORPIO),
        (date(2000, 11, 22), ZodiacSign.SAGITTARIUS),
        (date(2000, 12, 21), ZodiacSign.SAGITTARIUS),
        (date(2000, 12, 22), ZodiacSign.CAPRICORN),
        (date(2000, 12, 31), ZodiacSign.CAPRICORN),
    ],
)
def test_zodiac_sign_boundaries(birth_date: date, expected: ZodiacSign) -> None:
    assert zodiac_sign(birth_date) == expected


def test_every_day_has_a_sign() -> None:
    signs = {zodiac_sign(date.fromordinal(date(2024, 1, 1).toordinal() + i)) for i in range(366)}
    assert signs == set(ZodiacSign)
