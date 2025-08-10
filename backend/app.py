#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
from flask import Flask, jsonify, send_from_directory
from flask_socketio import SocketIO
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# 创建Flask应用
app = Flask(__name__, static_folder=None)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'default_secret_key')
socketio = SocketIO(app, cors_allowed_origins="*")

# 导入路由
from backend.api import routes

@app.route('/api/health')
def health_check():
    """健康检查接口"""
    return jsonify({"status": "ok", "message": "服务正常运行"})

# 提供前端静态文件
@app.route('/')
def index():
    """提供前端首页"""
    return send_from_directory('../frontend/public', 'index.html')

@app.route('/<path:path>')
def static_files(path):
    """提供前端静态文件"""
    return send_from_directory('../frontend/public', path)

if __name__ == '__main__':
    port = int(os.getenv('PORT', 5000))
    debug = os.getenv('DEBUG', 'False').lower() == 'true'
    socketio.run(app, host='0.0.0.0', port=port, debug=debug)
