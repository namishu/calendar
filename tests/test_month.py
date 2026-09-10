from datetime import date

import pytest

from namishu_calendar.month import CalendarMonth


@pytest.mark.parametrize("year,month,days", [(1, 1, 31), (2021, 2, 28), (2024, 2, 29), (2027, 5, 31), (9999, 12, 31)])
@pytest.mark.parametrize("first_day", range(7))
def test_calendar_dates_and_columns(year: int, month: int, days: int, first_day: int) -> None:
    names = [str(i) for i in range(7)]
    model = CalendarMonth(year, month, [str(i) for i in range(1, 13)], names, first_day)
    assert model.month_text() == str(month)
    assert model.weekday_texts() == [str((first_day + i) % 7) for i in range(7)]
    assert [day for week in model.days for day in week if day] == list(range(1, days + 1))
    assert all(len(week) == 7 for week in model.days)
    for week in model.days:
        for column, day in enumerate(week):
            if day:
                assert (column + first_day) % 7 == date(year, month, day).weekday()
    assert 4 <= model.row_count <= 6
    assert any(model.days[0]) and any(model.days[-1])


@pytest.mark.parametrize("year,month,rows", [(2021, 2, 4), (2027, 9, 5), (2027, 5, 6)])
def test_row_count(year: int, month: int, rows: int) -> None:
    model = CalendarMonth(year, month, [""] * 12, [""] * 7, 0)
    assert model.row_count == rows
