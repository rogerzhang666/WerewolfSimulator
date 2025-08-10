#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import json
from flask import jsonify, request
from backend.app import app, socketio
from backend.models.game_engine import GameEngine

# 创建游戏引擎实例
game_engine = GameEngine(socketio)

# 游戏配置API
@app.route('/api/config', methods=['GET', 'POST'])
def game_config():
    """获取或更新游戏配置"""
    if request.method == 'POST':
        # 更新游戏配置
        config_data = request.json
        # 保存配置到配置文件
        try:
            with open('config/game_config.json', 'w', encoding='utf-8') as f:
                json.dump(config_data, f, ensure_ascii=False, indent=2)
            return jsonify({"status": "success", "message": "配置已更新", "data": config_data})
        except Exception as e:
            return jsonify({"status": "error", "message": f"保存配置失败: {str(e)}"})
    else:
        # 获取游戏配置
        try:
            if os.path.exists('config/game_config.json'):
                with open('config/game_config.json', 'r', encoding='utf-8') as f:
                    config_data = json.load(f)
                return jsonify({"status": "success", "data": config_data})
            else:
                # 默认配置
                default_config = {
                    "players": 8,
                    "roles": {
                        "werewolf": 2,
                        "villager": 4,
                        "seer": 1,
                        "witch": 1
                    }
                }
                return jsonify({"status": "success", "data": default_config})
        except Exception as e:
            return jsonify({"status": "error", "message": f"读取配置失败: {str(e)}"})

# 角色API
@app.route('/api/characters', methods=['GET', 'POST'])
def characters():
    """获取或创建角色"""
    if request.method == 'POST':
        # 创建新角色配置
        characters_data = request.json
        # 保存角色配置到文件
        try:
            with open('config/characters.json', 'w', encoding='utf-8') as f:
                json.dump(characters_data, f, ensure_ascii=False, indent=2)
            return jsonify({"status": "success", "message": "角色配置已保存", "data": characters_data})
        except Exception as e:
            return jsonify({"status": "error", "message": f"保存角色配置失败: {str(e)}"})
    else:
        # 获取角色配置
        try:
            if os.path.exists('config/characters.json'):
                with open('config/characters.json', 'r', encoding='utf-8') as f:
                    characters_data = json.load(f)
                return jsonify({"status": "success", "data": characters_data})
            else:
                return jsonify({"status": "error", "message": "角色配置文件不存在"})
        except Exception as e:
            return jsonify({"status": "error", "message": f"读取角色配置失败: {str(e)}"})

# 游戏控制API
@app.route('/api/game/start', methods=['POST'])
def start_game():
    """开始游戏"""
    try:
        # 加载角色配置
        if not os.path.exists('config/characters.json'):
            return jsonify({"status": "error", "message": "角色配置文件不存在，请先创建角色"})

        # 加载角色到游戏引擎
        success = game_engine.load_characters_from_config('config/characters.json')
        if not success:
            return jsonify({"status": "error", "message": "加载角色配置失败"})

        # 启动游戏
        if game_engine.start_game():
            return jsonify({"status": "success", "message": "游戏已开始"})
        else:
            return jsonify({"status": "error", "message": "启动游戏失败，可能游戏已经在运行"})
    except Exception as e:
        return jsonify({"status": "error", "message": f"启动游戏失败: {str(e)}"})

@app.route('/api/game/pause', methods=['POST'])
def pause_game():
    """暂停游戏"""
    try:
        if game_engine.pause_game():
            return jsonify({"status": "success", "message": "游戏已暂停"})
        else:
            return jsonify({"status": "error", "message": "暂停游戏失败，可能游戏未在运行"})
    except Exception as e:
        return jsonify({"status": "error", "message": f"暂停游戏失败: {str(e)}"})

@app.route('/api/game/resume', methods=['POST'])
def resume_game():
    """恢复游戏"""
    try:
        if game_engine.resume_game():
            return jsonify({"status": "success", "message": "游戏已恢复"})
        else:
            return jsonify({"status": "error", "message": "恢复游戏失败，可能游戏未被暂停"})
    except Exception as e:
        return jsonify({"status": "error", "message": f"恢复游戏失败: {str(e)}"})

@app.route('/api/game/reset', methods=['POST'])
def reset_game():
    """重置游戏"""
    try:
        if game_engine.reset_game():
            return jsonify({"status": "success", "message": "游戏已重置"})
        else:
            return jsonify({"status": "error", "message": "重置游戏失败"})
    except Exception as e:
        return jsonify({"status": "error", "message": f"重置游戏失败: {str(e)}"})

@app.route('/api/game/state', methods=['GET'])
def get_game_state():
    """获取游戏状态"""
    try:
        game_state = game_engine.get_game_state()
        return jsonify({"status": "success", "data": game_state})
    except Exception as e:
        return jsonify({"status": "error", "message": f"获取游戏状态失败: {str(e)}"})

# WebSocket事件
@socketio.on('connect')
def handle_connect():
    """客户端连接事件"""
    print('Client connected')
    # 发送当前游戏状态
    try:
        game_state = game_engine.get_game_state()
        socketio.emit('game_state', game_state)
    except Exception as e:
        print(f"发送游戏状态失败: {str(e)}")

@socketio.on('disconnect')
def handle_disconnect():
    """客户端断开连接事件"""
    print('Client disconnected')

# 游戏操作事件
@socketio.on('game_action')
def handle_game_action(data):
    """处理游戏操作事件"""
    action = data.get('action')

    if action == 'start':
        start_game()
    elif action == 'pause':
        pause_game()
    elif action == 'resume':
        resume_game()
    elif action == 'reset':
        reset_game()
    else:
        socketio.emit('error', {"message": f"未知的游戏操作: {action}"})
