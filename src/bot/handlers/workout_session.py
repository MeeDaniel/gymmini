import re
from datetime import datetime
from aiogram import Router, F
from aiogram.types import CallbackQuery, Message, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from src.bot.messages import Messages
from src.bot.keyboards import get_time_now_menu, get_main_menu
from src.bot.callbacks import MenuCallback, TemplateCallback, PaginationCallback
from src.bot.states import WorkoutSessionState
from src.services.workout import create_workout_note_from_template, get_workout, get_workout_note
from src.services.exercise import add_set_to_exercise_note
from src.bot.formatters import parse_set_input, format_set_text
from src.db.database import get_db_session
from src.bot.keyboards import get_active_workout_menu, get_active_exercise_menu, get_active_workout_settings_menu
from src.bot.utils import cleanup_previous_file
from src.bot.handlers.history import show_history_card

router = Router()

@router.callback_query(MenuCallback.filter(F.action == "start_workout"))
async def start_workout(callback: CallbackQuery, state: FSMContext):
    await show_templates_start_page(callback, 1)

@router.callback_query(PaginationCallback.filter(F.target == "templates_start"))
async def paginate_templates_start(callback: CallbackQuery, callback_data: PaginationCallback):
    await show_templates_start_page(callback, callback_data.page)

async def show_templates_start_page(callback: CallbackQuery, page: int):
    PER_PAGE = 5
    from src.bot.keyboards import get_templates_start_menu
    from src.services.workout import get_workouts_for_user
    async for session in get_db_session():
        templates = await get_workouts_for_user(session, callback.from_user.id)
        if not templates:
            await callback.answer("У вас нет шаблонов тренировок! Сначала создайте шаблон.", show_alert=True)
            return
        
        total = len(templates)
        start_idx = (page - 1) * PER_PAGE
        end_idx = start_idx + PER_PAGE
        page_items = templates[start_idx:end_idx]
        
        await callback.message.edit_text(
            "Выберите шаблон тренировки для старта:",
            reply_markup=get_templates_start_menu(page_items, page, total)
        )

@router.callback_query(TemplateCallback.filter(F.action == "start"))
async def start_template_workout(callback: CallbackQuery, callback_data: TemplateCallback, state: FSMContext):
    await cleanup_previous_file(callback, state)
    await state.set_state(WorkoutSessionState.waiting_for_supplement)
    await state.update_data(workout_id=callback_data.id, prompt_msg_id=callback.message.message_id)
    keyboard = [
        [InlineKeyboardButton(text="Пропустить", callback_data=MenuCallback(action="skip_supplement").pack())],
        [InlineKeyboardButton(text="❌ Отмена", callback_data=TemplateCallback(action="view", id=callback_data.id).pack())]
    ]
    await callback.message.edit_text(
        "Введите дополнение к названию тренировки (например, 'лёгкая неделя') или нажмите 'Пропустить':",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard)
    )

@router.callback_query(WorkoutSessionState.waiting_for_supplement, MenuCallback.filter(F.action == "skip_supplement"))
async def skip_workout_supplement(callback: CallbackQuery, state: FSMContext):
    await state.update_data(supplement=None)
    await state.set_state(WorkoutSessionState.waiting_for_started_at)
    await callback.message.edit_text(
        "Укажите время начала тренировки (в формате 'DD-MM-YYYY HH:MM' или просто нажмите 'Сейчас'):",
        reply_markup=get_time_now_menu()
    )

@router.message(WorkoutSessionState.waiting_for_supplement)
async def process_workout_supplement(message: Message, state: FSMContext):
    try: await message.delete()
    except: pass
    if not message.text: return
    
    await state.update_data(supplement=message.text.strip())
    await state.set_state(WorkoutSessionState.waiting_for_started_at)
    
    data = await state.get_data()
    if data.get("prompt_msg_id"):
        try:
            await message.bot.edit_message_text(
                "Укажите время начала тренировки (в формате 'DD-MM-YYYY HH:MM' или просто нажмите 'Сейчас'):",
                chat_id=message.chat.id,
                message_id=data["prompt_msg_id"],
                reply_markup=get_time_now_menu()
            )
        except: pass

@router.callback_query(WorkoutSessionState.waiting_for_started_at, MenuCallback.filter(F.action == "time_now"))
async def process_started_at_now(callback: CallbackQuery, state: FSMContext):
    started_at = datetime.now()
    await create_and_start_workout_session(callback, state, started_at)

@router.message(WorkoutSessionState.waiting_for_started_at)
async def process_started_at_manual(message: Message, state: FSMContext):
    try: await message.delete()
    except: pass
    if not message.text: return
    
    data = await state.get_data()
    prompt_msg_id = data.get("prompt_msg_id")
    
    try:
        text = message.text.strip()
        started_at = datetime.strptime(text, "%d-%m-%Y %H:%M")
        
        if prompt_msg_id:
            try: await message.bot.delete_message(message.chat.id, prompt_msg_id)
            except: pass
            
        await create_and_start_workout_session(message, state, started_at)
    except ValueError:
        if prompt_msg_id:
            try:
                await message.bot.edit_message_text(
                    f"❌ Неверный формат времени!\n\nУкажите время начала тренировки (в формате 'DD-MM-YYYY HH:MM' или просто нажмите 'Сейчас'):",
                    chat_id=message.chat.id,
                    message_id=prompt_msg_id,
                    reply_markup=get_time_now_menu()
                )
            except: pass

async def create_and_start_workout_session(message_or_callback, state: FSMContext, started_at: datetime):
    data = await state.get_data()
    workout_id = data["workout_id"]
    supplement = data.get("supplement")
    
    is_callback = isinstance(message_or_callback, CallbackQuery)
    message = message_or_callback.message if is_callback else message_or_callback
    
    async for session in get_db_session():
        note = await create_workout_note_from_template(session, workout_id, started_at)
        if not note:
            if is_callback:
                await message_or_callback.answer(Messages.WORKOUT_CREATE_ERROR)
            else:
                await message.answer(Messages.WORKOUT_CREATE_ERROR)
            await state.clear()
            return
        
        if supplement:
            note.brief = f"{note.brief} ({supplement})"
            await session.commit()
        
        await state.update_data(note_id=note.id)
        await state.set_state(WorkoutSessionState.active)
        await show_active_workout(message_or_callback, state, note.id)

from src.bot.callbacks import HistoryCallback
@router.callback_query(HistoryCallback.filter(F.action == "continue"))
async def continue_workout(callback: CallbackQuery, callback_data: HistoryCallback, state: FSMContext):
    await state.update_data(note_id=callback_data.id)
    await state.set_state(WorkoutSessionState.active)
    await show_active_workout(callback, state, callback_data.id)

async def show_active_workout(message_or_callback, state: FSMContext, note_id: int):
    async for session in get_db_session():
        note = await get_workout_note(session, note_id)
        if not note: return
        
        text = Messages.ACTIVE_WORKOUT_TITLE.format(brief=note.brief, started_at=note.started_at.strftime('%d-%m-%Y %H:%M'))
        
        for i, ex_note in enumerate(note.exercise_notes, 1):
            text += f"{i}. {ex_note.exercise.name}: {len(ex_note.sets)} подх.\n"
            
        markup = get_active_workout_menu(note.id, note.exercise_notes)
        
        if isinstance(message_or_callback, CallbackQuery):
            await message_or_callback.message.edit_text(text, reply_markup=markup)
        else:
            await message_or_callback.answer(text, reply_markup=markup)

async def show_active_exercise_page(target: CallbackQuery | Message, note_id: int, ex_note_id: int, state: FSMContext | None = None):
    async for session in get_db_session():
        note = await get_workout_note(session, note_id)
        if not note:
            return
        ex_note = next((en for en in note.exercise_notes if en.id == ex_note_id), None)
        if not ex_note:
            return
            
        text = f"🏋️ Выбрано: {ex_note.exercise.name}\n"
        if ex_note.notes:
            text += f"💬 Заметка: {ex_note.notes}\n"
            
        hints = {
            "strength": "Отправьте вес и повторения (например: '50x10', '60.5 12')",
            "cardio": "Отправьте дистанцию и время (например: '2.5км 15мин', '500м 45с')",
            "bodyweight": "Отправьте количество повторений (например: '15', '20 раз')",
            "timed": "Отправьте время выполнения (например: '60', '1 мин 30 с')"
        }
        ex_type_val = ex_note.exercise.type.value if hasattr(ex_note.exercise.type, "value") else str(ex_note.exercise.type)
        hint = hints.get(ex_type_val, "Отправьте в чат данные подхода.")
        text += f"{hint}\n\nТекущие подходы:\n"
        
        for i, s in enumerate(ex_note.sets, 1):
            text += f"  {i}. {format_set_text(s)}\n"
            
        if not ex_note.sets:
            text += "  (нет подходов)"
            
        reply_markup = get_active_exercise_menu(note_id, ex_note_id, has_note=bool(ex_note.notes))
        
        if isinstance(target, CallbackQuery):
            await target.message.edit_text(text, reply_markup=reply_markup)
            if state:
                await state.update_data(current_card_msg_id=target.message.message_id)
        else:
            msg_edited = False
            if state:
                data = await state.get_data()
                msg_id = data.get("current_card_msg_id")
                if msg_id:
                    try:
                        await target.bot.edit_message_text(
                            chat_id=target.chat.id,
                            message_id=msg_id,
                            text=text,
                            reply_markup=reply_markup
                        )
                        msg_edited = True
                    except Exception:
                        pass
            if not msg_edited:
                msg = await target.answer(text, reply_markup=reply_markup)
                if state:
                    await state.update_data(current_card_msg_id=msg.message_id)

@router.callback_query(WorkoutSessionState.active, MenuCallback.filter(F.action.startswith("exnote_")))
async def select_exercise_for_sets(callback: CallbackQuery, state: FSMContext):
    ex_note_id = int(callback.data.split("_")[1])
    await state.update_data(current_ex_note_id=ex_note_id, current_card_msg_id=callback.message.message_id)
    data = await state.get_data()
    note_id = data["note_id"]
    await show_active_exercise_page(callback, note_id, ex_note_id, state)

@router.callback_query(WorkoutSessionState.active, MenuCallback.filter(F.action.startswith("editnotes_")))
async def edit_exercise_note_start(callback: CallbackQuery, state: FSMContext):
    ex_note_id = int(callback.data.split("_")[1])
    await state.update_data(current_ex_note_id=ex_note_id)
    await state.set_state(WorkoutSessionState.waiting_for_edit_notes)
    data = await state.get_data()
    note_id = data["note_id"]
    keyboard = [
        [InlineKeyboardButton(text="🗑 Очистить заметку", callback_data=MenuCallback(action=f"wex_notes_clear_{ex_note_id}").pack())],
        [InlineKeyboardButton(text="❌ Отмена", callback_data=MenuCallback(action=f"wex_notes_cancel_{ex_note_id}").pack())]
    ]
    await callback.message.edit_text("Введите текст заметки к упражнению:", reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard))

@router.callback_query(WorkoutSessionState.waiting_for_edit_notes, MenuCallback.filter(F.action.startswith("clearnotes_") | F.action.startswith("wex_notes_clear")))
async def clear_exercise_note_text(callback: CallbackQuery, state: FSMContext):
    ex_note_id = int(callback.data.split("_")[-1])
    async for session in get_db_session():
        from src.services.exercise import update_exercise_note
        await update_exercise_note(session, ex_note_id, notes=None)
    await state.set_state(WorkoutSessionState.active)
    data = await state.get_data()
    note_id = data["note_id"]
    await show_active_exercise_page(callback, note_id, ex_note_id, state)

@router.callback_query(WorkoutSessionState.waiting_for_edit_notes, MenuCallback.filter(F.action.startswith("exnote_") | F.action.startswith("wex_notes_cancel")))
async def cancel_exercise_note_text(callback: CallbackQuery, state: FSMContext):
    ex_note_id = int(callback.data.split("_")[-1])
    await state.set_state(WorkoutSessionState.active)
    data = await state.get_data()
    note_id = data["note_id"]
    await show_active_exercise_page(callback, note_id, ex_note_id, state)

@router.message(WorkoutSessionState.waiting_for_edit_notes)
async def process_exercise_note_text(message: Message, state: FSMContext):
    try: await message.delete()
    except: pass
    if not message.text: return
    
    data = await state.get_data()
    ex_note_id = data.get("current_ex_note_id")
    note_id = data.get("note_id")
    async for session in get_db_session():
        from src.services.exercise import update_exercise_note
        await update_exercise_note(session, ex_note_id, notes=message.text.strip())
    await state.set_state(WorkoutSessionState.active)
    await show_active_exercise_page(message, note_id, ex_note_id, state)

@router.message(WorkoutSessionState.active)
async def process_new_set(message: Message, state: FSMContext):
    data = await state.get_data()
    ex_note_id = data.get("current_ex_note_id")
    note_id = data.get("note_id")
    
    if not ex_note_id:
        await message.answer("Сначала выберите упражнение из списка выше для добавления подхода.")
        return
        
    async for session in get_db_session():
        note = await get_workout_note(session, note_id)
        ex_note = next((en for en in note.exercise_notes if en.id == ex_note_id), None)
        if not ex_note: return
        
        parsed = parse_set_input(message.text, ex_note.exercise.type)
        if not parsed:
            await message.answer(Messages.SET_PARSE_ERROR)
            return
            
        # Add set
        await add_set_to_exercise_note(session, ex_note_id, **parsed)
        
        try:
            await message.delete()
        except Exception:
            pass
            
        await show_active_exercise_page(message, note_id, ex_note_id, state)

@router.callback_query(WorkoutSessionState.active, MenuCallback.filter(F.action.startswith("wnote_")))
async def back_to_active_workout(callback: CallbackQuery, state: FSMContext):
    await state.update_data(current_ex_note_id=None)
    data = await state.get_data()
    await show_active_workout(callback, state, data["note_id"])

from src.bot.callbacks import ActiveExCallback
from src.bot.keyboards import get_active_add_exercise_menu
from src.services.exercise import get_exercises_for_user
from src.services.workout import add_exercise_to_workout_note

@router.callback_query(WorkoutSessionState.active, MenuCallback.filter(F.action.startswith("addex_")))
async def add_ex_to_active_start(callback: CallbackQuery, state: FSMContext):
    note_id = int(callback.data.split("_")[1])
    await show_add_ex_active_page(callback, note_id, 1)

@router.callback_query(PaginationCallback.filter(F.target == "act_add_ex"))
async def paginate_active_add_ex(callback: CallbackQuery, callback_data: PaginationCallback):
    await show_add_ex_active_page(callback, callback_data.parent_id, callback_data.page)

async def show_add_ex_active_page(callback: CallbackQuery, note_id: int, page: int):
    PER_PAGE = 5
    async for session in get_db_session():
        exercises = await get_exercises_for_user(session, callback.from_user.id)
        total = len(exercises)
        start_idx = (page - 1) * PER_PAGE
        end_idx = start_idx + PER_PAGE
        page_items = exercises[start_idx:end_idx]
        
        await callback.message.edit_text(
            Messages.SELECT_EXERCISE_TO_ADD,
            reply_markup=get_active_add_exercise_menu(note_id, page_items, page, total)
        )

@router.callback_query(ActiveExCallback.filter(F.action == "add"))
async def process_add_ex_to_active(callback: CallbackQuery, callback_data: ActiveExCallback, state: FSMContext):
    async for session in get_db_session():
        await add_exercise_to_workout_note(session, callback_data.note_id, callback_data.ex_id)
    await callback.answer(Messages.EXERCISE_ADDED_TO_TPL)
    await show_active_workout(callback, state, callback_data.note_id)

@router.callback_query(WorkoutSessionState.active, MenuCallback.filter(F.action.startswith("finish_")))
async def finish_workout(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.edit_text(Messages.WORKOUT_FINISHED, reply_markup=get_main_menu())

@router.callback_query(MenuCallback.filter(F.action.startswith("wsettings") | F.action.startswith("act_settings") | (F.action == "act_settings")))
async def active_workout_settings(callback: CallbackQuery, state: FSMContext):
    await state.set_state(WorkoutSessionState.active)
    parts = callback.data.split("_")
    if parts[-1].isdigit():
        note_id = int(parts[-1])
    else:
        data = await state.get_data()
        note_id = data["note_id"]
    await show_history_card(callback, note_id, state)

@router.callback_query(WorkoutSessionState.active, MenuCallback.filter(F.action.startswith("wset_brief_")))
async def active_wset_brief(callback: CallbackQuery, state: FSMContext):
    note_id = int(callback.data.split("_")[2])
    await state.set_state(WorkoutSessionState.waiting_for_edit_brief)
    await state.update_data(prompt_msg_id=callback.message.message_id)
    keyboard = [[InlineKeyboardButton(text="❌ Отмена", callback_data=MenuCallback(action=f"wsettings_{note_id}").pack())]]
    await callback.message.edit_text("Введите новое название для тренировки:", reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard))

@router.message(WorkoutSessionState.waiting_for_edit_brief)
async def process_active_wset_brief(message: Message, state: FSMContext):
    try: await message.delete()
    except: pass
    if not message.text or not message.text.strip(): return
    
    data = await state.get_data()
    note_id = data["note_id"]
    prompt_msg_id = data.get("prompt_msg_id")
    
    async for session in get_db_session():
        from src.services.workout import update_workout_note
        await update_workout_note(session, note_id, brief=message.text.strip())
        
    await state.set_state(WorkoutSessionState.active)
    
    async for session in get_db_session():
        note = await get_workout_note(session, note_id)
        text = f"⚙️ Настройки тренировки '{note.brief}':\nВыберите параметр для изменения или удаления тренировки."
        if prompt_msg_id:
            try:
                await message.bot.edit_message_text(text, chat_id=message.chat.id, message_id=prompt_msg_id, reply_markup=get_active_workout_settings_menu(note_id))
                return
            except: pass
        msg = await message.answer(text, reply_markup=get_active_workout_settings_menu(note_id))
        await state.update_data(current_card_msg_id=msg.message_id)

@router.callback_query(WorkoutSessionState.active, MenuCallback.filter(F.action.startswith("wset_desc_")))
async def active_wset_desc(callback: CallbackQuery, state: FSMContext):
    note_id = int(callback.data.split("_")[2])
    await state.set_state(WorkoutSessionState.waiting_for_edit_desc)
    await state.update_data(prompt_msg_id=callback.message.message_id)
    keyboard = [[InlineKeyboardButton(text="❌ Отмена", callback_data=MenuCallback(action=f"wsettings_{note_id}").pack())]]
    await callback.message.edit_text("Введите новое описание для тренировки:", reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard))

@router.message(WorkoutSessionState.waiting_for_edit_desc)
async def process_active_wset_desc(message: Message, state: FSMContext):
    try: await message.delete()
    except: pass
    if not message.text: return
    
    data = await state.get_data()
    note_id = data["note_id"]
    prompt_msg_id = data.get("prompt_msg_id")
    
    async for session in get_db_session():
        from src.services.workout import update_workout_note
        await update_workout_note(session, note_id, description=message.text.strip())
        
    await state.set_state(WorkoutSessionState.active)
    
    async for session in get_db_session():
        note = await get_workout_note(session, note_id)
        text = f"⚙️ Настройки тренировки '{note.brief}':\nВыберите параметр для изменения или удаления тренировки."
        if prompt_msg_id:
            try:
                await message.bot.edit_message_text(text, chat_id=message.chat.id, message_id=prompt_msg_id, reply_markup=get_active_workout_settings_menu(note_id))
                return
            except: pass
        msg = await message.answer(text, reply_markup=get_active_workout_settings_menu(note_id))
        await state.update_data(current_card_msg_id=msg.message_id)

@router.callback_query(WorkoutSessionState.active, MenuCallback.filter(F.action.startswith("wset_time_")))
async def active_wset_time(callback: CallbackQuery, state: FSMContext):
    note_id = int(callback.data.split("_")[2])
    await state.set_state(WorkoutSessionState.waiting_for_edit_time)
    await state.update_data(prompt_msg_id=callback.message.message_id)
    keyboard = [
        [InlineKeyboardButton(text="Сейчас", callback_data=MenuCallback(action=f"wset_timenow_{note_id}").pack())],
        [InlineKeyboardButton(text="❌ Отмена", callback_data=MenuCallback(action=f"wsettings_{note_id}").pack())]
    ]
    await callback.message.edit_text("Введите новое время начала в формате 'DD-MM-YYYY HH:MM' или нажмите 'Сейчас':", reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard))

@router.callback_query(WorkoutSessionState.waiting_for_edit_time, MenuCallback.filter(F.action.startswith("wset_timenow_")))
async def process_active_wset_timenow(callback: CallbackQuery, state: FSMContext):
    note_id = int(callback.data.split("_")[2])
    async for session in get_db_session():
        from src.services.workout import update_workout_note
        await update_workout_note(session, note_id, started_at=datetime.now())
    await state.set_state(WorkoutSessionState.active)
    async for session in get_db_session():
        note = await get_workout_note(session, note_id)
        text = f"⚙️ Настройки тренировки '{note.brief}':\nВыберите параметр для изменения или удаления тренировки."
        await callback.message.edit_text(text, reply_markup=get_active_workout_settings_menu(note_id))

@router.message(WorkoutSessionState.waiting_for_edit_time)
async def process_active_wset_time(message: Message, state: FSMContext):
    try: await message.delete()
    except: pass
    if not message.text: return
    
    data = await state.get_data()
    note_id = data["note_id"]
    prompt_msg_id = data.get("prompt_msg_id")
    
    try:
        text_val = message.text.strip()
        new_time = datetime.strptime(text_val, "%d-%m-%Y %H:%M")
        
        async for session in get_db_session():
            from src.services.workout import update_workout_note
            await update_workout_note(session, note_id, started_at=new_time)
            
        await state.set_state(WorkoutSessionState.active)
        
        async for session in get_db_session():
            note = await get_workout_note(session, note_id)
            text = f"⚙️ Настройки тренировки '{note.brief}':\nВыберите параметр для изменения или удаления тренировки."
            if prompt_msg_id:
                try:
                    await message.bot.edit_message_text(text, chat_id=message.chat.id, message_id=prompt_msg_id, reply_markup=get_active_workout_settings_menu(note_id))
                    return
                except: pass
            msg = await message.answer(text, reply_markup=get_active_workout_settings_menu(note_id))
            await state.update_data(current_card_msg_id=msg.message_id)
    except ValueError:
        if prompt_msg_id:
            try:
                await message.bot.edit_message_text(
                    f"❌ Неверный формат времени!\n\nВведите новое время начала в формате 'DD-MM-YYYY HH:MM' или нажмите 'Сейчас':",
                    chat_id=message.chat.id,
                    message_id=prompt_msg_id,
                    reply_markup=InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="Сейчас", callback_data=MenuCallback(action=f"wset_timenow_{note_id}").pack())], [InlineKeyboardButton(text="❌ Отмена", callback_data=MenuCallback(action=f"wsettings_{note_id}").pack())]])
                )
            except: pass

@router.callback_query(WorkoutSessionState.active, MenuCallback.filter(F.action.startswith("wset_del_")))
async def active_wset_del_start(callback: CallbackQuery, state: FSMContext):
    note_id = int(callback.data.split("_")[2])
    await state.set_state(WorkoutSessionState.waiting_for_delete_confirm)
    async for session in get_db_session():
        note = await get_workout_note(session, note_id)
        if not note: return
        await state.update_data(expected_brief=note.brief)
        keyboard = [[InlineKeyboardButton(text="❌ Отмена", callback_data=MenuCallback(action=f"wsettings_{note_id}").pack())]]
        await callback.message.edit_text(
            f"Для удаления активной тренировки введите её название: `{note.brief}`",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard),
            parse_mode="Markdown"
        )

@router.message(WorkoutSessionState.waiting_for_delete_confirm)
async def process_active_wset_del_confirm(message: Message, state: FSMContext):
    try: await message.delete()
    except: pass
    if not message.text: return
    
    data = await state.get_data()
    expected = data.get("expected_brief", "")
    
    if message.text.strip() == expected:
        note_id = data["note_id"]
        async for session in get_db_session():
            from src.services.workout import delete_workout_note
            await delete_workout_note(session, note_id)
            
        await state.clear()
        
        if data.get("prompt_msg_id"):
            try: await message.bot.delete_message(message.chat.id, data["prompt_msg_id"])
            except: pass
            
        await message.answer("✅ Тренировка успешно удалена.", reply_markup=get_main_menu())
    else:
        if data.get("prompt_msg_id"):
            try:
                await message.bot.edit_message_text(
                    f"❌ Название не совпадает.\n\nДля удаления активной тренировки введите её название: `{expected}`",
                    chat_id=message.chat.id,
                    message_id=data["prompt_msg_id"],
                    reply_markup=InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="❌ Отмена", callback_data=MenuCallback(action=f"wsettings_{data['note_id']}").pack())]]),
                    parse_mode="Markdown"
                )
            except: pass
