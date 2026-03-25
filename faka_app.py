import os
import time
import sqlite3
import hashlib
import random
import string
from flask import Flask, request, redirect, render_template_string

app = Flask(__name__)

# 配置信息
XUNHUPAY_APPID = "201906178077"
XUNHUPAY_APPSECRET = "8615d7b38baf39db7ec75b6bae498e26"
XUNHUPAY_API_URL = "https://api.xunhupay.com/payment/do.html"
ONE_API_DB_PATH = "/data/one-api.db"

# 定价逻辑：1元 = 10,000 积分
POINTS_PER_YUAN = 10000
QUOTA_PER_POINT = 1
QUOTA_PER_YUAN = POINTS_PER_YUAN * QUOTA_PER_POINT

def generate_signature(params, secret):
    sorted_params = sorted(params.items())
    query_string = "&".join([f"{k}={v}" for k, v in sorted_params if v])
    return hashlib.md5((query_string + secret).encode('utf-8')).hexdigest()

def generate_redemption_key():
    return 'sk-' + ''.join(random.choices(string.ascii_letters + string.digits, k=32))

def init_db():
    conn = sqlite3.connect('faka.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS orders
                 (trade_order_id TEXT PRIMARY KEY, amount REAL, quota INTEGER, code TEXT, status INTEGER)''')
    conn.commit()
    conn.close()

init_db()

@app.route('/')
def index():
    return render_template_string('''
        <!DOCTYPE html>
        <html>
        <head>
            <title>Water API 充值中心</title>
            <meta name="viewport" content="width=device-width, initial-scale=1">
            <style>
                body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif; display: flex; justify-content: center; align-items: center; height: 100vh; margin: 0; background: #f0f2f5; }
                .card { background: white; padding: 2.5rem; border-radius: 12px; box-shadow: 0 8px 24px rgba(0,0,0,0.08); width: 100%; max-width: 400px; text-align: center; }
                h2 { color: #1a1a1a; margin-bottom: 1.5rem; }
                input { width: 100%; padding: 12px; margin: 1rem 0; border: 1px solid #ddd; border-radius: 6px; box-sizing: border-box; font-size: 16px; }
                button { width: 100%; padding: 12px; background: #07c160; color: white; border: none; border-radius: 6px; font-size: 16px; font-weight: 600; cursor: pointer; transition: background 0.2s; }
                button:hover { background: #06ae56; }
                .info { margin-top: 1.5rem; color: #666; font-size: 14px; line-height: 1.6; }
                .highlight { color: #07c160; font-weight: bold; }
            </style>
        </head>
        <body>
            <div class="card">
                <h2>Water API 充值</h2>
                <form action="/pay" method="post">
                    <input type="number" name="amount" placeholder="输入充值金额 (元)" min="1" step="1" required>
                    <button type="submit">微信支付</button>
                </form>
                <div class="info">
                    当前定价：<span class="highlight">1 元 = 10,000 积分</span><br>
                    支付成功后将自动生成兑换码
                </div>
            </div>
        </body>
        </html>
    ''')

@app.route('/pay', methods=['POST'])
def pay():
    amount = request.form.get('amount')
    trade_order_id = str(int(time.time() * 1000))

    params = {
        "version": "1.1",
        "appid": XUNHUPAY_APPID,
        "trade_order_id": trade_order_id,
        "total_fee": amount,
        "title": f"Water API 充值 {amount}元",
        "time": str(int(time.time())),
        "notify_url": f"http://{request.host}/callback",
        "return_url": f"http://{request.host}/result?trade_order_id={trade_order_id}",
        "nonce_str": trade_order_id
    }
    params["hash"] = generate_signature(params, XUNHUPAY_APPSECRET)

    try:
        import requests
        response = requests.post(XUNHUPAY_API_URL, data=params)
        res_data = response.json()
        if res_data.get("errcode") == 0:
            conn = sqlite3.connect('faka.db')
            c = conn.cursor()
            c.execute("INSERT INTO orders VALUES (?, ?, ?, ?, ?)",
                      (trade_order_id, float(amount), int(float(amount) * QUOTA_PER_YUAN), "", 0))
            conn.commit()
            conn.close()
            return redirect(res_data.get("url"))
        else:
            return f"支付发起失败: {res_data.get('errmsg')}"
    except Exception as e:
        return f"系统错误: {str(e)}"

@app.route('/callback', methods=['POST'])
def callback():
    data = request.form.to_dict()
    signature = data.pop('hash', None)
    if generate_signature(data, XUNHUPAY_APPSECRET) == signature:
        if data.get('status') == 'OD':
            trade_order_id = data.get('trade_order_id')
            conn = sqlite3.connect('faka.db')
            c = conn.cursor()
            c.execute("SELECT quota, status FROM orders WHERE trade_order_id=?", (trade_order_id,))
            order = c.fetchone()

            if order and order[1] == 0:
                quota = order[0]
                try:
                    one_api_conn = sqlite3.connect(ONE_API_DB_PATH)
                    one_api_c = one_api_conn.cursor()
                    key = generate_redemption_key()
                    now = int(time.time())
                    one_api_c.execute("INSERT INTO redemptions (user_id, key, status, name, quota, created_time) VALUES (?, ?, ?, ?, ?, ?)",
                                      (1, key, 1, f"Order_{trade_order_id}", quota, now))
                    one_api_conn.commit()
                    one_api_conn.close()

                    c.execute("UPDATE orders SET code=?, status=1 WHERE trade_order_id=?", (key, trade_order_id))
                    conn.commit()
                except Exception as e:
                    print(f"Database error: {e}")
            conn.close()
            return "success"
    return "fail"

@app.route('/result')
def result():
    trade_order_id = request.args.get('trade_order_id')
    conn = sqlite3.connect('faka.db')
    c = conn.cursor()
    c.execute("SELECT code, status FROM orders WHERE trade_order_id=?", (trade_order_id,))
    order = c.fetchone()
    conn.close()

    if order:
        if order[1] == 1:
            return render_template_string('''
                <!DOCTYPE html>
                <html>
                <head>
                    <title>充值成功</title>
                    <meta name="viewport" content="width=device-width, initial-scale=1">
                    <style>
                        body { font-family: sans-serif; display: flex; justify-content: center; align-items: center; height: 100vh; margin: 0; background: #f4f7f6; }
                        .card { background: white; padding: 2rem; border-radius: 8px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); width: 100%; max-width: 400px; text-align: center; }
                        .code { background: #eee; padding: 15px; font-family: monospace; font-size: 18px; margin: 20px 0; word-break: break-all; border: 1px dashed #ccc; }
                        button { padding: 12px 24px; background: #007bff; color: white; border: none; border-radius: 4px; cursor: pointer; font-weight: bold; }
                        .info { background: #f8f9fa; padding: 15px; border-radius: 6px; margin: 15px 0; text-align: left; font-size: 14px; }
                        .info code { background: #e9ecef; padding: 2px 6px; border-radius: 4px; }
                    </style>
                </head>
                <body>
                    <div class="card">
                        <h2 style="color: #07c160;">支付成功！</h2>
                        <p>您的兑换码为：</p>
                        <div class="code">{{ code }}</div>
                        <div class="info">
                            <strong>使用方法：</strong><br>
                            1. 访问 <a href="http://144.202.121.4:3000" target="_blank">One-API</a> 登录<br>
                            2. 在充值页面粘贴兑换码<br>
                            3. 获得积分后创建令牌使用 API<br><br>
                            <strong>API 地址：</strong><br>
                            <code>http://144.202.121.4:3000/v1</code>
                        </div>
                        <button onclick="window.location.href='http://144.202.121.4:3000/topup'">前往充值页面</button>
                    </div>
                </body>
                </html>
            ''', code=order[0])
        else:
            return "支付处理中，请稍后刷新页面..."
    return "订单不存在"

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=3001)