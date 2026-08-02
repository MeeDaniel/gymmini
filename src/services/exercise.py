from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from src.models.exercise import Exercise, ExerciseNote, Set, ExerciseType

async def create_exercise(session: AsyncSession, user_id: int, name: str, ex_type: ExerciseType, description: str | None = None, image_path: str | None = None) -> Exercise:
    exercise = Exercise(user_id=user_id, name=name, type=ex_type, description=description, image_path=image_path)
    session.add(exercise)
    await session.commit()
    await session.refresh(exercise)
    return exercise

async def get_exercises_for_user(session: AsyncSession, user_id: int) -> list[Exercise]:
    result = await session.execute(select(Exercise).where(Exercise.user_id == user_id).order_by(Exercise.id.asc()))
    return list(result.scalars().all())

async def get_exercise(session: AsyncSession, exercise_id: int) -> Exercise | None:
    result = await session.execute(select(Exercise).where(Exercise.id == exercise_id))
    return result.scalar_one_or_none()

async def check_exercise_usage(session: AsyncSession, exercise_id: int) -> tuple[int, int]:
    from sqlalchemy import func
    from src.models.workout import workout_exercises
    hist_stmt = select(func.count()).select_from(ExerciseNote).where(
        ExerciseNote.exercise_id == exercise_id,
        ExerciseNote.workout_note_id.is_not(None)
    )
    hist_res = await session.execute(hist_stmt)
    history_count = hist_res.scalar() or 0

    tmpl_stmt = select(func.count()).select_from(workout_exercises).where(
        workout_exercises.c.exercise_id == exercise_id
    )
    tmpl_res = await session.execute(tmpl_stmt)
    template_count = tmpl_res.scalar() or 0

    return template_count, history_count

async def delete_exercise(session: AsyncSession, exercise_id: int) -> tuple[bool, str | None]:
    template_count, history_count = await check_exercise_usage(session, exercise_id)
    if template_count > 0 or history_count > 0:
        return False, f"⚠️ Невозможно удалить упражнение: оно используется в {template_count} шаблонах и {history_count} записях истории. Сначала удалите его оттуда."
    ex = await get_exercise(session, exercise_id)
    if ex:
        await session.delete(ex)
        await session.commit()
        return True, None
    return False, "Упражнение не найдено."

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

async def update_exercise_note(session: AsyncSession, exercise_note_id: int, notes: str | None = None):
    stmt = select(ExerciseNote).where(ExerciseNote.id == exercise_note_id)
    result = await session.execute(stmt)
    note = result.scalar_one_or_none()
    if note:
        note.notes = notes
        await session.commit()
    return note
