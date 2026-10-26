"""Weekly program validation and normalization."""

from __future__ import annotations

from typing import Any

DAYS = tuple(str(day) for day in range(7))
VALUES_PER_DAY = 8


class InvalidProgram(ValueError):
    """Raised when a weekly program is malformed."""


def normalize_program(raw: dict[str, Any]) -> dict[str, list[int]]:
    """Validate and normalize a thermostat weekly program.

    Each day is eight integers representing four [minute-of-day, Fahrenheit]
    pairs. CT50 day numbers are 0=Monday through 6=Sunday.
    """
    normalized: dict[str, list[int]] = {}
    for day in DAYS:
        values = raw.get(day)
        if not isinstance(values, (list, tuple)) or len(values) != VALUES_PER_DAY:
            raise InvalidProgram(f"Day {day} must contain exactly 8 integer values")
        day_values: list[int] = []
        for index, value in enumerate(values):
            if isinstance(value, bool) or not isinstance(value, int):
                raise InvalidProgram(f"Day {day}, value {index} must be an integer")
            day_values.append(value)

        for index in range(0, VALUES_PER_DAY, 2):
            minute = day_values[index]
            temperature = day_values[index + 1]
            if not 0 <= minute <= 1439:
                raise InvalidProgram(f"Day {day} has an invalid minute-of-day: {minute}")
            # CT50 schedules are Fahrenheit. Keep a broad equipment-safe range;
            # exact device limits should be confirmed for each supported model.
            if not 40 <= temperature <= 95:
                raise InvalidProgram(
                    f"Day {day} has an implausible Fahrenheit setpoint: {temperature}"
                )
        if [day_values[i] for i in range(0, VALUES_PER_DAY, 2)] != sorted(
            day_values[i] for i in range(0, VALUES_PER_DAY, 2)
        ):
            raise InvalidProgram(f"Day {day} schedule times must be in ascending order")
        normalized[day] = day_values
    return normalized


def programs_equal(left: dict[str, Any], right: dict[str, Any]) -> bool:
    """Compare programs after validating and normalizing their data."""
    return normalize_program(left) == normalize_program(right)
