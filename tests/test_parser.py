import pytest
from src.services.utils import parse_set_input
from src.models.exercise import ExerciseType

def test_parse_strength():
    assert parse_set_input("50.5x10", ExerciseType.strength) == {"reps": 10, "weight": 50.5}
    assert parse_set_input("50,5 x 10", ExerciseType.strength) == {"reps": 10, "weight": 50.5}
    assert parse_set_input("50 - 10", ExerciseType.strength) == {"reps": 10, "weight": 50.0}
    assert parse_set_input("50 10", ExerciseType.strength) == {"reps": 10, "weight": 50.0}
    assert parse_set_input("50 кг х 10", ExerciseType.strength) == {"reps": 10, "weight": 50.0}
    assert parse_set_input("20.5 kg x 15 раз", ExerciseType.strength) == {"reps": 15, "weight": 20.5}
    assert parse_set_input("abc", ExerciseType.strength) == {}
    assert parse_set_input("10", ExerciseType.strength) == {}
    assert parse_set_input("0x10", ExerciseType.strength) == {}
    assert parse_set_input("50x0", ExerciseType.strength) == {}
    assert parse_set_input("10x-5", ExerciseType.strength) == {"reps": 5, "weight": 10.0}
    assert parse_set_input("-50x10", ExerciseType.strength) == {"reps": 10, "weight": 50.0}

def test_parse_cardio():
    assert parse_set_input("5-20", ExerciseType.cardio) == {"distance": 5.0, "duration": 20.0}
    assert parse_set_input("5.5 км 20 мин", ExerciseType.cardio) == {"distance": 5500.0, "duration": 1200.0}
    assert parse_set_input("2.5км 12м30с", ExerciseType.cardio) == {"distance": 2500.0, "duration": 750.0}
    assert parse_set_input("500м 45с", ExerciseType.cardio) == {"distance": 500.0, "duration": 45.0}
    assert parse_set_input("10", ExerciseType.cardio) == {}
    assert parse_set_input("0 45", ExerciseType.cardio) == {}
    assert parse_set_input("500 0", ExerciseType.cardio) == {}

def test_parse_bodyweight():
    assert parse_set_input("15", ExerciseType.bodyweight) == {"reps": 15}
    assert parse_set_input("20 раз", ExerciseType.bodyweight) == {"reps": 20}
    assert parse_set_input("abc", ExerciseType.bodyweight) == {}
    assert parse_set_input("0", ExerciseType.bodyweight) == {}
    assert parse_set_input("-10", ExerciseType.bodyweight) == {}

def test_parse_timed():
    assert parse_set_input("60", ExerciseType.timed) == {"duration": 60.0}
    assert parse_set_input("60 мин", ExerciseType.timed) == {"duration": 3600.0}
    assert parse_set_input("abc", ExerciseType.timed) == {}
    assert parse_set_input("0", ExerciseType.timed) == {}

def test_format_set_text():
    from src.bot.formatters import format_set_text
    class DummySet:
        def __init__(self, **kwargs):
            for k, v in kwargs.items():
                setattr(self, k, v)
    assert format_set_text(DummySet(reps=10, weight=50.0)) == "50 кг на 10 повторений"
    assert format_set_text(DummySet(reps=15)) == "15 повторений"
    assert format_set_text(DummySet(distance=500.0, duration=45.0)) == "500 м, 45 сек"
    assert format_set_text(DummySet(distance=2500.0, duration=750.0)) == "2.5 км, 12 мин 30 сек"

