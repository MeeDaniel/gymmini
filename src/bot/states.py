from aiogram.fsm.state import State, StatesGroup

class WorkoutSessionState(StatesGroup):
    waiting_for_template = State()
    waiting_for_supplement = State()
    waiting_for_started_at = State()
    active = State()
    waiting_for_set = State()
    waiting_for_edit_brief = State()
    waiting_for_edit_desc = State()
    waiting_for_edit_time = State()
    waiting_for_delete_confirm = State()
    waiting_for_edit_notes = State()

class DeleteExerciseState(StatesGroup):
    waiting_for_confirm = State()

class CreateExerciseState(StatesGroup):
    waiting_for_name = State()
    waiting_for_type = State()
    waiting_for_photo = State()
    
class CreateWorkoutState(StatesGroup):
    waiting_for_brief = State()

class EditExerciseState(StatesGroup):
    waiting_for_name = State()
    waiting_for_type = State()
    waiting_for_desc = State()
    waiting_for_photo = State()

class EditTemplateState(StatesGroup):
    waiting_for_brief = State()
    waiting_for_desc = State()

class DeleteTemplateState(StatesGroup):
    waiting_for_confirm = State()

class EditHistoryState(StatesGroup):
    waiting_for_brief = State()
    waiting_for_desc = State()
    waiting_for_time = State()

class DeleteHistoryState(StatesGroup):
    waiting_for_confirm = State()
