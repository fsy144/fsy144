from flask import Flask, request, render_template, redirect, url_for
import sqlite3
import os
import requests
from ip2region.searcher import new_with_buffer
from ip2region.util import IPv4, load_content_from_file

app = Flask(__name__)
app.secret_key = 'PNZ@AntiFake#2026$Secure!Key'

# --- 配置项 ---
DOMESTIC_SITE = "https://pharmanewzealand.com.cn"
OVERSEAS_SITE = "https://pharmanewzealand.co.nz"
VERIFY_DOMAIN = "https://pharmanewzealand.com"  # 防伪核验专用域名

# --- IP离线库初始化 ---
XDB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'ip2region.xdb')
_ip_searcher = None


def init_ip_searcher():
    """初始化IP离线查询器（应用启动时调用一次）"""
    global _ip_searcher
    if os.path.exists(XDB_PATH):
        try:
            c_buffer = load_content_from_file(XDB_PATH)
            _ip_searcher = new_with_buffer(IPv4, c_buffer)
            print("IP离线库加载成功")
        except Exception as e:
            print(f"IP离线库加载失败: {e}")
            _ip_searcher = None
    else:
        print(f"警告：未找到IP数据库文件 {XDB_PATH}，IP定位功能不可用")
        _ip_searcher = None


# --- 数据库辅助函数 ---
def get_db_connection():
    conn = sqlite3.connect('database/anti_fake.db')
    conn.row_factory = sqlite3.Row
    return conn


def check_qr_status(qr_id):
    """
    检查二维码状态（通用）
    返回: (status_code, data)
    status_code: 'invalid'(不存在), 'warning'(>=2次), 'success'(0或1次)
    """
    conn = get_db_connection()
    record = conn.execute('SELECT * FROM anti_fake_records WHERE qr_id = ?', (qr_id,)).fetchone()

    if record is None:
        conn.close()
        return ('invalid', None)

    current_count = record['scan_count']
    serial_no = record['serial_no']
    conn.close()

    if current_count >= 3:
        return ('warning', {'serial_no': serial_no, 'count': current_count})
    else:
        return ('success', {'serial_no': serial_no, 'count': current_count})


def increment_scan_count(qr_id):
    """增加扫描次数（通用）"""
    conn = get_db_connection()
    conn.execute('UPDATE anti_fake_records SET scan_count = scan_count + 1 WHERE qr_id = ?', (qr_id,))
    conn.commit()
    conn.close()


def log_scan(qr_id, ip_address, platform="境外用户_无平台"):
    """
    记录扫码日志（兼容国内外）
    platform默认值设为"境外用户_无平台"
    """
    conn = get_db_connection()
    conn.execute(
        'INSERT INTO scan_logs (qr_id, ip_address, platform) VALUES (?, ?, ?)',
        (qr_id, ip_address, platform)
    )
    conn.commit()
    conn.close()


# --- IP地理位置判断函数 ---
def is_china_ip(ip):
    """
    判断IP是否在中国境内
    使用 ip2region 离线库（本地查询，无需联网，速度极快）
    返回格式：大洲|国家|省份|城市|区县|运营商|AS号
    例如：亚洲|中国|江苏省|南京市|||
    返回: True(国内) / False(境外) / None(查询失败)
    """
    if _ip_searcher is None:
        return None
    try:
        region = _ip_searcher.search(ip)
        if region:
            parts = region.split('|')
            # 国家在第1段（索引1），不是第0段
            country = parts[1] if len(parts) > 1 else ''
            # 内网IP视为国内（部署在国内服务器上）
            if country == '中国' or parts[0] == '内网IP':
                return True
            else:
                return False
        else:
            return None
    except Exception as e:
        print(f"IP查询出错: {e}")
        return None


# --- 获取用户真实IP ---
def get_user_ip():
    return request.remote_addr


# --- 路由 ---

@app.route('/')
def index():
    return "PharmaNewZealand防伪系统运行中。请通过带参数的链接访问。"


# 【核心入口：二维码扫码链接】
@app.route('/verify')
def verify_start():
    qr_id = request.args.get('qr_id')
    user_ip = get_user_ip()

    if not qr_id:
        return render_template('failed.html', msg="缺少防伪编号，无法核验。", language='zh')

    is_china = is_china_ip(user_ip)

    # --- 新增：处理IP查询失败的情况 ---
    if is_china is None:
        # 当无法判断IP归属地时，打印日志以便排查，并默认跳转到选平台页面
        # 这是一种更安全的策略，避免因误判而阻止国内用户
        print(f"警告：无法判断IP {user_ip} 的归属地，默认进入国内选平台流程。")
        return render_template('select_platform.html', qr_id=qr_id, language='zh')

    # --- 国内：跳转到国内官网，走选平台流程 ---
    if is_china:
        return render_template('select_platform.html', qr_id=qr_id, language='zh')

    # --- 境外：直接核验，不选平台，显示结果 ---
    else:
        status, data = check_qr_status(qr_id)
        log_scan(qr_id, user_ip, platform="境外用户")
        language = 'en'  # 境外用户默认英文

        if status == 'invalid':
            return render_template('failed.html', msg="该产品编码不存在，谨防假冒！", is_overseas=True, language=language)
        elif status == 'warning':
            return render_template('warning.html', serial_no=data['serial_no'], scan_count=data['count'],
                                   is_overseas=True, language=language)
        else:
            increment_scan_count(qr_id)
            return render_template('success.html', serial_no=data['serial_no'], scan_count=data['count'] + 1,
                                   is_overseas=True, language=language)


# 【仅国内使用：选平台后提交】
@app.route('/result', methods=['POST'])
def show_result():
    qr_id = request.form.get('qr_id')
    platform = request.form.get('platform')
    user_ip = get_user_ip()

    # 自动判定语言
    is_china = is_china_ip(user_ip)
    language = 'zh' if (is_china is None or is_china) else 'en'

    if not qr_id:
        return render_template('failed.html', msg="缺少防伪编号，无法核验。", language=language)
    if not platform:
        return render_template('select_platform.html', qr_id=qr_id, error="请先选择购买平台", language=language)

    status, data = check_qr_status(qr_id)
    log_scan(qr_id, user_ip, platform)

    if status == 'invalid':
        return render_template('failed.html', msg="该产品编码不存在，谨防假冒！", platform=platform, language=language)
    elif status == 'warning':
        return render_template('warning.html', serial_no=data['serial_no'], scan_count=data['count'], platform=platform,
                               language=language)
    else:
        increment_scan_count(qr_id)
        return render_template('success.html', serial_no=data['serial_no'], scan_count=data['count'] + 1,
                               platform=platform, language=language)


if __name__ == '__main__':
    if not os.path.exists('database/anti_fake.db'):
        print("错误：未找到数据库，请先运行 db_init.py")
    else:
        init_ip_searcher()
        app.run(debug=False, host='0.0.0.0', port=5000)
