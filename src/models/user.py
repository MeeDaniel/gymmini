from sqlalchemy import BigInteger, String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from src.db.base import Base

class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    telegram_id: Mapped[int] = mapped_column(BigInteger, unique=True, index=True)
    telegram_alias: Mapped[str | None] = mapped_column(String, nullable=True)

    workouts: Mapped[list["Workout"]] = relationship(back_populates="user")
    exercises: Mapped[list["Exercise"]] = relationship(back_populates="user")
    workout_notes: Mapped[list["WorkoutNote"]] = relationship(back_populates="user")
