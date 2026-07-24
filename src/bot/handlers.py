from aiogram import Router
from aiogram.filters import CommandStart
from aiogram.types import Message
from src.db.database import async_session_maker
from src.services.user import get_or_create_user

from src.bot.messages import Messages

router = Router()

@router.message(CommandStart())
async def command_start_handler(message: Message) -> None:
    async with async_session_maker() as session:
        user = await get_or_create_user(
            session, 
            telegram_id=message.from_user.id, 
            telegram_alias=message.from_user.username
        )
    text = Messages.START_MESSAGE.format(name=message.from_user.full_name)
    await message.answer(text)
