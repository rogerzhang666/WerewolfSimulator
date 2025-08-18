#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
语音系统测试脚本
测试狼人杀模拟器的语音功能
"""

import requests
import json
import time

def test_voice_api():
    """测试语音合成API"""
    print("=== 测试语音合成API ===")
    
    # 测试数据
    test_cases = [
        {"text": "大家好，我是张明盛！", "character": "张明盛"},
        {"text": "我是李思思，请多指教！", "character": "李思思"},
        {"text": "系统提示：游戏开始！", "character": "系统"},
        {"text": "我是王悟宁，理性分析中...", "character": "王悟宁"},
        {"text": "赵敏敏情绪激动地说！", "character": "赵敏敏"}
    ]
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n测试 {i}: {test_case['character']} - {test_case['text']}")
        
        try:
            response = requests.post(
                'http://localhost:5003/api/voice/synthesize',
                headers={'Content-Type': 'application/json'},
                json=test_case,
                timeout=30
            )
            
            if response.status_code == 200:
                audio_data = response.content
                filename = f"test_{test_case['character']}_{i}.mp3"
                
                with open(filename, 'wb') as f:
                    f.write(audio_data)
                
                print(f"  ✅ 成功 - 音频文件: {filename} (大小: {len(audio_data)} 字节)")
            else:
                print(f"  ❌ 失败 - HTTP状态码: {response.status_code}")
                try:
                    error_info = response.json()
                    print(f"      错误信息: {error_info}")
                except:
                    print(f"      响应内容: {response.text}")
                    
        except Exception as e:
            print(f"  ❌ 异常 - {str(e)}")
    
    print("\n=== API测试完成 ===")

def test_voice_client():
    """测试语音客户端"""
    print("\n=== 测试语音客户端 ===")
    
    try:
        from backend.utils.voice_client import voice_client
        
        # 测试所有角色
        characters = ["张明盛", "李思思", "王悟宁", "赵敏敏", "钱思达", "孙淼", "周久", "吴天天"]
        
        for char in characters:
            print(f"\n测试角色: {char}")
            try:
                result = voice_client.synthesize_speech(f"测试{char}的语音", char)
                if result:
                    print(f"  ✅ 成功 - 数据长度: {len(result)} 字节")
                else:
                    print(f"  ❌ 失败 - 无音频数据")
            except Exception as e:
                print(f"  ❌ 异常 - {str(e)}")
                
    except Exception as e:
        print(f"导入语音客户端失败: {str(e)}")
    
    print("\n=== 客户端测试完成 ===")

def test_game_engine_voice():
    """测试游戏引擎的语音功能"""
    print("\n=== 测试游戏引擎语音功能 ===")
    
    try:
        from backend.models.game_engine import GameEngine
        
        # 创建游戏引擎实例
        engine = GameEngine()
        
        # 测试语音播放通知
        print("测试语音播放通知...")
        engine.emit_voice_play("张明盛", "大家好，我是张明盛！")
        engine.emit_voice_play("李思思", "我是李思思，请多指教！")
        
        print("  ✅ 语音通知发送成功")
        
    except Exception as e:
        print(f"  ❌ 游戏引擎测试失败: {str(e)}")
    
    print("\n=== 游戏引擎测试完成 ===")

if __name__ == "__main__":
    print("狼人杀模拟器语音系统测试")
    print("=" * 50)
    
    # 检查服务器是否运行
    try:
        response = requests.get('http://localhost:5003/api/health', timeout=5)
        if response.status_code == 200:
            print("✅ 服务器运行正常")
        else:
            print("❌ 服务器响应异常")
            exit(1)
    except:
        print("❌ 无法连接到服务器，请确保服务器正在运行")
        exit(1)
    
    # 运行测试
    test_voice_api()
    test_voice_client()
    test_game_engine_voice()
    
    print("\n" + "=" * 50)
    print("所有测试完成！")
