from aiogram import Router, F, Bot
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from sqlalchemy import select

from app.bot.keyboards import kb_feedback_types
from app.bot.states import FeedbackState
from app.config import ADMIN_IDS
from app.db.session import SessionLocal
from app.db.models import User

router = Router()


# Вспомогательная функция (можно вынести в services, но пусть пока будет тут)
async def get_lang(user_id):
    async with SessionLocal() as s:
        user = await s.scalar(select(User).where(User.tg_id == user_id))
        return user.language if user and user.language else 'ru'


# 1. Нажатие на кнопку в меню
# Добавил "✍️ Qayta aloqa", так как мы использовали это в клавиатуре
@router.message(F.text.in_(["✍️ Обратная связь", "✍️ Qayta aloqa", "✍️ Taklif va murojaat", "Feedback"]))
async def feedback_start(message: Message, state: FSMContext):
    await state.clear()
    lang = await get_lang(message.from_user.id)

    if lang == 'uz':
        text = "Biz sizning g‘oyalaringiz va takliflaringizdan doim xursandmiz!\nIltimos, murojaat mavzusini tanlang:"
    else:
        text = "Мы всегда рады вашим идеям и предложениям! \nПожалуйста, выберите тему обращения:"

    # Передаем lang в клавиатуру (обновите клавиатуру, см. ниже)
    await message.answer(text, reply_markup=kb_feedback_types(lang))
    await state.set_state(FeedbackState.waiting_for_type)


# 2. Обработка выбора темы (Идея, Вопрос...)
@router.callback_query(F.data.startswith("feed_"))
async def feedback_type_chosen(call: CallbackQuery, state: FSMContext):
    choice = call.data
    lang = await get_lang(call.from_user.id)

    if choice == "feed_cancel":
        await state.clear()
        await call.message.delete()
        msg = "Bekor qilindi." if lang == 'uz' else "Отменено."
        await call.message.answer(msg)
        return

    # Сохраняем тему в память (на двух языках, чтобы админ понимал)
    # Формат: {ключ: {ru: ..., uz: ...}}
    titles_map = {
        "feed_idea": {"ru": "💡 Идея / Предложение", "uz": "💡 G‘oya / Taklif"},
        "feed_question": {"ru": "❓ Вопрос", "uz": "❓ Savol"},
        "feed_partnership": {"ru": "🤝 Сотрудничество", "uz": "🤝 Hamkorlik"}
    }

    # Получаем название темы на языке пользователя
    topic_dict = titles_map.get(choice, {"ru": "Сообщение", "uz": "Xabar"})
    topic_user = topic_dict.get(lang, topic_dict["ru"])

    # Для админа лучше сохранить на русском (или обоих), чтобы было понятно
    topic_admin = topic_dict["ru"]
    await state.update_data(topic=topic_admin)

    if lang == 'uz':
        text = f"Tanlandi: <b>{topic_user}</b>.\n\nXabaringizni yozing (matn, rasm yoki video):"
    else:
        text = f"Вы выбрали: <b>{topic_user}</b>.\n\nНапишите ваше сообщение (текст, фото или видео):"

    await call.message.edit_text(text, parse_mode="HTML")
    await state.set_state(FeedbackState.waiting_for_message)


# 3. Получение сообщения и отправка Админу
@router.message(FeedbackState.waiting_for_message)
async def feedback_send(message: Message, state: FSMContext, bot: Bot):
    data = await state.get_data()
    topic = data.get("topic", "Сообщение")
    user = message.from_user
    lang = await get_lang(user.id)

    # Формируем красивую шапку для админа (Админ всегда видит на русском или системном)
    admin_text = (
        f"🔔 <b>Новое обращение!</b>\n\n"
        f"📌 <b>Тема:</b> {topic}\n"
        f"👤 <b>От:</b> {user.full_name} (@{user.username})\n"
        f"🆔 ID: <code>{user.id}</code>\n"
        f"👇 <i>Сообщение ниже:</i>"
    )

    # Рассылаем всем админам
    for admin_id in ADMIN_IDS:
        try:
            await bot.send_message(chat_id=admin_id, text=admin_text, parse_mode="HTML")
            await message.copy_to(chat_id=admin_id)
        except Exception as e:
            print(f"Не удалось отправить админу {admin_id}: {e}")

    # Ответ пользователю на его языке
    if lang == 'uz':
        final_text = "✅ Rahmat! Xabaringiz «Yuksalish» jamoasiga yuborildi.\nTez orada ko‘rib chiqamiz."
    else:
        final_text = "✅ Спасибо! Ваше сообщение отправлено команде Юксалиш.\nМы рассмотрим его в ближайшее время."

    await message.answer(final_text)
    await state.clear()