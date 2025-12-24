from aiogram.fsm.state import State, StatesGroup

class Reg(StatesGroup):
    language = State()  # Выбор языка
    full_name = State()
    region = State()  # Регион
    sphere = State()  # Сфера деятельности
    birth_year = State()  # Год рождения
    gender = State()  # Пол
    phone = State()  # Телефон
    confirm = State()  # Подтверждение данных
    consent = State()  # Согласие (если нужно)

class FeedbackState(StatesGroup):
    waiting_for_type = State()    # Ждем выбора кнопки
    waiting_for_message = State() # Ждем текста сообщения