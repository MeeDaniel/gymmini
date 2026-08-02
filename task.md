# Задачи

## Этап 1: Функциональные исправления и UX по фидбеку
- [x] Пункт 1 (Telegraph Markdown): В `src/bot/utils.py` в функции `create_telegraph_page` перед формированием DOM-узлов преобразуй основные Markdown теги в HTML (например: `**текст**` -> `<b>текст</b>`, `*текст*` -> `<i>текст</i>`), чтобы на странице telegra.ph текст отображался красиво.
- [x] Пункт 2 (Настройки активной тренировки): В `src/bot/handlers/workout_session.py` в обработчике кнопки "⚙️ Настройки тренировки" (`action="act_settings"`) замени подменю настроек на прямой переход на карточку записи тренировки: вызови `await show_history_card(callback, note_id, state)`.
- [x] Пункт 3 (Текст кнопки в записи тренировки): В `src/bot/handlers/history.py` в `show_history_card` переименуй кнопку `"▶️ Продолжить / Ред. Подходы"` в `"▶️ Продолжить"`.
- [x] Пункт 4 (Текст кнопки заметки): В `src/bot/handlers/workout_session.py` в `show_active_exercise_page`: если у упражнения нет заметки (`not ex_note.notes`), отображай на кнопке текст `"➕ Добавить заметку"`, иначе `"✏️ Изменить заметку"`.
- [x] Пункт 5(б, в) (Возврат из заметки и отмена): В обработчиках `"❌ Отмена"` и `"🗑 Очистить заметку"` для заметки к упражнению (`wex_notes_cancel`, `wex_notes_clear` и др.) после изменения/очистки ОБЯЗАТЕЛЬНО возвращай пользователя на карточку упражнения вызовом `await show_active_exercise_page(callback, note_id, ex_note_id)`.
- [x] Пункт 5(г) (Подсказки для ввода подхода по типу упражнения): В `show_active_exercise_page` выводи понятную подсказку в зависимости от `ex_note.exercise.type`:
   - `strength`: `"Отправьте повторения и вес (например: '10x50', '12 60.5')"`
   - `cardio`: `"Отправьте дистанцию и время (например: '2.5км 15мин', '500м 45с')"`
   - `bodyweight`: `"Отправьте количество повторений (например: '15', '20 раз')"`
   - `timed`: `"Отправьте время выполнения (например: '60', '1 мин 30 с')"`
- [x] Пункт 9 (Кнопки "Сейчас" и "Отмена" при изменении времени): В `src/bot/handlers/history.py` в обработчик `edit_history_time_start` добавь клавиатуру с кнопками `"🕒 Сейчас"` (`HistoryCallback(action="time_now", id=callback_data.id).pack()`) и `"❌ Отмена"`. Обработай нажатие `"🕒 Сейчас"`: сразу обновляй `started_at = datetime.now()`, делай `await state.clear()` и показывай `show_history_card`.
- [x] Пункт 10 (Сброс FSM при /start и главном меню): В `src/bot/handlers/main_menu.py` добавь `state: FSMContext` в `cmd_start` и вызывай `await state.clear()` первой строчкой. Также делай сброс во всех обработчиках главного меню (`cb_cancel` и др.).
- [x] Пункт 12 (Кнопка "Отмена" в меню изменения): Убедись, что при нажатии `"❌ Отмена"` в меню редактирования (название/описание/тип/время в CRUD) сбрасывается `await state.clear()` и перерисовывается карточка.

## Этап 2: Аудит соблюдения Принципа одного сообщения
- [x] Провести детальный аудит КАЖДОГО состояния (state) и КАЖДОГО перехода из одного состояния в другое во всех обработчиках проекта Gymmini (`exercises.py`, `templates.py`, `history.py`, `workout_session.py`, `main_menu.py`) на соблюдение «Принципа одного сообщения»
- [x] Задокументировать детальный разбор 4 ключевых уязвимостей (создание упражнения с/без фото, уточнение при старте тренировки, удаление записи тренировки из истории, добавление подходов на карточке упражнения в активной тренировке) и составить итоговую сводку уязвимостей в артефакте `one_message_rule_audit_report.md`

## Этап 3: Проверка и исправление кнопок «❌ Отмена» во всех состояниях редактирования (CRUD)
- [x] Проверить и исправить состояния редактирования в `exercises.py` (`EditExerciseState`: `waiting_for_name`, `waiting_for_type`, `waiting_for_desc`, `waiting_for_photo` — кнопка отмены с `ExerciseCallback(action="view", id=id)`, сброс FSM `await state.clear()` в `view_exercise` перед `show_exercise_card`)
- [x] Проверить и исправить состояния редактирования в `templates.py` (`EditTemplateState`: `waiting_for_brief`, `waiting_for_desc` — кнопка отмены с `TemplateCallback(action="view", id=id)`, сброс FSM `await state.clear()` в `view_template` перед `show_template_card`, а также добавлена кнопка отмены при создании шаблона)
- [x] Проверить и исправить состояния редактирования в `history.py` (`EditHistoryState`: `waiting_for_brief`, `waiting_for_desc`, `waiting_for_time` — кнопка отмены с `HistoryCallback(action="view", id=id)`, сброс FSM `await state.clear()` в `view_history` перед `show_history_card`)
- [x] Проверить и исправить состояния редактирования в `workout_session.py` (`WorkoutSessionState.waiting_for_edit_notes` с возвратом в `active` и `show_active_exercise_page`, а также устранена уязвимость в `active_workout_settings`, блокировавшая отмену изменений названия/описания/времени тренировки в режиме активной сессии)
- [x] Написать и успешно выполнить тесты `tests/test_cancel_buttons.py` для 100% проверки кнопок отмены и очистки FSM во всех CRUD-состояниях
