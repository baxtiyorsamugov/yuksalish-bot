import logging
import os
import textwrap
from datetime import datetime
from PIL import Image, ImageDraw, ImageFont
import qrcode
from sqlalchemy import select, desc

from app.db.session import SessionLocal
from app.db.models import User, Certificate

# === НАСТРОЙКИ ===
ASSETS = "assets"
OUTDIR = "generated"
os.makedirs(OUTDIR, exist_ok=True)

# Цвета (взяты пипеткой с оригинала)
COLOR_DARK_BLUE = "#0f2e5c"  # Глубокий синий
COLOR_LIGHT_BLUE = "#2c82c9"  # Голубой (если нужен)
COLOR_TEXT = "#1a3b6e"  # Основной текст
COLOR_GREY = "#666666"

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')


def get_font(name, size):
    """
    Загружает шрифт с подробным логированием ошибок.
    """
    path = os.path.join(ASSETS, name)

    if os.path.exists(path):
        try:
            return ImageFont.truetype(path, size)
        except Exception as e:
            logging.error(f"Файл найден, но шрифт битый или ошибка чтения: {path} | Ошибка: {e}")
            return ImageFont.load_default()
    else:
        # === ВОТ ТУТ МЫ УВИДИМ ОШИБКУ В КОНСОЛИ ===
        logging.warning(f"⚠️ ШРИФТ НЕ НАЙДЕН ПО ПУТИ: {path}")
        logging.warning(f"Проверьте, лежит ли файл {name} в папке {ASSETS}")

        # Попытка найти системный шрифт как запасной вариант
        try:
            return ImageFont.truetype("arial.ttf", size)
        except:
            return ImageFont.load_default()


def draw_centered_text(draw, text, font, y, color, image_width, line_spacing=15):
    """Рисует текст по центру с переносом строк"""
    # Для заголовков и имен перенос не нужен, но для длинного текста - да.
    # width=50 символов - подбираем под размер шрифта
    lines = textwrap.wrap(text, width=60)

    current_y = y
    for line in lines:
        bbox = draw.textbbox((0, 0), line, font=font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]

        x = (image_width - text_width) / 2
        draw.text((x, current_y), line, font=font, fill=color)
        current_y += text_height + line_spacing
    return current_y


def paste_image(bg, img_name, x, y, width_target=None):
    """Вспомогательная функция для вставки логотипов"""
    path = os.path.join(ASSETS, img_name)
    if not os.path.exists(path):
        logging.warning(f"Файл {img_name} не найден.")
        return

    img = Image.open(path).convert("RGBA")

    if width_target:
        # Ресайз с сохранением пропорций
        w_percent = (width_target / float(img.size[0]))
        h_size = int((float(img.size[1]) * float(w_percent)))
        img = img.resize((width_target, h_size), Image.Resampling.LANCZOS)

    # Вставка с учетом прозрачности
    bg.alpha_composite(img, dest=(int(x), int(y)))


def _render_certificate_png(path: str, full_name: str, member_code: str):
    logging.info(f"Рисуем сертификат: {full_name}")

    # 1. Загружаем фон
    try:
        # Ожидаем размер фона ~2000x1414 px
        bg = Image.open(os.path.join(ASSETS, "cert_bg.png")).convert("RGBA")
        W, H = bg.size
    except FileNotFoundError:
        logging.error("Нет фона cert_bg.png!")
        return

    draw = ImageDraw.Draw(bg)

    # 2. Шрифты (РАЗМЕРЫ ОЧЕНЬ ВАЖНЫ)
    # Serif (с засечками) для слова SERTIFIKAT
    # font_serif_title = get_font("font_serif.ttf", 140)
    # # Bold для имени
    # font_name = get_font("font_bold.ttf", 90)
    # # Regular для основного текста
    # font_body = get_font("font_reg.ttf", 36)
    # # Small для подписей
    # font_small = get_font("font_reg.ttf", 24)
    # font_director = get_font("font_bold.ttf", 32)
    font_serif_title = get_font("Montserrat-ExtraBold.ttf", 140)
    font_name = get_font("Montserrat-Bold.ttf", 90)
    font_body = get_font("Montserrat-Medium.ttf", 36)
    font_small = get_font("Montserrat-Regular.ttf", 24)
    font_director = get_font("Montserrat-Bold.ttf", 32)

    # === БЛОК 1: ЛОГОТИПЫ (ВЕРХ) ===
    # Координаты подобраны под ширину 2000px
    # Лого ЕС (слева)
    # paste_image(bg, "logo_eu.png", x=150, y=100, width_target=250)

    # Лого KAS (центр-лево)
    # paste_image(bg, "logo_kas.png", x=450, y=100, width_target=250)

    # Лого Yuksalish (справа) - если его нет на фоне
    # paste_image(bg, "logo_yuksalish.png", x=1400, y=100, width_target=350)

    # Лого 100 Community (по центру чуть ниже)
    # paste_image(bg, "logo_100.png", x=850, y=200, width_target=200)

    # === БЛОК 4: ИМЯ УЧАСТНИКА ===
    # Рисуем на высоте Y = 850
    draw_centered_text(draw, full_name, font_name, 550, COLOR_DARK_BLUE, W)

    # === БЛОК 2: ТЕКСТ ПОЗДРАВЛЕНИЯ ===
    # intro_text = (
    #     "Tabriklaymiz, siz Yuksalish harakatiga a'zo bo'ldingiz. Birgalikda mamlakatimiz rivoji uchun hissa qo'shamiz."
    # )
    # # Рисуем на высоте Y = 500
    # draw_centered_text(draw, intro_text, font_body, 500, COLOR_TEXT, W, line_spacing=20)

    # === БЛОК 3: ЗАГОЛОВОК SERTIFIKAT ===
    # Буквы в разрядку (с пробелами) для стиля
    # title = "S E R T I F I K A T"
    # draw_centered_text(draw, title, font_serif_title, 650, COLOR_DARK_BLUE, W)



    # === БЛОК 5: ПОДПИСЬ ДИРЕКТОРА ===
    # Сама подпись (картинка)
    sign_y_pos = 1000
    # Вставляем подпись по центру. Считаем, что ширина подписи ~300px
    # paste_image(bg, "signature.png", x=(W - 300) // 2, y=sign_y_pos, width_target=300)

    # Текст под подписью
    # text_y_pos = sign_y_pos + 160
    # draw_centered_text(draw, "Askar Mamatxanov", font_director, text_y_pos, COLOR_DARK_BLUE, W)
    # draw_centered_text(draw, "\"Yuksalish\" harakati\nijrochi direktori", font_small, text_y_pos + 40, COLOR_LIGHT_BLUE,
    #                    W)

    # === БЛОК 6: QR КОД (СПРАВА ВНИЗУ) ===
    # qr_size = 220
    # qr = qrcode.make(member_code).convert("RGBA").resize((qr_size, qr_size))

    # Позиция: отступ 100px справа и снизу
    # qr_x = W - qr_size - 100
    # qr_y = H - qr_size - 120

    # Белая подложка под QR (чтобы не сливался с фоном)
    # qr_bg = Image.new("RGBA", (qr_size + 20, qr_size + 20), "white")
    # bg.alpha_composite(qr_bg, dest=(qr_x - 10, qr_y - 10))
    # bg.alpha_composite(qr, dest=(qr_x, qr_y))

    # Надпись "Modular" под QR
    # draw.text((qr_x + 60, qr_y + qr_size + 10), "Modullar", font=font_small, fill="black")

    # === БЛОК 7: ID и ДАТА (СЛЕВА ВНИЗУ) ===
    # Позиция: слева внизу, на уровне QR
    # 1. Координата X = Ровно центр картинки
    center_x = W / 2

    # 2. Координата Y = Отступ снизу
    # H - 220 поднимет текст над нижним узором (ракетой/орнаментом)
    start_y = H - 220

    # Рисуем ID
    draw.text(
        (center_x, start_y),
        f"ID raqami: {member_code}",
        font=font_small,
        fill=COLOR_GREY,
        anchor="mm",  # <--- mm = Middle Middle (Центр текста совпадает с точкой)
        align="center"
    )

    # Рисуем Дату (ниже ID на 40 пикселей)
    draw.text(
        (center_x, start_y + 40),
        f"Sana: {datetime.now().strftime('%d.%m.%Y')}",
        font=font_small,
        fill=COLOR_GREY,
        anchor="mm",  # <--- Центрирование
        align="center"
    )

    # Сохранение
    bg.convert("RGB").save(path, "PNG")
    logging.info(f"Сохранено: {path}")


# === АСИНХРОННАЯ ОБЕРТКА (та же самая) ===
def _next_member_code(n: int) -> str:
    year = datetime.now().year
    return f"YK-{year}-{n:06d}"


async def ensure_certificate_and_get_path(tg_id: int) -> str:
    async with SessionLocal() as s:
        # 1. Получаем пользователя
        result = await s.execute(select(User).where(User.tg_id == tg_id))
        user = result.scalar_one_or_none()

        if not user:
            raise ValueError(f"User with tg_id {tg_id} not found")

        # 2. Проверяем, есть ли уже сертификат
        q2 = await s.execute(select(Certificate).where(Certificate.user_id == user.id))
        cert = q2.scalar_one_or_none()

        # Если сертификат есть в БД и файл существует физически — отдаем его
        if cert and cert.file_path and os.path.exists(cert.file_path):
            return cert.file_path

        # === 3. НАДЕЖНАЯ ГЕНЕРАЦИЯ НОВОГО НОМЕРА ===
        year = datetime.now().year
        pattern = f"YK-{year}-%"

        # Получаем ВСЕ коды за текущий год
        q3 = await s.execute(select(Certificate.member_code).where(Certificate.member_code.like(pattern)))
        existing_codes = q3.scalars().all()

        max_number = 0

        # Проходимся по всем кодам и ищем самый большой номер
        for code in existing_codes:
            # code имеет формат "YK-2025-000005"
            try:
                # Берем часть после последнего тире и превращаем в число
                number_part = int(code.split('-')[-1])
                if number_part > max_number:
                    max_number = number_part
            except (ValueError, IndexError):
                continue

        # Новый номер всегда на 1 больше самого большого существующего
        new_number = max_number + 1
        member_code = _next_member_code(new_number)
        # ============================================

        path = os.path.join(OUTDIR, f"cert_{member_code}.png")

        # Формируем имя для сертификата
        full_name = f"{user.first_name or ''} {user.last_name or ''}".strip()
        if not full_name:
            full_name = "Hurmatli Foydalanuvchi"

        # Генерируем картинку (ваша функция отрисовки)
        _render_certificate_png(path, full_name, member_code)

        # 4. Сохраняем в БД
        if not cert:
            cert = Certificate(user_id=user.id, member_code=member_code, file_path=path)
            s.add(cert)
        else:
            # Если запись была, но без файла — обновляем
            cert.member_code = member_code
            cert.file_path = path

        await s.commit()
        return path