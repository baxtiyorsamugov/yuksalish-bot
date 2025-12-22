import logging
import asyncio
from aiogram import Router, F, Bot, types
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from sqlalchemy import select

# Импорты вашей БД
from app.db.session import SessionLocal
from app.db.models import User

# === НАСТРОЙКИ ===
# Укажите здесь свой Telegram ID (можно узнать через @userinfobot)
ADMIN_IDS = [372688693]

router = Router()


# Состояния для FSM (машины состояний)
class BroadcastState(StatesGroup):
    waiting_for_content = State()
    confirm_sending = State()


# Клавиатура подтверждения
confirm_kb = InlineKeyboardMarkup(inline_keyboard=[
    [
        InlineKeyboardButton(text="✅ Отправить", callback_data="broadcast_confirm"),
        InlineKeyboardButton(text="❌ Отмена", callback_data="broadcast_cancel")
    ]
])

# Временный хендлер, чтобы узнать ID видео
# @router.message(F.video)
# async def get_video_id(message: Message):
#     # Бот пришлет вам ID отправленного видео
#     await message.answer(f"ID вашего видео:\n<code>{message.video.file_id}</code>")


# 1. Команда /post - начало создания рассылки
@router.message(Command("post"))
async def cmd_post(message: Message, state: FSMContext):
    if message.from_user.id not in ADMIN_IDS:
        return  # Игнорируем обычных юзеров

    await message.answer("Отправьте сообщение (текст, фото или видео), которое нужно разослать всем пользователям.")
    await state.set_state(BroadcastState.waiting_for_content)


# 2. Получение контента поста
@router.message(BroadcastState.waiting_for_content)
async def process_content(message: Message, state: FSMContext):
    # Сохраняем ID чата и ID сообщения, чтобы потом его скопировать
    await state.update_data(
        chat_id=message.chat.id,
        message_id=message.message_id
    )

    # Отправляем админу предпросмотр
    await message.copy_to(chat_id=message.chat.id)
    await message.answer("Вот так будет выглядеть пост. Отправляем?", reply_markup=confirm_kb)
    await state.set_state(BroadcastState.confirm_sending)


# 3. Обработка кнопки "Отмена"
@router.callback_query(F.data == "broadcast_cancel", BroadcastState.confirm_sending)
async def cancel_broadcast(call: CallbackQuery, state: FSMContext):
    await state.clear()
    await call.message.edit_text("Рассылка отменена.")


# 4. Обработка кнопки "Отправить" - САМА РАССЫЛКА
@router.callback_query(F.data == "broadcast_confirm", BroadcastState.confirm_sending)
async def start_broadcast(call: CallbackQuery, state: FSMContext, bot: Bot):
    data = await state.get_data()
    chat_id = data['chat_id']
    message_id = data['message_id']

    await call.message.edit_text("⏳ Начинаю рассылку... Это может занять время.")

    # Получаем всех пользователей из БД
    async with SessionLocal() as session:
        result = await session.execute(select(User.tg_id))
        users = result.scalars().all()

    count_success = 0
    count_blocked = 0

    for user_id in users:
        try:
            # copy_message - универсальный метод копирования любого контента
            await bot.copy_message(chat_id=user_id, from_chat_id=chat_id, message_id=message_id)
            count_success += 1
            # Небольшая задержка, чтобы Телеграм не забанил за спам (20-30 сообщений в секунду лимит)
            await asyncio.sleep(0.05)

        except Exception as e:
            # Обычно ошибки: "Bot was blocked by the user"
            logging.error(f"Не удалось отправить юзеру {user_id}: {e}")
            count_blocked += 1

    await call.message.answer(
        f"✅ Рассылка завершена!\n\n"
        f"Получили: {count_success}\n"
        f"Заблокировали бота/ошибки: {count_blocked}"
    )
    await state.clear()