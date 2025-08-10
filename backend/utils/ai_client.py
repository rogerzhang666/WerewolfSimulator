#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import json
import requests
from datetime import datetime
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

class AIClient:
    """AI模型客户端基类"""

    def __init__(self):
        """初始化AI客户端"""
        pass

    def generate_response(self, prompt, character=None):
        """
        生成AI响应

        Args:
            prompt (str): 提示词
            character (Character, optional): 角色对象. 默认为None.

        Returns:
            str: AI生成的响应
        """
        raise NotImplementedError("子类必须实现此方法")

    def _record_ai_call(self, character, system_prompt, user_prompt, response, model_name, call_type="general"):
        """
        记录AI调用信息

        Args:
            character: 角色对象
            system_prompt: 系统提示词
            user_prompt: 用户提示词
            response: AI响应
            model_name: 模型名称
            call_type: 调用类型
        """
        if character and hasattr(character, 'memory'):
            ai_call_record = {
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "model": model_name,
                "call_type": call_type,
                "input": {
                    "system_prompt": system_prompt,
                    "user_prompt": user_prompt
                },
                "output": response,
                "character": character.name,
                "role": character.role
            }

            # 确保memory中有ai_calls字段
            if "ai_calls" not in character.memory:
                character.memory["ai_calls"] = []

            character.memory["ai_calls"].append(ai_call_record)

            # 只保留最近20次调用记录，避免内存过大
            if len(character.memory["ai_calls"]) > 20:
                character.memory["ai_calls"] = character.memory["ai_calls"][-20:]

class DeepseekClient(AIClient):
    """Deepseek模型客户端"""

    def __init__(self):
        """初始化Deepseek客户端"""
        super().__init__()
        self.api_key = os.getenv("DEEPSEEK_API_KEY")
        if not self.api_key:
            raise ValueError("未设置DEEPSEEK_API_KEY环境变量")

        self.api_url = "https://api.deepseek.com/v1/chat/completions"  # 示例URL，需替换为实际URL

    def generate_response(self, prompt, character=None, call_type="general"):
        """
        生成Deepseek模型响应

        Args:
            prompt (str): 提示词
            character (Character, optional): 角色对象. 默认为None.
            call_type (str): 调用类型，用于调试

        Returns:
            str: AI生成的响应
        """
        # 构建角色提示词
        if character:
            system_prompt = f"你是一名叫{character.name}的{character.gender}性角色，性格{character.style}。"
            if character.role == "werewolf":
                system_prompt += "你是一名狼人，你的目标是消灭所有好人。"
            elif character.role == "seer":
                system_prompt += "你是一名预言家，你可以查验玩家的身份。"
            elif character.role == "witch":
                system_prompt += "你是一名女巫，你有一瓶解药和一瓶毒药。"
            elif character.role == "guard":
                system_prompt += "你是一名守卫，你可以保护玩家不被狼人杀害。"
            elif character.role == "villager":
                system_prompt += "你是一名普通村民，你的目标是找出并消灭所有狼人。"
        else:
            system_prompt = "你是狼人杀游戏中的一名角色。"

        # 构建请求数据
        data = {
            "model": "deepseek-chat",
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt}
            ],
            "temperature": 0.7,
            "max_tokens": 500
        }

        # 发送请求
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }

        try:
            response = requests.post(self.api_url, headers=headers, json=data)
            response.raise_for_status()
            result = response.json()
            ai_response = result["choices"][0]["message"]["content"]

            # 记录AI调用
            self._record_ai_call(character, system_prompt, prompt, ai_response, "deepseek-chat", call_type)

            return ai_response
        except Exception as e:
            print(f"Deepseek API调用失败: {str(e)}")
            fallback_response = f"这是{character.name if character else '某角色'}的回应：根据当前情况，我认为我们应该仔细思考..."

            # 记录失败的调用
            self._record_ai_call(character, system_prompt, prompt, f"[API调用失败] {fallback_response}", "deepseek-chat", call_type)

            return fallback_response

class QwenClient(AIClient):
    """Qwen模型客户端"""

    def __init__(self):
        """初始化Qwen客户端"""
        super().__init__()
        self.api_key = os.getenv("QWEN_API_KEY")
        if not self.api_key:
            raise ValueError("未设置QWEN_API_KEY环境变量")

        self.api_url = "https://dashscope.aliyuncs.com/api/v1/services/aigc/text-generation/generation"  # 示例URL，需替换为实际URL

    def generate_response(self, prompt, character=None, call_type="general"):
        """
        生成Qwen模型响应

        Args:
            prompt (str): 提示词
            character (Character, optional): 角色对象. 默认为None.
            call_type (str): 调用类型，用于调试

        Returns:
            str: AI生成的响应
        """
        # 构建角色提示词
        if character:
            system_prompt = f"你是一名叫{character.name}的{character.gender}性角色，性格{character.style}。"
            if character.role == "werewolf":
                system_prompt += "你是一名狼人，你的目标是消灭所有好人。"
            elif character.role == "seer":
                system_prompt += "你是一名预言家，你可以查验玩家的身份。"
            elif character.role == "witch":
                system_prompt += "你是一名女巫，你有一瓶解药和一瓶毒药。"
            elif character.role == "guard":
                system_prompt += "你是一名守卫，你可以保护玩家不被狼人杀害。"
            elif character.role == "villager":
                system_prompt += "你是一名普通村民，你的目标是找出并消灭所有狼人。"
        else:
            system_prompt = "你是狼人杀游戏中的一名角色。"

        # 构建请求数据
        data = {
            "model": "qwen-max",
            "input": {
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": prompt}
                ]
            },
            "parameters": {
                "temperature": 0.7,
                "max_tokens": 500
            }
        }

        # 发送请求
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }

        try:
            response = requests.post(self.api_url, headers=headers, json=data)
            response.raise_for_status()
            result = response.json()
            ai_response = result["output"]["text"]

            # 记录AI调用
            self._record_ai_call(character, system_prompt, prompt, ai_response, "qwen-max", call_type)

            return ai_response
        except Exception as e:
            print(f"Qwen API调用失败: {str(e)}")
            fallback_response = f"这是{character.name if character else '某角色'}的回应：我认为我们应该仔细分析每个人的发言..."

            # 记录失败的调用
            self._record_ai_call(character, system_prompt, prompt, f"[API调用失败] {fallback_response}", "qwen-max", call_type)

            return fallback_response

def get_ai_client(model_name):
    """
    获取指定模型的AI客户端

    Args:
        model_name (str): 模型名称

    Returns:
        AIClient: AI客户端对象
    """
    # 统一使用DeepseekClient
    return DeepseekClient()
