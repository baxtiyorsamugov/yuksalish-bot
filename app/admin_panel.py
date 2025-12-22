import sys
import os

# Фикс для импортов
sys.path.append(os.getcwd())

import uvicorn
from fastapi import FastAPI
from sqladmin import Admin, ModelView, action
from sqladmin.authentication import AuthenticationBackend
from starlette.requests import Request
from starlette.responses import RedirectResponse
import shutil  # <--- Нужно для сохранения файла
import time    # <--- Нужно для генерации уникального имени
from wtforms.fields import FileField
# Импорт вашей БД и Моделей
from app.db.session import engine, SessionLocal
from app.db.models import User, Profile, Region, Sphere, Certificate, Event, EventRegistration


# === НАСТРОЙКА БЕЗОПАСНОСТИ ===
class AdminAuth(AuthenticationBackend):
    async def login(self, request: Request) -> bool:
        form = await request.form()
        username = form.get("username")
        password = form.get("password")

        # Логин и пароль
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


# === НАСТРОЙКА АДМИНКИ ===

# 1. Управление Членами (Профили)
class ProfileAdmin(ModelView, model=Profile):
    name = "Участник"
    name_plural = "Список участников"
    icon = "fa-solid fa-users"

    # Список колонок (строки работают отлично)
    column_list = [
        "id",
        "user.first_name",
        "user.last_name",
        "user.phone",
        "region.name_ru",
        "sphere.name_ru",
        "birth_year",
        "gender"
    ]

    column_searchable_list = [
        "user.first_name",
        "user.last_name",
        "user.phone",
        "user.tg_id"
    ]

    column_sortable_list = ["id", "birth_year"]

    # === ИСПРАВЛЕНИЕ ЗДЕСЬ ===
    # Используем Profile.region вместо Region.name_ru
    # SQLAdmin сам поймет, что это связь, и сделает выпадающий список
    # column_filters = [
    #     Profile.region_id,   # Было Profile.region -> Стало Profile.region_id
    #     Profile.sphere_id,   # Было Profile.sphere -> Стало Profile.sphere_id
    #     Profile.gender,
    #     Profile.birth_year
    # ]

    column_details_list = "__all__"
    can_create = False
    can_edit = True
    can_delete = True


# 2. Просмотр Сертификатов
class CertificateAdmin(ModelView, model=Certificate):
    name = "Сертификат"
    name_plural = "Сертификаты"
    icon = "fa-solid fa-certificate"

    column_list = [
        "member_code",
        "user.first_name",
        "user.last_name",
        "issued_at"
    ]

    # !!! В ФИЛЬТРАХ ОБЪЕКТЫ !!!
    # column_filters = [
    #     Certificate.issued_at,
    #     Certificate.member_code
    # ]

    column_searchable_list = ["member_code", "user.last_name"]


# 3. Справочники
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


# 1. Админка Мероприятий
# 1. Админка Мероприятий
class EventAdmin(ModelView, model=Event):
    name = "Мероприятие"
    name_plural = "📅 Мероприятия"
    icon = "fa-solid fa-calendar"

    # ИСПРАВЛЕНИЕ: Используем СТРОКИ ("id", "title"...), а не объекты (Event.id)
    column_list = ["id", "title", "date_event", "status"]

    column_searchable_list = ["title"]

    # === 1. МЕНЯЕМ ОБЫЧНОЕ ПОЛЕ НА ПОЛЕ ЗАГРУЗКИ ФАЙЛА ===
    form_overrides = dict(program_file=FileField)

    # Красивая подпись для поля
    form_args = dict(program_file=dict(label="Файл программы (PDF/Word/Картинка)"))

    # В фильтрах оставляем ОБЪЕКТЫ
  #  column_filters = [Event.status, Event.date_event]

    form_columns = ["title", "description", "date_event", "location", "status", "program_file"]

    # === 2. ЛОГИКА СОХРАНЕНИЯ ФАЙЛА ===
    async def on_model_change(self, data, model, is_created, request):
        # Получаем объект файла из формы
        file_object = data.get("program_file")

        # Проверяем, загрузил ли админ новый файл
        # (у file_object должен быть атрибут filename и он не должен быть пустым)
        if file_object and hasattr(file_object, "filename") and file_object.filename:
            # Генерируем уникальное имя (добавляем время), чтобы файлы не затерли друг друга
            # Пример: 17055555_program.pdf
            unique_name = f"{int(time.time())}_{file_object.filename}"
            save_path = os.path.join(UPLOAD_DIR, unique_name)

            # Сохраняем файл на диск
            with open(save_path, "wb") as buffer:
                shutil.copyfileobj(file_object.file, buffer)

            # ЗАПИСЫВАЕМ В БАЗУ ПУТЬ К ФАЙЛУ (строку)
            model.program_file = save_path

        # Если файл не загружен, но мы редактируем, старый путь останется в model.program_file сам по себе

# 2. Админка Регистраций (Модерация)
# 2. Админка Регистраций (Модерация)
class EventRegistrationAdmin(ModelView, model=EventRegistration):
    name = "Заявка"
    name_plural = "📝 Заявки на участие"
    icon = "fa-solid fa-clipboard-check"

    column_list = [
        "id",
        "user.first_name",
        "user.last_name",
        "user.phone",
        "event.title",
        "status",
        "created_at"
    ]

    # === ОТКЛЮЧАЕМ ФИЛЬТРЫ, ЧТОБЫ НЕ БЫЛО ОШИБОК ===
    # column_filters = [EventRegistration.status, EventRegistration.event_id]

    can_create = False
    can_edit = True
    can_delete = True

    # === ДЕЙСТВИЕ 1: ОДОБРИТЬ ===
    @action(
        name="approve",
        label="✅ Одобрить",
        confirmation_message="Вы уверены, что хотите одобрить выбранные заявки?",
        add_in_detail=True,
        add_in_list=True
    )
    async def approve_users(self, request: Request):
        # Получаем ID выбранных строк
        pks = request.query_params.get("pks", "").split(",")

        if pks:
            async with SessionLocal() as session:
                for pk in pks:
                    # Находим заявку и меняем статус
                    model = await session.get(EventRegistration, int(pk))
                    if model:
                        model.status = "approved"
                        session.add(model)
                await session.commit()

        # Обновляем страницу
        return RedirectResponse(request.url_for("admin:list", identity=self.identity))

    # === ДЕЙСТВИЕ 2: ОТКЛОНИТЬ ===
    @action(
        name="reject",
        label="❌ Отклонить",
        confirmation_message="Отклонить выбранные заявки?",
        add_in_detail=True,
        add_in_list=True
    )
    async def reject_users(self, request: Request):
        pks = request.query_params.get("pks", "").split(",")

        if pks:
            async with SessionLocal() as session:
                for pk in pks:
                    model = await session.get(EventRegistration, int(pk))
                    if model:
                        model.status = "rejected"
                        session.add(model)
                await session.commit()

        return RedirectResponse(request.url_for("admin:list", identity=self.identity))

# === ЗАПУСК ===
def run_admin():
    app = FastAPI()
    authentication_backend = AdminAuth(secret_key="super_secret_key")

    admin = Admin(app=app, engine=engine, authentication_backend=authentication_backend)

    admin.add_view(ProfileAdmin)
    admin.add_view(CertificateAdmin)
    admin.add_view(RegionAdmin)
    admin.add_view(SphereAdmin)
    admin.add_view(EventAdmin)
    admin.add_view(EventRegistrationAdmin)

    print("🚀 Админ-панель запущена: http://127.0.0.1:8000/admin")
    uvicorn.run(app, host="0.0.0.0", port=8000)


if __name__ == "__main__":
    run_admin()