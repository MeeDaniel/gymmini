from aiogram.filters.callback_data import CallbackData

class MenuCallback(CallbackData, prefix="menu"):
    action: str

class PaginationCallback(CallbackData, prefix="page"):
    target: str # 'exercises', 'templates', 'history', 'tpl_exercises'
    page: int
    parent_id: int | None = None

class ExerciseCallback(CallbackData, prefix="ex"):
    action: str # 'view', 'edit', 'delete'
    id: int

class TemplateCallback(CallbackData, prefix="tpl"):
    action: str # 'view', 'edit', 'delete', 'start', 'manage_ex'
    id: int

class TplExerciseCallback(CallbackData, prefix="tplex"):
    action: str # 'up', 'down', 'remove', 'add'
    tpl_id: int
    ex_id: int
    
class HistoryCallback(CallbackData, prefix="hist"):
    action: str # 'view', 'continue'
    id: int

class ActiveExCallback(CallbackData, prefix="actex"):
    action: str # 'add'
    note_id: int
    ex_id: int
