from aiogram import Router, F, types
from sqlalchemy import select

from app.bot.keyboards import kb_about_menu, kb_back_to_about
from app.db.session import SessionLocal
from app.db.models import User

router = Router()

# === СЛОВАРЬ ТЕКСТОВ (RU / UZ) ===
CONTENT = {
    "ru": {
        "main": (
            "<b>О движении «Юксалиш»</b> 🇺🇿\n\n"
            "Движение «Юксалиш» создано для объединения граждан, "
            "бизнеса и государства ради устойчивого развития Узбекистана.\n\n"
            "Мы строим мост между народом и властью, продвигаем реформы и "
            "развиваем гражданское общество.\n\n"
            "👇 <i>Выберите раздел ниже, чтобы узнать больше:</i>"
        ),
        "directions": (
            "<b>🎯 Наши основные направления:</b>\n\n"
            "1️⃣ <b>Мониторинг реформ</b> — следим за исполнением государственных программ.\n"
            "2️⃣ <b>Диалог</b> — организуем площадки для обсуждения проблем общества.\n"
            "3️⃣ <b>Поддержка инициатив</b> — помогаем активным гражданам реализовать идеи.\n"
            "4️⃣ <b>Международное сотрудничество</b> — привлекаем опыт зарубежных партнеров. \n"
            "4️⃣ <b>Исследования</b> — изучаем общественное мнение, проводим исследования и опросы, формируем аналитические выводы и практические предложения по социальным проблемам. "
        ),
        "activity": (
            "<b>💼 Наша деятельность:</b>\n\n"
            "Мониторинг, общественная экспертиза проектов нормативно-правовых актов, исследования \n"
            "Мы проводим форумы, общественные слушания, благотворительные акции и "
            "образовательные тренинги.\n\n"
            ""
        ),
        "projects": (
            "<b>🚀 Текущие проекты:</b>\n\n"
            "🔹 <b>«100 Community»</b> — развитие лидерства.\n"
            "🔹 <b>«Гражданский мониторинг»</b> — контроль инфраструктуры.\n"
            "🔹 <b>«Bir million daraxt»</b> —  расширение зелёных территорий.\n"
            "🔹 <b>«Start Up» инициативы</b> — поддержка молодежного бизнеса.\n"
            "🔹 <b>«Hayot ulash»</b> —  решение проблемы питьевой воды в отдалённых районах, бурение колодцев и повышение качества жизни населения.\n"
            "🔹 <b>«Biz donormiz»</b> — формирование культуры донорства крови.\n"
            "🔹 <b>«Ziyoli kelajak»</b> — улучшение школьной инфраструктуры, укрепление материальной базы и развитие образовательной среды.\n\n"
            "<i>Следите за анонсами в разделе Мероприятия!</i>"
        )
    },
    "uz": {
        "main": (
            "<b>«Yuksalish» harakati haqida</b> 🇺🇿\n\n"
            "«Yuksalish» harakati O‘zbekistonning barqaror rivojlanishi yo‘lida "
            "fuqarolar, biznes va davlatni birlashtirish maqsadida tashkil etilgan.\n\n"
            "Biz xalq va davlat o‘rtasida ko‘prik bo‘lib, islohotlarni ilgari suramiz va "
            "fuqarolik jamiyatini rivojlantiramiz.\n\n"
            "👇 <i>Batafsil ma’lumot olish uchun quyidagi bo‘limlardan birini tanlang:</i>"
        ),
        "directions": (
            "<b>🎯 Bizning asosiy yo‘nalishlarimiz:</b>\n\n"
            "1️⃣ <b>Islohotlar monitoringi</b> — davlat dasturlarining ijrosini kuzatib boramiz.\n"
            "2️⃣ <b>Muloqot</b> — jamiyat muammolarini muhokama qilish uchun maydonlar tashkil etamiz.\n"
            "3️⃣ <b>Tashabbuslarni qo‘llab-quvvatlash</b> — faol fuqarolarga g‘oyalarini amalga oshirishda yordam beramiz.\n"
            "4️⃣ <b>Xalqaro hamkorlik</b> — xorijiy hamkorlarning tajribasini jalb qilamiz. \n"
            "4️⃣ <b>Tadqiqot</b> — jamoatchilik fikrini o‘rganib, tadqiqotlar va so‘rovlar o‘tkazamiz, ijtimoiy muammolar bo‘yicha tahliliy xulosalar va amaliy takliflar shakllantiramiz. "
        ),
        "activity": (
            "<b>💼 Bizning faoliyatimiz:</b>\n\n"
            " Monitoring, normativ-huquqiy hujjatlar loyihalarining jamoatchilik ekspertizasi, tadqiqotlar\n"
            "Biz forumlar, jamoatchilik eshituvlari, xayriya aksiyalari va "
            "o‘quv treninglarini o‘tkazamiz.\n\n"
            "Har yili bizning a‘zolarimiz respublika bo‘ylab yuzlab tadbirlarda ishtirok etadilar."
        ),
        "projects": (
            "<b>🚀 Joriy loyihalar:</b>\n\n"
            "🔹 <b>“100 Community”</b> — liderlikni rivojlantirish.\n"
            "🔹 <b>“Jamoatchilik monitoringi”</b> — infratuzilma nazorati.\n"
            "🔹 <b>“Bir million daraxt”</b> — yashil hududlarni kengaytirish. \n"
            "🔹 <b>“Hayot ulash”</b> — chekka hududlarda ichimlik suvi muammosini hal etish, quduqlar qazish va aholining hayot sifatini yaxshilash.\n"
            "🔹 <b>“Biz donormiz”</b> — qon donorligi madaniyatini shakllantirish. \n"
            "🔹 <b>“Ziyoli kelajak”</b> — maktab infratuzilmasini yaxshilash, moddiy bazasini mustahkamlash va ta’lim muhitini rivojlantirish \n\n"
            "<i>E’lonlarni «Tadbirlar» bo‘limida kuzatib boring!</i>"
        )
    }
}

VIDEO_ID = "BAACAgIAAxkBAAIDWWlI7DA4gRrFX2rus7RAu2Bu8JVZAALsiAACiMdJSnoQ4wMOhZnENgQ"


# Вспомогательная функция для получения языка
async def get_user_lang(user_id: int):
    async with SessionLocal() as s:
        user = await s.scalar(select(User).where(User.tg_id == user_id))
        return user.language if user and user.language else 'ru'


# === ХЕНДЛЕРЫ ===

# 1. Главная кнопка меню
@router.message(F.text.in_(["О движении", "Harakat haqida"]))
async def show_about_section(message: types.Message):
    lang = await get_user_lang(message.from_user.id)

    await message.answer_video(
        video=VIDEO_ID,
        caption=CONTENT[lang]["main"],
        reply_markup=kb_about_menu(lang),  # Передаем язык в клавиатуру
        parse_mode="HTML"
    )


# 2. Обработка кнопок (Направления)
@router.callback_query(F.data == "about_directions")
async def show_directions(call: types.CallbackQuery):
    lang = await get_user_lang(call.from_user.id)
    text = CONTENT[lang]["directions"]

    if call.message.caption:
        await call.message.edit_caption(caption=text, reply_markup=kb_back_to_about(lang), parse_mode="HTML")
    else:
        await call.message.edit_text(text=text, reply_markup=kb_back_to_about(lang), parse_mode="HTML")
    await call.answer()


# 3. Обработка кнопок (Деятельность)
@router.callback_query(F.data == "about_activity")
async def show_activity(call: types.CallbackQuery):
    lang = await get_user_lang(call.from_user.id)
    text = CONTENT[lang]["activity"]

    if call.message.caption:
        await call.message.edit_caption(caption=text, reply_markup=kb_back_to_about(lang), parse_mode="HTML")
    else:
        await call.message.edit_text(text=text, reply_markup=kb_back_to_about(lang), parse_mode="HTML")
    await call.answer()


# 4. Обработка кнопок (Проекты)
@router.callback_query(F.data == "about_projects")
async def show_projects(call: types.CallbackQuery):
    lang = await get_user_lang(call.from_user.id)
    text = CONTENT[lang]["projects"]

    if call.message.caption:
        await call.message.edit_caption(caption=text, reply_markup=kb_back_to_about(lang), parse_mode="HTML")
    else:
        await call.message.edit_text(text=text, reply_markup=kb_back_to_about(lang), parse_mode="HTML")
    await call.answer()


# 5. Кнопка "Назад"
@router.callback_query(F.data == "about_main")
async def back_to_main_about(call: types.CallbackQuery):
    lang = await get_user_lang(call.from_user.id)
    text = CONTENT[lang]["main"]

    if call.message.caption:
        await call.message.edit_caption(caption=text, reply_markup=kb_about_menu(lang), parse_mode="HTML")
    else:
        await call.message.edit_text(text=text, reply_markup=kb_about_menu(lang), parse_mode="HTML")
    await call.answer()