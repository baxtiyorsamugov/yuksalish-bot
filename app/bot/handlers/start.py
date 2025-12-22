from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from sqlalchemy import select

from app.bot.states import Reg
from app.bot.keyboards import kb_language, kb_main
from app.db.session import SessionLocal
from app.db.models import User
from app.db.repo import is_user_registered

router = Router()


@router.message(F.text == "/start")
async def start(message: Message, state: FSMContext):
    await state.clear()
    await state.set_state(Reg.language)
    await message.answer("Выберите язык / Tilni tanlang / Choose language:", reply_markup=kb_language())


@router.callback_query(F.data.startswith("lang:"))
async def set_lang(call: CallbackQuery, state: FSMContext):
    lang = call.data.split(":")[1]
    tg = call.from_user

    # 1. Сохраняем пользователя (если его нет) и язык
    async with SessionLocal() as s:
        q = await s.execute(select(User).where(User.tg_id == tg.id))
        user = q.scalar_one_or_none()
        if not user:
            user = User(
                tg_id=tg.id,
                username=tg.username,
                first_name=tg.first_name,
                last_name=tg.last_name,
                language=lang
            )
            s.add(user)
        else:
            user.language = lang
        await s.commit()

    # 2. Проверяем, есть ли профиль
    is_reg = await is_user_registered(tg.id)

    # 3. Формируем текст
    if is_reg:
        if lang == 'uz':
            text = "Xush kelibsiz! Bosh menyu 👇"
        elif lang == 'en':
            text = "Welcome! Main menu 👇"
        else:
            text = "Добро пожаловать! Главное меню 👇"
    else:
        if lang == 'uz':
            text = "Yaxshi. Ro‘yxatdan o‘tishni boshlaymiz 👇\nBosing: Ro‘yxatdan o‘tish"
        elif lang == 'en':
            text = "Ok. Let's start registration 👇\nPress: Registration"
        else:
            text = "Ок. Начнём регистрацию 👇\nНажмите: Регистрация"

    # 4. ОТПРАВЛЯЕМ КЛАВИАТУРУ (ВОТ ТУТ БЫЛА ОШИБКА)
    # Нужно обязательно написать имена параметров: is_registered=...
    await call.message.answer(
        text,
        reply_markup=kb_main(is_registered=is_reg, lang=lang)
    )

    await call.answer()