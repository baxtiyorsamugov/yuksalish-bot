from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton

def kb_language():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Русский", callback_data="lang:ru"),
         InlineKeyboardButton(text="O‘zbek", callback_data="lang:uz"),
         InlineKeyboardButton(text="English", callback_data="lang:en")]
    ])

def kb_main(lang="ru"):
    # можно позже сделать i18n
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🎫 Мероприятия"), KeyboardButton(text="📌 Мои мероприятия")],
            [KeyboardButton(text="🧾 Профиль"), KeyboardButton(text="Сертификат")],
            [KeyboardButton(text="Регистрация")],
            [KeyboardButton(text="⚙️ Настройки")]
        ],
        resize_keyboard=True
    )

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
