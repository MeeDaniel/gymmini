from sqlalchemy import ForeignKey, String, Text, Date, Table, Column, Integer, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship
from src.db.base import Base
from datetime import datetime

workout_exercises = Table(
    "workout_exercises",
    Base.metadata,
    Column("workout_id", Integer, ForeignKey("workouts.id", ondelete="CASCADE"), primary_key=True),
    Column("exercise_id", Integer, ForeignKey("exercises.id", ondelete="CASCADE"), primary_key=True),
    Column("sort_order", Integer, default=0)
)

class Workout(Base):
    __tablename__ = "workouts"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    brief: Mapped[str] = mapped_column(String(255))
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    user: Mapped["User"] = relationship(back_populates="workouts")
    notes: Mapped[list["WorkoutNote"]] = relationship(back_populates="workout")
    exercises: Mapped[list["Exercise"]] = relationship(
        secondary=workout_exercises, 
        back_populates="workouts",
        order_by="workout_exercises.c.sort_order",
    )


class WorkoutNote(Base):
    __tablename__ = "workout_notes"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    workout_id: Mapped[int | None] = mapped_column(ForeignKey("workouts.id", ondelete="SET NULL"), nullable=True)
    brief: Mapped[str] = mapped_column(String(255))
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    started_at: Mapped[datetime] = mapped_column(DateTime)

    user: Mapped["User"] = relationship(back_populates="workout_notes")
    workout: Mapped["Workout"] = relationship(back_populates="notes")
    exercise_notes: Mapped[list["ExerciseNote"]] = relationship(
        back_populates="workout_note",
        order_by="ExerciseNote.sort_order",
        cascade="all, delete-orphan"
    )
