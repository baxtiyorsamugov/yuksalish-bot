from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext

from app.bot.states import Reg
from app.bot.keyboards import kb_language, kb_main
from app.db.session import SessionLocal
from sqlalchemy import select
from app.db.models import User

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

    async with SessionLocal() as s:
        q = await s.execute(select(User).where(User.tg_id == tg.id))
        user = q.scalar_one_or_none()
        if not user:
            user = User(tg_id=tg.id, username=tg.username, first_name=tg.first_name, last_name=tg.last_name, language=lang)
            s.add(user)
        else:
            user.language = lang
        await s.commit()

    await call.message.answer("Ок. Начнём регистрацию 👇\nНажмите: Регистрация", reply_markup=kb_main(lang))
    await call.answer()
