#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
极简发卡程序 v3 - 直接操作 One-API 数据库
支持虎皮椒支付回调，自动生成兑换码
"""

from flask import Flask, render_string, request, jsonify
import requests
import sqlite3
import json
import hashlib
import time
from datetime import datetime

app = Flask(__name__)

# 配置
XUNHUPAY_APPID = "201906178077"
XUNHUPAY_KEY = "8615d7b38baf39db7ec75b6bae498e26"
XUNHUPAY_API = "https://api.xunhupay.com/payment/do.html"
ONE_API_DB = "/opt/one-api/data/one-api.db"

# 1 元 = 10,000 积分的映射
QUOTA_PER_YUAN = 10000  # 实际存储为 50亿 额度单位

@app.route('/')
def index():
    html = """
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <title>Water API - 积分充值</title>
        <style>
            body { font-family: Arial; text-align: center; padding: 50px; }
            .container { max-width: 400px; margin: 0 auto; border: 1px solid #ddd; padding: 30px; border-radius: 8px; }
            input { padding: 10px; margin: 10px 0; width: 100%; box-sizing: border-box; }
            button { padding: 10px 20px; background: #007bff; color: white; border: none; border-radius: 4px; cursor: pointer; width: 100%; }
            button:hover { background: #0056b3; }
            .price { font-size: 24px; color: #28a745; margin: 20px 0; }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>💰 Water API 积分充值</h1>
            <p>1 元 = 10,000 积分</p>
            <form id="payForm">
                <input type="number" id="amount" placeholder="充值金额（元）" min="0.01" step="0.01" required>
                <div class="price">预计获得：<span id="quota">0</span> 积分</div>
                <button type="submit">立即支付</button>
            </form>
        </div>
        <script>
            document.getElementById('amount').addEventListener('input', function() {
                var amount = parseFloat(this.value) || 0;
                document.getElementById('quota').textContent = (amount * 10000).toLocaleString();
            });
            document.getElementById('payForm').addEventListener('submit', function(e) {
                e.preventDefault();
                var amount = document.getElementById('amount').value;
                window.location.href = '/pay?amount=' + amount;
            });
        </script>
    </body>
    </html>
    """
    return render_string(html)

@app.route('/pay')
def pay():
    """生成虎皮椒支付链接"""
    try:
        amount = float(request.args.get('amount', 0))
        if amount <= 0:
            return "金额必须大于0", 400
        
        # 生成订单号
        order_id = f"WaterAPI_{int(time.time() * 1000)}"
        
        # 构建支付参数
        params = {
            'pid': XUNHUPAY_APPID,
            'type': 'wxpay',  # 微信支付
            'out_trade_no': order_id,
            'notify_url': 'http://144.202.121.4:3001/callback',
            'return_url': 'http://144.202.121.4:3001/success',
            'name': f'Water API - {int(amount * 10000)} 积分',
            'money': str(amount),
        }
        
        # 生成签名
        sign_str = f"{XUNHUPAY_APPID}{order_id}{amount}{XUNHUPAY_KEY}"
        params['sign'] = hashlib.md5(sign_str.encode()).hexdigest()
        
        # 重定向到虎皮椒
        redirect_url = f"{XUNHUPAY_API}?" + "&".join([f"{k}={v}" for k, v in params.items()])
        
        return f"""
        <html>
        <body>
            <p>正在跳转到支付页面...</p>
            <script>
                window.location.href = '{redirect_url}';
            </script>
        </body>
        </html>
        """
    except Exception as e:
        return f"错误: {str(e)}", 500

@app.route('/callback', methods=['POST'])
def callback():
    """虎皮椒支付回调"""
    try:
        # 获取回调参数
        out_trade_no = request.form.get('out_trade_no')
        trade_no = request.form.get('trade_no')
        money = float(request.form.get('money', 0))
        sign = request.form.get('sign')
        
        # 验证签名
        sign_str = f"{XUNHUPAY_APPID}{out_trade_no}{money}{XUNHUPAY_KEY}"
        expected_sign = hashlib.md5(sign_str.encode()).hexdigest()
        
        if sign != expected_sign:
            return "签名验证失败", 403
        
        # 计算积分
        quota = int(money * QUOTA_PER_YUAN)
        
        # 生成兑换码
        redemption_code = generate_redemption_code(quota)
        
        return "success"
    except Exception as e:
        print(f"回调错误: {str(e)}")
        return "error", 500

@app.route('/success')
def success():
    """支付成功页面"""
    try:
        out_trade_no = request.args.get('out_trade_no')
        money = float(request.args.get('money', 0))
        
        # 从数据库查询兑换码
        conn = sqlite3.connect(ONE_API_DB)
        cursor = conn.cursor()
        cursor.execute(
            "SELECT code FROM redemptions WHERE key LIKE ? ORDER BY id DESC LIMIT 1",
            (f"%{out_trade_no}%",)
        )
        result = cursor.fetchone()
        conn.close()
        
        redemption_code = result[0] if result else "生成中..."
        quota = int(money * 10000)
        
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <title>支付成功</title>
            <style>
                body {{ font-family: Arial; text-align: center; padding: 50px; background: #f0f0f0; }}
                .container {{ max-width: 500px; margin: 0 auto; background: white; padding: 40px; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
                .success {{ color: #28a745; font-size: 48px; margin: 20px 0; }}
                .code {{ background: #f9f9f9; padding: 20px; margin: 20px 0; border-radius: 4px; font-family: monospace; word-break: break-all; }}
                button {{ padding: 10px 20px; background: #007bff; color: white; border: none; border-radius: 4px; cursor: pointer; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="success">✓ 支付成功！</div>
                <p>您已充值 ¥{money:.2f}</p>
                <p style="font-size: 24px; color: #28a745;">获得 {quota:,} 积分</p>
                <p style="margin-top: 30px; color: #666;">您的兑换码：</p>
                <div class="code">{redemption_code}</div>
                <button onclick="copyCode()">复制兑换码</button>
                <p style="margin-top: 20px; color: #999; font-size: 12px;">请妥善保管兑换码，在 One-API 充值页面粘贴使用</p>
            </div>
            <script>
                function copyCode() {{
                    var code = '{redemption_code}';
                    navigator.clipboard.writeText(code).then(function() {{
                        alert('兑换码已复制到剪贴板');
                    }});
                }}
            </script>
        </body>
        </html>
        """
        return html
    except Exception as e:
        return f"错误: {str(e)}", 500

def generate_redemption_code(quota):
    """在 One-API 数据库中生成兑换码"""
    try:
        conn = sqlite3.connect(ONE_API_DB)
        cursor = conn.cursor()
        
        # 生成唯一的兑换码
        code = f"sk-{hashlib.md5(f'{time.time()}{quota}'.encode()).hexdigest()[:32]}"
        
        # 插入到 redemptions 表
        cursor.execute(
            "INSERT INTO redemptions (code, quota, created_time, status) VALUES (?, ?, ?, ?)",
            (code, quota, int(time.time()), 0)
        )
        conn.commit()
        conn.close()
        
        return code
    except Exception as e:
        print(f"生成兑换码错误: {str(e)}")
        return "生成失败"

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=3001, debug=False)
