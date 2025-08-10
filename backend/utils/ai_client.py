#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import json
import requests
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

class DeepseekClient(AIClient):
    """Deepseek模型客户端"""

    def __init__(self):
        """初始化Deepseek客户端"""
        super().__init__()
        self.api_key = os.getenv("DEEPSEEK_API_KEY")
        if not self.api_key:
            raise ValueError("未设置DEEPSEEK_API_KEY环境变量")

        self.api_url = "https://api.deepseek.com/v1/chat/completions"  # 示例URL，需替换为实际URL

    def generate_response(self, prompt, character=None):
        """
        生成Deepseek模型响应

        Args:
            prompt (str): 提示词
            character (Character, optional): 角色对象. 默认为None.

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
            return result["choices"][0]["message"]["content"]
        except Exception as e:
            print(f"Deepseek API调用失败: {str(e)}")
            return f"这是{character.name if character else '某角色'}的回应：根据当前情况，我认为我们应该仔细思考..."

class QwenClient(AIClient):
    """Qwen模型客户端"""

    def __init__(self):
        """初始化Qwen客户端"""
        super().__init__()
        self.api_key = os.getenv("QWEN_API_KEY")
        if not self.api_key:
            raise ValueError("未设置QWEN_API_KEY环境变量")

        self.api_url = "https://dashscope.aliyuncs.com/api/v1/services/aigc/text-generation/generation"  # 示例URL，需替换为实际URL

    def generate_response(self, prompt, character=None):
        """
        生成Qwen模型响应

        Args:
            prompt (str): 提示词
            character (Character, optional): 角色对象. 默认为None.

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
            return result["output"]["text"]
        except Exception as e:
            print(f"Qwen API调用失败: {str(e)}")
            return f"这是{character.name if character else '某角色'}的回应：我认为我们应该仔细分析每个人的发言..."

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
