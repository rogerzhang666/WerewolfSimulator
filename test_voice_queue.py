#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
语音队列机制测试脚本
测试角色发言的顺序控制
"""

import asyncio
import time

async def simulate_character_speech(character_name, speech_text, delay=0):
    """模拟角色发言"""
    if delay > 0:
        await asyncio.sleep(delay)
    
    print(f"[{time.strftime('%H:%M:%S')}] {character_name}开始发言...")
    print(f"    内容: {speech_text}")
    
    # 模拟语音播放时间（根据文本长度）
    speech_duration = len(speech_text) * 0.1  # 每个字符0.1秒
    print(f"    预计语音时长: {speech_duration:.1f}秒")
    
    await asyncio.sleep(speech_duration)
    
    print(f"[{time.strftime('%H:%M:%S')}] {character_name}发言完成")
    return f"{character_name}_completed"

async def test_sequential_speech():
    """测试顺序发言机制"""
    print("=== 测试顺序发言机制 ===")
    
    # 模拟8个角色的发言
    characters = [
        ("张明盛", "大家好，我是张明盛！我认为我们应该仔细分析每个人的发言，找出狼人的破绽。"),
        ("李思思", "我是李思思，我觉得张明盛说得有道理，但我们也需要更多的证据。"),
        ("王悟宁", "作为理性分析者，我认为我们应该从逻辑角度来思考这个问题。"),
        ("赵敏敏", "我情绪很激动！我觉得有些人说话很奇怪，大家要小心！"),
        ("钱思达", "冷静一点，我们需要理性地分析，而不是情绪化地判断。"),
        ("孙淼", "我多疑的性格让我觉得每个人都有嫌疑，但我们需要证据。"),
        ("周久", "我保持沉默，但我会仔细观察每个人的行为。"),
        ("吴天天", "大家好呀！我是活跃的吴天天，我觉得我们应该积极讨论！")
    ]
    
    print("开始顺序发言测试...")
    start_time = time.time()
    
    # 顺序执行，每个角色等待前一个完成
    for i, (character, speech) in enumerate(characters):
        print(f"\n--- 第{i+1}个角色发言 ---")
        result = await simulate_character_speech(character, speech)
        print(f"结果: {result}")
    
    total_time = time.time() - start_time
    print(f"\n=== 测试完成 ===")
    print(f"总耗时: {total_time:.1f}秒")
    print(f"平均每个角色: {total_time/len(characters):.1f}秒")

async def test_voice_queue_simulation():
    """测试语音队列模拟"""
    print("\n=== 测试语音队列模拟 ===")
    
    # 模拟语音队列
    voice_queue = []
    
    async def add_to_voice_queue(character, text):
        """添加语音到队列"""
        voice_queue.append({"character": character, "text": text, "timestamp": time.time()})
        print(f"语音已加入队列: {character} - {text[:30]}...")
        print(f"当前队列长度: {len(voice_queue)}")
    
    async def process_voice_queue():
        """处理语音队列"""
        while voice_queue:
            voice_item = voice_queue.pop(0)
            character = voice_item["character"]
            text = voice_item["text"]
            
            print(f"\n开始播放队列中的语音: {character}")
            await simulate_character_speech(character, text)
            print(f"语音播放完成: {character}")
    
    # 模拟多个角色同时请求语音播放
    print("模拟多个角色同时请求语音播放...")
    
    # 同时添加多个语音请求
    await asyncio.gather(
        add_to_voice_queue("张明盛", "我是第一个角色！"),
        add_to_voice_queue("李思思", "我是第二个角色！"),
        add_to_voice_queue("王悟宁", "我是第三个角色！")
    )
    
    print(f"\n队列构建完成，开始顺序处理...")
    await process_voice_queue()
    
    print("语音队列处理完成！")

if __name__ == "__main__":
    print("语音队列机制测试")
    print("=" * 50)
    
    # 运行测试
    asyncio.run(test_sequential_speech())
    asyncio.run(test_voice_queue_simulation())
    
    print("\n" + "=" * 50)
    print("所有测试完成！")
