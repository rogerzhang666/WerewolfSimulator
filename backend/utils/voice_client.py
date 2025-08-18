#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
语音合成客户端
使用阿里百炼平台的CosyVoice模型为游戏角色生成语音
"""

import os
import uuid
import hashlib
from datetime import datetime
from dotenv import load_dotenv
import dashscope
from dashscope.audio.tts_v2 import SpeechSynthesizer

# 加载环境变量
load_dotenv()

class VoiceClient:
    """语音合成客户端"""

    def __init__(self):
        """初始化语音客户端"""
        self.api_key = os.getenv("DASHSCOPE_API_KEY")
        if not self.api_key:
            raise ValueError("未设置DASHSCOPE_API_KEY环境变量")
        
        # 设置DashScope API密钥
        dashscope.api_key = self.api_key
        
        # 音色映射表 - 使用已知可用的音色
        self.voice_mapping = {
            "系统": "longxiaochun_v2",
            "张明盛": "longfei_v2", 
            "李思思": "longxiaochun_v2",  # 暂时使用系统音色
            "王悟宁": "longfei_v2",        # 暂时使用张明盛音色
            "赵敏敏": "longxiaochun_v2",   # 暂时使用系统音色
            "钱思达": "longfei_v2",        # 暂时使用张明盛音色
            "孙淼": "longxiaochun_v2",     # 暂时使用系统音色
            "周久": "longfei_v2",          # 暂时使用张明盛音色
            "吴天天": "longxiaochun_v2"    # 暂时使用系统音色
        }
        
        # 确保音频文件夹存在
        self.audio_dir = "/Users/rogerchang/狼人杀模拟器/data/audio"
        os.makedirs(self.audio_dir, exist_ok=True)

    def synthesize_speech(self, text, character_name):
        """
        合成语音，返回音频数据
        
        Args:
            text (str): 要合成的文本
            character_name (str): 角色名称
            
        Returns:
            bytes: 音频数据，失败时返回None
        """
        try:
            # 获取音色
            voice = self.voice_mapping.get(character_name, "longxiang")
            
            # 文本长度检查（CosyVoice限制2000字符）
            if len(text) > 2000:
                text = text[:1900] + "..."
                
            print(f"正在为{character_name}合成语音: {text[:50]}...")
            
            # 调用CosyVoice API - 使用官方推荐的方式
            synthesizer = SpeechSynthesizer(model='cosyvoice-v2', voice=voice)
            audio = synthesizer.call(text)
            
            if audio:
                print(f"语音合成成功，角色: {character_name}")
                return audio
            else:
                print(f"语音合成失败，无音频数据")
                return None
                
        except Exception as e:
            print(f"语音合成失败: {str(e)}")
            return None

    def get_character_voice(self, character_name):
        """
        获取角色对应的音色
        
        Args:
            character_name (str): 角色名称
            
        Returns:
            str: 音色名称
        """
        return self.voice_mapping.get(character_name, "longxiang")

    def cleanup_old_audio(self, max_files=100):
        """
        清理旧的音频文件，保持文件数量在合理范围
        
        Args:
            max_files (int): 最大保留文件数
        """
        try:
            if not os.path.exists(self.audio_dir):
                return
                
            files = [f for f in os.listdir(self.audio_dir) if f.endswith('.wav')]
            
            if len(files) <= max_files:
                return
                
            # 按修改时间排序，删除最旧的文件
            files_with_time = []
            for f in files:
                file_path = os.path.join(self.audio_dir, f)
                try:
                    mtime = os.path.getmtime(file_path)
                    files_with_time.append((mtime, file_path))
                except OSError:
                    continue
                    
            files_with_time.sort()
            
            # 删除最旧的文件
            files_to_delete = len(files_with_time) - max_files
            for i in range(files_to_delete):
                try:
                    os.remove(files_with_time[i][1])
                    print(f"清理旧音频文件: {files_with_time[i][1]}")
                except OSError:
                    continue
                    
        except Exception as e:
            print(f"清理音频文件失败: {str(e)}")

# 全局语音客户端实例
voice_client = VoiceClient()
