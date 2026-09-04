from datetime import datetime, timezone


AGING_BANDS = (
    (60, "FRESH"),
    (240, "AGING"),
    (1440, "ATTENTION"),
)


def calculate_exception_age(
    created_at: datetime,
    now: datetime | None = None,
) -> tuple[int, float, str]:
    """
    Calculate the operational age of an exception.

    Age is derived from ExceptionRecord.created_at.
    It is not persisted and does not modify the exception record.

    Aging bands:
    - 0 <= age < 1 hour   -> FRESH
    - 1 <= age < 4 hours  -> AGING
    - 4 <= age < 24 hours -> ATTENTION
    - age >= 24 hours     -> OVERDUE
    """

    if now is None:
        now = datetime.now(timezone.utc)

    if created_at.tzinfo is None:
        created_at = created_at.replace(tzinfo=timezone.utc)

    if now.tzinfo is None:
        now = now.replace(tzinfo=timezone.utc)

    age_seconds = max(
        0.0,
        (now - created_at).total_seconds(),
    )

    age_minutes = int(age_seconds // 60)
    age_hours = age_seconds / 3600

    if age_minutes < AGING_BANDS[0][0]:
        aging_band = "FRESH"
    elif age_minutes < AGING_BANDS[1][0]:
        aging_band = "AGING"
    elif age_minutes < AGING_BANDS[2][0]:
        aging_band = "ATTENTION"
    else:
        aging_band = "OVERDUE"

    return age_minutes, age_hours, aging_band
