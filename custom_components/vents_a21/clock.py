"""Clock of the controller, and keeping it on Home Assistant's time.

The weekly schedule of the unit follows its own clock. Nothing sets that
clock besides the manufacturer's app: without it the clock drifts and
misses the change between summer and winter time.

Four holding registers of two bytes each, layout confirmed on a DF 350
Connect (the written time read back correctly):

    61  high byte: minutes        low byte: seconds
    62                            low byte: hours
    63  high byte: day of month   low byte: weekday, 1 (Monday) to 7
    64  high byte: month          low byte: year on two digits

The clock holds local time, with no notion of time zone.
"""

from __future__ import annotations

from datetime import datetime
from typing import Final

from .api import A21Data, RegistersWrite

HR_RTC_MIN_SEC: Final = 61
HR_RTC_HOURS: Final = 62
HR_RTC_DAY_WEEKDAY: Final = 63
HR_RTC_MONTH_YEAR: Final = 64

DEFAULT_CLOCK_TOLERANCE: Final = 5  # minutes
MIN_CLOCK_TOLERANCE: Final = 1
MAX_CLOCK_TOLERANCE: Final = 60
# The clock is set once an hour at most, whatever it reads afterwards.
SYNC_MIN_INTERVAL: Final = 3600.0


def clock_write(now: datetime) -> RegistersWrite:
    """Return the write setting the controller clock to now (local time).

    One frame for the four registers, so the time cannot be torn by a
    change of minute or of day between two writes.
    """
    return RegistersWrite(
        HR_RTC_MIN_SEC,
        (
            now.minute << 8 | now.second,
            now.hour,
            now.day << 8 | now.isoweekday(),
            now.month << 8 | now.year % 100,
        ),
    )


def read_clock(data: A21Data) -> datetime | None:
    """Return the local time the controller clock shows, without time zone.

    None when the firmware does not expose the clock or when it holds
    something that is not a date (a clock never set, a flat battery).
    """
    words = [
        data.hr(address)
        for address in (
            HR_RTC_MIN_SEC,
            HR_RTC_HOURS,
            HR_RTC_DAY_WEEKDAY,
            HR_RTC_MONTH_YEAR,
        )
    ]
    if any(word is None for word in words):
        return None
    min_sec, hours, day_weekday, month_year = words
    try:
        return datetime(
            2000 + (month_year & 0xFF),
            month_year >> 8,
            day_weekday >> 8,
            hours & 0xFF,
            min_sec >> 8,
            min_sec & 0xFF,
        )
    except ValueError:
        return None


def clock_drift(data: A21Data, now: datetime) -> float | None:
    """Return how far the controller clock is ahead of now, in seconds.

    Both are compared as wall-clock time, so a clock left on summer time
    reads one hour ahead once winter time has started.
    """
    machine = read_clock(data)
    if machine is None:
        return None
    return (machine - now.replace(tzinfo=None)).total_seconds()
