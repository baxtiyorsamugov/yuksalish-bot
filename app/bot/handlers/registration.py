import re
from aiogram import Router, F, types
from aiogram.types import Message, CallbackQuery, FSInputFile, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from sqlalchemy import select
from app.bot.keyboards import kb_confirm

# Импорты из вашего проекта
from app.bot.states import Reg
from app.bot.keyboards import kb_phone, kb_confirm, get_regions_keyboard, get_spheres_keyboard, kb_main, kb_gender
from app.db.session import SessionLocal
from app.db.models import User, Profile, Region, Sphere
from app.db.repo import get_all_regions, get_all_spheres  # Новые функции запросов
from app.services.certificate import ensure_certificate_and_get_path
from app.services.validator import validate_fullname


router = Router()


# === 1. Обработчик кнопки "Сертификат" ===
@router.message(F.text.in_(["Сертификат", "Sertifikat"]))
async def send_certificate_btn(message: Message, state: FSMContext):
    # 1. Показываем статус "загрузка документа", пока бот думает
    await message.bot.send_chat_action(chat_id=message.chat.id, action="upload_document")

    try:
        # 2. Узнаем язык пользователя из базы данных
        async with SessionLocal() as s:
            user = await s.scalar(select(User).where(User.tg_id == message.from_user.id))
            lang = user.language if user and user.language else 'ru'

        # 3. Выбираем текст подписи в зависимости от языка
        if lang == 'uz':
            caption_text = "Sizning a'zolik sertifikatingiz 🪪"
        else:
            caption_text = "Ваш сертификат членства 🪪"

        # 4. Получаем путь и отправляем файл
        cert_path = await ensure_certificate_and_get_path(tg_id=message.from_user.id)
        document = FSInputFile(cert_path)

        # Подставляем переменную caption_text
        await message.answer_document(document, caption=caption_text)

    except Exception as e:
        await message.answer(f"Xatolik / Ошибка: {e}")


# === 2. Старт регистрации ===
@router.message(F.text.in_(["Регистрация", "Ro‘yxatdan o‘tish", "Registration"]))
async def reg_start(message: Message, state: FSMContext):
    # Проверка, если уже зарегистрирован (Ваш код проверки БД)
    async with SessionLocal() as session:
        q_user = await session.execute(select(User).where(User.tg_id == message.from_user.id))
        user = q_user.scalar_one_or_none()
        if user:
            q_prof = await session.execute(select(Profile).where(Profile.user_id == user.id))
            prof = q_prof.scalar_one_or_none()
            if prof:
                # Если профиль есть, отвечаем на нужном языке (можно упростить)
                await message.answer("Вы уже зарегистрированы / Siz allaqachon ro‘yxatdan o‘tgansiz ✅")
                return

    # === ИСПРАВЛЕНИЕ: ОПРЕДЕЛЯЕМ ЯЗЫК ПО КНОПКЕ ===
    if message.text == "Ro‘yxatdan o‘tish":
        lang = "uz"
    elif message.text == "Registration":
        lang = "en"
    else:
        lang = "ru"

    # ВАЖНО: Сохраняем язык в память, чтобы следующие шаги (регион, сфера) тоже были на этом языке
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


# 2. НОВЫЙ ХЕНДЛЕР: ПОЛУЧАЕМ ИМЯ И СПРАШИВАЕМ РЕГИОН
@router.message(Reg.full_name)
async def reg_name_entered(message: Message, state: FSMContext):
    # Получаем язык для ответов об ошибках
    data = await state.get_data()
    lang = data.get('language', 'ru')

    # Запускаем проверку
    validation = validate_fullname(message.text)

    if not validation["valid"]:
        error_code = validation["error"]

        # Формируем текст ошибки в зависимости от языка
        if lang == 'uz':
            errors = {
                "short": "Ism juda qisqa. Iltimos, to‘liq ismingizni kiriting.",
                "long": "Ism juda uzun.",
                "symbols": "Ismda faqat harflar bo‘lishi kerak (raqamlar va smayliklar mumkin emas).",
                "bad_word": "Iltimos, haqiqiy ismingizni yozing. So‘kinish yoki noto‘g‘ri so‘zlar taqiqlangan."
            }
            msg = errors.get(error_code, "Noto‘g‘ri format.")
        else:
            errors = {
                "short": "Имя слишком короткое. Введите полное имя.",
                "long": "Имя слишком длинное.",
                "symbols": "В имени должны быть только буквы (цифры и смайлики запрещены).",
                "bad_word": "Пожалуйста, введите реальное имя. Некорректные слова запрещены."
            }
            msg = errors.get(error_code, "Неверный формат.")

        await message.answer(f"❌ {msg}\n👇")
        return

    # Если всё хорошо — сохраняем чистое красивое имя (Title Case)
    full_name = validation["clean_name"]
    await state.update_data(full_name=full_name)

    # === ДАЛЬШЕ ПЕРЕХОД К РЕГИОНАМ (Ваш старый код) ===
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


# === 3. Выбор региона (нажатие кнопки) ===
@router.callback_query(F.data.startswith("reg_"), Reg.region)
async def reg_region_chosen(call: CallbackQuery, state: FSMContext):
    # 1. Сохраняем ID региона
    region_id = int(call.data.split("_")[1])
    await state.update_data(region_id=region_id)

    # 2. Получаем язык пользователя из памяти
    data = await state.get_data()
    lang = data.get('language', 'ru')

    # 3. Получаем список сфер из БД
    spheres = await get_all_spheres()

    # 4. Определяем тексты сообщений
    if lang == 'uz':
        text_accepted = "Hudud tanlandi ✅"
        text_ask_sphere = "Faoliyat sohangizni tanlang:"
    else:
        text_accepted = "Регион принят ✅"
        text_ask_sphere = "Выберите сферу деятельности:"

    # 5. Меняем старое сообщение (убираем кнопки регионов)
    await call.message.edit_text(text_accepted)

    # 6. Отправляем вопрос о сферах с ПРАВИЛЬНЫМ языком клавиатуры
    await call.message.answer(
        text_ask_sphere,
        reply_markup=get_spheres_keyboard(spheres, lang=lang) # <--- Передаем lang
    )

    # 7. Переключаем состояние
    await state.set_state(Reg.sphere)
    await call.answer()


# === 4. Выбор сферы (нажатие кнопки) ===
@router.callback_query(F.data.startswith("sph_"), Reg.sphere)
async def reg_sphere_chosen(call: CallbackQuery, state: FSMContext):
    # 1. Сохраняем ID сферы
    sphere_id = int(call.data.split("_")[1])
    await state.update_data(sphere_id=sphere_id)

    # 2. Получаем язык
    data = await state.get_data()
    lang = data.get('language', 'ru')

    # 3. Определяем тексты
    if lang == 'uz':
        text_accepted = "Soha tanlandi ✅"
        text_ask_year = "Tug‘ilgan yilingiz? Masalan: 1998"
    else:
        text_accepted = "Сфера принята ✅"
        text_ask_year = "Год рождения? Например: 1998"

    # 4. Меняем сообщение с кнопками на текст подтверждения
    await call.message.edit_text(text_accepted)

    # 5. Переходим к следующему шагу (Год рождения)
    await state.set_state(Reg.birth_year)
    await call.message.answer(text_ask_year)

    await call.answer()


# === 5. Год рождения ===
@router.message(Reg.birth_year)
async def reg_birth(message: Message, state: FSMContext):
    # Получаем язык
    data = await state.get_data()
    lang = data.get('language', 'ru')

    # Тексты ошибок
    if lang == 'uz':
        err_num = "Iltimos, yilni raqamda kiriting."
        err_range = "Xatolik. Iltimos, haqiqiy tug‘ilgan yilingizni kiriting (masalan, 1998)."
        msg_gender = "Jinsingizni tanlang:"
    else:
        err_num = "Пожалуйста, введите год числом."
        err_range = "Похоже на ошибку. Введите реальный год (например 1998)."
        msg_gender = "Выберите ваш пол:"

    # Проверка ввода
    try:
        y = int(message.text.strip())
        if y < 1930 or y > 2018:
            return await message.answer(err_range)
        await state.update_data(birth_year=y)
    except ValueError:
        return await message.answer(err_num)

    # Если всё ок — переходим к Полу и даем КНОПКИ
    await state.set_state(Reg.gender)
    await message.answer(msg_gender, reply_markup=kb_gender(lang))


# 2. ОБРАБОТКА ВЫБОРА ПОЛА (КНОПКИ)
# Вместо @router.message используем @router.callback_query
@router.callback_query(F.data.startswith("gender_"), Reg.gender)
async def reg_gender_chosen(call: CallbackQuery, state: FSMContext):
    # gender_male -> male
    gender_code = call.data.split("_")[1]
    await state.update_data(gender=gender_code)

    # Получаем язык
    data = await state.get_data()
    lang = data.get('language', 'ru')

    # Удаляем сообщение с кнопками пола или меняем текст
    if lang == 'uz':
        text_accepted = "Qabul qilindi ✅"
        text_phone = "Endi telefon raqamingizni yuboring (tugmani bosing):"
    else:
        text_accepted = "Принято ✅"
        text_phone = "Теперь отправьте номер телефона (нажмите кнопку ниже):"

    await call.message.edit_text(text_accepted)

    # Переходим к телефону
    await state.set_state(Reg.phone)
    # Кнопка телефона (kb_phone) — это Reply кнопка (внизу), она не зависит от языка в текущей реализации,
    # но лучше бы ее тоже перевести (см. ниже совет)
    await call.message.answer(text_phone, reply_markup=kb_phone(lang))
    await call.answer()


# === 7. Телефон и Предварительное сохранение ===
@router.message(Reg.phone, F.contact)
async def reg_phone(message: Message, state: FSMContext):
    data = await state.get_data()
    lang = data.get('language', 'ru')

    phone_to_save = None

    # === 1. ПРОВЕРКА: Кнопка или Текст? ===
    if message.contact:
        # Если нажали кнопку
        phone_to_save = message.contact.phone_number
    elif message.text:
        # Если написали вручную: убираем пробелы, скобки, тире
        clean_text = re.sub(r'[ \-\(\)]', '', message.text)

        # Проверяем регуляркой (от 7 до 15 цифр, может быть плюс в начале)
        if re.match(r'^\+?\d{7,15}$', clean_text):
            phone_to_save = clean_text
        else:
            # Ошибка формата
            msg = "Noto‘g‘ri format (masalan: +998901234567)." if lang == 'uz' else "Неверный формат (пример: +998901234567)."
            await message.answer(msg)
            return
    else:
        # Если прислали картинку или стикер
        msg = "Iltimos, telefon raqamingizni yuboring." if lang == 'uz' else "Пожалуйста, отправьте номер телефона."
        await message.answer(msg)
        return

    # Сохраняем валидный номер
    await state.update_data(phone=phone_to_save)

    # === 2. ПОДГОТОВКА ДАННЫХ ДЛЯ ПРОВЕРКИ ===
    async with SessionLocal() as s:
        reg_obj = await s.get(Region, data['region_id'])
        sph_obj = await s.get(Sphere, data['sphere_id'])

        # Имя (которое ввели в начале)
        full_name = data.get("full_name", message.from_user.full_name)

        if lang == 'uz':
            # --- УЗБЕКСКИЙ ВАРИАНТ ---
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
            # --- РУССКИЙ ВАРИАНТ ---
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

    # === 3. ОТПРАВКА ===
    await state.set_state(Reg.confirm)
    # Передаем lang в клавиатуру, чтобы кнопки были на нужном языке
    await message.answer(text, reply_markup=kb_confirm(lang), parse_mode="HTML")


# === 8. Отмена / Заново ===
@router.callback_query(Reg.confirm, F.data == "confirm_no")
async def confirm_no(call: CallbackQuery, state: FSMContext):
    await state.clear()
    await call.message.edit_text("Регистрация отменена. Нажмите /start или выберите Регистрацию снова.")


# === 9. Финал: Сохранение в БД и Сертификат ===
from aiogram.types import FSInputFile
from app.bot.keyboards import kb_main  # <--- Убедитесь, что импортировали это


@router.callback_query(Reg.confirm, F.data == "confirm_yes")
async def reg_final(call: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    # Получаем язык пользователя (ru или uz)
    lang = data.get('language', 'ru')

    # Достаем введенное имя
    full_name_input = data.get("full_name", "Unknown")

    # 1. СОХРАНЕНИЕ ДАННЫХ В БД
    async with SessionLocal() as s:
        # Получаем пользователя
        q = await s.execute(select(User).where(User.tg_id == call.from_user.id))
        user = q.scalar_one()

        # === ОБНОВЛЯЕМ ИМЯ В БАЗЕ ДАННЫХ ===
        parts = full_name_input.split()
        if len(parts) >= 2:
            user.first_name = parts[0]
            user.last_name = " ".join(parts[1:])
        else:
            user.first_name = full_name_input
            user.last_name = ""

        # Обновляем телефон
        user.phone = data['phone']

        # Сохраняем профиль
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

    # 2. Удаляем старое сообщение с кнопками
    await call.message.delete()

    # Определяем текст ожидания на нужном языке
    wait_text = "⏳ Sertifikat tayyorlanmoqda..." if lang == 'uz' else "⏳ Генерируем сертификат..."

    # Отправляем сообщение "Генерируем..."
    wait_msg = await call.message.answer(wait_text)

    try:
        # Генерируем файл сертификата
        cert_path = await ensure_certificate_and_get_path(tg_id=call.from_user.id)

        # Удаляем сообщение "Генерируем..."
        await wait_msg.delete()

        # === 3. ОПРЕДЕЛЯЕМ ТЕКСТЫ ПОЗДРАВЛЕНИЯ ===
        if lang == 'uz':
            text_success = "Tabriklaymiz! Ro‘yxatdan o‘tish muvaffaqiyatli yakunlandi! 🎉\nSiz hamjamiyatga qabul qilindingiz."
            caption_cert = "Sizning a'zolik sertifikatingiz tayyor! 🪪"
        else:
            text_success = "Поздравляем! Регистрация успешно завершена! 🎉\nВы приняты в сообщество."
            caption_cert = "Ваш сертификат готов! 🪪"

        # Отправляем Поздравление и ГЛАВНОЕ МЕНЮ (на нужном языке)
        await call.message.answer(
            text_success,
            reply_markup=kb_main(is_registered=True, lang=lang)  # Передаем язык в меню
        )

        # 4. Отправляем сам сертификат с переведенной подписью
        document = FSInputFile(cert_path)
        await call.message.answer_document(
            document,
            caption=caption_cert
        )

    except Exception as e:
        err_msg = f"Xatolik: {e}" if lang == 'uz' else f"Ошибка при создании сертификата: {e}"
        await call.message.answer(err_msg)

    await state.clear()
    await call.answer()


# === 10. Кнопка просмотра сертификата ===
@router.callback_query(F.data == "view_certificate")
async def view_certificate_btn(call: CallbackQuery, state: FSMContext):
    cert_path = await ensure_certificate_and_get_path(tg_id=call.from_user.id)
    document = FSInputFile(cert_path)
    await call.message.answer_document(document, caption="Ваш сертификат членства 🪪")
    await call.answer()