class Messages:
    EXERCISE_TYPE_RU = {
        "strength": "Силовая",
        "cardio": "Кардио",
        "bodyweight": "Свой вес",
        "timed": "На время"
    }
    
    START_MESSAGE = "Привет, {name}! Твой профиль Gymmini готов к работе."
    MAIN_MENU = "Главное меню:"
    
    BTN_WORKOUTS = "📋 Шаблоны Тренировок"
    BTN_EXERCISES = "🏃 Мои Упражнения"
    BTN_START_WORKOUT = "🏋️ Начать тренировку"
    BTN_HISTORY = "📖 История тренировок"
    BTN_FINISH_WORKOUT = "⏹ Завершить тренировку"
    BTN_ADD_SET = "➕ Добавить подход"
    BTN_CANCEL = "❌ Отмена"
    BTN_BACK = "🔙 Назад"
    BTN_CREATE_WORKOUT = "➕ Создать шаблон"
    BTN_CREATE_EXERCISE = "➕ Создать упражнение"
    
    ASK_EXERCISE_NAME = "Введите название нового упражнения:"
    ASK_NEW_EXERCISE_NAME = "Введите новое название для упражнения:"
    ASK_NEW_EXERCISE_DESC = "Введите новое описание для упражнения (текстом в чате или отправьте файл .txt / .md до 1 МБ):"
    ASK_EXERCISE_PHOTO = "Отправьте фото для упражнения (или нажмите кнопку 'Пропустить'):"
    EXERCISE_CREATED = "Упражнение '{name}' успешно создано!"
    EXERCISE_UPDATED = "Упражнение успешно обновлено!"
    EXERCISE_DELETED = "Упражнение удалено"
    YOUR_EXERCISES = "Ваши упражнения:"
    YOUR_TEMPLATES = "Ваши шаблоны тренировок:"
    YOUR_HISTORY = "Ваша история тренировок:"
    TEMPLATE_MANAGE = "Управление упражнениями: {brief}\nИспользуйте стрелочки для изменения порядка:"
    SELECT_EXERCISE_TO_ADD = "Выберите упражнение для добавления:"
    EXERCISE_ADDED_TO_TPL = "Упражнение добавлено!"
    CHOOSE_TEMPLATE_TO_START = "Выберите шаблон тренировки для старта:"
    NO_TEMPLATES = "У вас нет шаблонов тренировок! Сначала создайте шаблон."
    CHOOSE_START_TIME = "Укажите время начала тренировки (в формате 'YYYY-MM-DD HH:MM' или просто нажмите 'Сейчас'):"
    INVALID_TIME_FORMAT = "Неверный формат. Попробуйте 'YYYY-MM-DD HH:MM' или нажмите 'Сейчас'."
    WORKOUT_CREATE_ERROR = "Ошибка создания тренировки."
    ACTIVE_WORKOUT_TITLE = "🔥 Тренировка: {brief}\nНачалась: {started_at}\n\nУпражнения:\n"
    SELECT_EX_FOR_SET = "🏋️ Выбрано: {name}\nОтправьте в чат данные подхода (например: '50x10', '15', '10 км 30 мин').\n\nТекущие подходы:\n"
    EMPTY_SETS = "  (нет подходов)"
    NEED_SELECT_EX_FIRST = "Сначала выберите упражнение из списка выше для добавления подхода."
    IN_DEVELOPMENT = "В разработке"
    
    FILE_TOO_LARGE = "Файл слишком большой! Максимальный размер 4MB."
    
    ASK_WORKOUT_BRIEF = "Введите краткое название для шаблона тренировки:"
    WORKOUT_CREATED = "Тренировка '{brief}' успешно создана!"
    
    ASK_SET_INFO = "Введите данные подхода (например: '10x50' или '15'):"
    SET_ADDED = "Подход добавлен: {reps} раз(а) x {weight} кг"
    SET_PARSE_ERROR = "Не удалось распознать подход. Попробуйте в формате '10x50' или '15'."
    INVALID_PHOTO_INPUT = "Пожалуйста, отправьте фото или нажмите кнопку 'Пропустить'."
    
    WORKOUT_FINISHED = "Тренировка завершена! Отличная работа."
    
    ASK_NEW_TEMPLATE_BRIEF = "Введите новое название для шаблона тренировки:"
    ASK_NEW_TEMPLATE_DESC = "Введите новое описание для шаблона тренировки (текстом в чате или отправьте файл .txt / .md до 1 МБ):"
    ASK_DELETE_TEMPLATE_CONFIRM = "⚠️ Для удаления шаблона '{brief}' введите его название в чат для подтверждения:"
    TEMPLATE_UPDATED = "Шаблон успешно обновлён!"
    TEMPLATE_DELETED = "Шаблон успешно удалён!"
    DELETE_CONFIRM_MISMATCH = "❌ Введённое название не совпадает. Удаление отменено."
    
    ASK_NEW_HISTORY_BRIEF = "Введите новое название для тренировки:"
    ASK_NEW_HISTORY_DESC = "Введите новое описание для тренировки (текстом в чате или отправьте файл .txt / .md до 1 МБ):"
    ASK_NEW_HISTORY_TIME = "Укажите новое время начала (в формате 'YYYY-MM-DD HH:MM'):"
    ASK_DELETE_HISTORY_CONFIRM = "⚠️ Для удаления записи тренировки '{brief}' введите её название в чат для подтверждения:"
    HISTORY_UPDATED = "Запись тренировки успешно обновлена!"
    HISTORY_DELETED = "Запись тренировки успешно удалена!"
    EXERCISE_REMOVED_FROM_WORKOUT = "Упражнение удалено из тренировки."

    @classmethod
    def get_set_prompt(cls, ex_type, ex_name: str) -> str:
        type_str = getattr(ex_type, "value", str(ex_type))
        if type_str == "strength":
            return f"🏋️ Выбрано: {ex_name}\nОтправьте в чат вес и повторения (например: '50x10' или '15'):\n\nТекущие подходы:\n"
        elif type_str == "cardio":
            return f"🏃 Выбрано: {ex_name}\nОтправьте в чат дистанцию в км и время в мин (например: '5 за 25' или '10 км 50 мин', либо просто время '30 мин'):\n\nТекущие подходы:\n"
        elif type_str == "bodyweight":
            return f"🤸 Выбрано: {ex_name}\nОтправьте в чат количество повторений (например: '15' или '20'):\n\nТекущие подходы:\n"
        elif type_str == "timed":
            return f"⏱ Выбрано: {ex_name}\nОтправьте в чат время подхода в минутах (например: '2' или '5 мин'):\n\nТекущие подходы:\n"
        return f"🏋️ Выбрано: {ex_name}\nОтправьте в чат данные подхода (например: '10x50', '15'):\n\nТекущие подходы:\n"
