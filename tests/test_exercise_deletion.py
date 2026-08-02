import pytest
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from src.services.user import create_user
from src.services.workout import create_workout, create_workout_note_from_template
from src.services.exercise import create_exercise, create_exercise_note_from_template, delete_exercise, check_exercise_usage
from src.models.exercise import ExerciseType

@pytest.mark.asyncio
async def test_delete_unused_exercise(db_session: AsyncSession):
    user = await create_user(db_session, telegram_id=9001)
    ex = await create_exercise(db_session, user.id, name="Free Exercise", ex_type=ExerciseType.strength)
    
    tmpl_count, hist_count = await check_exercise_usage(db_session, ex.id)
    assert tmpl_count == 0
    assert hist_count == 0
    
    success, err_msg = await delete_exercise(db_session, ex.id)
    assert success is True
    assert err_msg is None

@pytest.mark.asyncio
async def test_delete_used_exercise(db_session: AsyncSession):
    user = await create_user(db_session, telegram_id=9002)
    workout = await create_workout(db_session, user.id, brief="Used Workout")
    workout_note = await create_workout_note_from_template(db_session, workout.id, started_at=datetime.now())
    
    ex = await create_exercise(db_session, user.id, name="Used Exercise", ex_type=ExerciseType.strength)
    ex_note = await create_exercise_note_from_template(db_session, ex.id, workout_note.id, notes="Used in history")
    
    tmpl_count, hist_count = await check_exercise_usage(db_session, ex.id)
    assert hist_count == 1
    
    success, err_msg = await delete_exercise(db_session, ex.id)
    assert success is False
    assert "Невозможно удалить упражнение" in err_msg
