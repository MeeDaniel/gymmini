from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from src.models.user import User

async def get_user_by_telegram_id(session: AsyncSession, telegram_id: int) -> User | None:
    result = await session.execute(select(User).where(User.telegram_id == telegram_id))
    return result.scalar_one_or_none()

async def create_user(session: AsyncSession, telegram_id: int, telegram_alias: str | None = None) -> User:
    user = User(telegram_id=telegram_id, telegram_alias=telegram_alias)
    session.add(user)
    await session.commit()
    await session.refresh(user)
    return user

async def get_or_create_user(session: AsyncSession, telegram_id: int, telegram_alias: str | None = None) -> User:
    user = await get_user_by_telegram_id(session, telegram_id)
    if not user:
        user = await create_user(session, telegram_id, telegram_alias)
    return user
