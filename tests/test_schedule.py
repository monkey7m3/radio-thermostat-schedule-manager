"""Tests for CT50 weekly program validation.

Load the pure helper module directly so the unit tests do not require Home Assistant.
"""

import importlib.util
from pathlib import Path

import pytest


MODULE_PATH = (
    Path(__file__).parents[1]
    / "custom_components"
    / "radio_thermostat_schedule_manager"
    / "schedule.py"
)
SPEC = importlib.util.spec_from_file_location("schedule_under_test", MODULE_PATH)
assert SPEC is not None and SPEC.loader is not None
SCHEDULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(SCHEDULE)
InvalidProgram = SCHEDULE.InvalidProgram
normalize_program = SCHEDULE.normalize_program
programs_equal = SCHEDULE.programs_equal


VALID_PROGRAM = {
    str(day): [360, 72, 540, 72, 990, 72, 1320, 70]
    for day in range(7)
}


def test_normalize_program_preserves_ct50_schedule() -> None:
    assert normalize_program(VALID_PROGRAM) == VALID_PROGRAM


def test_program_requires_all_seven_days() -> None:
    invalid = dict(VALID_PROGRAM)
    del invalid["6"]
    with pytest.raises(InvalidProgram):
        normalize_program(invalid)


def test_program_requires_four_time_temperature_pairs() -> None:
    invalid = dict(VALID_PROGRAM)
    invalid["0"] = [360, 72]
    with pytest.raises(InvalidProgram):
        normalize_program(invalid)


def test_program_rejects_out_of_range_minute() -> None:
    invalid = dict(VALID_PROGRAM)
    invalid["0"] = [-1, 72, 540, 72, 990, 72, 1320, 70]
    with pytest.raises(InvalidProgram):
        normalize_program(invalid)


def test_program_rejects_unsorted_times() -> None:
    invalid = dict(VALID_PROGRAM)
    invalid["0"] = [540, 72, 360, 72, 990, 72, 1320, 70]
    with pytest.raises(InvalidProgram):
        normalize_program(invalid)


def test_programs_compare_after_normalization() -> None:
    reordered_keys = {key: value[:] for key, value in VALID_PROGRAM.items()}
    assert programs_equal(VALID_PROGRAM, reordered_keys)
