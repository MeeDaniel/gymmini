import pytest
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from src.services.user import create_user, get_or_create_user
from src.services.workout import create_workout, create_workout_note_from_template, get_workout_notes_for_user
from src.services.exercise import create_exercise, create_exercise_note_from_template, add_set_to_exercise_note
from src.models.exercise import ExerciseType

@pytest.mark.asyncio
async def test_user_crud(db_session: AsyncSession):
    user = await create_user(db_session, telegram_id=123, telegram_alias="testuser")
    assert user.id is not None
    assert user.telegram_alias == "testuser"
    
    fetched = await get_or_create_user(db_session, telegram_id=123)
    assert fetched.id == user.id

@pytest.mark.asyncio
async def test_workout_flow(db_session: AsyncSession):
    user = await create_user(db_session, telegram_id=456)
    
    # Template
    workout = await create_workout(db_session, user.id, brief="Leg Day", description="Squats")
    assert workout.id is not None
    
    # Note
    note = await create_workout_note_from_template(db_session, workout.id, started_at=datetime.now())
    assert note.brief == "Leg Day"
    assert note.workout_id == workout.id
    
    notes = await get_workout_notes_for_user(db_session, user.id)
    assert len(notes) == 1
    assert notes[0].id == note.id

@pytest.mark.asyncio
async def test_exercise_flow(db_session: AsyncSession):
    user = await create_user(db_session, telegram_id=789)
    workout = await create_workout(db_session, user.id, brief="Arm Day")
    workout_note = await create_workout_note_from_template(db_session, workout.id, started_at=datetime.now())
    
    # Exercise Template
    exercise = await create_exercise(db_session, user.id, name="Bicep Curl", ex_type=ExerciseType.strength, image_path="media/bicep.jpg")
    assert exercise.id is not None
    
    # Exercise Note
    exercise_note = await create_exercise_note_from_template(db_session, exercise.id, workout_note.id, notes="Felt good")
    assert exercise_note.workout_note_id == workout_note.id
    assert exercise_note.notes == "Felt good"
    
    # Set
    s = await add_set_to_exercise_note(db_session, exercise_note.id, reps=10, weight=15.5)
    assert s.reps == 10
    assert s.weight == 15.5
