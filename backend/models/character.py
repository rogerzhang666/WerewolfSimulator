#!/usr/bin/env python
# -*- coding: utf-8 -*-

from datetime import datetime

class Character:
    """角色类，代表游戏中的一个角色"""

    def __init__(self, id, name, gender, style, model, role="", voice="longxiang"):
        """
        初始化角色

        Args:
            id (int): 角色ID
            name (str): 角色姓名
            gender (str): 角色性别
            style (str): 角色性格风格
            model (str): 驱动模型名称
            role (str, optional): 角色身份. 默认为空字符串.
            voice (str, optional): 语音音色. 默认为"longxiang".
        """
        self.id = id
        self.name = name
        self.gender = gender
        self.style = style
        self.model = model
        self.role = role
        self.voice = voice
        self.alive = True
        self.history = []  # 角色行为历史
        self.memory = {    # 角色记忆系统
            "observations": [],     # 观察到的事件
            "beliefs": {},          # 对其他角色的看法
            "decisions": [],        # 做出的决策
            "statements": [],       # 发表的公开言论
            "inner_thoughts": []    # 内心想法（不公开）
        }

    def to_dict(self):
        """
        将角色转换为字典

        Returns:
            dict: 角色信息字典
        """
        return {
            "id": self.id,
            "name": self.name,
            "gender": self.gender,
            "style": self.style,
            "model": self.model,
            "role": self.role,
            "voice": self.voice,
            "alive": self.alive
        }

    @classmethod
    def from_dict(cls, data):
        """
        从字典创建角色

        Args:
            data (dict): 角色信息字典

        Returns:
            Character: 创建的角色对象
        """
        character = cls(
            id=data.get("id"),
            name=data.get("name"),
            gender=data.get("gender"),
            style=data.get("style"),
            model=data.get("model"),
            role=data.get("role", ""),
            voice=data.get("voice", "longxiang")
        )
        character.alive = data.get("alive", True)
        return character

    def add_history(self, action, target=None, result=None):
        """
        添加角色行为历史

        Args:
            action (str): 行为描述
            target (Character, optional): 行为目标. 默认为None.
            result (str, optional): 行为结果. 默认为None.
        """
        history_entry = {
            "action": action,
            "target": target.name if target else None,
            "result": result,
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        self.history.append(history_entry)

    def add_observation(self, event, day, phase):
        """
        添加角色观察到的事件

        Args:
            event (str): 事件描述
            day (int): 游戏天数
            phase (str): 游戏阶段
        """
        observation = {
            "event": event,
            "day": day,
            "phase": phase,
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        self.memory["observations"].append(observation)

    def add_statement(self, content, day, phase):
        """
        记录角色发表的公开言论

        Args:
            content (str): 言论内容
            day (int): 游戏天数
            phase (str): 游戏阶段
        """
        statement = {
            "content": content,
            "day": day,
            "phase": phase,
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        self.memory["statements"].append(statement)

    def add_inner_thought(self, content, day, phase, thought_type="general"):
        """
        记录角色内心想法（不公开）

        Args:
            content (str): 内心想法内容
            day (int): 游戏天数
            phase (str): 游戏阶段
            thought_type (str): 想法类型（如"decision_reason", "action_reason"等）
        """
        inner_thought = {
            "content": content,
            "day": day,
            "phase": phase,
            "type": thought_type,
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        self.memory["inner_thoughts"].append(inner_thought)

    def update_belief(self, target_name, belief, confidence=0.5):
        """
        更新对其他角色的看法

        Args:
            target_name (str): 目标角色名称
            belief (str): 看法内容
            confidence (float, optional): 确信度. 默认为0.5.
        """
        if target_name not in self.memory["beliefs"]:
            self.memory["beliefs"][target_name] = []

        belief_entry = {
            "belief": belief,
            "confidence": confidence,
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        self.memory["beliefs"][target_name].append(belief_entry)

    def add_decision(self, decision_type, target_name=None, reason=None, day=None, phase=None):
        """
        记录角色做出的决策

        Args:
            decision_type (str): 决策类型（如"vote", "kill", "check"等）
            target_name (str, optional): 决策目标. 默认为None.
            reason (str, optional): 决策原因. 默认为None.
            day (int, optional): 游戏天数. 默认为None.
            phase (str, optional): 游戏阶段. 默认为None.
        """
        decision = {
            "type": decision_type,
            "target": target_name,
            "reason": reason,
            "day": day,
            "phase": phase,
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        self.memory["decisions"].append(decision)

    def get_recent_observations(self, count=5):
        """
        获取最近的观察记录

        Args:
            count (int, optional): 记录数量. 默认为5.

        Returns:
            list: 最近的观察记录列表
        """
        return self.memory["observations"][-count:] if self.memory["observations"] else []

    def get_recent_statements(self, count=3):
        """
        获取最近的公开发言记录

        Args:
            count (int, optional): 记录数量. 默认为3.

        Returns:
            list: 最近的发言记录列表
        """
        return self.memory["statements"][-count:] if self.memory["statements"] else []

    def get_recent_inner_thoughts(self, count=5, thought_type=None):
        """
        获取最近的内心想法记录

        Args:
            count (int, optional): 记录数量. 默认为5.
            thought_type (str, optional): 想法类型过滤. 默认为None（获取所有类型）.

        Returns:
            list: 最近的内心想法记录列表
        """
        thoughts = self.memory["inner_thoughts"]
        if thought_type:
            thoughts = [t for t in thoughts if t.get("type") == thought_type]
        return thoughts[-count:] if thoughts else []

    def get_beliefs_summary(self):
        """
        获取对其他角色看法的摘要

        Returns:
            dict: 对其他角色的看法摘要
        """
        summary = {}
        for target_name, beliefs in self.memory["beliefs"].items():
            if beliefs:
                # 获取最新的看法
                latest_belief = beliefs[-1]
                summary[target_name] = {
                    "belief": latest_belief["belief"],
                    "confidence": latest_belief["confidence"]
                }
        return summary

    def get_memory_summary(self):
        """
        获取角色记忆的摘要，用于AI提示词

        Returns:
            str: 记忆摘要
        """
        summary = []

        # 添加最近的观察
        recent_observations = self.get_recent_observations()
        if recent_observations:
            summary.append("最近观察到的事件:")
            for obs in recent_observations:
                summary.append(f"- 第{obs['day']}天{obs['phase']}：{obs['event']}")

        # 添加对其他角色的看法
        beliefs_summary = self.get_beliefs_summary()
        if beliefs_summary:
            summary.append("\n对其他角色的看法:")
            for target, belief_info in beliefs_summary.items():
                confidence = "非常确信" if belief_info["confidence"] > 0.8 else "比较确信" if belief_info["confidence"] > 0.5 else "不太确定"
                summary.append(f"- 对{target}：{belief_info['belief']}（{confidence}）")

        # 添加最近的发言
        recent_statements = self.get_recent_statements()
        if recent_statements:
            summary.append("\n我最近的发言:")
            for stmt in recent_statements:
                summary.append(f"- 第{stmt['day']}天：'{stmt['content']}'")

        return "\n".join(summary)

    def __str__(self):
        """字符串表示"""
        return f"{self.name} ({self.role})"
