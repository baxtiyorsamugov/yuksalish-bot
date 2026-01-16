import sys
import os
import shutil
import time
from wtforms.fields import FileField

# Добавляем путь к проекту
sys.path.append(os.getcwd())

import uvicorn
from fastapi import FastAPI
from sqladmin import Admin, ModelView, action
from sqladmin.authentication import AuthenticationBackend
from starlette.requests import Request
from starlette.responses import RedirectResponse
from markupsafe import Markup

from aiogram import Bot
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from sqlalchemy import select

# Импорты проекта
from app.config import BOT_TOKEN
from app.db.session import engine, SessionLocal
from app.db.models import User, Profile, Region, Sphere, Certificate, Event, EventRegistration

# Папка для файлов
UPLOAD_DIR = "assets/programs"
os.makedirs(UPLOAD_DIR, exist_ok=True)

# === СОЗДАЕМ ПРИЛОЖЕНИЕ ===
app = FastAPI()

# === БЕЗОПАСНОСТЬ ===
class AdminAuth(AuthenticationBackend):
    async def login(self, request: Request) -> bool:
        form = await request.form()
        username = form.get("username")
        password = form.get("password")
        if username == "admin" and password == "yuksalish2025":
            request.session.update({"token": "secret_token"})
            return True
        return False

    async def logout(self, request: Request) -> bool:
        request.session.clear()
        return True

    async def authenticate(self, request: Request) -> bool:
        token = request.session.get("token")
        return bool(token)


authentication_backend = AdminAuth(secret_key="super_secret_key")
admin = Admin(app=app, engine=engine, authentication_backend=authentication_backend)


# =====================================================
# === ВОТ ЭТИХ ФУНКЦИЙ НЕ ХВАТАЛО (ОНИ ЧИНЯТ 404) ===
# =====================================================

@app.get("/fast_approve/{profile_id}")
async def fast_approve(profile_id: int):
    async with SessionLocal() as session:
        profile = await session.get(Profile, profile_id)
        if profile and profile.status != 'active':
            profile.status = "active"
            session.add(profile)

            # Уведомляем пользователя
            user = await session.get(User, profile.user_id)
            if user and user.tg_id:
                bot = Bot(token=BOT_TOKEN)
                lang = user.language if user.language else 'ru'
                if lang == 'uz':
                    msg = "✅ <b>Tabriklaymiz! Profilingiz tasdiqlandi.</b>\nEndi «Sertifikat» tugmasini bosib, hujjatingizni olishingiz mumkin."
                else:
                    msg = "✅ <b>Поздравляем! Ваш профиль подтвержден.</b>\nТеперь вы можете получить свой сертификат, нажав кнопку в меню."

                try:
                    await bot.send_message(user.tg_id, msg, parse_mode="HTML")
                    await bot.session.close()
                except:
                    pass

            await session.commit()
    return RedirectResponse(url="/admin/profile/list")


@app.get("/fast_reject/{profile_id}")
async def fast_reject(profile_id: int):
    async with SessionLocal() as session:
        profile = await session.get(Profile, profile_id)
        if profile:
            profile.status = "rejected"
            session.add(profile)

            user = await session.get(User, profile.user_id)
            if user and user.tg_id:
                bot = Bot(token=BOT_TOKEN)
                lang = user.language if user.language else 'ru'
                msg = "❌ Arizangiz rad etildi." if lang == 'uz' else "❌ Ваша заявка отклонена."
                try:
                    await bot.send_message(user.tg_id, msg)
                    await bot.session.close()
                except:
                    pass

            await session.commit()
    return RedirectResponse(url="/admin/profile/list")


# =====================================================


# === МОДЕЛИ АДМИНКИ ===

class ProfileAdmin(ModelView, model=Profile):
    name = "Участник"
    name_plural = "Список участников"
    icon = "fa-solid fa-users"

    # Сортировка (сверху новые)
    column_default_sort = ("id", True)

    column_list = [
        "id",
        "status",  # Сюда применится форматтер
        "fio",
        "user.phone",
        "region.name_ru",
        "sphere.name_ru",
        "birth_year",
        "controls"
    ]

    column_searchable_list = [
        User.first_name,
        User.last_name,
        User.phone
    ]

    can_create = False
    can_edit = True
    can_delete = True

    # 1. Форматтер Статуса (Цветные плашки)
    def status_formatter(model, attribute):
        if model.status == 'pending':
            return Markup(
                '<span style="background: #fff3cd; color: #856404; padding: 5px 10px; border-radius: 5px; font-weight: bold;">⏳ На проверке</span>')
        elif model.status == 'active':
            return Markup(
                '<span style="background: #d4edda; color: #155724; padding: 5px 10px; border-radius: 5px; font-weight: bold;">✅ Одобрено</span>')
        elif model.status == 'rejected':
            return Markup(
                '<span style="background: #f8d7da; color: #721c24; padding: 5px 10px; border-radius: 5px; font-weight: bold;">❌ Отклонено</span>')
        return model.status

    # 2. Форматтер ФИО
    def fio_formatter(model, attribute):
        try:
            if not model.user: return "—"
            fname = model.user.first_name or ""
            lname = model.user.last_name or ""
            return f"👤 {fname} {lname}".strip()
        except:
            return "—"

    # 3. Форматтер Кнопок
    def controls_formatter(model, attribute):
        if model.status == 'pending':
            return Markup(
                f'<a href="/fast_approve/{model.id}" title="Одобрить">✅</a> '
                f'<a href="/fast_reject/{model.id}" title="Отклонить" style="margin-left: 10px;">❌</a>'
            )
        elif model.status == 'active':
            return Markup('<span style="color:green;">Доступ открыт</span>')
        else:
            return Markup('<span style="color:red;">Доступ закрыт</span>')

    # === ВАЖНО: ПОДКЛЮЧЕНИЕ ФОРМАТТЕРОВ ===
    column_formatters = {
        "status": status_formatter,  # <-- Вот этого, скорее всего, не хватало
        "fio": fio_formatter,
        "controls": controls_formatter
    }

    column_labels = {
        "status": "Статус",
        "fio": "Ф.И.О.",
        "controls": "Управление",
        "user.phone": "Телефон",
        "region.name_ru": "Регион",
        "sphere.name_ru": "Сфера",
        "birth_year": "Год"
    }


class EventAdmin(ModelView, model=Event):
    name = "Мероприятие"
    name_plural = "📅 Мероприятия"
    icon = "fa-solid fa-calendar"
    column_default_sort = ("id", True)
    column_list = ["id", "title", "date_event", "status"]
    column_searchable_list = ["title"]
    form_overrides = dict(program_file=FileField)
    form_args = dict(program_file=dict(label="Файл программы"))
    form_choices = {
        "status": [("active", "🟢 Активно"), ("closed", "🏁 Завершено (Опрос)"), ("cancelled", "❌ Отменено")]}
    form_columns = ["title", "description", "date_event", "location", "status", "program_file"]

    async def on_model_change(self, data, model, is_created, request):
        file_object = data.get("program_file")
        if file_object and hasattr(file_object, "filename") and file_object.filename:
            unique_name = f"{int(time.time())}_{file_object.filename}"
            save_path = os.path.join(UPLOAD_DIR, unique_name)
            with open(save_path, "wb") as buffer:
                shutil.copyfileobj(file_object.file, buffer)
            model.program_file = save_path

        new_status = data.get("status")
        if new_status == "closed":
            await self.send_feedback_request(model)

    async def send_feedback_request(self, event):
        bot = Bot(token=BOT_TOKEN)
        kb = InlineKeyboardMarkup(inline_keyboard=[[
            InlineKeyboardButton(text="1 😡", callback_data=f"rate_{event.id}_1"),
            InlineKeyboardButton(text="2 ☹️", callback_data=f"rate_{event.id}_2"),
            InlineKeyboardButton(text="3 😐", callback_data=f"rate_{event.id}_3"),
            InlineKeyboardButton(text="4 🙂", callback_data=f"rate_{event.id}_4"),
            InlineKeyboardButton(text="5 😍", callback_data=f"rate_{event.id}_5"),
        ]])
        async with SessionLocal() as session:
            stmt = select(EventRegistration).where(EventRegistration.event_id == event.id).where(
                EventRegistration.status == "approved")
            result = await session.execute(stmt)
            registrations = result.scalars().all()
            for reg in registrations:
                user = await session.get(User, reg.user_id)
                if user and user.tg_id:
                    lang = user.language if user.language else 'ru'
                    text = f"🏁 <b>«{event.title}»</b> tadbiri yakunlandi!" if lang == 'uz' else f"🏁 Мероприятие <b>«{event.title}»</b> завершено!"
                    try:
                        await bot.send_message(user.tg_id, text, reply_markup=kb, parse_mode="HTML")
                    except:
                        pass
        await bot.session.close()


class EventRegistrationAdmin(ModelView, model=EventRegistration):
    name = "Заявка"
    name_plural = "📝 Заявки и Оценки"
    icon = "fa-solid fa-clipboard-check"
    column_list = ["id", "user.first_name", "user.last_name", "event.title", "status", "rating", "created_at"]
    can_create = False
    can_edit = True
    can_delete = True

    @action(name="approve", label="✅ Одобрить", confirmation_message="Одобрить?", add_in_detail=True, add_in_list=True)
    async def approve_users(self, request: Request):
        pks = request.query_params.get("pks", "").split(",")
        if pks:
            async with SessionLocal() as session:
                for pk in pks:
                    model = await session.get(EventRegistration, int(pk))
                    if model:
                        model.status = "approved"
                        session.add(model)
                await session.commit()
        return RedirectResponse(request.url_for("admin:list", identity=self.identity))


class CertificateAdmin(ModelView, model=Certificate):
    name = "Сертификат"
    name_plural = "Сертификаты"
    icon = "fa-solid fa-certificate"
    column_list = ["member_code", "user.first_name", "user.last_name", "issued_at"]


class RegionAdmin(ModelView, model=Region):
    name = "Регион"
    name_plural = "Регионы"
    icon = "fa-solid fa-map"
    column_list = ["id", "name_ru", "name_uz"]


class SphereAdmin(ModelView, model=Sphere):
    name = "Сфера"
    name_plural = "Сферы"
    icon = "fa-solid fa-briefcase"
    column_list = ["id", "name_ru", "name_uz"]


# Подключение
admin.add_view(ProfileAdmin)
admin.add_view(EventAdmin)
admin.add_view(EventRegistrationAdmin)
admin.add_view(CertificateAdmin)
admin.add_view(RegionAdmin)
admin.add_view(SphereAdmin)

if __name__ == "__main__":
    print("🚀 Админ-панель запущена: http://127.0.0.1:8000/admin")
    uvicorn.run(app, host="0.0.0.0", port=8000)