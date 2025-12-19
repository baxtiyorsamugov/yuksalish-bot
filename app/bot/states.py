from aiogram.fsm.state import State, StatesGroup

class Reg(StatesGroup):
    language = State()  # Выбор языка
    region = State()  # Регион
    sphere = State()  # Сфера деятельности
    birth_year = State()  # Год рождения
    gender = State()  # Пол
    phone = State()  # Телефон
    confirm = State()  # Подтверждение данных
    consent = State()  # Согласие (если нужно)