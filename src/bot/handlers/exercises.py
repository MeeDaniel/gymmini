import os
from aiogram import Router, F
from aiogram.types import CallbackQuery, Message, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from src.bot.messages import Messages
from src.bot.keyboards import get_exercises_menu, get_exercise_types_menu, get_skip_photo_menu, get_main_menu
from src.bot.callbacks import MenuCallback, PaginationCallback, ExerciseCallback
from src.bot.states import CreateExerciseState, EditExerciseState, DeleteExerciseState
from src.services.exercise import get_exercises_for_user, create_exercise, get_exercise, delete_exercise
from src.services.utils import MEDIA_DIR, generate_image_path
from src.models.exercise import ExerciseType
from src.db.database import get_db_session
from src.bot.utils import format_description_preview, send_card_with_optional_file, cleanup_previous_file, extract_description_text, edit_message_text_or_caption

router = Router()

PER_PAGE = 5

@router.callback_query(MenuCallback.filter(F.action == "exercises"))
async def list_exercises_menu(callback: CallbackQuery, state: FSMContext):
    await cleanup_previous_file(callback, state)
    try:
        await callback.message.delete()
    except:
        pass
    await show_exercises_page(callback, 1, edit=False)

@router.callback_query(PaginationCallback.filter(F.target == "exercises"))
async def paginate_exercises(callback: CallbackQuery, callback_data: PaginationCallback):
    await show_exercises_page(callback, callback_data.page, edit=True)

async def show_exercises_page(callback: CallbackQuery, page: int, edit: bool = True):
    async for session in get_db_session():
        exercises = await get_exercises_for_user(session, callback.from_user.id)
        total = len(exercises)
        start_idx = (page - 1) * PER_PAGE
        end_idx = start_idx + PER_PAGE
        page_items = exercises[start_idx:end_idx]
        
        text = Messages.YOUR_EXERCISES
        markup = get_exercises_menu(page_items, page, total)
        
        if edit:
            await callback.message.edit_text(text, reply_markup=markup)
        else:
            await callback.message.answer(text, reply_markup=markup)
        return

from aiogram.types import FSInputFile
from src.bot.keyboards import get_exercises_menu, get_exercise_types_menu, get_skip_photo_menu, get_main_menu, get_exercise_view_menu

async def show_exercise_card(target, ex_id: int, state: FSMContext | None = None, warning_text: str | None = None):
    async for session in get_db_session():
        ex = await get_exercise(session, ex_id)
        if ex:
            ex_type_str = Messages.EXERCISE_TYPE_RU.get(ex.type.value, ex.type.value)
            desc_str = await format_description_preview(ex.description, title=ex.name)
            prefix = f"{warning_text}\n\n" if warning_text else ""
            text = f"{prefix}🏋️ {ex.name}\nТип: {ex_type_str}\nОписание:\n{desc_str}"
            
            await send_card_with_optional_file(
                target=target,
                title=ex.name,
                description=ex.description,
                card_text=text,
                reply_markup=get_exercise_view_menu(ex.id),
                image_path=ex.image_path,
                state=state
            )

@router.callback_query(ExerciseCallback.filter(F.action == "view"))
async def view_exercise(callback: CallbackQuery, callback_data: ExerciseCallback, state: FSMContext):
    await state.clear()
    await show_exercise_card(callback, callback_data.id, state)

@router.callback_query(ExerciseCallback.filter(F.action == "edit_name"))
async def edit_exercise_name_start(callback: CallbackQuery, callback_data: ExerciseCallback, state: FSMContext):
    await cleanup_previous_file(callback, state)
    await state.set_state(EditExerciseState.waiting_for_name)
    await state.update_data(exercise_id=callback_data.id)
    keyboard = [[InlineKeyboardButton(text="❌ Отмена", callback_data=ExerciseCallback(action="view", id=callback_data.id).pack())]]
    await edit_message_text_or_caption(callback.message, Messages.ASK_NEW_EXERCISE_NAME, reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard))

@router.message(EditExerciseState.waiting_for_name)
async def process_edit_exercise_name(message: Message, state: FSMContext):
    data = await state.get_data()
    ex_id = data.get("exercise_id")
    new_name = message.text
    async for session in get_db_session():
        ex = await get_exercise(session, ex_id)
        if ex:
            ex.name = new_name
            await session.commit()
    await state.clear()
    await show_exercise_card(message, ex_id)

@router.callback_query(ExerciseCallback.filter(F.action == "edit_type"))
async def edit_exercise_type_start(callback: CallbackQuery, callback_data: ExerciseCallback, state: FSMContext):
    await cleanup_previous_file(callback, state)
    await state.set_state(EditExerciseState.waiting_for_type)
    await state.update_data(exercise_id=callback_data.id)
    await edit_message_text_or_caption(callback.message, "Выберите новый тип упражнения:", reply_markup=get_exercise_types_menu(callback_data.id))

@router.callback_query(EditExerciseState.waiting_for_type, F.data.startswith("extype_"))
async def process_edit_exercise_type(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    ex_id = data.get("exercise_id")
    ex_type = callback.data.split("_")[1]
    
    async for session in get_db_session():
        ex = await get_exercise(session, ex_id)
        if ex:
            ex.type = ExerciseType(ex_type)
            await session.commit()
            
    await state.clear()
    await show_exercise_card(callback, ex_id, state)

@router.callback_query(ExerciseCallback.filter(F.action == "edit_desc"))
async def edit_exercise_desc_start(callback: CallbackQuery, callback_data: ExerciseCallback, state: FSMContext):
    await cleanup_previous_file(callback, state)
    await state.set_state(EditExerciseState.waiting_for_desc)
    await state.update_data(exercise_id=callback_data.id)
    keyboard = [[InlineKeyboardButton(text="❌ Отмена", callback_data=ExerciseCallback(action="view", id=callback_data.id).pack())]]
    await edit_message_text_or_caption(callback.message, Messages.ASK_NEW_EXERCISE_DESC, reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard))

@router.message(EditExerciseState.waiting_for_desc)
async def process_edit_exercise_desc(message: Message, state: FSMContext):
    data = await state.get_data()
    ex_id = data.get("exercise_id")
    new_desc, err = await extract_description_text(message)
    if err:
        await message.answer(err)
        return
    async for session in get_db_session():
        ex = await get_exercise(session, ex_id)
        if ex:
            ex.description = new_desc
            await session.commit()
    await state.clear()
    await show_exercise_card(message, ex_id, state)

@router.callback_query(ExerciseCallback.filter(F.action == "edit_photo"))
async def edit_exercise_photo_start(callback: CallbackQuery, callback_data: ExerciseCallback, state: FSMContext):
    await cleanup_previous_file(callback, state)
    await state.set_state(EditExerciseState.waiting_for_photo)
    await state.update_data(exercise_id=callback_data.id)
    keyboard = [[InlineKeyboardButton(text="❌ Отмена", callback_data=ExerciseCallback(action="view", id=callback_data.id).pack())]]
    await edit_message_text_or_caption(callback.message, "Отправьте новое фото для упражнения:", reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard))

@router.message(EditExerciseState.waiting_for_photo)
async def process_edit_exercise_photo(message: Message, state: FSMContext):
    if not message.photo:
        await message.answer("Пожалуйста, отправьте фото.")
        return
        
    photo = message.photo[-1]
    if photo.file_size > 4 * 1024 * 1024:
        await message.answer(Messages.FILE_TOO_LARGE)
        return
        
    os.makedirs(MEDIA_DIR, exist_ok=True)
    file_path = generate_image_path()
    
    bot = message.bot
    await bot.download(photo, destination=file_path)
    
    data = await state.get_data()
    ex_id = data.get("exercise_id")
    
    async for session in get_db_session():
        ex = await get_exercise(session, ex_id)
        if ex:
            ex.image_path = file_path
            await session.commit()
            
    await state.clear()
    await show_exercise_card(message, ex_id, state)

@router.callback_query(ExerciseCallback.filter(F.action == "delete"))
async def delete_exercise_handler(callback: CallbackQuery, callback_data: ExerciseCallback, state: FSMContext):
    await cleanup_previous_file(callback, state)
    async for session in get_db_session():
        ex = await get_exercise(session, callback_data.id)
        if not ex: return
        await state.set_state(DeleteExerciseState.waiting_for_confirm)
        await state.update_data(
            exercise_id=callback_data.id,
            expected_name=ex.name,
            prompt_msg_id=callback.message.message_id,
            chat_id=callback.message.chat.id
        )
        keyboard = [[InlineKeyboardButton(text="❌ Отмена", callback_data=ExerciseCallback(action="view", id=callback_data.id).pack())]]
        await edit_message_text_or_caption(
            callback.message,
            f"Для удаления упражнения введите его название: {ex.name}",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard)
        )

@router.message(DeleteExerciseState.waiting_for_confirm)
async def process_delete_exercise_confirm(message: Message, state: FSMContext):
    data = await state.get_data()
    expected = data.get("expected_name", "")
    prompt_msg_id = data.get("prompt_msg_id")
    chat_id = data.get("chat_id", message.chat.id)
    if message.text.strip() == expected:
        ex_id = data["exercise_id"]
        success = False
        err_msg = None
        async for session in get_db_session():
            success, err_msg = await delete_exercise(session, ex_id)
        await state.clear()
        try:
            await message.delete()
        except Exception:
            pass
        if prompt_msg_id:
            try:
                await message.bot.delete_message(chat_id, prompt_msg_id)
            except Exception:
                pass
        if not success and err_msg:
            await show_exercise_card(message, ex_id, state, warning_text=err_msg)
        else:
            await message.answer(Messages.EXERCISE_DELETED)
            await show_exercises_page_answer(message, user_id=message.from_user.id)
    else:
        try:
            await message.delete()
        except Exception:
            pass
        await message.answer("Название не совпадает. Попробуйте снова или нажмите 'Отмена'.")

@router.callback_query(MenuCallback.filter(F.action == "create_exercise"))
async def create_exercise_start(callback: CallbackQuery, state: FSMContext):
    await state.set_state(CreateExerciseState.waiting_for_name)
    from src.bot.keyboards import get_cancel_button
    await callback.message.edit_text(Messages.ASK_EXERCISE_NAME, reply_markup=InlineKeyboardMarkup(inline_keyboard=[get_cancel_button()]))

@router.message(CreateExerciseState.waiting_for_name)
async def process_exercise_name(message: Message, state: FSMContext):
    await state.update_data(name=message.text)
    await state.set_state(CreateExerciseState.waiting_for_type)
    await message.answer("Выберите тип упражнения (определяет, какие данные будут записываться в подходы):", reply_markup=get_exercise_types_menu())

@router.callback_query(CreateExerciseState.waiting_for_type, F.data.startswith("extype_"))
async def process_exercise_type(callback: CallbackQuery, state: FSMContext):
    ex_type = callback.data.split("_")[1]
    await state.update_data(type=ex_type)
    await state.set_state(CreateExerciseState.waiting_for_photo)
    await callback.message.edit_text(Messages.ASK_EXERCISE_PHOTO, reply_markup=get_skip_photo_menu())

@router.callback_query(CreateExerciseState.waiting_for_photo, MenuCallback.filter(F.action == "skip_photo"))
async def process_exercise_photo_skip(callback: CallbackQuery, state: FSMContext):
    await save_new_exercise(callback.from_user.id, callback.message, state, None)

@router.message(CreateExerciseState.waiting_for_photo)
async def process_exercise_photo(message: Message, state: FSMContext):
    if not message.photo:
        await message.answer(Messages.INVALID_PHOTO_INPUT, reply_markup=get_skip_photo_menu())
        return
    
    photo = message.photo[-1]
    if photo.file_size > 4 * 1024 * 1024:
        await message.answer(Messages.FILE_TOO_LARGE)
        return
        
    os.makedirs(MEDIA_DIR, exist_ok=True)
    file_path = generate_image_path()
    
    bot = message.bot
    await bot.download(photo, destination=file_path)
    
    await save_new_exercise(message.from_user.id, message, state, file_path)

async def show_exercises_page_answer(message: Message, user_id: int | None = None):
    uid = user_id or message.from_user.id
    async for session in get_db_session():
        exercises = await get_exercises_for_user(session, uid)
        total = len(exercises)
        page_items = exercises[0:PER_PAGE]
        await message.answer(
            Messages.YOUR_EXERCISES,
            reply_markup=get_exercises_menu(page_items, 1, total)
        )

async def save_new_exercise(user_id: int, message: Message, state: FSMContext, image_path: str | None):
    data = await state.get_data()
    ex_type = ExerciseType(data['type'])
    
    async for session in get_db_session():
        await create_exercise(session, user_id, data['name'], ex_type, None, image_path) 
        
    await state.clear()
    await message.answer(Messages.EXERCISE_CREATED.format(name=data['name']))
    await show_exercises_page_answer(message, user_id=user_id)
