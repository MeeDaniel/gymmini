from aiogram import Router, F
from aiogram.filters import CommandStart
from aiogram.types import Message, CallbackQuery

from src.bot.messages import Messages
from src.bot.keyboards import get_main_menu
from src.bot.callbacks import MenuCallback
from src.services.user import get_or_create_user

router = Router()

from src.db.database import get_db_session

from aiogram.fsm.context import FSMContext

@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext):
    await state.clear()
    async for session in get_db_session():
        user = await get_or_create_user(session, message.from_user.id, message.from_user.username)
    await message.answer(
        text=Messages.START_MESSAGE.format(name=message.from_user.first_name),
        reply_markup=get_main_menu()
    )

@router.callback_query(MenuCallback.filter(F.action == "cancel"))
async def cb_cancel(callback: CallbackQuery, state):
    await state.clear()
    await callback.message.edit_text(Messages.MAIN_MENU, reply_markup=get_main_menu())
