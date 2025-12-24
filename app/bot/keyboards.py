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

    # Текст для кнопки регистрации в зависимости от языка
    reg_text = "Регистрация"
    if lang == "uz":
        reg_text = "Ro‘yxatdan o‘tish"
    elif lang == "en":
        reg_text = "Registration"

    # 1 ряд: Мероприятия (всегда видны)
    builder.row(
        KeyboardButton(text="🎫 Мероприятия"),
        KeyboardButton(text="📌 Мои мероприятия")
    )

    # 2 ряд: О ДВИЖЕНИИ + СЕРТИФИКАТ (Условие!)
    if is_registered:
        # Если зарегистрирован: Показываем и "О движении", и "Сертификат"
        builder.row(
            KeyboardButton(text="ℹ️ О движении"),
            KeyboardButton(text="Сертификат")
        )
    else:
        # Если НЕ зарегистрирован: Показываем только "О движении"
        builder.row(KeyboardButton(text="ℹ️ О движении"))

    # 3 ряд: РЕГИСТРАЦИЯ (Только если НЕ зарегистрирован)
    if not is_registered:
        builder.row(KeyboardButton(text=reg_text))

    # 4 ряд: Настройки
    builder.row(KeyboardButton(text="✍️ Обратная связь"))

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


def kb_events_list(events):
    builder = InlineKeyboardBuilder()
    for event in events:
        # Кнопка с названием мероприятия
        builder.row(InlineKeyboardButton(text=f"📅 {event.title}", callback_data=f"evt_view_{event.id}"))
    return builder.as_markup()


# Кнопки управления конкретным мероприятием
def kb_event_actions(event_id, is_registered=False, status=None):
    builder = InlineKeyboardBuilder()

    if not is_registered:
        # Если еще не записан -> Кнопка "Участвовать"
        builder.row(InlineKeyboardButton(text="✍️ Подать заявку", callback_data=f"evt_reg_{event_id}"))
    else:
        # Если уже записан -> Показываем статус
        if status == "approved":
            # Если одобрено -> Можно скачать программу
            builder.row(InlineKeyboardButton(text="📥 Скачать программу/Инфо", callback_data=f"evt_prog_{event_id}"))
        elif status == "pending":
            builder.row(InlineKeyboardButton(text="⏳ Заявка на рассмотрении", callback_data="ignore"))
        elif status == "rejected":
            builder.row(InlineKeyboardButton(text="❌ Заявка отклонена", callback_data="ignore"))

    builder.row(InlineKeyboardButton(text="⬅️ Назад", callback_data="evt_back"))
    return builder.as_markup()

# === НОВАЯ КЛАВИАТУРА ДЛЯ ТИПОВ ОБРАЩЕНИЯ ===
def kb_feedback_types():
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="💡 Предложить идею", callback_data="feed_idea"))
    builder.row(InlineKeyboardButton(text="❓ Задать вопрос", callback_data="feed_question"))
    builder.row(InlineKeyboardButton(text="🤝 Сотрудничество", callback_data="feed_partnership"))
    builder.row(InlineKeyboardButton(text="❌ Отмена", callback_data="feed_cancel"))
    builder.adjust(1)
    return builder.as_markup()