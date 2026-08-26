import sqlite3
import os

# 创建数据库文件夹
if not os.path.exists('database'):
    os.makedirs('database')

# 连接数据库
conn = sqlite3.connect('database/anti_fake.db')
cursor = conn.cursor()

# 创建防伪记录表
cursor.execute('''
CREATE TABLE IF NOT EXISTS anti_fake_records (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    qr_id TEXT UNIQUE NOT NULL,
    serial_no TEXT NOT NULL,
    scan_count INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
''')

# 创建扫码日志表（之前漏掉了这个表！）
cursor.execute('''
CREATE TABLE IF NOT EXISTS scan_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    qr_id TEXT NOT NULL,
    ip_address TEXT NOT NULL,
    platform TEXT NOT NULL,
    verification_result TEXT NOT NULL DEFAULT 'unknown',
    scan_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (qr_id) REFERENCES anti_fake_records(qr_id)
)
''')

conn.commit()
conn.close()

print("数据库初始化完成！")
