from datetime import UTC, datetime


def utcnow() -> datetime:
    """Timezone-aware current UTC time."""
    return datetime.now(UTC)


def as_utc(dt: datetime) -> datetime:
    """Normalise a datetime to timezone-aware UTC.

    Postgres (``DateTime(timezone=True)``) returns aware datetimes, but SQLite
    returns naive ones. Treating a naive value as UTC keeps expiry comparisons
    correct on both backends.
    """
    if dt.tzinfo is None:
        return dt.replace(tzinfo=UTC)
    return dt
