import sqlite3
import uuid
import os
import qrcode

# 配置（已更新为正式域名）
DOMAIN = "https://pharmanewzealand.com"
QR_SAVE_PATH = "static/qr_codes"

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


def create_qr_code(data, filename):
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(data)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    img.save(os.path.join(QR_SAVE_PATH, filename))


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
            url = f"{DOMAIN}/verify?qr_id={qr_id}"
            filename = f"QR_{serial_no}.png"
            create_qr_code(url, filename)
            print(f"[成功] 编号: {serial_no} | 链接: {url}")
        else:
            print(f"[失败] 编号重复，跳过: {serial_no}")


if __name__ == "__main__":
    main(3)