from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from src.models.exercise import Exercise, ExerciseNote, Set

async def create_exercise(session: AsyncSession, user_id: int, name: str, description: str | None = None, image_path: str | None = None) -> Exercise:
    exercise = Exercise(user_id=user_id, name=name, description=description, image_path=image_path)
    session.add(exercise)
    await session.commit()
    await session.refresh(exercise)
    return exercise

async def get_exercises_for_user(session: AsyncSession, user_id: int) -> list[Exercise]:
    result = await session.execute(select(Exercise).where(Exercise.user_id == user_id))
    return list(result.scalars().all())

async def get_exercise(session: AsyncSession, exercise_id: int) -> Exercise | None:
    result = await session.execute(select(Exercise).where(Exercise.id == exercise_id))
    return result.scalar_one_or_none()

async def create_exercise_note_from_template(
    session: AsyncSession, 
    exercise_id: int, 
    workout_note_id: int,
    notes: str | None = None
) -> ExerciseNote | None:
    exercise = await get_exercise(session, exercise_id)
    if not exercise:
        return None
    
    note = ExerciseNote(
        exercise_id=exercise.id,
        workout_note_id=workout_note_id,
        notes=notes
    )
    session.add(note)
    await session.commit()
    await session.refresh(note)
    return note

async def add_set_to_exercise_note(
    session: AsyncSession, 
    exercise_note_id: int, 
    reps: int | None = None, 
    weight: float | None = None, 
    duration: float | None = None, 
    distance: float | None = None
) -> Set:
    new_set = Set(
        exercise_note_id=exercise_note_id,
        reps=reps,
        weight=weight,
        duration=duration,
        distance=distance
    )
    session.add(new_set)
    await session.commit()
    await session.refresh(new_set)
    return new_set
