from aiogram import Router, F, types
from aiogram.types import FSInputFile, InlineKeyboardButton
from sqlalchemy import select, and_
from aiogram.utils.keyboard import InlineKeyboardBuilder
from app.db.session import SessionLocal
from app.db.models import Event, EventRegistration, User
from app.bot.keyboards import kb_events_list, kb_event_actions

router = Router()


# 1. Показать список активных мероприятий
@router.message(F.text == "🎫 Мероприятия")
@router.callback_query(F.data == "evt_back")
async def show_events(update: types.Message | types.CallbackQuery):
    # Универсальная функция (работает и от кнопки, и от сообщения)
    if isinstance(update, types.CallbackQuery):
        message = update.message
    else:
        message = update

    async with SessionLocal() as s:
        # Берем только активные мероприятия
        q = await s.execute(select(Event).where(Event.status == "active").order_by(Event.date_event.desc()))
        events = q.scalars().all()

    if not events:
        await message.answer("На данный момент активных мероприятий нет.")
    else:
        text = "<b>📅 Актуальные мероприятия:</b>\n\nВыберите мероприятие, чтобы узнать подробности и подать заявку."

        # Если это было редактирование (кнопка Назад)
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

    async with SessionLocal() as s:
        event = await s.get(Event, event_id)

        # Проверяем, зарегистрирован ли уже этот юзер на этот ивент
        q_user = await s.execute(select(User).where(User.tg_id == user_id))
        db_user = q_user.scalar_one()

        q_reg = await s.execute(
            select(EventRegistration)
            .where(and_(EventRegistration.event_id == event_id, EventRegistration.user_id == db_user.id))
        )
        reg = q_reg.scalar_one_or_none()

    if not event:
        await call.answer("Мероприятие не найдено", show_alert=True)
        return

    # Формируем красивый текст
    text = (
        f"<b>{event.title}</b>\n\n"
        f"📍 <b>Локация:</b> {event.location}\n"
        f"🗓 <b>Дата:</b> {event.date_event.strftime('%d.%m.%Y %H:%M')}\n\n"
        f"ℹ️ <b>Описание:</b>\n{event.description}\n\n"
    )

    # Определяем статус для кнопок
    is_reg = (reg is not None)
    status = reg.status if reg else None

    if is_reg:
        if status == 'pending':
            text += "\n⚠️ <i>Ваша заявка находится на рассмотрении модератора.</i>"
        elif status == 'approved':
            text += "\n✅ <i>Ваша заявка одобрена! Вы можете скачать материалы.</i>"
        elif status == 'rejected':
            text += "\n❌ <i>К сожалению, заявка отклонена.</i>"

    await call.message.edit_text(
        text,
        reply_markup=kb_event_actions(event_id, is_reg, status),
        parse_mode="HTML"
    )
    await call.answer()


# 3. Подача заявки
@router.callback_query(F.data.startswith("evt_reg_"))
async def register_event(call: types.CallbackQuery):
    event_id = int(call.data.split("_")[2])

    async with SessionLocal() as s:
        # Находим User ID в БД
        q_user = await s.execute(select(User).where(User.tg_id == call.from_user.id))
        user = q_user.scalar_one()

        # Создаем запись
        new_reg = EventRegistration(
            user_id=user.id,
            event_id=event_id,
            status="pending"  # Сразу ставим "на рассмотрении"
        )
        s.add(new_reg)
        await s.commit()

    await call.answer("Заявка отправлена!", show_alert=True)

    # Обновляем сообщение (чтобы кнопка изменилась на "На рассмотрении")
    # Просто перезагружаем view_event для этого же ID
    await view_event(call)


# 4. Скачивание программы (Только если approved)
@router.callback_query(F.data.startswith("evt_prog_"))
async def download_program(call: types.CallbackQuery):
    event_id = int(call.data.split("_")[2])

    async with SessionLocal() as s:
        event = await s.get(Event, event_id)

    if event.program_file:
        try:
            # Если это file_id телеграма
            if len(event.program_file) > 50 and not "." in event.program_file:
                await call.message.answer_document(event.program_file, caption=f"Материалы к {event.title}")
            # Если это путь к файлу на диске
            else:
                file = FSInputFile(event.program_file)
                await call.message.answer_document(file, caption=f"Материалы к {event.title}")
        except Exception as e:
            await call.answer("Ошибка файла", show_alert=True)
    else:
        await call.answer("Файл программы не загружен организатором", show_alert=True)

    await call.answer()


# 5. Кнопка "Мои мероприятия" (История)
@router.message(F.text == "📌 Мои мероприятия")
async def my_events(message: types.Message):
    async with SessionLocal() as s:
        user = (await s.execute(select(User).where(User.tg_id == message.from_user.id))).scalar_one()

        # Получаем все регистрации юзера + данные о самом ивенте
        # Join нужен, чтобы достать название мероприятия
        q = await s.execute(
            select(EventRegistration, Event)
            .join(Event, EventRegistration.event_id == Event.id)
            .where(EventRegistration.user_id == user.id)
            .order_by(EventRegistration.created_at.desc())
        )
        results = q.all()  # Вернет список пар [(Reg, Event), (Reg, Event)...]

    if not results:
        await message.answer("Вы пока не участвовали ни в одном мероприятии.")
        return

    text = "<b>📌 Ваша история мероприятий:</b>\n\n"

    builder = InlineKeyboardBuilder()

    for reg, event in results:
        status_emoji = {
            "pending": "⏳",
            "approved": "✅",
            "rejected": "❌"
        }.get(reg.status, "❓")

        # Текст для списка
        text += f"{status_emoji} <b>{event.title}</b> ({reg.status})\n"

        # Добавляем кнопку для быстрого перехода к мероприятию
        builder.row(InlineKeyboardButton(
            text=f"{status_emoji} {event.title}",
            callback_data=f"evt_view_{event.id}"
        ))

    await message.answer(text, reply_markup=builder.as_markup(), parse_mode="HTML")


# 6. Обработка оценки (Рейтинг)
@router.callback_query(F.data.startswith("rate_"))
async def process_rating(call: types.CallbackQuery):
    # data имеет формат: rate_{event_id}_{score}
    # Например: rate_5_5 (Ивент №5, Оценка 5)
    parts = call.data.split("_")
    event_id = int(parts[1])
    score = int(parts[2])

    async with SessionLocal() as s:
        # 1. Находим пользователя в БД
        q_user = await s.execute(select(User).where(User.tg_id == call.from_user.id))
        user = q_user.scalar_one()

        # 2. Находим его регистрацию на этот ивент
        # Используем and_, чтобы найти совпадение и по юзеру, и по ивенту
        q_reg = await s.execute(
            select(EventRegistration)
            .where(and_(
                EventRegistration.event_id == event_id,
                EventRegistration.user_id == user.id
            ))
        )
        reg = q_reg.scalar_one_or_none()

        if reg:
            # 3. Записываем оценку
            reg.rating = score
            await s.commit()

            # 4. Меняем сообщение на благодарность
            await call.message.edit_text(f"Спасибо! Вы поставили оценку: {score} ⭐\nМы учтем ваше мнение.")
        else:
            await call.message.edit_text("Ошибка: не найдена ваша запись на это мероприятие.")

    await call.answer()