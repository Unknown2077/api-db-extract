from datetime import datetime

_DATE_FORMATS = [
    "%Y-%m-%d",
    "%d/%m/%Y",
    "%m/%d/%Y",
    "%d-%m-%Y",
    "%Y/%m/%d",
    "%Y-%m-%dT%H:%M:%S",
    "%Y-%m-%dT%H:%M:%SZ",
]


def parse_date_iso(value: str | None) -> str | None:
    """Parse any common date string to ISO 8601 YYYY-MM-DD.

    Returns:
        ISO date string, or None if value is empty.

    Raises:
        ValueError: If value is non-empty but no format matches.
    """
    if not value or not value.strip():
        return None
    cleaned = value.strip()
    for fmt in _DATE_FORMATS:
        try:
            return datetime.strptime(cleaned, fmt).strftime("%Y-%m-%d")
        except ValueError:
            continue
    raise ValueError(f"Cannot parse date {value!r} — no matching format")
