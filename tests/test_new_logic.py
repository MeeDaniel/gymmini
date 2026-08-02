import pytest
from datetime import date, datetime
from src.services.user import create_user
from src.services.workout import create_workout, add_exercise_to_workout, create_workout_note_from_template
from src.services.exercise import create_exercise
from src.services.utils import parse_set_input
from src.models.exercise import ExerciseType

@pytest.mark.asyncio
async def test_create_workout_note_copies_exercises(db_session):
    user = await create_user(db_session, 123, "test_user")
    workout = await create_workout(db_session, user.id, "Leg Day")
    ex1 = await create_exercise(db_session, user.id, "Squats", ExerciseType.strength)
    ex2 = await create_exercise(db_session, user.id, "Lunges", ExerciseType.strength)
    
    await add_exercise_to_workout(db_session, workout.id, ex1.id)
    await add_exercise_to_workout(db_session, workout.id, ex2.id)
    
    note = await create_workout_note_from_template(db_session, workout.id, datetime.now())
    assert note is not None
    
    from sqlalchemy import select
    from src.models.exercise import ExerciseNote
    result = await db_session.execute(select(ExerciseNote).where(ExerciseNote.workout_note_id == note.id))
    ex_notes = list(result.scalars().all())
    
    assert len(ex_notes) == 2
    assert ex_notes[0].exercise_id in [ex1.id, ex2.id]

@pytest.mark.asyncio
async def test_format_description_preview():
    from src.bot.utils import format_description_preview
    short_desc = "Короткое описание тренировки."
    res = await format_description_preview(short_desc, title="Тест")
    assert res == short_desc
    
    long_desc = "А" * 400
    res_long = await format_description_preview(long_desc, title="Тест")
    assert "(полное описание:" in res_long or "telegra.ph" in res_long
