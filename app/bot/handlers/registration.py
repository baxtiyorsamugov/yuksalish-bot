import re
from aiogram import Router, F, types
from aiogram.types import Message, CallbackQuery, FSInputFile, InlineKeyboardMarkup, InlineKeyboardButton, \
    ReplyKeyboardMarkup
from aiogram.fsm.context import FSMContext
from sqlalchemy import select

# Импорты из вашего проекта
from app.bot.states import Reg
from app.bot.keyboards import (
    kb_phone, kb_confirm, get_regions_keyboard, get_spheres_keyboard,
    kb_main, kb_gender
)
from app.db.session import SessionLocal
from app.db.models import User, Profile, Region, Sphere
from app.db.repo import get_all_regions, get_all_spheres
from app.services.certificate import ensure_certificate_and_get_path
from app.services.validator import validate_fullname

router = Router()


# === 1. СТАРТ РЕГИСТРАЦИИ ===
@router.message(F.text.in_(["Регистрация", "A'zo bo‘lish", "Registration"]))
async def reg_start(message: Message, state: FSMContext):
    # Проверка, если уже зарегистрирован
    async with SessionLocal() as s:
        q_user = await s.execute(select(User).where(User.tg_id == message.from_user.id))
        user = q_user.scalar_one_or_none()
        if user:
            q_prof = await s.execute(select(Profile).where(Profile.user_id == user.id))
            prof = q_prof.scalar_one_or_none()
            if prof:
                await message.answer("Вы уже зарегистрированы / Siz allaqachon ro‘yxatdan o‘tgansiz ✅")
                return

    # ОПРЕДЕЛЯЕМ ЯЗЫК ПО КНОПКЕ
    if message.text == "A'zo bo‘lish":
        lang = "uz"
    elif message.text == "Registration":
        lang = "en"
    else:
        lang = "ru"

    await state.update_data(language=lang)

    # Выдаем текст на нужном языке
    if lang == 'uz':
        text = "Iltimos, <b>Ism va Familiyangizni</b> kiriting:\n(Masalan: Baxtiyor Samugov)"
    elif lang == 'en':
        text = "Please enter your <b>First and Last Name</b>:\n(Example: John Doe)"
    else:
        text = "Пожалуйста, введите ваши <b>Имя и Фамилию</b>:\n(Например: Бахтиёр Самугов)"

    await state.set_state(Reg.full_name)
    await message.answer(text, parse_mode="HTML")


# === 2. ПОЛУЧАЕМ ИМЯ И СПРАШИВАЕМ РЕГИОН ===
@router.message(Reg.full_name)
async def reg_name_entered(message: Message, state: FSMContext):
    data = await state.get_data()
    lang = data.get('language', 'ru')

    # Валидация имени
    validation = validate_fullname(message.text)

    if not validation["valid"]:
        error_code = validation["error"]
        if lang == 'uz':
            errors = {
                "short": "Ism juda qisqa.",
                "long": "Ism juda uzun.",
                "symbols": "Ismda faqat harflar bo‘lishi kerak.",
                "bad_word": "Iltimos, haqiqiy ismingizni yozing."
            }
            msg = errors.get(error_code, "Noto‘g‘ri format.")
        else:
            errors = {
                "short": "Имя слишком короткое.",
                "long": "Имя слишком длинное.",
                "symbols": "В имени должны быть только буквы.",
                "bad_word": "Пожалуйста, введите реальное имя."
            }
            msg = errors.get(error_code, "Неверный формат.")

        await message.answer(f"❌ {msg}\n👇")
        return

    full_name = validation["clean_name"]
    await state.update_data(full_name=full_name)

    # Переход к регионам
    regions = await get_all_regions()

    if lang == 'uz':
        text = "Yashash hududingizni tanlang:"
    else:
        text = "Выберите регион проживания:"

    await state.set_state(Reg.region)
    await message.answer(
        text,
        reply_markup=get_regions_keyboard(regions, lang=lang)
    )


# === 3. ВЫБОР РЕГИОНА ===
@router.callback_query(F.data.startswith("reg_"), Reg.region)
async def reg_region_chosen(call: CallbackQuery, state: FSMContext):
    region_id = int(call.data.split("_")[1])
    await state.update_data(region_id=region_id)

    data = await state.get_data()
    lang = data.get('language', 'ru')

    spheres = await get_all_spheres()

    if lang == 'uz':
        text_accepted = "Hudud tanlandi ✅"
        text_ask_sphere = "Qaysi ijtimoiy toifaga mansubsiz? Iltimos belgilang."
    else:
        text_accepted = "Регион принят ✅"
        text_ask_sphere = "Выберите сферу деятельности:"

    await call.message.edit_text(text_accepted)
    await call.message.answer(
        text_ask_sphere,
        reply_markup=get_spheres_keyboard(spheres, lang=lang)
    )

    await state.set_state(Reg.sphere)
    await call.answer()


# === 4. ВЫБОР СФЕРЫ ===
@router.callback_query(F.data.startswith("sph_"), Reg.sphere)
async def reg_sphere_chosen(call: CallbackQuery, state: FSMContext):
    sphere_id = int(call.data.split("_")[1])
    await state.update_data(sphere_id=sphere_id)

    data = await state.get_data()
    lang = data.get('language', 'ru')

    if lang == 'uz':
        text_accepted = "Soha tanlandi ✅"
        text_ask_year = "Tug‘ilgan yilingiz? Masalan: 1998"
    else:
        text_accepted = "Сфера принята ✅"
        text_ask_year = "Год рождения? Например: 1998"

    await call.message.edit_text(text_accepted)
    await state.set_state(Reg.birth_year)
    await call.message.answer(text_ask_year)
    await call.answer()


# === 5. ГОД РОЖДЕНИЯ ===
@router.message(Reg.birth_year)
async def reg_birth(message: Message, state: FSMContext):
    data = await state.get_data()
    lang = data.get('language', 'ru')

    if lang == 'uz':
        err_num = "Iltimos, yilni raqamda kiriting."
        err_range = "Xatolik. Iltimos, haqiqiy yilni kiriting."
        msg_gender = "Jinsingizni tanlang:"
    else:
        err_num = "Пожалуйста, введите год числом."
        err_range = "Похоже на ошибку. Введите реальный год."
        msg_gender = "Выберите ваш пол:"

    try:
        y = int(message.text.strip())
        if y < 1930 or y > 2018:
            return await message.answer(err_range)
        await state.update_data(birth_year=y)
    except ValueError:
        return await message.answer(err_num)

    await state.set_state(Reg.gender)
    await message.answer(msg_gender, reply_markup=kb_gender(lang))


# === 6. ВЫБОР ПОЛА ===
@router.callback_query(F.data.startswith("gender_"), Reg.gender)
async def reg_gender_chosen(call: CallbackQuery, state: FSMContext):
    gender_code = call.data.split("_")[1]
    await state.update_data(gender=gender_code)

    data = await state.get_data()
    lang = data.get('language', 'ru')

    if lang == 'uz':
        text_accepted = "Qabul qilindi ✅"
        text_phone = "Endi telefon raqamingizni yuboring (tugmani bosing):"
    else:
        text_accepted = "Принято ✅"
        text_phone = "Теперь отправьте номер телефона (нажмите кнопку ниже):"

    await call.message.edit_text(text_accepted)
    await state.set_state(Reg.phone)
    await call.message.answer(text_phone, reply_markup=kb_phone(lang))
    await call.answer()


# === 7. ТЕЛЕФОН И ПРЕДВАРИТЕЛЬНАЯ ПРОВЕРКА ===
@router.message(Reg.phone)
async def reg_phone(message: Message, state: FSMContext):
    data = await state.get_data()
    lang = data.get('language', 'ru')
    phone_to_save = None

    if message.contact:
        phone_to_save = message.contact.phone_number
    elif message.text:
        clean_text = re.sub(r'[ \-\(\)]', '', message.text)
        if re.match(r'^\+?\d{7,15}$', clean_text):
            phone_to_save = clean_text
        else:
            msg = "Noto‘g‘ri format." if lang == 'uz' else "Неверный формат."
            await message.answer(msg)
            return
    else:
        msg = "Telefon raqam yuboring." if lang == 'uz' else "Отправьте номер телефона."
        await message.answer(msg)
        return

    await state.update_data(phone=phone_to_save)

    async with SessionLocal() as s:
        reg_obj = await s.get(Region, data['region_id'])
        sph_obj = await s.get(Sphere, data['sphere_id'])
        full_name = data.get("full_name", message.from_user.full_name)

        if lang == 'uz':
            reg_name = reg_obj.name_uz if reg_obj else "Topilmadi"
            sph_name = sph_obj.name_uz if sph_obj else "Topilmadi"
            gender_txt = "Erkak" if data['gender'] == 'male' else "Ayol"

            text = (
                f"📋 <b>Ma’lumotlarni tekshiring:</b>\n\n"
                f"👤 <b>F.I.Sh:</b> {full_name}\n"
                f"📍 <b>Hudud:</b> {reg_name}\n"
                f"💼 <b>Soha:</b> {sph_name}\n"
                f"📅 <b>Tug‘ilgan yil:</b> {data['birth_year']}\n"
                f"👤 <b>Jins:</b> {gender_txt}\n"
                f"📞 <b>Telefon:</b> {phone_to_save}"
            )
        else:
            reg_name = reg_obj.name_ru if reg_obj else "Не найден"
            sph_name = sph_obj.name_ru if sph_obj else "Не найден"
            gender_txt = "Мужской" if data['gender'] == 'male' else "Женский"

            text = (
                f"📋 <b>Проверьте данные:</b>\n\n"
                f"👤 <b>ФИО:</b> {full_name}\n"
                f"📍 <b>Регион:</b> {reg_name}\n"
                f"💼 <b>Сфера:</b> {sph_name}\n"
                f"📅 <b>Год рождения:</b> {data['birth_year']}\n"
                f"👤 <b>Пол:</b> {gender_txt}\n"
                f"📞 <b>Телефон:</b> {phone_to_save}"
            )

    await state.set_state(Reg.confirm)
    await message.answer(text, reply_markup=kb_confirm(lang), parse_mode="HTML")


# === 8. ОТМЕНА / ЗАНОВО ===
@router.callback_query(Reg.confirm, F.data == "confirm_no")
async def confirm_no(call: CallbackQuery, state: FSMContext):
    await state.clear()
    await call.message.edit_text("Bekor qilindi / Отменено.")


# === 9. ФИНАЛ: СОХРАНЕНИЕ (БЕЗ ВЫДАЧИ ФАЙЛА) ===
@router.callback_query(Reg.confirm, F.data == "confirm_yes")
async def reg_final(call: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    lang = data.get('language', 'ru')
    full_name_input = data.get("full_name", "Unknown")

    async with SessionLocal() as s:
        q = await s.execute(select(User).where(User.tg_id == call.from_user.id))
        user = q.scalar_one()

        # Обновляем имя
        parts = full_name_input.split()
        if len(parts) >= 2:
            user.first_name = parts[0]
            user.last_name = " ".join(parts[1:])
        else:
            user.first_name = full_name_input
            user.last_name = ""
        user.phone = data['phone']

        # Создаем профиль (PENDING)
        q2 = await s.execute(select(Profile).where(Profile.user_id == user.id))
        prof = q2.scalar_one_or_none()

        if not prof:
            prof = Profile(
                user_id=user.id,
                region_id=data["region_id"],
                sphere_id=data["sphere_id"],
                birth_year=data["birth_year"],
                gender=data["gender"],
                status="pending"
            )
            s.add(prof)
        else:
            prof.region_id = data["region_id"]
            prof.sphere_id = data["sphere_id"]
            prof.birth_year = data["birth_year"]
            prof.gender = data["gender"]
            prof.status = "pending"

        await s.commit()

    await call.message.delete()

    if lang == 'uz':
        text = (
            "✅ <b>Ro‘yxatdan o‘tish yakunlandi!</b>\n\n"
            "Sizning ma'lumotlaringiz moderatorga yuborildi.\n"
            "Tasdiqlangandan so‘ng, sizga xabar keladi va sertifikat olishingiz mumkin bo‘ladi."
        )
    else:
        text = (
            "✅ <b>Регистрация завершена!</b>\n\n"
            "Ваши данные отправлены модератору на проверку.\n"
            "Как только профиль будет подтвержден, вам придет уведомление, и вы сможете получить сертификат."
        )

    await call.message.answer(
        text,
        reply_markup=kb_main(is_registered=True, lang=lang),
        parse_mode="HTML"
    )
    await state.clear()
    await call.answer()


# === 10. КНОПКА СЕРТИФИКАТА (INLINE - "ПОСМОТРЕТЬ") ===
@router.callback_query(F.data == "view_certificate")
async def view_certificate_btn(call: CallbackQuery, state: FSMContext):
    async with SessionLocal() as s:
        user = await s.scalar(select(User).where(User.tg_id == call.from_user.id))
        lang = user.language if user and user.language else 'ru'
        profile = await s.scalar(select(Profile).where(Profile.user_id == user.id))

    if not profile:
        await call.answer("Error", show_alert=True)
        return

    # ПРОВЕРКА
    if profile.status == 'pending':
        msg = "⏳ Profilingiz tekshirilmoqda." if lang == 'uz' else "⏳ Ваш профиль на проверке."
        await call.answer(msg, show_alert=True)
        return

    if profile.status == 'rejected':
        msg = "❌ Rad etilgan." if lang == 'uz' else "❌ Отклонено."
        await call.answer(msg, show_alert=True)
        return

    # ВЫДАЧА
    await call.message.answer_chat_action("upload_document")
    try:
        cert_path = await ensure_certificate_and_get_path(tg_id=call.from_user.id)
        document = FSInputFile(cert_path)
        caption = "Sizning a'zolik sertifikatingiz 🪪" if lang == 'uz' else "Ваш сертификат членства 🪪"
        await call.message.answer_document(document, caption=caption)
        await call.answer()
    except Exception as e:
        await call.answer("Error", show_alert=True)


# === 11. КНОПКА СЕРТИФИКАТА (ГЛАВНОЕ МЕНЮ) ===
@router.message(F.text.in_(["Сертификат", "Sertifikat"]))
async def show_certificate_button(message: Message):
    async with SessionLocal() as s:
        user = await s.scalar(select(User).where(User.tg_id == message.from_user.id))
        lang = user.language if user and user.language else 'ru'
        profile = await s.scalar(select(Profile).where(Profile.user_id == user.id))

    if not profile:
        msg = "Avval ro‘yxatdan o‘ting." if lang == 'uz' else "Сначала пройдите регистрацию."
        await message.answer(msg)
        return

    # ПРОВЕРКА
    if profile.status == 'pending':
        if lang == 'uz':
            text = "⏳ <b>Sizning ma'lumotlaringiz tekshirilmoqda.</b>"
        else:
            text = "⏳ <b>Ваш профиль находится на проверке.</b>"
        await message.answer(text, parse_mode="HTML")
        return

    if profile.status == 'rejected':
        if lang == 'uz':
            text = "❌ <b>Sizning arizangiz rad etilgan.</b>"
        else:
            text = "❌ <b>Ваша заявка была отклонена.</b>"
        await message.answer(text, parse_mode="HTML")
        return

    # ВЫДАЧА
    await message.bot.send_chat_action(chat_id=message.chat.id, action="upload_document")
    try:
        caption_text = "Sizning a'zolik sertifikatingiz 🪪" if lang == 'uz' else "Ваш сертификат членства 🪪"
        cert_path = await ensure_certificate_and_get_path(tg_id=message.from_user.id)
        document = FSInputFile(cert_path)
        await message.answer_document(document, caption=caption_text)
    except Exception as e:
        await message.answer(f"Error: {e}")