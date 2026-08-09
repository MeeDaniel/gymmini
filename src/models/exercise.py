from sqlalchemy import ForeignKey, String, Text, Float, Enum, Numeric, CheckConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from src.db.base import Base
import enum

class ExerciseType(str, enum.Enum):
    strength = "strength"
    cardio = "cardio"
    bodyweight = "bodyweight"
    timed = "timed"

class Exercise(Base):
    __tablename__ = "exercises"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    name: Mapped[str] = mapped_column(String(255))
    type: Mapped[ExerciseType] = mapped_column(Enum(ExerciseType), default=ExerciseType.strength)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    image_path: Mapped[str | None] = mapped_column(String(255), nullable=True)

    user: Mapped["User"] = relationship(back_populates="exercises")
    notes: Mapped[list["ExerciseNote"]] = relationship(back_populates="exercise", cascade="all, delete-orphan")
    workouts: Mapped[list["Workout"]] = relationship(secondary="workout_exercises", back_populates="exercises")


class ExerciseNote(Base):
    __tablename__ = "exercise_notes"

    id: Mapped[int] = mapped_column(primary_key=True)
    exercise_id: Mapped[int] = mapped_column(ForeignKey("exercises.id"))
    workout_note_id: Mapped[int] = mapped_column(ForeignKey("workout_notes.id"))
    sort_order: Mapped[int] = mapped_column(default=0)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    exercise: Mapped["Exercise"] = relationship(back_populates="notes")
    workout_note: Mapped["WorkoutNote"] = relationship(back_populates="exercise_notes")
    sets: Mapped[list["Set"]] = relationship(back_populates="exercise_note", order_by="Set.sort_order", cascade="all, delete-orphan")


class Set(Base):
    __tablename__ = "sets"

    id: Mapped[int] = mapped_column(primary_key=True)
    exercise_note_id: Mapped[int] = mapped_column(ForeignKey("exercise_notes.id"))
    sort_order: Mapped[int] = mapped_column(default=0)
    reps: Mapped[int | None] = mapped_column(CheckConstraint("reps >= 0"), nullable=True)
    weight: Mapped[float | None] = mapped_column(Numeric(6, 2), CheckConstraint("weight >= 0"), nullable=True)
    duration: Mapped[float | None] = mapped_column(Float, CheckConstraint("duration >= 0"), nullable=True)
    distance: Mapped[float | None] = mapped_column(Float, CheckConstraint("distance >= 0"), nullable=True)

    exercise_note: Mapped["ExerciseNote"] = relationship(back_populates="sets")
