from aiogram import Router, F, types
from aiogram.types import Message, CallbackQuery, FSInputFile, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from sqlalchemy import select

# Импорты из вашего проекта
from app.bot.states import Reg
from app.bot.keyboards import kb_phone, kb_confirm, get_regions_keyboard, get_spheres_keyboard
from app.db.session import SessionLocal
from app.db.models import User, Profile, Region, Sphere
from app.db.repo import get_all_regions, get_all_spheres  # Новые функции запросов
from app.services.certificate import ensure_certificate_and_get_path

router = Router()


# === 1. Обработчик кнопки "Сертификат" ===
@router.message(F.text == "Сертификат")
async def send_certificate_btn(message: Message, state: FSMContext):
    cert_path = await ensure_certificate_and_get_path(tg_id=message.from_user.id)
    document = FSInputFile(cert_path)
    await message.answer_document(document, caption="Ваш сертификат членства 🪪")


# === 2. Старт регистрации ===
@router.message(F.text.in_(["Регистрация", "Ro‘yxatdan o‘tish", "Registration"]))
async def reg_start(message: Message, state: FSMContext):
    # Проверка: есть ли уже профиль?
    async with SessionLocal() as session:
        # Находим юзера по tg_id
        q_user = await session.execute(select(User).where(User.tg_id == message.from_user.id))
        user = q_user.scalar_one_or_none()

        if user:
            # Проверяем профиль
            q_prof = await session.execute(select(Profile).where(Profile.user_id == user.id))
            prof = q_prof.scalar_one_or_none()
            if prof:
                await message.answer("Вы уже зарегистрированы ✅")
                return

    # Если профиля нет, начинаем регистрацию
    # Получаем список регионов
    regions = await get_all_regions()

    if not regions:
        await message.answer("Ошибка: Список регионов пуст. Обратитесь к администратору.")
        return

    # Записываем язык (если есть логика выбора языка, добавьте сюда. Пока 'ru')
    await state.update_data(language='ru')

    await state.set_state(Reg.region)
    await message.answer(
        "Выберите регион проживания:",
        reply_markup=get_regions_keyboard(regions, lang='ru')
    )


# === 3. Выбор региона (нажатие кнопки) ===
@router.callback_query(F.data.startswith("reg_"), Reg.region)
async def reg_region_chosen(call: CallbackQuery, state: FSMContext):
    # reg_5 -> id=5
    region_id = int(call.data.split("_")[1])
    await state.update_data(region_id=region_id)

    # Получаем сферы
    spheres = await get_all_spheres()

    # Красиво меняем старое сообщение
    await call.message.edit_text("Регион принят ✅")

    # Отправляем кнопки сфер
    await call.message.answer(
        "Выберите сферу деятельности:",
        reply_markup=get_spheres_keyboard(spheres, lang='ru')
    )

    await state.set_state(Reg.sphere)
    await call.answer()


# === 4. Выбор сферы (нажатие кнопки) ===
@router.callback_query(F.data.startswith("sph_"), Reg.sphere)
async def reg_sphere_chosen(call: CallbackQuery, state: FSMContext):
    sphere_id = int(call.data.split("_")[1])
    await state.update_data(sphere_id=sphere_id)

    await call.message.edit_text("Сфера принята ✅")

    # Переходим к году рождения
    await state.set_state(Reg.birth_year)
    await call.message.answer("Год рождения? Например: 1998")
    await call.answer()


# === 5. Год рождения ===
@router.message(Reg.birth_year)
async def reg_birth(message: Message, state: FSMContext):
    try:
        y = int(message.text.strip())
        if y < 1930 or y > 2015:
            return await message.answer("Похоже на ошибку. Введите реальный год (например 1998).")
        await state.update_data(birth_year=y)
    except ValueError:
        return await message.answer("Пожалуйста, введите год числом.")

    await state.set_state(Reg.gender)
    await message.answer("Ваш пол: напишите M (мужской) или F (женский)")


# === 6. Пол ===
@router.message(Reg.gender)
async def reg_gender(message: Message, state: FSMContext):
    g = message.text.strip().upper()
    if g not in ["M", "F", "М", "Ж"]:  # Добавил русские буквы на всякий случай
        return await message.answer("Введите M или F.")

    # Нормализация
    gender_code = "male" if g in ["M", "М"] else "female"
    await state.update_data(gender=gender_code)

    await state.set_state(Reg.phone)
    await message.answer("Отправьте номер телефона, нажав кнопку ниже:", reply_markup=kb_phone())


# === 7. Телефон и Предварительное сохранение ===
@router.message(Reg.phone, F.contact)
async def reg_phone(message: Message, state: FSMContext):
    phone = message.contact.phone_number
    # Сохраняем телефон в state, чтобы потом вывести в подтверждении
    await state.update_data(phone=phone)

    data = await state.get_data()

    # Получаем названия региона и сферы для красивого вывода
    async with SessionLocal() as s:
        reg_obj = await s.get(Region, data['region_id'])
        sph_obj = await s.get(Sphere, data['sphere_id'])
        reg_name = reg_obj.name_ru if reg_obj else "Не найден"
        sph_name = sph_obj.name_ru if sph_obj else "Не найден"

    # Формируем текст подтверждения
    text = (
        f"📋 <b>Проверьте данные:</b>\n\n"
        f"📍 Регион: {reg_name}\n"
        f"💼 Сфера: {sph_name}\n"
        f"📅 Год: {data['birth_year']}\n"
        f"👤 Пол: {data['gender']}\n"
        f"📞 Телефон: {phone}"
    )

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ Все верно", callback_data="confirm_yes")],
        [InlineKeyboardButton(text="❌ Заполнить заново", callback_data="confirm_no")]
    ])

    await state.set_state(Reg.confirm)
    await message.answer(text, reply_markup=kb, parse_mode="HTML")


# === 8. Отмена / Заново ===
@router.callback_query(Reg.confirm, F.data == "confirm_no")
async def confirm_no(call: CallbackQuery, state: FSMContext):
    await state.clear()
    await call.message.edit_text("Регистрация отменена. Нажмите /start или выберите Регистрацию снова.")


# === 9. Финал: Сохранение в БД и Сертификат ===
@router.callback_query(Reg.confirm, F.data == "confirm_yes")
async def reg_final(call: CallbackQuery, state: FSMContext):
    data = await state.get_data()

    # 1. Сохраняем в БД
    async with SessionLocal() as s:
        # Обновляем телефон у User
        q = await s.execute(select(User).where(User.tg_id == call.from_user.id))
        user = q.scalar_one()
        user.phone = data['phone']

        # Создаем или обновляем Profile
        q2 = await s.execute(select(Profile).where(Profile.user_id == user.id))
        prof = q2.scalar_one_or_none()

        if not prof:
            prof = Profile(
                user_id=user.id,
                region_id=data["region_id"],
                sphere_id=data["sphere_id"],
                birth_year=data["birth_year"],
                gender=data["gender"],
            )
            s.add(prof)
        else:
            prof.region_id = data["region_id"]
            prof.sphere_id = data["sphere_id"]
            prof.birth_year = data["birth_year"]
            prof.gender = data["gender"]

        await s.commit()

    # 2. Генерация сертификата
    await call.message.edit_text("⏳ Генерируем ваш сертификат...")

    try:
        cert_path = await ensure_certificate_and_get_path(tg_id=call.from_user.id)

        # 3. Отправка (Используем FSInputFile!)
        document = FSInputFile(cert_path)

        await call.message.delete()  # Удаляем "Генерируем..."

        await call.message.answer(
            "Поздравляем! Регистрация успешно завершена! 🎉\nВы приняты в сообщество.",
            reply_markup=InlineKeyboardMarkup(
                inline_keyboard=[
                    [InlineKeyboardButton(text="Посмотреть сертификат 🪪", callback_data="view_certificate")]
                ]
            )
        )
        # Сразу кидаем файл
        await call.message.answer_document(document, caption="Ваш сертификат готов!")

    except Exception as e:
        await call.message.answer(f"Произошла ошибка при создании сертификата: {e}")

    await state.clear()
    await call.answer()


# === 10. Кнопка просмотра сертификата ===
@router.callback_query(F.data == "view_certificate")
async def view_certificate_btn(call: CallbackQuery, state: FSMContext):
    cert_path = await ensure_certificate_and_get_path(tg_id=call.from_user.id)
    document = FSInputFile(cert_path)
    await call.message.answer_document(document, caption="Ваш сертификат членства 🪪")
    await call.answer()