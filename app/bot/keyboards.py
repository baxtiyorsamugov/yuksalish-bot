from aiogram.utils.keyboard import InlineKeyboardBuilder, ReplyKeyboardBuilder
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton

def kb_language():
    return InlineKeyboardMarkup(inline_keyboard=[
        [
        InlineKeyboardButton(text="O‘zbek", callback_data="lang:uz"),
         InlineKeyboardButton(text="Русский", callback_data="lang:ru")

         # InlineKeyboardButton(text="English", callback_data="lang:en")
        ]
    ])

# === ОБНОВЛЕННОЕ ГЛАВНОЕ МЕНЮ ===
def kb_main(is_registered=False, lang="ru"):
    builder = ReplyKeyboardBuilder()

    # Словарь с текстами кнопок
    # Вы можете поменять переводы на свой вкус
    texts = {
        "ru": {
            "events": "Мероприятия",
            "my_events": "Мои мероприятия",
            "about": "О движении",
            "cert": "Сертификат",
            "reg": "Регистрация",
            "feedback": "✍️ Обратная связь"
        },
        "uz": {
            "events": "Tadbirlar",
            "my_events": "Mening tadbirlarim",
            "about": "Harakat haqida",
            "cert": "Sertifikat",
            "reg": "Ro‘yxatdan o‘tish",
            "feedback": "✍️ Taklif va murojaat" # Или "Taklif va murojaat"
        }
    }

    # Выбираем нужный язык (если lang неизвестен, берем 'ru')
    t = texts.get(lang, texts["ru"])

    # Текст для кнопки регистрации в зависимости от языка
    reg_text = "Регистрация"
    if lang == "uz":
        reg_text = "Ro‘yxatdan o‘tish"
    elif lang == "en":
        reg_text = "Registration"

    # 1 ряд: Мероприятия (всегда видны)
    builder.row(
        KeyboardButton(text=t["events"]),
        KeyboardButton(text=t["my_events"])
    )

    # 2 ряд: О ДВИЖЕНИИ + СЕРТИФИКАТ (Условие!)
    if is_registered:
        # Если зарегистрирован: Показываем и "О движении", и "Сертификат"
        builder.row(
            KeyboardButton(text=t["about"]),
            KeyboardButton(text=t["cert"])
        )
    else:
        # Если НЕ зарегистрирован: Показываем только "О движении"
        builder.row(KeyboardButton(text=t["about"]))

    # 3 ряд: РЕГИСТРАЦИЯ (Только если НЕ зарегистрирован)
    if not is_registered:
        builder.row(KeyboardButton(text=reg_text))

    # 4 ряд: Настройки
    builder.row(KeyboardButton(text=t["feedback"]))

    return builder.as_markup(resize_keyboard=True)


# === НОВЫЕ КНОПКИ ДЛЯ РАЗДЕЛА "О ДВИЖЕНИИ" ===
def kb_about_menu(lang="ru"):
    builder = InlineKeyboardBuilder()

    if lang == 'uz':
        builder.row(InlineKeyboardButton(text="🎯 Yo‘nalishlar", callback_data="about_directions"))
        builder.row(InlineKeyboardButton(text="💼 Faoliyat", callback_data="about_activity"))
        builder.row(InlineKeyboardButton(text="🚀 Loyihalar", callback_data="about_projects"))
        builder.row(InlineKeyboardButton(text="🌐 Saytimiz", url="https://yuksalish.org"))
    else:
        builder.row(InlineKeyboardButton(text="🎯 Направления", callback_data="about_directions"))
        builder.row(InlineKeyboardButton(text="💼 Деятельность", callback_data="about_activity"))
        builder.row(InlineKeyboardButton(text="🚀 Проекты", callback_data="about_projects"))
        builder.row(InlineKeyboardButton(text="🌐 Наш сайт", url="https://yuksalish.org"))

    builder.adjust(1)
    return builder.as_markup()


def kb_back_to_about(lang="ru"):
    builder = InlineKeyboardBuilder()
    if lang == 'uz':
        builder.row(InlineKeyboardButton(text="⬅️ Ortga", callback_data="about_main"))
    else:
        builder.row(InlineKeyboardButton(text="⬅️ Назад к описанию", callback_data="about_main"))
    return builder.as_markup()


def kb_phone(lang="ru"):
    if lang == "uz":
        text = "📱 Telefon raqamni yuborish"
    else:
        text = "📱 Поделиться номером"

    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text=text, request_contact=True)]],
        resize_keyboard=True, one_time_keyboard=True
    )

# Кнопки для подтверждения данных в процессе регистрации
def kb_confirm(lang="ru"):
    builder = InlineKeyboardBuilder()

    if lang == 'uz':
        builder.row(InlineKeyboardButton(text="✅ Tasdiqlash", callback_data="confirm_yes"))
        builder.row(InlineKeyboardButton(text="❌ O‘zgartirish", callback_data="confirm_no"))
    else:
        builder.row(InlineKeyboardButton(text="✅ Все верно", callback_data="confirm_yes"))
        builder.row(InlineKeyboardButton(text="❌ Заполнить заново", callback_data="confirm_no"))

    return builder.as_markup()


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
def kb_event_actions(event_id, is_registered=False, status=None, lang="ru"):
    builder = InlineKeyboardBuilder()

    # Тексты кнопок
    if lang == 'uz':
        btn_reg = "✍️ Ariza topshirish"
        btn_prog = "📥 Dasturni yuklab olish"
        btn_pend = "⏳ Ariza ko‘rib chiqilmoqda"
        btn_rej = "❌ Ariza rad etildi"
        btn_back = "⬅️ Ortga"
    else:
        btn_reg = "✍️ Подать заявку"
        btn_prog = "📥 Скачать программу/Инфо"
        btn_pend = "⏳ Заявка на рассмотрении"
        btn_rej = "❌ Заявка отклонена"
        btn_back = "⬅️ Назад"

    if not is_registered:
        builder.row(InlineKeyboardButton(text=btn_reg, callback_data=f"evt_reg_{event_id}"))
    else:
        if status == "approved":
            builder.row(InlineKeyboardButton(text=btn_prog, callback_data=f"evt_prog_{event_id}"))
        elif status == "pending":
            builder.row(InlineKeyboardButton(text=btn_pend, callback_data="ignore"))
        elif status == "rejected":
            builder.row(InlineKeyboardButton(text=btn_rej, callback_data="ignore"))

    builder.row(InlineKeyboardButton(text=btn_back, callback_data="evt_back"))
    return builder.as_markup()

# === НОВАЯ КЛАВИАТУРА ДЛЯ ТИПОВ ОБРАЩЕНИЯ ===
def kb_feedback_types(lang="ru"):
    builder = InlineKeyboardBuilder()

    if lang == 'uz':
        builder.row(InlineKeyboardButton(text="💡 G‘oya taklif qilish", callback_data="feed_idea"))
        builder.row(InlineKeyboardButton(text="❓ Savol berish", callback_data="feed_question"))
        builder.row(InlineKeyboardButton(text="🤝 Hamkorlik", callback_data="feed_partnership"))
        builder.row(InlineKeyboardButton(text="❌ Bekor qilish", callback_data="feed_cancel"))
    else:
        builder.row(InlineKeyboardButton(text="💡 Предложить идею", callback_data="feed_idea"))
        builder.row(InlineKeyboardButton(text="❓ Задать вопрос", callback_data="feed_question"))
        builder.row(InlineKeyboardButton(text="🤝 Сотрудничество", callback_data="feed_partnership"))
        builder.row(InlineKeyboardButton(text="❌ Отмена", callback_data="feed_cancel"))

    builder.adjust(1)
    return builder.as_markup()


def kb_gender(lang="ru"):
    builder = InlineKeyboardBuilder()

    if lang == 'uz':
        builder.button(text="👨 Erkak", callback_data="gender_male")
        builder.button(text="👩 Ayol", callback_data="gender_female")
    else:
        builder.button(text="👨 Мужской", callback_data="gender_male")
        builder.button(text="👩 Женский", callback_data="gender_female")

    builder.adjust(2)
    return builder.as_markup()