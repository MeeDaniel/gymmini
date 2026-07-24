from sqlalchemy import ForeignKey, String, Text, Float
from sqlalchemy.orm import Mapped, mapped_column, relationship
from src.db.base import Base

class Exercise(Base):
    __tablename__ = "exercises"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    name: Mapped[str] = mapped_column(String(255))
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    image_path: Mapped[str | None] = mapped_column(String(255), nullable=True)

    user: Mapped["User"] = relationship(back_populates="exercises")
    notes: Mapped[list["ExerciseNote"]] = relationship(back_populates="exercise")


class ExerciseNote(Base):
    __tablename__ = "exercise_notes"

    id: Mapped[int] = mapped_column(primary_key=True)
    exercise_id: Mapped[int] = mapped_column(ForeignKey("exercises.id"))
    workout_note_id: Mapped[int] = mapped_column(ForeignKey("workout_notes.id"))
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    exercise: Mapped["Exercise"] = relationship(back_populates="notes")
    workout_note: Mapped["WorkoutNote"] = relationship(back_populates="exercise_notes")
    sets: Mapped[list["Set"]] = relationship(back_populates="exercise_note")


class Set(Base):
    __tablename__ = "sets"

    id: Mapped[int] = mapped_column(primary_key=True)
    exercise_note_id: Mapped[int] = mapped_column(ForeignKey("exercise_notes.id"))
    reps: Mapped[int | None] = mapped_column(nullable=True)
    weight: Mapped[float | None] = mapped_column(Float, nullable=True)
    duration: Mapped[float | None] = mapped_column(Float, nullable=True)
    distance: Mapped[float | None] = mapped_column(Float, nullable=True)

    exercise_note: Mapped["ExerciseNote"] = relationship(back_populates="sets")
