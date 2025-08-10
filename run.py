#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
狼人杀模拟器启动脚本
"""

import os
from backend.app import app, socketio

if __name__ == '__main__':
    port = int(os.getenv('PORT', 5001))  # 修改默认端口为5001
    debug = os.getenv('DEBUG', 'True').lower() == 'true'

    print(f"启动狼人杀模拟器服务器，端口: {port}, 调试模式: {debug}")
    socketio.run(app, host='0.0.0.0', port=port, debug=debug)
