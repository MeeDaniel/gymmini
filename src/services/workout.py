from datetime import datetime
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from src.models.workout import Workout, WorkoutNote
from src.models.exercise import Exercise, ExerciseNote, Set

async def create_workout(session: AsyncSession, user_id: int, brief: str, description: str | None = None) -> Workout:
    workout = Workout(user_id=user_id, brief=brief, description=description)
    session.add(workout)
    await session.commit()
    await session.refresh(workout)
    return workout

async def get_workouts_for_user(session: AsyncSession, user_id: int) -> list[Workout]:
    result = await session.execute(select(Workout).where(Workout.user_id == user_id).order_by(Workout.id.asc()))
    return list(result.scalars().all())

async def get_workout(session: AsyncSession, workout_id: int) -> Workout | None:
    result = await session.execute(
        select(Workout)
        .where(Workout.id == workout_id)
        .options(selectinload(Workout.exercises))
    )
    return result.scalar_one_or_none()

async def create_workout_note_from_template(
    session: AsyncSession, 
    workout_id: int, 
    started_at: datetime
) -> WorkoutNote | None:
    workout = await get_workout(session, workout_id)
    if not workout:
        return None
    
    note = WorkoutNote(
        user_id=workout.user_id,
        workout_id=workout.id,
        brief=workout.brief,
        description=workout.description,
        started_at=started_at
    )
    session.add(note)
    await session.commit()
    await session.refresh(note)

    for exercise in workout.exercises:
        ex_note = ExerciseNote(
            exercise_id=exercise.id,
            workout_note_id=note.id
        )
        session.add(ex_note)

    if workout.exercises:
        await session.commit()

    return note

async def get_workout_notes_for_user(session: AsyncSession, user_id: int) -> list[WorkoutNote]:
    result = await session.execute(
        select(WorkoutNote)
        .where(WorkoutNote.user_id == user_id)
        .options(selectinload(WorkoutNote.exercise_notes).selectinload(ExerciseNote.exercise))
        .options(selectinload(WorkoutNote.exercise_notes).selectinload(ExerciseNote.sets))
        .order_by(WorkoutNote.started_at.desc(), WorkoutNote.id.desc())
    )
    return list(result.scalars().all())

async def get_workout_note(session: AsyncSession, note_id: int) -> WorkoutNote | None:
    result = await session.execute(
        select(WorkoutNote)
        .where(WorkoutNote.id == note_id)
        .options(selectinload(WorkoutNote.exercise_notes).selectinload(ExerciseNote.exercise))
        .options(selectinload(WorkoutNote.exercise_notes).selectinload(ExerciseNote.sets))
    )
    return result.scalar_one_or_none()

from src.models.workout import workout_exercises
from sqlalchemy import insert, delete, update

async def add_exercise_to_workout(session: AsyncSession, workout_id: int, exercise_id: int) -> None:
    # Lock workout to prevent race conditions
    await session.execute(select(Workout.id).where(Workout.id == workout_id).with_for_update())
    
    # Check if already exists
    result = await session.execute(
        select(workout_exercises.c.exercise_id)
        .where(workout_exercises.c.workout_id == workout_id, workout_exercises.c.exercise_id == exercise_id)
    )
    if result.scalar_one_or_none() is not None:
        return
        
    # Get max order
    result = await session.execute(
        select(workout_exercises.c.sort_order)
        .where(workout_exercises.c.workout_id == workout_id)
        .order_by(workout_exercises.c.sort_order.desc())
        .limit(1)
    )
    max_order = result.scalar_one_or_none() or 0
    
    await session.execute(
        insert(workout_exercises).values(workout_id=workout_id, exercise_id=exercise_id, sort_order=max_order + 1)
    )
    await session.commit()

async def remove_exercise_from_workout(session: AsyncSession, workout_id: int, exercise_id: int) -> None:
    await session.execute(
        delete(workout_exercises)
        .where(workout_exercises.c.workout_id == workout_id, workout_exercises.c.exercise_id == exercise_id)
    )
    await session.commit()

async def move_exercise_in_workout(session: AsyncSession, workout_id: int, exercise_id: int, direction: int) -> None:
    # direction: -1 for UP, 1 for DOWN
    await session.execute(select(Workout.id).where(Workout.id == workout_id).with_for_update())
    
    result = await session.execute(
        select(workout_exercises.c.exercise_id, workout_exercises.c.sort_order)
        .where(workout_exercises.c.workout_id == workout_id)
        .order_by(workout_exercises.c.sort_order)
    )
    exercises = list(result.all())
    
    idx = -1
    for i, ex in enumerate(exercises):
        if ex.exercise_id == exercise_id:
            idx = i
            break
            
    if idx == -1: return
    
    swap_idx = idx + direction
    if swap_idx < 0 or swap_idx >= len(exercises):
        return
        
    ex1 = exercises[idx]
    ex2 = exercises[swap_idx]
    
    await session.execute(
        update(workout_exercises)
        .where(workout_exercises.c.workout_id == workout_id, workout_exercises.c.exercise_id == ex1.exercise_id)
        .values(sort_order=ex2.sort_order)
    )
    await session.execute(
        update(workout_exercises)
        .where(workout_exercises.c.workout_id == workout_id, workout_exercises.c.exercise_id == ex2.exercise_id)
        .values(sort_order=ex1.sort_order)
    )
    await session.commit()

async def add_exercise_to_workout_note(session: AsyncSession, note_id: int, exercise_id: int) -> None:
    ex_note = ExerciseNote(exercise_id=exercise_id, workout_note_id=note_id)
    session.add(ex_note)
    await session.commit()

async def delete_workout(session: AsyncSession, workout_id: int):
    workout = await get_workout(session, workout_id)
    if workout:
        await session.delete(workout)
        await session.commit()

async def delete_workout_note(session: AsyncSession, note_id: int):
    note = await get_workout_note(session, note_id)
    if note:
        await session.delete(note)
        await session.commit()

async def delete_exercise_note_from_workout(session: AsyncSession, ex_note_id: int):
    result = await session.execute(select(ExerciseNote).where(ExerciseNote.id == ex_note_id))
    ex_note = result.scalar_one_or_none()
    if ex_note:
        await session.delete(ex_note)
        await session.commit()
