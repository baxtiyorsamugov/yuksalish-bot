from aiogram import Router, F, types
from aiogram.types import FSInputFile, InlineKeyboardButton
from sqlalchemy import select, and_
from aiogram.utils.keyboard import InlineKeyboardBuilder
from app.db.session import SessionLocal
from app.db.models import Event, EventRegistration, User
from app.bot.keyboards import kb_events_list, kb_event_actions

router = Router()


# Вспомогательная функция для получения языка
async def get_lang(user_id):
    async with SessionLocal() as s:
        user = await s.scalar(select(User).where(User.tg_id == user_id))
        return user.language if user and user.language else 'ru'


# 1. Показать список активных мероприятий
@router.message(F.text.in_(["Мероприятия", "Tadbirlar"]))
@router.callback_query(F.data == "evt_back")
async def show_events(update: types.Message | types.CallbackQuery):
    if isinstance(update, types.CallbackQuery):
        message = update.message
        user_id = update.from_user.id
    else:
        message = update
        user_id = message.from_user.id

    lang = await get_lang(user_id)

    async with SessionLocal() as s:
        q = await s.execute(select(Event).where(Event.status == "active").order_by(Event.date_event.desc()))
        events = q.scalars().all()

    if not events:
        msg = "Hozirda faol tadbirlar yo‘q." if lang == 'uz' else "На данный момент активных мероприятий нет."
        await message.answer(msg)
    else:
        if lang == 'uz':
            text = "<b>📅 Dolzarb tadbirlar:</b>\n\nBatafsil ma'lumot olish va ariza topshirish uchun tadbirni tanlang."
        else:
            text = "<b>📅 Актуальные мероприятия:</b>\n\nВыберите мероприятие, чтобы узнать подробности и подать заявку."

        if isinstance(update, types.CallbackQuery):
            await message.edit_text(text, reply_markup=kb_events_list(events), parse_mode="HTML")
        else:
            await message.answer(text, reply_markup=kb_events_list(events), parse_mode="HTML")

    if isinstance(update, types.CallbackQuery):
        await update.answer()


# 2. Просмотр конкретного мероприятия
@router.callback_query(F.data.startswith("evt_view_"))
async def view_event(call: types.CallbackQuery):
    event_id = int(call.data.split("_")[2])
    user_id = call.from_user.id
    lang = await get_lang(user_id)

    async with SessionLocal() as s:
        event = await s.get(Event, event_id)
        # Получаем пользователя БД по tg_id
        q_user = await s.execute(select(User).where(User.tg_id == user_id))
        db_user = q_user.scalar_one()

        q_reg = await s.execute(
            select(EventRegistration)
            .where(and_(EventRegistration.event_id == event_id, EventRegistration.user_id == db_user.id))
        )
        reg = q_reg.scalar_one_or_none()

    if not event:
        msg = "Tadbir topilmadi" if lang == 'uz' else "Мероприятие не найдено"
        await call.answer(msg, show_alert=True)
        return

    # Тексты полей
    if lang == 'uz':
        txt_loc = "📍 <b>Manzil:</b>"
        txt_date = "🗓 <b>Sana:</b>"
        txt_desc = "ℹ️ <b>Tavsif:</b>"
    else:
        txt_loc = "📍 <b>Локация:</b>"
        txt_date = "🗓 <b>Дата:</b>"
        txt_desc = "ℹ️ <b>Описание:</b>"

    text = (
        f"<b>{event.title}</b>\n\n"
        f"{txt_loc} {event.location}\n"
        f"{txt_date} {event.date_event.strftime('%d.%m.%Y %H:%M')}\n\n"
        f"{txt_desc}\n{event.description}\n\n"
    )

    is_reg = (reg is not None)
    status = reg.status if reg else None

    if is_reg:
        if status == 'pending':
            msg = "⚠️ <i>Sizning arizangiz moderator tomonidan ko‘rib chiqilmoqda.</i>" if lang == 'uz' else "\n⚠️ <i>Ваша заявка находится на рассмотрении модератора.</i>"
            text += msg
        elif status == 'approved':
            msg = "✅ <i>Sizning arizangiz tasdiqlandi! Materiallarni yuklab olishingiz mumkin.</i>" if lang == 'uz' else "\n✅ <i>Ваша заявка одобрена! Вы можете скачать материалы.</i>"
            text += msg
        elif status == 'rejected':
            msg = "❌ <i>Afsuski, arizangiz rad etildi.</i>" if lang == 'uz' else "\n❌ <i>К сожалению, заявка отклонена.</i>"
            text += msg

    # Передаем lang в клавиатуру (нужно будет обновить клавиатуру тоже, см. ниже)
    await call.message.edit_text(
        text,
        reply_markup=kb_event_actions(event_id, is_reg, status, lang),  # <--- Передаем lang
        parse_mode="HTML"
    )
    await call.answer()


# 3. Подача заявки
@router.callback_query(F.data.startswith("evt_reg_"))
async def register_event(call: types.CallbackQuery):
    event_id = int(call.data.split("_")[2])
    lang = await get_lang(call.from_user.id)

    async with SessionLocal() as s:
        q_user = await s.execute(select(User).where(User.tg_id == call.from_user.id))
        user = q_user.scalar_one()

        new_reg = EventRegistration(
            user_id=user.id,
            event_id=event_id,
            status="pending"
        )
        s.add(new_reg)
        await s.commit()

    msg = "Ariza yuborildi!" if lang == 'uz' else "Заявка отправлена!"
    await call.answer(msg, show_alert=True)
    await view_event(call)


# 4. Скачивание программы
@router.callback_query(F.data.startswith("evt_prog_"))
async def download_program(call: types.CallbackQuery):
    event_id = int(call.data.split("_")[2])
    lang = await get_lang(call.from_user.id)

    async with SessionLocal() as s:
        event = await s.get(Event, event_id)

    if event.program_file:
        caption = f"{event.title} materiallari" if lang == 'uz' else f"Материалы к {event.title}"
        try:
            if len(event.program_file) > 50 and not "." in event.program_file:
                await call.message.answer_document(event.program_file, caption=caption)
            else:
                file = FSInputFile(event.program_file)
                await call.message.answer_document(file, caption=caption)
        except Exception:
            msg = "Fayl xatoligi" if lang == 'uz' else "Ошибка файла"
            await call.answer(msg, show_alert=True)
    else:
        msg = "Dastur fayli yuklanmagan" if lang == 'uz' else "Файл программы не загружен организатором"
        await call.answer(msg, show_alert=True)

    await call.answer()


# 5. Кнопка "Мои мероприятия" (История)
@router.message(F.text.in_(["Мои мероприятия", "Mening tadbirlarim"]))
async def my_events(message: types.Message):
    lang = await get_lang(message.from_user.id)

    async with SessionLocal() as s:
        user = (await s.execute(select(User).where(User.tg_id == message.from_user.id))).scalar_one()
        q = await s.execute(
            select(EventRegistration, Event)
            .join(Event, EventRegistration.event_id == Event.id)
            .where(EventRegistration.user_id == user.id)
            .order_by(EventRegistration.created_at.desc())
        )
        results = q.all()

    if lang == 'uz':
        text_header = "<b>📌 Sizning tadbirlar tarixingiz:</b>\n\n"
        text_empty = "Siz hali hech qanday tadbirda qatnashmagansiz."
        status_names = {"pending": "⏳ Ko‘rib chiqilmoqda", "approved": "✅ Tasdiqlangan", "rejected": "❌ Rad etilgan"}
    else:
        text_header = "<b>📌 Ваша история мероприятий:</b>\n\n"
        text_empty = "Вы пока не участвовали ни в одном мероприятии."
        status_names = {"pending": "⏳ На рассмотрении", "approved": "✅ Одобрено", "rejected": "❌ Отклонено"}

    if not results:
        await message.answer(text_empty)
        return

    text = text_header
    builder = InlineKeyboardBuilder()

    for reg, event in results:
        status_text = status_names.get(reg.status, reg.status)
        text += f"🔹 <b>{event.title}</b>\n   └ <i>{status_text}</i>\n\n"
        builder.row(InlineKeyboardButton(text=f"{event.title}", callback_data=f"evt_view_{event.id}"))

    await message.answer(text, reply_markup=builder.as_markup(), parse_mode="HTML")


# 6. Обработка оценки
@router.callback_query(F.data.startswith("rate_"))
async def process_rating(call: types.CallbackQuery):
    parts = call.data.split("_")
    event_id = int(parts[1])
    score = int(parts[2])
    lang = await get_lang(call.from_user.id)

    async with SessionLocal() as s:
        q_user = await s.execute(select(User).where(User.tg_id == call.from_user.id))
        user = q_user.scalar_one()

        q_reg = await s.execute(select(EventRegistration).where(
            and_(EventRegistration.event_id == event_id, EventRegistration.user_id == user.id)))
        reg = q_reg.scalar_one_or_none()

        if reg:
            reg.rating = score
            await s.commit()
            msg = f"Rahmat! Bahongiz: {score} ⭐" if lang == 'uz' else f"Спасибо! Вы поставили оценку: {score} ⭐"
            await call.message.edit_text(msg)
        else:
            msg = "Xatolik: Siz bu tadbirga yozilmagansiz." if lang == 'uz' else "Ошибка: не найдена ваша регистрация."
            await call.message.edit_text(msg)

    await call.answer()