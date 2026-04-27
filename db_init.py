import sqlite3
import os

if not os.path.exists('database'):
    os.makedirs('database')

conn = sqlite3.connect('database/anti_fake.db')
cursor = conn.cursor()

# 二维码主表
cursor.execute('''
    CREATE TABLE IF NOT EXISTS anti_fake_records (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        qr_id TEXT NOT NULL UNIQUE,
        serial_no TEXT NOT NULL UNIQUE,
        scan_count INTEGER DEFAULT 0,
        created_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
''')

# 扫码日志表
cursor.execute('''
    CREATE TABLE IF NOT EXISTS scan_logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        qr_id TEXT NOT NULL,
        ip_address TEXT NOT NULL,
        platform TEXT NOT NULL,
        scan_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (qr_id) REFERENCES anti_fake_records(qr_id)
    )
''')

conn.commit()
conn.close()
print("数据库初始化完成！")