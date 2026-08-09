from aiogram import Router, F
from aiogram.types import CallbackQuery, Message, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from src.bot.messages import Messages
from src.bot.keyboards import get_history_menu, get_main_menu
from src.bot.callbacks import MenuCallback, PaginationCallback, HistoryCallback, TemplateCallback
from src.bot.states import EditHistoryState, DeleteHistoryState
from src.services.workout import get_workout_notes_for_user, get_workout_note, delete_workout_note
from src.db.database import get_db_session
from src.bot.utils import format_description_preview, send_card_with_optional_file, cleanup_previous_file, extract_description_text, edit_message_text_or_caption
from src.bot.formatters import format_set_text

router = Router()

PER_PAGE = 5

@router.callback_query(MenuCallback.filter(F.action == "history"))
async def list_history_menu(callback: CallbackQuery, state: FSMContext):
    await cleanup_previous_file(callback, state)
    await show_history_page(callback, 1)

@router.callback_query(PaginationCallback.filter(F.target == "history"))
async def paginate_history(callback: CallbackQuery, callback_data: PaginationCallback):
    await show_history_page(callback, callback_data.page)

async def show_history_page(callback: CallbackQuery, page: int):
    async for session in get_db_session():
        notes = await get_workout_notes_for_user(session, callback.from_user.id)
        total = len(notes)
        start_idx = (page - 1) * PER_PAGE
        end_idx = start_idx + PER_PAGE
        page_items = notes[start_idx:end_idx]
        
        await callback.message.edit_text(
            Messages.YOUR_HISTORY,
            reply_markup=get_history_menu(page_items, page, total)
        )
        return

async def show_history_page_answer(message: Message, user_id: int | None = None):
    uid = user_id or message.from_user.id
    async for session in get_db_session():
        notes = await get_workout_notes_for_user(session, uid)
        total = len(notes)
        page_items = notes[0:PER_PAGE]
        await message.answer(
            Messages.YOUR_HISTORY,
            reply_markup=get_history_menu(page_items, 1, total)
        )


async def show_history_card(target, note_id: int, state: FSMContext | None = None):
    async for session in get_db_session():
        note = await get_workout_note(session, note_id)
        if not note:
            return
            
        text = f"📖 Тренировка: {note.brief}\n"
        text += f"Дата начала: {note.started_at.strftime('%d-%m-%Y %H:%M')}\n"
        desc_str = await format_description_preview(note.description, title=note.brief)
        if note.description:
            text += f"Описание:\n{desc_str}\n"
        text += "\n"
        
        for ex_note in note.exercise_notes:
            text += f"🏋️ {ex_note.exercise.name}:\n"
            if ex_note.sets:
                for i, s in enumerate(ex_note.sets, 1):
                    text += f"  {i}. {format_set_text(s)}\n"
            else:
                text += "  (нет подходов)\n"
            text += "\n"
                
        keyboard = [
            [InlineKeyboardButton(text="▶️ Продолжить", callback_data=HistoryCallback(action="continue", id=note.id).pack())]
        ]
        if note.workout_id:
            keyboard.append([InlineKeyboardButton(text="📋 Перейти к шаблону", callback_data=TemplateCallback(action="view", id=note.workout_id).pack())])
        
        keyboard.extend([
            [InlineKeyboardButton(text="✏️ Изменить название", callback_data=HistoryCallback(action="edit_brief", id=note.id).pack()),
             InlineKeyboardButton(text="✏️ Изменить описание", callback_data=HistoryCallback(action="edit_desc", id=note.id).pack())],
            [InlineKeyboardButton(text="✏️ Изменить время начала", callback_data=HistoryCallback(action="edit_time", id=note.id).pack())],
            [InlineKeyboardButton(text="🗑 Удалить тренировку", callback_data=HistoryCallback(action="delete", id=note.id).pack())],
            [InlineKeyboardButton(text=Messages.BTN_BACK, callback_data=MenuCallback(action="history").pack())]
        ])
        await send_card_with_optional_file(
            target=target,
            title=note.brief,
            description=note.description,
            card_text=text,
            reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard),
            state=state
        )

@router.callback_query(HistoryCallback.filter(F.action == "view"))
async def view_history(callback: CallbackQuery, callback_data: HistoryCallback, state: FSMContext):
    await state.clear()
    await show_history_card(callback, callback_data.id, state)
    return

@router.callback_query(HistoryCallback.filter(F.action == "edit_brief"))
async def edit_history_brief_start(callback: CallbackQuery, callback_data: HistoryCallback, state: FSMContext):
    await cleanup_previous_file(callback, state)
    await state.set_state(EditHistoryState.waiting_for_brief)
    await state.update_data(note_id=callback_data.id, prompt_msg_id=callback.message.message_id)
    keyboard = [[InlineKeyboardButton(text="❌ Отмена", callback_data=HistoryCallback(action="view", id=callback_data.id).pack())]]
    await edit_message_text_or_caption(callback.message, Messages.ASK_NEW_HISTORY_BRIEF, reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard))

@router.message(EditHistoryState.waiting_for_brief)
async def process_edit_history_brief(message: Message, state: FSMContext):
    try: await message.delete()
    except: pass
    if not message.text or not message.text.strip(): return
    
    data = await state.get_data()
    n_id = data.get("note_id")
    
    if data.get("prompt_msg_id"):
        try: await message.bot.delete_message(message.chat.id, data["prompt_msg_id"])
        except: pass
        
    async for session in get_db_session():
        n = await get_workout_note(session, n_id)
        if n:
            n.brief = message.text.strip()
            await session.commit()
    await state.clear()
    await show_history_card(message, n_id, state)

@router.callback_query(HistoryCallback.filter(F.action == "edit_desc"))
async def edit_history_desc_start(callback: CallbackQuery, callback_data: HistoryCallback, state: FSMContext):
    await cleanup_previous_file(callback, state)
    await state.set_state(EditHistoryState.waiting_for_desc)
    await state.update_data(note_id=callback_data.id, prompt_msg_id=callback.message.message_id)
    keyboard = [[InlineKeyboardButton(text="❌ Отмена", callback_data=HistoryCallback(action="view", id=callback_data.id).pack())]]
    await edit_message_text_or_caption(callback.message, Messages.ASK_NEW_HISTORY_DESC, reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard))

@router.message(EditHistoryState.waiting_for_desc)
async def process_edit_history_desc(message: Message, state: FSMContext):
    try: await message.delete()
    except: pass
    
    new_desc, err = await extract_description_text(message)
    if err: return
        
    data = await state.get_data()
    n_id = data.get("note_id")
    
    if data.get("prompt_msg_id"):
        try: await message.bot.delete_message(message.chat.id, data["prompt_msg_id"])
        except: pass
        
    async for session in get_db_session():
        n = await get_workout_note(session, n_id)
        if n:
            n.description = new_desc
            await session.commit()
    await state.clear()
    await show_history_card(message, n_id, state)

@router.callback_query(HistoryCallback.filter(F.action == "edit_time"))
async def edit_history_time_start(callback: CallbackQuery, callback_data: HistoryCallback, state: FSMContext):
    await cleanup_previous_file(callback, state)
    await state.set_state(EditHistoryState.waiting_for_time)
    await state.update_data(note_id=callback_data.id, prompt_msg_id=callback.message.message_id)
    keyboard = [
        [InlineKeyboardButton(text="🕒 Сейчас", callback_data=HistoryCallback(action="time_now", id=callback_data.id).pack())],
        [InlineKeyboardButton(text="❌ Отмена", callback_data=HistoryCallback(action="view", id=callback_data.id).pack())]
    ]
    await edit_message_text_or_caption(
        callback.message,
        "Введите новое время начала в формате 'DD-MM-YYYY HH:MM' или нажмите 'Сейчас':",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard)
    )

@router.callback_query(HistoryCallback.filter(F.action == "time_now"))
async def process_history_time_now(callback: CallbackQuery, callback_data: HistoryCallback, state: FSMContext):
    from datetime import datetime
    async for session in get_db_session():
        n = await get_workout_note(session, callback_data.id)
        if n:
            n.started_at = datetime.now()
            await session.commit()
    await state.clear()
    await show_history_card(callback, callback_data.id, state)

@router.message(EditHistoryState.waiting_for_time)
async def process_edit_history_time(message: Message, state: FSMContext):
    try: await message.delete()
    except: pass
    if not message.text: return
    
    data = await state.get_data()
    n_id = data.get("note_id")
    prompt_msg_id = data.get("prompt_msg_id")
    
    from datetime import datetime
    try:
        new_time = datetime.strptime(message.text.strip(), "%d-%m-%Y %H:%M")
        
        if prompt_msg_id:
            try: await message.bot.delete_message(message.chat.id, prompt_msg_id)
            except: pass
            
        async for session in get_db_session():
            n = await get_workout_note(session, n_id)
            if n:
                n.started_at = new_time
                await session.commit()
        await state.clear()
        await show_history_card(message, n_id, state)
    except ValueError:
        if prompt_msg_id:
            try:
                keyboard = [
                    [InlineKeyboardButton(text="🕒 Сейчас", callback_data=HistoryCallback(action="time_now", id=n_id).pack())],
                    [InlineKeyboardButton(text="❌ Отмена", callback_data=HistoryCallback(action="view", id=n_id).pack())]
                ]
                await message.bot.edit_message_text(
                    f"❌ Неверный формат времени!\n\nВведите новое время начала в формате 'DD-MM-YYYY HH:MM' или нажмите 'Сейчас':",
                    chat_id=message.chat.id,
                    message_id=prompt_msg_id,
                    reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard)
                )
            except: pass

@router.callback_query(HistoryCallback.filter(F.action == "delete"))
async def delete_history_start(callback: CallbackQuery, callback_data: HistoryCallback, state: FSMContext):
    await cleanup_previous_file(callback, state)
    async for session in get_db_session():
        n = await get_workout_note(session, callback_data.id)
        if not n: return
        await state.set_state(DeleteHistoryState.waiting_for_confirm)
        await state.update_data(note_id=n.id, expected_brief=n.brief, prompt_msg_id=callback.message.message_id)
        text = Messages.ASK_DELETE_HISTORY_CONFIRM.format(brief=n.brief)
        keyboard = [[InlineKeyboardButton(text=Messages.BTN_CANCEL, callback_data=HistoryCallback(action="view", id=n.id).pack())]]
        await edit_message_text_or_caption(callback.message, text, reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard))

@router.message(DeleteHistoryState.waiting_for_confirm)
async def process_delete_history_confirm(message: Message, state: FSMContext):
    try: await message.delete()
    except: pass
    if not message.text: return
    
    data = await state.get_data()
    n_id = data.get("note_id")
    expected_brief = data.get("expected_brief")
    prompt_msg_id = data.get("prompt_msg_id")
    
    if message.text.strip() == expected_brief.strip():
        if prompt_msg_id:
            try: await message.bot.delete_message(message.chat.id, prompt_msg_id)
            except: pass
            
        async for session in get_db_session():
            await delete_workout_note(session, n_id)
        await state.clear()
        
        async for session in get_db_session():
            notes = await get_workout_notes_for_user(session, message.from_user.id)
            total = len(notes)
            page_items = notes[0:PER_PAGE]
            text = f"✅ {Messages.HISTORY_DELETED}\n\n{Messages.YOUR_HISTORY}"
            await message.answer(text, reply_markup=get_history_menu(page_items, 1, total))
    else:
        if prompt_msg_id:
            try:
                keyboard = [[InlineKeyboardButton(text=Messages.BTN_CANCEL, callback_data=HistoryCallback(action="view", id=n_id).pack())]]
                text = f"❌ Название не совпадает.\n\n" + Messages.ASK_DELETE_HISTORY_CONFIRM.format(brief=expected_brief)
                await message.bot.edit_message_text(text, chat_id=message.chat.id, message_id=prompt_msg_id, reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard))
            except: pass
