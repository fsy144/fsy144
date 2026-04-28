import sqlite3
import uuid
import os
import qrcode
from PIL import Image, ImageDraw, ImageFont

# 配置（修改为官网首页）
DOMAIN = "https://pharmanewzealand.com.cn"  # 改为.cn的官网
QR_SAVE_PATH = "static/qr_codes"
LOGO_PATH = "static/images/logo.jpg"

# 图片尺寸配置
CANVAS_WIDTH = 800
CANVAS_HEIGHT = 1200
QR_SIZE = 600
LOGO_WIDTH = 600
TOP_MARGIN = 15
SERIAL_SPACING = 15

if not os.path.exists(QR_SAVE_PATH):
    os.makedirs(QR_SAVE_PATH)


def get_next_serial_no():
    conn = sqlite3.connect('database/anti_fake.db')
    cursor = conn.cursor()
    cursor.execute("SELECT serial_no FROM anti_fake_records ORDER BY serial_no DESC LIMIT 1")
    result = cursor.fetchone()
    conn.close()

    if result:
        last_no = int(result[0])
        next_no = last_no + 1
    else:
        next_no = 1
    return f"{next_no:010d}"


def create_branded_qr_code(url, serial_no, filename):
    canvas = Image.new('RGB', (CANVAS_WIDTH, CANVAS_HEIGHT), color='black')
    draw = ImageDraw.Draw(canvas)

    logo = Image.open(LOGO_PATH).convert('RGB')
    logo_ratio = logo.height / logo.width
    logo_height = int(LOGO_WIDTH * logo_ratio)
    logo = logo.resize((LOGO_WIDTH, logo_height), Image.Resampling.LANCZOS)

    logo_x = (CANVAS_WIDTH - LOGO_WIDTH) // 2
    logo_y = TOP_MARGIN
    canvas.paste(logo, (logo_x, logo_y))

    try:
        font_serial = ImageFont.truetype("arial.ttf", 60)
    except IOError:
        try:
            font_serial = ImageFont.truetype("/Library/Fonts/Arial.ttf", 60)
        except IOError:
            font_serial = ImageFont.load_default(size=60)

    serial_text = serial_no
    serial_width = draw.textlength(serial_text, font=font_serial)
    serial_x = (CANVAS_WIDTH - serial_width) // 2
    serial_y = logo_y + logo_height + SERIAL_SPACING
    draw.text((serial_x, serial_y), serial_text, fill="white", font=font_serial)

    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(url)
    qr.make(fit=True)
    qr_img = qr.make_image(fill_color="black", back_color="white")
    qr_img = qr_img.resize((QR_SIZE, QR_SIZE))

    qr_x = (CANVAS_WIDTH - QR_SIZE) // 2
    qr_y = serial_y + 60 + 80
    canvas.paste(qr_img, (qr_x, qr_y))

    canvas.save(os.path.join(QR_SAVE_PATH, filename))


def insert_into_db(qr_id, serial_no):
    conn = sqlite3.connect('database/anti_fake.db')
    cursor = conn.cursor()
    try:
        cursor.execute("INSERT INTO anti_fake_records (qr_id, serial_no) VALUES (?, ?)", (qr_id, serial_no))
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False
    finally:
        conn.close()


def main(num_to_generate=5):
    print(f"开始生成 {num_to_generate} 个防伪码...")
    for i in range(num_to_generate):
        qr_id = str(uuid.uuid4())
        serial_no = get_next_serial_no()

        if insert_into_db(qr_id, serial_no):
            # 【核心修改】链接格式变为：官网首页#qr_id=xxx
            url = f"{DOMAIN}#qr_id={qr_id}"
            filename = f"QR_{serial_no}.png"
            create_branded_qr_code(url, serial_no, filename)
            print(f"[成功] 编号: {serial_no} | 链接: {url}")
        else:
            print(f"[失败] 编号重复，跳过: {serial_no}")


if __name__ == "__main__":
    main(3)