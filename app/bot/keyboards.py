from aiogram.utils.keyboard import InlineKeyboardBuilder, ReplyKeyboardBuilder
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton

def kb_language():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Русский", callback_data="lang:ru"),
         InlineKeyboardButton(text="O‘zbek", callback_data="lang:uz"),
         InlineKeyboardButton(text="English", callback_data="lang:en")]
    ])

# === ОБНОВЛЕННОЕ ГЛАВНОЕ МЕНЮ ===
def kb_main(is_registered=False, lang="ru"):
    builder = ReplyKeyboardBuilder()

    reg_text = "Регистрация"
    if lang == "uz":
        reg_text = "Ro‘yxatdan o‘tish"
    elif lang == "en":
        reg_text = "Registration"

    # 1 ряд
    builder.row(
        KeyboardButton(text="🎫 Мероприятия"),
        KeyboardButton(text="📌 Мои мероприятия")
    )

    # 2 ряд: ВМЕСТО ПРОФИЛЯ СТАВИМ "О ДВИЖЕНИИ"
    builder.row(
        KeyboardButton(text="ℹ️ О движении"), # <-- Изменили здесь
        KeyboardButton(text="🪪 Сертификат")
    )

    # 3 ряд
    if not is_registered:
        builder.row(KeyboardButton(text=reg_text))

    # 4 ряд
    builder.row(KeyboardButton(text="⚙️ Настройки"))

    return builder.as_markup(resize_keyboard=True)


# === НОВЫЕ КНОПКИ ДЛЯ РАЗДЕЛА "О ДВИЖЕНИИ" ===
def kb_about_menu():
    """Кнопки под видео о движении"""
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="🎯 Направления", callback_data="about_directions"))
    builder.row(InlineKeyboardButton(text="💼 Деятельность", callback_data="about_activity"))
    builder.row(InlineKeyboardButton(text="🚀 Проекты", callback_data="about_projects"))
    # Можно добавить ссылку на сайт или канал
    builder.row(InlineKeyboardButton(text="🌐 Наш сайт", url="https://yuksalish.org"))
    return builder.as_markup()

def kb_back_to_about():
    """Кнопка 'Назад' внутри раздела"""
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="⬅️ Назад к описанию", callback_data="about_main"))
    return builder.as_markup()

def kb_phone():
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="📱 Поделиться номером", request_contact=True)]],
        resize_keyboard=True, one_time_keyboard=True
    )

# Кнопки для подтверждения данных в процессе регистрации
def kb_confirm():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="✅ Подтвердить", callback_data="confirm_yes")],
            [InlineKeyboardButton(text="❌ Изменить", callback_data="confirm_no")]
        ]
    )


def get_regions_keyboard(regions_list, lang='ru'):
    """
    Генерирует кнопки регионов.
    lang: 'ru', 'uz' или 'en' (зависит от того, какой язык выбрал юзер)
    """
    builder = InlineKeyboardBuilder()

    for region in regions_list:
        # Динамически берем нужное поле: name_ru, name_uz или name_en
        # Если такого языка нет, берем name_ru
        region_name = getattr(region, f"name_{lang}", region.name_ru)

        builder.button(text=region_name, callback_data=f"reg_{region.id}")

    builder.adjust(2)  # Кнопки в 2 колонки
    return builder.as_markup()


def get_spheres_keyboard(spheres_list, lang='ru'):
    builder = InlineKeyboardBuilder()

    for sphere in spheres_list:
        sphere_name = getattr(sphere, f"name_{lang}", sphere.name_ru)
        builder.button(text=sphere_name, callback_data=f"sph_{sphere.id}")

    builder.adjust(1)  # Сферы в 1 колонку (обычно названия длинные)
    return builder.as_markup()
