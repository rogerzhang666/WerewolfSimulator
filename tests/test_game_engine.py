#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
游戏引擎测试脚本
"""

import os
import sys
import time
import json

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.models.game_engine import GameEngine
from backend.models.character import Character
from backend.utils.mock_ai_client import get_mock_ai_client

def test_game_engine():
    """测试游戏引擎的基本功能"""
    print("开始测试游戏引擎...")

    # 创建游戏引擎
    engine = GameEngine()

    # 测试加载角色配置
    print("\n测试加载角色配置...")
    if os.path.exists('config/characters.json'):
        success = engine.load_characters_from_config('config/characters.json')
        if success:
            print("成功加载角色配置")
            print(f"加载了{len(engine.game.characters)}个角色")
            for character in engine.game.characters:
                print(f"- {character.name} ({character.gender}, {character.style}, 模型: {character.model})")
                # 替换为模拟AI客户端
                engine.ai_clients[character.id] = get_mock_ai_client()
        else:
            print("加载角色配置失败")
    else:
        print("角色配置文件不存在，创建测试角色...")
        # 创建测试角色
        for i in range(8):
            gender = "男" if i % 2 == 0 else "女"
            style = ["激进", "保守", "理性", "情绪化", "冷静", "多疑", "沉默", "活跃"][i]
            model = "deepseek-R1" if i % 2 == 0 else "qwen"
            character = Character(
                id=i+1,
                name=f"测试角色{i+1}",
                gender=gender,
                style=style,
                model=model
            )
            engine.game.add_character(character)
            # 为每个角色创建模拟AI客户端
            engine.ai_clients[character.id] = get_mock_ai_client()

        print(f"创建了{len(engine.game.characters)}个测试角色")

    # 测试开始游戏
    print("\n测试开始游戏...")
    success = engine.start_game()
    if success:
        print("游戏成功启动")
        print(f"当前游戏状态: {engine.game.status.value}")
        print(f"当前游戏阶段: {engine.game.phase.value}")
        print(f"当前天数: {engine.game.current_day}")

        # 打印角色分配结果
        print("\n角色分配结果:")
        for character in engine.game.characters:
            print(f"- {character.name}: {character.role}")

        # 等待游戏运行一段时间
        print("\n游戏正在运行，等待10秒...")
        time.sleep(10)

        # 打印游戏日志
        print("\n游戏日志:")
        for log in engine.game.logs[-20:]:  # 最近20条日志
            print(f"[{log['timestamp']}] [{log['day']}天-{log['phase']}] {log['source']}: {log['message']}")

        # 测试暂停游戏
        print("\n测试暂停游戏...")
        success = engine.pause_game()
        if success:
            print("游戏成功暂停")
            print(f"当前游戏状态: {engine.game.status.value}")
        else:
            print("暂停游戏失败")

        # 测试恢复游戏
        print("\n测试恢复游戏...")
        success = engine.resume_game()
        if success:
            print("游戏成功恢复")
            print(f"当前游戏状态: {engine.game.status.value}")
        else:
            print("恢复游戏失败")

        # 等待游戏运行一段时间
        print("\n游戏正在运行，等待10秒...")
        time.sleep(10)

        # 打印游戏日志
        print("\n游戏日志:")
        for log in engine.game.logs[-20:]:  # 最近20条日志
            print(f"[{log['timestamp']}] [{log['day']}天-{log['phase']}] {log['source']}: {log['message']}")

        # 测试重置游戏
        print("\n测试重置游戏...")
        success = engine.reset_game()
        if success:
            print("游戏成功重置")
            print(f"当前游戏状态: {engine.game.status.value}")
        else:
            print("重置游戏失败")
    else:
        print("启动游戏失败")

    print("\n游戏引擎测试完成")

if __name__ == "__main__":
    test_game_engine()
