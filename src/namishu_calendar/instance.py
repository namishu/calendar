from __future__ import annotations

import calendar
from dataclasses import dataclass
from datetime import date


@dataclass
class MonthCalendarInstance:
    year: int
    month: int
    months: list[str]
    weekdays: list[str]
    first_day: int

    def __post_init__(self) -> None:
        if self.year < 1:
            raise ValueError(f"Invalid year: {self.year}")
        if not (1 <= self.month <= 12):
            raise ValueError(f"Invalid month: {self.month}")
        if len(self.months) != 12:
            raise ValueError("Invalid months: expected 12 names")
        if len(self.weekdays) != 7:
            raise ValueError("Invalid weekdays: expected 7 names")
        if not (0 <= self.first_day <= 6):
            raise ValueError(f"Invalid first_day: {self.first_day}")

    def month_text(self) -> str:
        return self.months[self.month - 1]

    def weekday_texts(self) -> list[str]:
        return [self.weekdays[(i + self.first_day) % 7] for i in range(7)]

    def weeks_across(self) -> int:
        weekday = date(self.year, self.month, 1).weekday()
        first_column = (weekday - self.first_day) % 7
        days = calendar.monthrange(self.year, self.month)[1]
        total = first_column + days
        weeks = total // 7
        if total % 7 != 0:
            weeks += 1
        return weeks

    def day_matrix(self) -> list[list[int]]:
        matrix = [[0] * 7 for _ in range(self.weeks_across())]
        days = calendar.monthrange(self.year, self.month)[1]
        weekday = date(self.year, self.month, 1).weekday()
        first_column = (weekday - self.first_day) % 7

        row = 0
        col = first_column
        for day in range(1, days + 1):
            matrix[row][col] = day
            col += 1
            if col >= 7:
                col = 0
                row += 1
        return matrix
