from dataclasses import dataclass
import re


@dataclass(frozen=True)
class PartialDate:
    """Calendar components the traveler explicitly supplied."""

    month: int
    day: int | None = None
    year: int | None = None


_MONTHS = {
    "jan": 1,
    "january": 1,
    "feb": 2,
    "february": 2,
    "mar": 3,
    "march": 3,
    "apr": 4,
    "april": 4,
    "may": 5,
    "jun": 6,
    "june": 6,
    "jul": 7,
    "july": 7,
    "aug": 8,
    "august": 8,
    "sep": 9,
    "sept": 9,
    "september": 9,
    "oct": 10,
    "october": 10,
    "nov": 11,
    "november": 11,
    "dec": 12,
    "december": 12,
}


def parse_partial_date_text(
    value: str,
) -> PartialDate | None:
    """
    Parse supported explicit calendar-date shapes without filling gaps.

    A missing day or year remains missing. This function deliberately does
    not apply defaults from ``datetime`` or from the current date.
    """

    cleaned = re.sub(
        r"(?<=\d)(st|nd|rd|th)\b",
        "",
        value.strip().lower(),
    )
    tokens = cleaned.replace(",", " ").split()

    if len(tokens) not in {1, 2, 3}:
        return None

    normalized = [token.rstrip(".") for token in tokens]

    if len(normalized) == 1:
        month = _MONTHS.get(normalized[0])
        return PartialDate(month=month) if month else None

    if len(normalized) == 2:
        first, second = normalized
        first_month = _MONTHS.get(first)
        second_month = _MONTHS.get(second)

        if first_month and second.isdigit():
            number = int(second)

            if _is_year(number):
                return PartialDate(
                    month=first_month,
                    year=number,
                )

            if _is_day(number):
                return PartialDate(
                    month=first_month,
                    day=number,
                )

        if first.isdigit() and second_month:
            day = int(first)

            if _is_day(day):
                return PartialDate(
                    month=second_month,
                    day=day,
                )

        return None

    first, second, third = normalized
    first_month = _MONTHS.get(first)
    second_month = _MONTHS.get(second)

    if first_month and second.isdigit() and third.isdigit():
        day = int(second)
        year = int(third)

        if _is_day(day) and _is_year(year):
            return PartialDate(
                month=first_month,
                day=day,
                year=year,
            )

    if first.isdigit() and second_month and third.isdigit():
        day = int(first)
        year = int(third)

        if _is_day(day) and _is_year(year):
            return PartialDate(
                month=second_month,
                day=day,
                year=year,
            )

    return None


def get_missing_start_date_field(
    start_date_text: str | None,
) -> str:
    """Describe the explicit component needed to complete a start date."""

    if not start_date_text:
        return "start_date"

    partial_date = parse_partial_date_text(
        start_date_text
    )

    if partial_date is None:
        return "start_date"

    if (
        partial_date.day is not None
        and partial_date.year is None
    ):
        return "start_date_year"

    if (
        partial_date.year is not None
        and partial_date.day is None
    ):
        return "start_date_day"

    return "start_date"


def extract_explicit_day(
    value: str,
    expected_month: int,
) -> int | None:
    """Return a day explicitly tied to the known month or stated alone."""

    partial_date = parse_partial_date_text(value)

    if (
        partial_date is not None
        and partial_date.month == expected_month
        and partial_date.day is not None
    ):
        return partial_date.day

    month_names = sorted(
        (
            name
            for name, month in _MONTHS.items()
            if month == expected_month
        ),
        key=len,
        reverse=True,
    )
    month_pattern = "|".join(
        re.escape(name)
        for name in month_names
    )
    ordinal = r"(?:st|nd|rd|th)?"
    normalized = value.strip().lower()

    patterns = (
        rf"\b(?:{month_pattern})\.?\s+(\d{{1,2}}){ordinal}\b",
        rf"\b(\d{{1,2}}){ordinal}\s+(?:{month_pattern})\.?\b",
        rf"\b(?:on\s+)?the\s+(\d{{1,2}}){ordinal}\b",
        rf"\bday\s+(\d{{1,2}}){ordinal}\b",
    )

    for pattern in patterns:
        match = re.search(pattern, normalized)

        if match is not None:
            day = int(match.group(1))

            if _is_day(day):
                return day

    bare_day = re.fullmatch(
        rf"(\d{{1,2}}){ordinal}",
        normalized,
    )

    if bare_day is not None:
        day = int(bare_day.group(1))
        return day if _is_day(day) else None

    return None


def _is_day(value: int) -> bool:
    return 1 <= value <= 31


def _is_year(value: int) -> bool:
    return 1900 <= value <= 2200
