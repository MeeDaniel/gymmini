from aiogram import Router, F
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.context import FSMContext
from src.bot.messages import Messages
from src.bot.keyboards import get_templates_menu, get_main_menu, get_cancel_button
from src.bot.callbacks import MenuCallback, PaginationCallback, TemplateCallback, TplExerciseCallback
from src.bot.states import CreateWorkoutState, EditTemplateState, DeleteTemplateState
from src.services.workout import get_workouts_for_user, create_workout, get_workout, remove_exercise_from_workout, delete_workout
from src.db.database import get_db_session
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from src.bot.utils import format_description_preview, send_card_with_optional_file, cleanup_previous_file, extract_description_text, edit_message_text_or_caption

router = Router()

PER_PAGE = 5

@router.callback_query(MenuCallback.filter(F.action == "templates"))
async def list_templates_menu(callback: CallbackQuery, state: FSMContext):
    await cleanup_previous_file(callback, state)
    await show_templates_page(callback, 1)

@router.callback_query(PaginationCallback.filter(F.target == "templates"))
async def paginate_templates(callback: CallbackQuery, callback_data: PaginationCallback):
    await show_templates_page(callback, callback_data.page)

async def show_templates_page(callback: CallbackQuery, page: int):
    async for session in get_db_session():
        templates = await get_workouts_for_user(session, callback.from_user.id)
        total = len(templates)
        start_idx = (page - 1) * PER_PAGE
        end_idx = start_idx + PER_PAGE
        page_items = templates[start_idx:end_idx]
        
        await callback.message.edit_text(
            Messages.YOUR_TEMPLATES,
            reply_markup=get_templates_menu(page_items, page, total)
        )
        return

async def show_templates_page_answer(message: Message, user_id: int | None = None):
    uid = user_id or message.from_user.id
    async for session in get_db_session():
        templates = await get_workouts_for_user(session, uid)
        total = len(templates)
        page_items = templates[0:PER_PAGE]
        await message.answer(
            Messages.YOUR_TEMPLATES,
            reply_markup=get_templates_menu(page_items, 1, total)
        )

@router.callback_query(MenuCallback.filter(F.action == "create_template"))
async def create_template_start(callback: CallbackQuery, state: FSMContext):
    await state.set_state(CreateWorkoutState.waiting_for_brief)
    await callback.message.edit_text(Messages.ASK_WORKOUT_BRIEF, reply_markup=InlineKeyboardMarkup(inline_keyboard=[get_cancel_button()]))

@router.message(CreateWorkoutState.waiting_for_brief)
async def process_template_brief(message: Message, state: FSMContext):
    brief = message.text
    async for session in get_db_session():
        workout = await create_workout(session, message.from_user.id, brief)
        
    await state.clear()
    
    # Automatically redirect to manage exercises
    async for session in get_db_session():
        workout_refreshed = await get_workout(session, workout.id)
        text = Messages.TEMPLATE_MANAGE.format(brief=workout_refreshed.brief)
        await message.answer(text, reply_markup=get_template_manage_menu(workout_refreshed.id, workout_refreshed.exercises))

async def show_template_card(target, workout_id: int, state: FSMContext | None = None):
    async for session in get_db_session():
        workout = await get_workout(session, workout_id)
        if not workout:
            return
        
        text = f"📋 Шаблон: {workout.brief}\n"
        desc_str = await format_description_preview(workout.description, title=workout.brief)
        if workout.description:
            text += f"Описание:\n{desc_str}\n"
        
        text += "\nУпражнения:\n"
        if not workout.exercises:
            text += "Нет упражнений."
        else:
            for i, ex in enumerate(workout.exercises, 1):
                type_ru = Messages.EXERCISE_TYPE_RU.get(ex.type.value, ex.type.value)
                text += f"{i}. {ex.name} ({type_ru})\n"
                
        keyboard = [
            [InlineKeyboardButton(text="Редактировать упражнения", callback_data=TemplateCallback(action="manage_ex", id=workout.id).pack())],
            [InlineKeyboardButton(text="✏️ Изменить название", callback_data=TemplateCallback(action="edit_brief", id=workout.id).pack()),
             InlineKeyboardButton(text="✏️ Изменить описание", callback_data=TemplateCallback(action="edit_desc", id=workout.id).pack())],
            [InlineKeyboardButton(text="🗑 Удалить шаблон", callback_data=TemplateCallback(action="delete", id=workout.id).pack())],
            [InlineKeyboardButton(text="▶️ Начать эту тренировку", callback_data=TemplateCallback(action="start", id=workout.id).pack())],
            [InlineKeyboardButton(text=Messages.BTN_BACK, callback_data=MenuCallback(action="templates").pack())]
        ]
        await send_card_with_optional_file(
            target=target,
            title=workout.brief,
            description=workout.description,
            card_text=text,
            reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard),
            state=state
        )

@router.callback_query(TemplateCallback.filter(F.action == "view"))
async def view_template(callback: CallbackQuery, callback_data: TemplateCallback, state: FSMContext):
    await state.clear()
    await show_template_card(callback, callback_data.id, state)
    return

@router.callback_query(TemplateCallback.filter(F.action == "edit_brief"))
async def edit_template_brief_start(callback: CallbackQuery, callback_data: TemplateCallback, state: FSMContext):
    await cleanup_previous_file(callback, state)
    await state.set_state(EditTemplateState.waiting_for_brief)
    await state.update_data(workout_id=callback_data.id)
    keyboard = [[InlineKeyboardButton(text="❌ Отмена", callback_data=TemplateCallback(action="view", id=callback_data.id).pack())]]
    await edit_message_text_or_caption(callback.message, Messages.ASK_NEW_TEMPLATE_BRIEF, reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard))

@router.message(EditTemplateState.waiting_for_brief)
async def process_edit_template_brief(message: Message, state: FSMContext):
    data = await state.get_data()
    w_id = data.get("workout_id")
    async for session in get_db_session():
        w = await get_workout(session, w_id)
        if w:
            w.brief = message.text
            await session.commit()
    await state.clear()
    await show_template_card(message, w_id, state)

@router.callback_query(TemplateCallback.filter(F.action == "edit_desc"))
async def edit_template_desc_start(callback: CallbackQuery, callback_data: TemplateCallback, state: FSMContext):
    await cleanup_previous_file(callback, state)
    await state.set_state(EditTemplateState.waiting_for_desc)
    await state.update_data(workout_id=callback_data.id)
    keyboard = [[InlineKeyboardButton(text="❌ Отмена", callback_data=TemplateCallback(action="view", id=callback_data.id).pack())]]
    await edit_message_text_or_caption(callback.message, Messages.ASK_NEW_TEMPLATE_DESC, reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard))

@router.message(EditTemplateState.waiting_for_desc)
async def process_edit_template_desc(message: Message, state: FSMContext):
    data = await state.get_data()
    w_id = data.get("workout_id")
    new_desc, err = await extract_description_text(message)
    if err:
        await message.answer(err)
        return
    async for session in get_db_session():
        w = await get_workout(session, w_id)
        if w:
            w.description = new_desc
            await session.commit()
    await state.clear()
    await show_template_card(message, w_id, state)

@router.callback_query(TemplateCallback.filter(F.action == "delete"))
async def delete_template_start(callback: CallbackQuery, callback_data: TemplateCallback, state: FSMContext):
    await cleanup_previous_file(callback, state)
    async for session in get_db_session():
        w = await get_workout(session, callback_data.id)
        if not w: return
        await state.set_state(DeleteTemplateState.waiting_for_confirm)
        await state.update_data(workout_id=w.id, expected_brief=w.brief)
        text = Messages.ASK_DELETE_TEMPLATE_CONFIRM.format(brief=w.brief)
        keyboard = [[InlineKeyboardButton(text=Messages.BTN_CANCEL, callback_data=TemplateCallback(action="view", id=w.id).pack())]]
        await edit_message_text_or_caption(callback.message, text, reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard))

@router.message(DeleteTemplateState.waiting_for_confirm)
async def process_delete_template_confirm(message: Message, state: FSMContext):
    data = await state.get_data()
    w_id = data.get("workout_id")
    expected_brief = data.get("expected_brief")
    if message.text.strip() == expected_brief.strip():
        async for session in get_db_session():
            await delete_workout(session, w_id)
        await state.clear()
        await message.answer(Messages.TEMPLATE_DELETED)
        await show_templates_page_answer(message, user_id=message.from_user.id)
    else:
        await message.answer(Messages.DELETE_CONFIRM_MISMATCH)
        await state.clear()
        await show_template_card(message, w_id, state)

from src.bot.keyboards import get_template_manage_menu, get_template_add_exercise_menu
from src.services.exercise import get_exercises_for_user
from src.services.workout import add_exercise_to_workout, remove_exercise_from_workout, move_exercise_in_workout

@router.callback_query(TemplateCallback.filter(F.action == "manage_ex"))
async def manage_template_exercises(callback: CallbackQuery, callback_data: TemplateCallback, state: FSMContext):
    await cleanup_previous_file(callback, state)
    async for session in get_db_session():
        workout = await get_workout(session, callback_data.id)
        if not workout: return
        text = f"Управление упражнениями: {workout.brief}\nИспользуйте стрелочки для изменения порядка:"
        await callback.message.edit_text(text, reply_markup=get_template_manage_menu(workout.id, workout.exercises))

@router.callback_query(TplExerciseCallback.filter(F.action.in_(["up", "down", "del"])))
async def tpl_exercise_actions(callback: CallbackQuery, callback_data: TplExerciseCallback):
    async for session in get_db_session():
        if callback_data.action == "up":
            await move_exercise_in_workout(session, callback_data.tpl_id, callback_data.ex_id, -1)
        elif callback_data.action == "down":
            await move_exercise_in_workout(session, callback_data.tpl_id, callback_data.ex_id, 1)
        elif callback_data.action == "del":
            await remove_exercise_from_workout(session, callback_data.tpl_id, callback_data.ex_id)
        
        # refresh
        workout = await get_workout(session, callback_data.tpl_id)
        await callback.message.edit_reply_markup(reply_markup=get_template_manage_menu(workout.id, workout.exercises))

@router.callback_query(TemplateCallback.filter(F.action == "add_ex_list"))
async def add_ex_list(callback: CallbackQuery, callback_data: TemplateCallback):
    await show_add_ex_page(callback, callback_data.id, 1)

@router.callback_query(PaginationCallback.filter(F.target == "tpl_add_ex"))
async def paginate_add_ex(callback: CallbackQuery, callback_data: PaginationCallback):
    await show_add_ex_page(callback, callback_data.parent_id, callback_data.page)

async def show_add_ex_page(callback: CallbackQuery, workout_id: int, page: int):
    async for session in get_db_session():
        exercises = await get_exercises_for_user(session, callback.from_user.id)
        total = len(exercises)
        start_idx = (page - 1) * PER_PAGE
        end_idx = start_idx + PER_PAGE
        page_items = exercises[start_idx:end_idx]
        
        await callback.message.edit_text(
            Messages.SELECT_EXERCISE_TO_ADD,
            reply_markup=get_template_add_exercise_menu(workout_id, page_items, page, total)
        )

@router.callback_query(TplExerciseCallback.filter(F.action == "add"))
async def add_ex_to_tpl(callback: CallbackQuery, callback_data: TplExerciseCallback):
    async for session in get_db_session():
        await add_exercise_to_workout(session, callback_data.tpl_id, callback_data.ex_id)
        workout = await get_workout(session, callback_data.tpl_id)
        text = Messages.TEMPLATE_MANAGE.format(brief=workout.brief)
        await callback.message.edit_text(text, reply_markup=get_template_manage_menu(workout.id, workout.exercises))
        await callback.answer(Messages.EXERCISE_ADDED_TO_TPL)
