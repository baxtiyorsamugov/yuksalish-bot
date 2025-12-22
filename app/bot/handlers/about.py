from aiogram import Router, F, types
from aiogram.types import FSInputFile
from app.bot.keyboards import kb_about_menu, kb_back_to_about
import os

router = Router()

# === ТЕКСТЫ (ЛУЧШЕ ХРАНИТЬ В ОТДЕЛЬНОМ ФАЙЛЕ, НО ПОКА ТАК) ===
TEXT_MAIN = (
    "<b>О движении «Юксалиш»</b> 🇺🇿\n\n"
    "Общенациональное движение «Юксалиш» создано для объединения граждан, "
    "бизнеса и государства ради устойчивого развития Узбекистана.\n\n"
    "Мы строим мост между народом и властью, продвигаем реформы и "
    "развиваем гражданское общество.\n\n"
    "👇 <i>Выберите раздел ниже, чтобы узнать больше:</i>"
)

TEXT_DIRECTIONS = (
    "<b>🎯 Наши основные направления:</b>\n\n"
    "1️⃣ <b>Мониторинг реформ</b> — следим за исполнением государственных программ.\n"
    "2️⃣ <b>Диалог</b> — организуем площадки для обсуждения проблем общества.\n"
    "3️⃣ <b>Поддержка инициатив</b> — помогаем активным гражданам реализовать идеи.\n"
    "4️⃣ <b>Международное сотрудничество</b> — привлекаем опыт зарубежных партнеров."
)

TEXT_ACTIVITY = (
    "<b>💼 Наша деятельность:</b>\n\n"
    "Мы проводим форумы, общественные слушания, благотворительные акции и "
    "образовательные тренинги.\n\n"
    "Ежегодно наши волонтеры участвуют в сотнях мероприятий по всей республике."
)

TEXT_PROJECTS = (
    "<b>🚀 Текущие проекты:</b>\n\n"
    "🔹 <b>«100 Community»</b> — развитие лидерства.\n"
    "🔹 <b>«Гражданский мониторинг»</b> — контроль инфраструктуры.\n"
    "🔹 <b>«Start Up» инициативы</b> — поддержка молодежного бизнеса.\n\n"
    "<i>Следите за анонсами в разделе Мероприятия!</i>"
)

# ПУТЬ К ВИДЕО ИЛИ ФОТО
# Положите красивое видео (video.mp4) или картинку (about_cover.jpg) в папку assets
VIDEO_ID = "BAACAgIAAxkBAAIDWWlI7DA4gRrFX2rus7RAu2Bu8JVZAALsiAACiMdJSnoQ4wMOhZnENgQ"

# === ХЕНДЛЕРЫ ===

# 1. Главная кнопка меню
@router.message(F.text == "ℹ️ О движении")
async def show_about_section(message: types.Message):
    # Отправляем видео по ID (это мгновенно и без лимитов по размеру)
    await message.answer_video(
        video=VIDEO_ID,
        caption=TEXT_MAIN,
        reply_markup=kb_about_menu(),
        parse_mode="HTML"
    )

# 2. Обработка кнопок (Направления, Проекты...)
# Мы используем edit_caption, чтобы менять текст под тем же видео/фото

@router.callback_query(F.data == "about_directions")
async def show_directions(call: types.CallbackQuery):
    # Если сообщение с медиа (видео/фото) - меняем caption
    # Если просто текст - меняем text
    if call.message.caption:
        await call.message.edit_caption(caption=TEXT_DIRECTIONS, reply_markup=kb_back_to_about(), parse_mode="HTML")
    else:
        await call.message.edit_text(text=TEXT_DIRECTIONS, reply_markup=kb_back_to_about(), parse_mode="HTML")
    await call.answer()

@router.callback_query(F.data == "about_activity")
async def show_activity(call: types.CallbackQuery):
    if call.message.caption:
        await call.message.edit_caption(caption=TEXT_ACTIVITY, reply_markup=kb_back_to_about(), parse_mode="HTML")
    else:
        await call.message.edit_text(text=TEXT_ACTIVITY, reply_markup=kb_back_to_about(), parse_mode="HTML")
    await call.answer()

@router.callback_query(F.data == "about_projects")
async def show_projects(call: types.CallbackQuery):
    if call.message.caption:
        await call.message.edit_caption(caption=TEXT_PROJECTS, reply_markup=kb_back_to_about(), parse_mode="HTML")
    else:
        await call.message.edit_text(text=TEXT_PROJECTS, reply_markup=kb_back_to_about(), parse_mode="HTML")
    await call.answer()

# 3. Кнопка "Назад" - возвращает главное описание
@router.callback_query(F.data == "about_main")
async def back_to_main_about(call: types.CallbackQuery):
    if call.message.caption:
        await call.message.edit_caption(caption=TEXT_MAIN, reply_markup=kb_about_menu(), parse_mode="HTML")
    else:
        await call.message.edit_text(text=TEXT_MAIN, reply_markup=kb_about_menu(), parse_mode="HTML")
    await call.answer()