from sqlalchemy import select
from app.db.session import SessionLocal
from app.db.models import Region, Sphere, User, Profile

async def get_all_regions():
    """Получает все регионы из таблицы regions"""
    async with SessionLocal() as session:
        result = await session.execute(select(Region))
        return result.scalars().all()

async def get_all_spheres():
    """Получает все сферы из таблицы spheres"""
    async with SessionLocal() as session:
        result = await session.execute(select(Sphere))
        return result.scalars().all()


async def is_user_registered(tg_id: int) -> bool:
    """Проверяет, есть ли у пользователя заполненный профиль"""
    async with SessionLocal() as session:
        # 1. Ищем юзера по ID телеграма
        q_user = await session.execute(select(User).where(User.tg_id == tg_id))
        user = q_user.scalar_one_or_none()

        if not user:
            return False

        # 2. Ищем профиль этого юзера
        q_prof = await session.execute(select(Profile).where(Profile.user_id == user.id))
        profile = q_prof.scalar_one_or_none()

        # Если профиль найден — возвращаем True, иначе False
        return profile is not None