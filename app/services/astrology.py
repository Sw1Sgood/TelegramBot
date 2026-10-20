from datetime import date
from enum import StrEnum


class ZodiacSign(StrEnum):
    ARIES = "aries"
    TAURUS = "taurus"
    GEMINI = "gemini"
    CANCER = "cancer"
    LEO = "leo"
    VIRGO = "virgo"
    LIBRA = "libra"
    SCORPIO = "scorpio"
    SAGITTARIUS = "sagittarius"
    CAPRICORN = "capricorn"
    AQUARIUS = "aquarius"
    PISCES = "pisces"


ZODIAC_EMOJI: dict[ZodiacSign, str] = {
    ZodiacSign.ARIES: "♈",
    ZodiacSign.TAURUS: "♉",
    ZodiacSign.GEMINI: "♊",
    ZodiacSign.CANCER: "♋",
    ZodiacSign.LEO: "♌",
    ZodiacSign.VIRGO: "♍",
    ZodiacSign.LIBRA: "♎",
    ZodiacSign.SCORPIO: "♏",
    ZodiacSign.SAGITTARIUS: "♐",
    ZodiacSign.CAPRICORN: "♑",
    ZodiacSign.AQUARIUS: "♒",
    ZodiacSign.PISCES: "♓",
}

# Первый день каждого знака (тропический зодиак, общепринятая таблица дат).
# На стыке знаков реальная граница плавает на ±1 день от года к году;
# для точного расчёта по времени рождения понадобятся эфемериды.
_SIGN_STARTS: tuple[tuple[tuple[int, int], ZodiacSign], ...] = (
    ((1, 20), ZodiacSign.AQUARIUS),
    ((2, 19), ZodiacSign.PISCES),
    ((3, 21), ZodiacSign.ARIES),
    ((4, 20), ZodiacSign.TAURUS),
    ((5, 21), ZodiacSign.GEMINI),
    ((6, 21), ZodiacSign.CANCER),
    ((7, 23), ZodiacSign.LEO),
    ((8, 23), ZodiacSign.VIRGO),
    ((9, 23), ZodiacSign.LIBRA),
    ((10, 23), ZodiacSign.SCORPIO),
    ((11, 22), ZodiacSign.SAGITTARIUS),
    ((12, 22), ZodiacSign.CAPRICORN),
)


def zodiac_sign(birth_date: date) -> ZodiacSign:
    sign = ZodiacSign.CAPRICORN  # 1–19 января
    for start, candidate in _SIGN_STARTS:
        if (birth_date.month, birth_date.day) >= start:
            sign = candidate
    return sign
