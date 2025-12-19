from sqlalchemy import select
from app.db.session import SessionLocal
from app.db.models import Region, Sphere

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