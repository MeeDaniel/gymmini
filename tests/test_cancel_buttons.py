import pytest
from unittest.mock import AsyncMock, patch
from aiogram.fsm.storage.memory import MemoryStorage, StorageKey
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message, User, Chat
from src.bot.callbacks import ExerciseCallback, TemplateCallback, HistoryCallback, MenuCallback
from src.bot.keyboards import get_exercise_types_menu, get_cancel_button
from src.bot.states import EditExerciseState, EditTemplateState, EditHistoryState, WorkoutSessionState

@pytest.fixture
def fsm_state():
    storage = MemoryStorage()
    key = StorageKey(bot_id=1, chat_id=1, user_id=1)
    return FSMContext(storage=storage, key=key)

@pytest.fixture
def dummy_callback():
    cb = AsyncMock(spec=CallbackQuery)
    cb.from_user = User(id=1, is_bot=False, first_name="Test")
    cb.message = AsyncMock(spec=Message)
    cb.message.chat = Chat(id=1, type="private")
    cb.message.message_id = 100
    return cb

def test_exercise_types_menu_cancel():
    markup = get_exercise_types_menu(ex_id=42)
    cancel_btn = markup.inline_keyboard[-1][0]
    assert cancel_btn.text == "❌ Отмена"
    assert cancel_btn.callback_data == ExerciseCallback(action="view", id=42).pack()

    default_cancel = get_exercise_types_menu()
    cancel_btn_default = default_cancel.inline_keyboard[-1][0]
    assert cancel_btn_default.text == "❌ Отмена"

@pytest.mark.asyncio
async def test_view_exercise_clears_state(fsm_state, dummy_callback):
    from src.bot.handlers.exercises import view_exercise
    await fsm_state.set_state(EditExerciseState.waiting_for_name)
    assert await fsm_state.get_state() == EditExerciseState.waiting_for_name
    
    cb_data = ExerciseCallback(action="view", id=10)
    with patch("src.bot.handlers.exercises.show_exercise_card", new_callable=AsyncMock) as mock_show:
        await view_exercise(dummy_callback, cb_data, fsm_state)
        assert await fsm_state.get_state() is None
        mock_show.assert_called_once_with(dummy_callback, 10, fsm_state)

@pytest.mark.asyncio
async def test_view_template_clears_state(fsm_state, dummy_callback):
    from src.bot.handlers.templates import view_template
    await fsm_state.set_state(EditTemplateState.waiting_for_brief)
    assert await fsm_state.get_state() == EditTemplateState.waiting_for_brief
    
    cb_data = TemplateCallback(action="view", id=20)
    with patch("src.bot.handlers.templates.show_template_card", new_callable=AsyncMock) as mock_show:
        await view_template(dummy_callback, cb_data, fsm_state)
        assert await fsm_state.get_state() is None
        mock_show.assert_called_once_with(dummy_callback, 20, fsm_state)

@pytest.mark.asyncio
async def test_view_history_clears_state(fsm_state, dummy_callback):
    from src.bot.handlers.history import view_history
    await fsm_state.set_state(EditHistoryState.waiting_for_brief)
    assert await fsm_state.get_state() == EditHistoryState.waiting_for_brief
    
    cb_data = HistoryCallback(action="view", id=30)
    with patch("src.bot.handlers.history.show_history_card", new_callable=AsyncMock) as mock_show:
        await view_history(dummy_callback, cb_data, fsm_state)
        assert await fsm_state.get_state() is None
        mock_show.assert_called_once_with(dummy_callback, 30, fsm_state)

@pytest.mark.asyncio
async def test_workout_session_notes_cancel_and_clear(fsm_state, dummy_callback):
    from src.bot.handlers.workout_session import cancel_exercise_note_text, clear_exercise_note_text
    await fsm_state.set_state(WorkoutSessionState.waiting_for_edit_notes)
    await fsm_state.update_data(note_id=99)
    
    dummy_callback.data = MenuCallback(action="wex_notes_cancel_15").pack()
    with patch("src.bot.handlers.workout_session.show_active_exercise_page", new_callable=AsyncMock) as mock_show:
        await cancel_exercise_note_text(dummy_callback, fsm_state)
        assert await fsm_state.get_state() == WorkoutSessionState.active
        mock_show.assert_called_once_with(dummy_callback, 99, 15, fsm_state)
        
    await fsm_state.set_state(WorkoutSessionState.waiting_for_edit_notes)
    dummy_callback.data = MenuCallback(action="wex_notes_clear_15").pack()
    with patch("src.bot.handlers.workout_session.show_active_exercise_page", new_callable=AsyncMock) as mock_show, \
         patch("src.bot.handlers.workout_session.get_db_session") as mock_db:
        # Mock db generator
        async def mock_gen():
            yield AsyncMock()
        mock_db.return_value = mock_gen()
        with patch("src.services.exercise.update_exercise_note", new_callable=AsyncMock):
            await clear_exercise_note_text(dummy_callback, fsm_state)
            assert await fsm_state.get_state() == WorkoutSessionState.active
            mock_show.assert_called_once_with(dummy_callback, 99, 15, fsm_state)

@pytest.mark.asyncio
async def test_workout_session_active_workout_settings_resets_state(fsm_state, dummy_callback):
    from src.bot.handlers.workout_session import active_workout_settings
    await fsm_state.set_state(WorkoutSessionState.waiting_for_edit_brief)
    await fsm_state.update_data(note_id=88)
    
    dummy_callback.data = MenuCallback(action="wsettings_88").pack()
    with patch("src.bot.handlers.workout_session.show_history_card", new_callable=AsyncMock) as mock_show:
        await active_workout_settings(dummy_callback, fsm_state)
        assert await fsm_state.get_state() == WorkoutSessionState.active
        mock_show.assert_called_once_with(dummy_callback, 88, fsm_state)
