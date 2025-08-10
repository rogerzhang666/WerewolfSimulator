#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
模拟AI客户端，用于测试
"""

import random
from backend.utils.ai_client import AIClient

class MockAIClient(AIClient):
    """模拟AI客户端，用于测试"""

    def __init__(self):
        """初始化模拟AI客户端"""
        super().__init__()
        self.responses = {
            "werewolf": [
                "我认为这个人行为很可疑，应该是好人阵营的重要角色。",
                "这个人昨天的发言很矛盾，可能是预言家或女巫。",
                "这个人太安静了，我们需要除掉他。",
                "这个人一直在怀疑我的同伴，必须干掉他。"
            ],
            "seer": [
                "我选择查验这个人是因为他的发言很奇怪。",
                "验出狼人了！我需要在明天告诉大家。",
                "是好人，那我需要继续寻找狼人。",
                "这个人的行为很可疑，但查验结果是好人，有点意外。"
            ],
            "witch": [
                "这个人很重要，值得我使用解药。",
                "我决定不救他，因为他可能是狼人。",
                "这个人的行为很可疑，我要用毒药毒死他。",
                "我需要保留药水，等待更关键的时刻。"
            ],
            "guard": [
                "这个人可能是重要角色，需要保护。",
                "我觉得狼人今晚会袭击他，所以我选择保护他。",
                "这个人的发言表明他可能是预言家，需要我的保护。",
                "我决定保护一个不同的人，避免狼人猜到我的策略。"
            ],
            "villager": [
                "根据昨晚的情况，我怀疑这个人是狼人。",
                "我是普通村民，但我观察到一些可疑的行为。",
                "我相信那个人是好人，他的发言很有逻辑。",
                "我们应该团结起来，找出真正的狼人。"
            ],
            "discussion": [
                "我认为昨晚死的人可能是被狼人盯上的预言家。",
                "根据大家的发言，我怀疑某某可能是狼人。",
                "我是好人，请相信我，我们需要一起找出狼人。",
                "昨天的投票很奇怪，我觉得有人在故意混淆视听。",
                "我们应该关注那些保持沉默的人，他们可能是狼人。"
            ]
        }

    def generate_response(self, prompt, character=None):
        """
        生成模拟AI响应

        Args:
            prompt (str): 提示词
            character (Character, optional): 角色对象. 默认为None.

        Returns:
            str: 模拟AI生成的响应
        """
        # 根据角色和提示词选择合适的响应
        if character and character.role:
            if "讨论阶段" in prompt:
                return random.choice(self.responses["discussion"])
            elif character.role in self.responses:
                return random.choice(self.responses[character.role])

        # 默认响应
        return f"这是{character.name if character else '某角色'}的回应：我需要仔细思考当前的情况..."

# 修改AI客户端工厂函数，支持模拟客户端
def get_mock_ai_client(model_name=None):
    """
    获取模拟AI客户端

    Args:
        model_name (str, optional): 模型名称，在模拟模式下忽略

    Returns:
        MockAIClient: 模拟AI客户端对象
    """
    return MockAIClient()
