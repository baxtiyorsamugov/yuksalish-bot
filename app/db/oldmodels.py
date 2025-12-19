from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy import String, BigInteger, Integer, ForeignKey, DateTime, func


class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    tg_id: Mapped[int] = mapped_column(BigInteger, unique=True, index=True)
    username: Mapped[str | None] = mapped_column(String(64))
    first_name: Mapped[str | None] = mapped_column(String(128))
    last_name: Mapped[str | None] = mapped_column(String(128))
    language: Mapped[str] = mapped_column(String(5), default="ru")
    phone: Mapped[str | None] = mapped_column(String(32))
    status: Mapped[str] = mapped_column(String(16), default="active")
    created_at = mapped_column(DateTime, server_default=func.now())

    # Связи (Relationships)
    # uselist=False означает, что у одного User только один Profile (1 к 1)
    profile: Mapped["Profile"] = relationship("Profile", back_populates="user", uselist=False)
    certificates: Mapped[list["Certificate"]] = relationship("Certificate", back_populates="user")


class Profile(Base):
    __tablename__ = "profiles"
    # Добавили ID, чтобы исправить ошибку в админке
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)

    # user_id теперь просто внешний ключ
    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.id"))

    region_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("regions.id"))
    sphere_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("spheres.id"))
    gender: Mapped[str | None] = mapped_column(String(16))
    birth_year: Mapped[int | None] = mapped_column(Integer)

    # Связи
    user: Mapped["User"] = relationship("User", back_populates="profile")
    region: Mapped["Region"] = relationship("Region", back_populates="profiles")
    sphere: Mapped["Sphere"] = relationship("Sphere", back_populates="profiles")


class Certificate(Base):
    __tablename__ = "certificates"
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.id"))
    member_code: Mapped[str] = mapped_column(String(32), unique=True)
    file_path: Mapped[str | None] = mapped_column(String(255))
    issued_at = mapped_column(DateTime, server_default=func.now())

    # Связь
    user: Mapped["User"] = relationship("User", back_populates="certificates")


class Region(Base):
    __tablename__ = "regions"
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    name_ru: Mapped[str] = mapped_column(String(128), nullable=False)
    name_uz: Mapped[str] = mapped_column(String(128), nullable=False)
    name_en: Mapped[str] = mapped_column(String(128), nullable=False)

    profiles: Mapped[list["Profile"]] = relationship("Profile", back_populates="region")


class Sphere(Base):
    __tablename__ = "spheres"
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    name_ru: Mapped[str] = mapped_column(String(128), nullable=False)
    name_uz: Mapped[str] = mapped_column(String(128), nullable=False)
    name_en: Mapped[str] = mapped_column(String(128), nullable=False)

    profiles: Mapped[list["Profile"]] = relationship("Profile", back_populates="sphere")