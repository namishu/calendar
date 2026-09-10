from __future__ import annotations

from calendar import Calendar
from dataclasses import dataclass, field


@dataclass
class CalendarMonth:
    """A month built from validated configuration and dates."""

    year: int
    month: int
    months: list[str]
    weekdays: list[str]
    first_day: int
    days: list[list[int]] = field(init=False)

    def __post_init__(self) -> None:
        self.days = Calendar(self.first_day).monthdayscalendar(self.year, self.month)

    @property
    def row_count(self) -> int:
        return len(self.days)

    def month_text(self) -> str:
        return self.months[self.month - 1]

    def weekday_texts(self) -> list[str]:
        return self.weekdays[self.first_day :] + self.weekdays[: self.first_day]
