from aiogram import Router, F
from aiogram import types
from aiogram.types import Message
from aiogram.fsm.context import FSMContext
from sqlalchemy import select
from app.bot.states import Reg
from app.bot.keyboards import kb_phone, kb_main, kb_confirm
from app.db.session import SessionLocal
from app.db.models import User, Profile, Region, Sphere
from app.services.certificate import ensure_certificate_and_get_path
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, InputFile, FSInputFile, Message, CallbackQuery
from app.db.repo import get_all_regions, get_all_spheres
from app.bot.keyboards import get_regions_keyboard, get_spheres_keyboard

router = Router()


@router.message(F.text == "Сертификат")
async def send_certificate(message: Message, state: FSMContext):
    # Генерация сертификата и получение пути
    cert_path = await ensure_certificate_and_get_path(tg_id=message.from_user.id)

    # В aiogram 3 используем FSInputFile для файлов с диска
    # Просто передаем путь к файлу
    document = FSInputFile(cert_path)

    # Отправка документа
    await message.answer_document(document, caption="Ваш сертификат членства 🪪")

@router.message(F.text.in_(["Регистрация", "Ro‘yxatdan o‘tish", "Registration"]))
async def reg_start(message: Message, state: FSMContext):
    # Проверка, если пользователь уже зарегистрирован
    user = (await SessionLocal().execute(select(User).where(User.tg_id == message.from_user.id))).scalar_one()
    prof = (await SessionLocal().execute(select(Profile).where(Profile.user_id == user.id))).scalar_one_or_none()

    if prof:
        await message.answer("Вы уже зарегистрированы ✅")
        return

    await state.set_state(Reg.region)
    await message.answer("Выберите регион (напишите цифру ID региона):")


@router.message(Reg.region)
async def reg_region(message: Message, state: FSMContext):
    try:
        region_id = int(message.text.strip())
        await state.update_data(region_id=region_id)
    except ValueError:
        return await message.answer("Введите число (ID региона).")

    await state.set_state(Reg.sphere)
    await message.answer("Выберите сферу деятельности (ID):")


@router.message(Reg.sphere)
async def reg_sphere(message: Message, state: FSMContext):
    try:
        sphere_id = int(message.text.strip())
        await state.update_data(sphere_id=sphere_id)
    except ValueError:
        return await message.answer("Введите число (ID сферы).")

    await state.set_state(Reg.birth_year)
    await message.answer("Год рождения? Например: 1998")


@router.message(Reg.birth_year)
async def reg_birth(message: Message, state: FSMContext):
    try:
        y = int(message.text.strip())
        if y < 1930 or y > 2010:
            return await message.answer("Похоже на ошибку. Введите нормальный год (например 1998).")
        await state.update_data(birth_year=y)
    except ValueError:
        return await message.answer("Введите год числом.")

    await state.set_state(Reg.gender)
    await message.answer("Пол: напишите M или F")




@router.message(Reg.gender)
async def reg_gender(message: Message, state: FSMContext):
    g = message.text.strip().upper()
    if g not in ["M", "F"]:
        return await message.answer("Введите M или F.")
    await state.update_data(gender=("male" if g == "M" else "female"))

    await state.set_state(Reg.phone)
    await message.answer("Теперь номер телефона (кнопкой):", reply_markup=kb_phone())


@router.message(Reg.phone, F.contact)
async def reg_phone(message: Message, state: FSMContext):
    phone = message.contact.phone_number
    data = await state.get_data()

    async with SessionLocal() as s:
        q = await s.execute(select(User).where(User.tg_id == message.from_user.id))
        user = q.scalar_one()
        user.phone = phone

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

    # Подтверждение данных перед сохранением
    await state.set_state(Reg.confirm)
    await message.answer("Проверьте введённые данные:", reply_markup=kb_confirm())


@router.callback_query(Reg.confirm, F.data == "confirm_data")
async def confirm_data(call: types.CallbackQuery, state: FSMContext):
    # Завершаем регистрацию
    data = await state.get_data()
    region = (await SessionLocal().execute(select(Region).where(Region.id == data["region_id"]))).scalar_one()
    sphere = (await SessionLocal().execute(select(Sphere).where(Sphere.id == data["sphere_id"]))).scalar_one()

    text = f"Подтверждение:\n\nФИО: {data['full_name']}\nТелефон: {data['phone']}\nРегион: {region.name_ru}\nСфера: {sphere.name_ru}"
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ Подтвердить", callback_data="confirm_yes")],
        [InlineKeyboardButton(text="❌ Изменить", callback_data="confirm_no")]
    ])

    await call.message.edit_text(text, reply_markup=kb)

@router.callback_query(Reg.confirm, F.data == "confirm_yes")
async def reg_final(call: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()

    # Генерация сертификата
    cert_path = await ensure_certificate_and_get_path(tg_id=call.from_user.id)

    # Завершаем процесс регистрации
    await state.clear()

    # Сообщение об успешной регистрации с inline кнопкой для дальнейших действий
    await call.message.edit_text(
        "Регистрация завершена ✅ Вы зарегистрированы как член Юксалиш.",
        reply_markup=InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text="Посмотреть сертификат", callback_data="view_certificate")]
            ]
        )
    )

    # Отправка сертификата
    await call.message.answer_document(open(cert_path, "rb"), caption="Ваш сертификат членства 🪪")
    await call.answer()

# Дополнительная обработка нажатия на кнопку "Посмотреть сертификат"
@router.callback_query(F.data == "view_certificate")
async def view_certificate(call: types.CallbackQuery, state: FSMContext):
    # Генерация сертификата
    cert_path = await ensure_certificate_and_get_path(tg_id=call.from_user.id)

    # В aiogram 3 используем FSInputFile для файлов с диска
    document = FSInputFile(cert_path)

    # Отправка документа
    await call.message.answer_document(document, caption="Ваш сертификат членства 🪪")

    # Убираем часики загрузки у кнопки
    await call.answer()

# @router.callback_query(Reg.confirm, F.data == "confirm_yes")
# async def reg_final(call: types.CallbackQuery, state: FSMContext):
#     data = await state.get_data()
#
#     # Генерация сертификата
#     cert_path = await ensure_certificate_and_get_path(tg_id=call.from_user.id)
#
#     # Завершаем процесс регистрации
#     await state.clear()
#
#     # Сообщение об успешной регистрации
#     await call.message.edit_text("Регистрация завершена ✅ Вы зарегистрированы как член Юксалиш.",
#                                  reply_markup=kb_main())
#
#     # Отправка сертификата
#     await call.message.answer_document(open(cert_path, "rb"), caption="Ваш сертификат членства 🪪")
#     await call.answer()


# @router.callback_query(Reg.confirm, F.data == "confirm_yes")
# async def reg_final(call: types.CallbackQuery, state: FSMContext):
#     data = await state.get_data()
#
#     # Генерация сертификата
#     cert_path = await ensure_certificate_and_get_path(tg_id=call.from_user.id)
#
#     # Завершаем процесс регистрации
#     await state.clear()
#
#     # Сообщение об успешной регистрации
#     await call.message.edit_text("Регистрация завершена ✅ Вы зарегистрированы как член Юксалиш.",
#                                  reply_markup=kb_main())
#
#     # Отправка сертификата
#     await call.message.answer_document(open(cert_path, "rb"), caption="Ваш сертификат членства 🪪")
#     await call.answer()