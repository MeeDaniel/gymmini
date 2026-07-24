from datetime import date
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from src.models.workout import Workout, WorkoutNote

async def create_workout(session: AsyncSession, user_id: int, brief: str, description: str | None = None) -> Workout:
    workout = Workout(user_id=user_id, brief=brief, description=description)
    session.add(workout)
    await session.commit()
    await session.refresh(workout)
    return workout

async def get_workouts_for_user(session: AsyncSession, user_id: int) -> list[Workout]:
    result = await session.execute(select(Workout).where(Workout.user_id == user_id))
    return list(result.scalars().all())

async def get_workout(session: AsyncSession, workout_id: int) -> Workout | None:
    result = await session.execute(select(Workout).where(Workout.id == workout_id))
    return result.scalar_one_or_none()

async def create_workout_note_from_template(
    session: AsyncSession, 
    workout_id: int, 
    current_date: date, 
    current_time: str | None = None
) -> WorkoutNote | None:
    workout = await get_workout(session, workout_id)
    if not workout:
        return None
    
    note = WorkoutNote(
        user_id=workout.user_id,
        workout_id=workout.id,
        brief=workout.brief,
        description=workout.description,
        date=current_date,
        time=current_time
    )
    session.add(note)
    await session.commit()
    await session.refresh(note)
    return note

async def get_workout_notes_for_user(session: AsyncSession, user_id: int) -> list[WorkoutNote]:
    result = await session.execute(
        select(WorkoutNote)
        .where(WorkoutNote.user_id == user_id)
        .options(selectinload(WorkoutNote.exercise_notes))
        .order_by(WorkoutNote.date.desc(), WorkoutNote.id.desc())
    )
    return list(result.scalars().all())
