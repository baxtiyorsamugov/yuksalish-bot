from aiogram import Router, F, Bot
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext

from app.bot.keyboards import kb_feedback_types
from app.bot.states import FeedbackState
from app.config import ADMIN_IDS

router = Router()


# 1. Нажатие на кнопку в меню
@router.message(F.text.in_(["✍️ Обратная связь", "Feedback", "Aloqa"]))
async def feedback_start(message: Message, state: FSMContext):
    await state.clear()
    await message.answer(
        "Мы всегда рады вашим идеям и предложениям! \n"
        "Пожалуйста, выберите тему обращения:",
        reply_markup=kb_feedback_types()
    )
    await state.set_state(FeedbackState.waiting_for_type)


# 2. Обработка выбора темы (Идея, Вопрос...)
@router.callback_query(F.data.startswith("feed_"))
async def feedback_type_chosen(call: CallbackQuery, state: FSMContext):
    choice = call.data

    if choice == "feed_cancel":
        await state.clear()
        await call.message.delete()
        await call.message.answer("Отменено.")
        return

    # Сохраняем тему в память, чтобы потом добавить к сообщению админу
    titles = {
        "feed_idea": "💡 Идея / Предложение",
        "feed_question": "❓ Вопрос",
        "feed_partnership": "🤝 Сотрудничество"
    }
    topic = titles.get(choice, "Сообщение")
    await state.update_data(topic=topic)

    await call.message.edit_text(f"Вы выбрали: <b>{topic}</b>.\n\nНапишите ваше сообщение (текст, фото или видео):",
                                 parse_mode="HTML")
    await state.set_state(FeedbackState.waiting_for_message)


# 3. Получение сообщения и отправка Админу
@router.message(FeedbackState.waiting_for_message)
async def feedback_send(message: Message, state: FSMContext, bot: Bot):
    data = await state.get_data()
    topic = data.get("topic", "Сообщение")
    user = message.from_user

    # Формируем красивую шапку для админа
    # Ссылка tg://user?id=... позволяет кликнуть и сразу открыть личку
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
            # 1. Сначала отправляем инфо о юзере
            await bot.send_message(chat_id=admin_id, text=admin_text, parse_mode="HTML")

            # 2. Потом пересылаем само сообщение (чтобы сохранить фото/видео/голос)
            # copy_message копирует контент, но от имени бота
            await message.copy_to(chat_id=admin_id)
        except Exception as e:
            print(f"Не удалось отправить админу {admin_id}: {e}")

    await message.answer("✅ Спасибо! Ваше сообщение отправлено команде Юксалиш.\nМы рассмотрим его в ближайшее время.")
    await state.clear()