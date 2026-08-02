from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from src.bot.messages import Messages
from src.bot.callbacks import (
    MenuCallback, PaginationCallback, ExerciseCallback, 
    TemplateCallback, TplExerciseCallback, HistoryCallback
)
import math

def get_main_menu() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=Messages.BTN_START_WORKOUT, callback_data=MenuCallback(action="start_workout").pack())],
        [InlineKeyboardButton(text=Messages.BTN_WORKOUTS, callback_data=MenuCallback(action="templates").pack())],
        [InlineKeyboardButton(text=Messages.BTN_EXERCISES, callback_data=MenuCallback(action="exercises").pack())],
        [InlineKeyboardButton(text=Messages.BTN_HISTORY, callback_data=MenuCallback(action="history").pack())]
    ])

def get_pagination_row(target: str, current_page: int, total_items: int, per_page: int = 5, parent_id: int | None = None) -> list[InlineKeyboardButton]:
    total_pages = max(1, math.ceil(total_items / per_page))
    row = []
    if current_page > 1:
        row.append(InlineKeyboardButton(text="⬅️ Назад", callback_data=PaginationCallback(target=target, page=current_page-1, parent_id=parent_id).pack()))
    if current_page < total_pages:
        row.append(InlineKeyboardButton(text="Вперед ➡️", callback_data=PaginationCallback(target=target, page=current_page+1, parent_id=parent_id).pack()))
    return row

def get_cancel_button() -> list[InlineKeyboardButton]:
    return [InlineKeyboardButton(text=Messages.BTN_CANCEL, callback_data=MenuCallback(action="cancel").pack())]

def get_back_button() -> list[InlineKeyboardButton]:
    return [InlineKeyboardButton(text=Messages.BTN_BACK, callback_data=MenuCallback(action="cancel").pack())]

def get_exercises_menu(exercises: list, page: int, total: int) -> InlineKeyboardMarkup:
    keyboard = []
    for ex in exercises:
        ex_type_str = Messages.EXERCISE_TYPE_RU.get(ex.type.value, ex.type.value)
        keyboard.append([InlineKeyboardButton(text=f"{ex.name} ({ex_type_str})", callback_data=ExerciseCallback(action="view", id=ex.id).pack())])
    
    pag_row = get_pagination_row("exercises", page, total)
    if pag_row:
        keyboard.append(pag_row)
        
    keyboard.append([InlineKeyboardButton(text=Messages.BTN_CREATE_EXERCISE, callback_data=MenuCallback(action="create_exercise").pack())])
    keyboard.append(get_back_button())
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def get_exercise_view_menu(ex_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="✏️ Имя", callback_data=ExerciseCallback(action="edit_name", id=ex_id).pack()),
            InlineKeyboardButton(text="✏️ Тип", callback_data=ExerciseCallback(action="edit_type", id=ex_id).pack())
        ],
        [
            InlineKeyboardButton(text="✏️ Описание", callback_data=ExerciseCallback(action="edit_desc", id=ex_id).pack()),
            InlineKeyboardButton(text="🖼 Фотография", callback_data=ExerciseCallback(action="edit_photo", id=ex_id).pack())
        ],
        [InlineKeyboardButton(text="🗑 Удалить", callback_data=ExerciseCallback(action="delete", id=ex_id).pack())],
        [InlineKeyboardButton(text="🔙 Назад", callback_data=MenuCallback(action="exercises").pack())]
    ])

def get_templates_menu(templates: list, page: int, total: int) -> InlineKeyboardMarkup:
    keyboard = []
    for tpl in templates:
        keyboard.append([InlineKeyboardButton(text=tpl.brief, callback_data=TemplateCallback(action="view", id=tpl.id).pack())])
    
    pag_row = get_pagination_row("templates", page, total)
    if pag_row:
        keyboard.append(pag_row)
        
    keyboard.append([InlineKeyboardButton(text=Messages.BTN_CREATE_WORKOUT, callback_data=MenuCallback(action="create_template").pack())])
    keyboard.append(get_back_button())
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def get_templates_start_menu(templates: list, page: int, total: int) -> InlineKeyboardMarkup:
    keyboard = []
    for tpl in templates:
        keyboard.append([InlineKeyboardButton(text=tpl.brief, callback_data=TemplateCallback(action="start", id=tpl.id).pack())])
    
    pag_row = get_pagination_row("templates_start", page, total)
    if pag_row:
        keyboard.append(pag_row)
        
    keyboard.append(get_back_button())
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def get_template_manage_menu(workout_id: int, exercises: list) -> InlineKeyboardMarkup:
    keyboard = []
    for ex in exercises:
        # TplExerciseCallback action="move_up", action="move_down", action="del"
        keyboard.append([
            InlineKeyboardButton(text=f"{ex.name}", callback_data="ignore"),
            InlineKeyboardButton(text="⬆️", callback_data=TplExerciseCallback(action="up", tpl_id=workout_id, ex_id=ex.id).pack()),
            InlineKeyboardButton(text="⬇️", callback_data=TplExerciseCallback(action="down", tpl_id=workout_id, ex_id=ex.id).pack()),
            InlineKeyboardButton(text="❌", callback_data=TplExerciseCallback(action="del", tpl_id=workout_id, ex_id=ex.id).pack())
        ])
    
    keyboard.append([InlineKeyboardButton(text="➕ Добавить упражнение", callback_data=TemplateCallback(action="add_ex_list", id=workout_id).pack())])
    keyboard.append([InlineKeyboardButton(text="🔙 Назад", callback_data=TemplateCallback(action="view", id=workout_id).pack())])
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def get_template_add_exercise_menu(workout_id: int, exercises: list, page: int, total: int) -> InlineKeyboardMarkup:
    keyboard = []
    for ex in exercises:
        ex_type_str = Messages.EXERCISE_TYPE_RU.get(ex.type.value, ex.type.value)
        keyboard.append([InlineKeyboardButton(text=f"➕ {ex.name} ({ex_type_str})", callback_data=TplExerciseCallback(action="add", tpl_id=workout_id, ex_id=ex.id).pack())])
    
    pag_row = get_pagination_row("tpl_add_ex", page, total, parent_id=workout_id)
    if pag_row:
        keyboard.append(pag_row)
        
    keyboard.append([InlineKeyboardButton(text="🔙 Назад", callback_data=TemplateCallback(action="manage_ex", id=workout_id).pack())])
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def get_history_menu(history: list, page: int, total: int) -> InlineKeyboardMarkup:
    keyboard = []
    for h in history:
        date_str = h.started_at.strftime("%Y-%m-%d %H:%M")
        keyboard.append([InlineKeyboardButton(text=f"{h.brief} ({date_str})", callback_data=HistoryCallback(action="view", id=h.id).pack())])
        
    pag_row = get_pagination_row("history", page, total)
    if pag_row:
        keyboard.append(pag_row)
        
    keyboard.append(get_back_button())
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def get_skip_photo_menu() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Пропустить", callback_data=MenuCallback(action="skip_photo").pack())],
        get_cancel_button()
    ])

def get_time_now_menu() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Сейчас", callback_data=MenuCallback(action="time_now").pack())],
        get_cancel_button()
    ])

def get_exercise_types_menu(ex_id: int | None = None) -> InlineKeyboardMarkup:
    cancel_row = [InlineKeyboardButton(text=Messages.BTN_CANCEL, callback_data=ExerciseCallback(action="view", id=ex_id).pack())] if ex_id else get_cancel_button()
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Силовая (повторения + вес)", callback_data="extype_strength")],
        [InlineKeyboardButton(text="Кардио (дистанция + время)", callback_data="extype_cardio")],
        [InlineKeyboardButton(text="Свой вес (только повторения)", callback_data="extype_bodyweight")],
        [InlineKeyboardButton(text="На время (только время)", callback_data="extype_timed")],
        cancel_row
    ])

def get_active_workout_menu(note_id: int, exercise_notes: list) -> InlineKeyboardMarkup:
    keyboard = []
    for en in exercise_notes:
        keyboard.append([InlineKeyboardButton(text=f"{en.exercise.name} ({len(en.sets)} подх.)", callback_data=MenuCallback(action=f"exnote_{en.id}").pack())])
    
    keyboard.append([InlineKeyboardButton(text="➕ Добавить упражнение", callback_data=MenuCallback(action=f"addex_{note_id}").pack())])
    keyboard.append([InlineKeyboardButton(text="⚙️ Настройки тренировки", callback_data=MenuCallback(action="act_settings").pack())])
    keyboard.append([InlineKeyboardButton(text=Messages.BTN_FINISH_WORKOUT, callback_data=MenuCallback(action=f"finish_{note_id}").pack())])
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def get_active_workout_settings_menu(note_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✏️ Изменить название", callback_data=MenuCallback(action=f"wset_brief_{note_id}").pack())],
        [InlineKeyboardButton(text="✏️ Изменить описание", callback_data=MenuCallback(action=f"wset_desc_{note_id}").pack())],
        [InlineKeyboardButton(text="✏️ Изменить время начала", callback_data=MenuCallback(action=f"wset_time_{note_id}").pack())],
        [InlineKeyboardButton(text="🗑 Удалить тренировку", callback_data=MenuCallback(action=f"wset_del_{note_id}").pack())],
        [InlineKeyboardButton(text="🔙 Назад к тренировке", callback_data=MenuCallback(action=f"wnote_{note_id}").pack())]
    ])

def get_active_exercise_menu(note_id: int, ex_note_id: int | None = None, has_note: bool = False) -> InlineKeyboardMarkup:
    keyboard = []
    if ex_note_id:
        btn_text = "✏️ Изменить заметку" if has_note else "➕ Добавить заметку"
        keyboard.append([InlineKeyboardButton(text=btn_text, callback_data=MenuCallback(action=f"editnotes_{ex_note_id}").pack())])
    keyboard.append([InlineKeyboardButton(text="🔙 Назад к тренировке", callback_data=MenuCallback(action=f"wnote_{note_id}").pack())])
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

from src.bot.callbacks import ActiveExCallback
def get_active_add_exercise_menu(note_id: int, exercises: list, page: int, total: int) -> InlineKeyboardMarkup:
    keyboard = []
    for ex in exercises:
        ex_type_str = Messages.EXERCISE_TYPE_RU.get(ex.type.value, ex.type.value)
        keyboard.append([InlineKeyboardButton(text=f"➕ {ex.name} ({ex_type_str})", callback_data=ActiveExCallback(action="add", note_id=note_id, ex_id=ex.id).pack())])
    
    pag_row = get_pagination_row("act_add_ex", page, total, parent_id=note_id)
    if pag_row:
        keyboard.append(pag_row)
        
    keyboard.append([InlineKeyboardButton(text="🔙 Назад", callback_data=MenuCallback(action=f"wnote_{note_id}").pack())])
    return InlineKeyboardMarkup(inline_keyboard=keyboard)
