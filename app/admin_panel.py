import sys
import os

# Фикс для импортов
sys.path.append(os.getcwd())

import uvicorn
from fastapi import FastAPI
from sqladmin import Admin, ModelView
from sqladmin.authentication import AuthenticationBackend
from starlette.requests import Request
from starlette.responses import RedirectResponse

# Импорт вашей БД и Моделей
from app.db.session import engine
from app.db.models import User, Profile, Region, Sphere, Certificate


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
    column_filters = [
        Profile.region_id,   # Было Profile.region -> Стало Profile.region_id
        Profile.sphere_id,   # Было Profile.sphere -> Стало Profile.sphere_id
        Profile.gender,
        Profile.birth_year
    ]

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
    column_filters = [
        Certificate.issued_at,
        Certificate.member_code
    ]

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


# === ЗАПУСК ===
def run_admin():
    app = FastAPI()
    authentication_backend = AdminAuth(secret_key="super_secret_key")

    admin = Admin(app=app, engine=engine, authentication_backend=authentication_backend)

    admin.add_view(ProfileAdmin)
    admin.add_view(CertificateAdmin)
    admin.add_view(RegionAdmin)
    admin.add_view(SphereAdmin)

    print("🚀 Админ-панель запущена: http://127.0.0.1:8000/admin")
    uvicorn.run(app, host="0.0.0.0", port=8000)


if __name__ == "__main__":
    run_admin()