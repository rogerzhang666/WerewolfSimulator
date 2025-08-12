#!/usr/bin/env python
# -*- coding: utf-8 -*-

import random
from enum import Enum
from datetime import datetime

class GamePhase(Enum):
    """游戏阶段枚举"""
    SETUP = "setup"           # 游戏设置阶段
    NIGHT = "night"           # 夜晚阶段
    WEREWOLF = "werewolf"     # 狼人行动阶段
    SEER = "seer"             # 预言家行动阶段
    WITCH = "witch"           # 女巫行动阶段
    GUARD = "guard"           # 守卫行动阶段
    DAWN = "dawn"             # 天亮阶段
    DISCUSSION = "discussion" # 讨论阶段
    VOTE = "vote"             # 投票阶段
    END = "end"               # 游戏结束阶段

class GameStatus(Enum):
    """游戏状态枚举"""
    WAITING = "waiting"       # 等待开始
    RUNNING = "running"       # 游戏进行中
    PAUSED = "paused"         # 游戏暂停
    FINISHED = "finished"     # 游戏结束

class Game:
    """游戏类，负责管理游戏状态和角色"""

    def __init__(self):
        """初始化游戏"""
        self.characters = []  # 角色列表
        self.current_day = 0  # 当前天数
        self.phase = GamePhase.SETUP  # 当前游戏阶段
        self.status = GameStatus.WAITING  # 当前游戏状态
        self.logs = []  # 游戏日志
        self.votes = {}  # 投票记录
        self.killed_at_night = None  # 夜晚被杀的角色
        self.saved_by_witch = False  # 是否被女巫救
        self.poisoned_by_witch = None  # 被女巫毒死的角色
        self.protected_by_guard = None  # 被守卫保护的角色
        self.witch_used_save = False  # 女巫是否已使用解药
        self.witch_used_poison = False  # 女巫是否已使用毒药

    def add_character(self, character):
        """添加角色到游戏"""
        self.characters.append(character)

    def assign_roles(self):
        """随机分配角色身份"""
        roles = ["werewolf", "werewolf", "seer", "witch"] + ["villager"] * 4
        random.shuffle(roles)

        for i, character in enumerate(self.characters):
            character.role = roles[i]

        self.log("系统", "角色身份已分配")

    def start_game(self):
        """开始游戏"""
        if len(self.characters) != 8:
            raise ValueError("游戏需要8名角色才能开始")

        self.assign_roles()
        self.status = GameStatus.RUNNING
        self.current_day = 1
        self.phase = GamePhase.NIGHT
        self.log("系统", f"游戏开始，当前为第{self.current_day}天夜晚")

        return True

    def next_phase(self):
        """进入下一个游戏阶段"""
        phase_order = [
            GamePhase.NIGHT,
            GamePhase.WEREWOLF,
            GamePhase.SEER,
            GamePhase.WITCH,
            GamePhase.GUARD,
            GamePhase.DAWN,
            GamePhase.DISCUSSION,
            GamePhase.VOTE,
        ]

        current_index = phase_order.index(self.phase)
        next_index = (current_index + 1) % len(phase_order)
        self.phase = phase_order[next_index]

        # 如果是新的一天
        if self.phase == GamePhase.NIGHT:
            self.current_day += 1
            self.log("系统", f"第{self.current_day}天夜晚降临")

        # 检查游戏是否结束
        if self.check_game_over():
            self.phase = GamePhase.END
            self.status = GameStatus.FINISHED

        return self.phase

    def check_game_over(self):
        """检查游戏是否结束"""
        werewolf_count = 0
        villager_count = 0

        for character in self.characters:
            if not character.alive:
                continue

            if character.role == "werewolf":
                werewolf_count += 1
            else:
                villager_count += 1

        # 狼人全部出局，好人胜利
        if werewolf_count == 0:
            self.log("系统", "游戏结束，好人阵营胜利！")
            return True

        # 狼人数量大于等于好人，狼人胜利
        if werewolf_count >= villager_count:
            self.log("系统", "游戏结束，狼人阵营胜利！")
            return True

        return False

    def log(self, source, message, phase=None, is_public=True, message_type="system", ai_call_ids=None):
        """
        记录游戏日志

        Args:
            source (str): 消息来源
            message (str): 消息内容
            phase (str, optional): 游戏阶段. 默认为None.
            is_public (bool, optional): 是否为公开信息. 默认为True.
            message_type (str, optional): 消息类型. 可选值:
                - "system": 系统信息
                - "public_statement": 公开发言
                - "inner_thought": 内心想法
                - "action": 角色行动
            ai_call_ids (list, optional): 关联的AI调用记录ID列表. 默认为None.
        """
        log_entry = {
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "day": self.current_day,
            "phase": phase or self.phase.value,
            "source": source,
            "message": message,
            "is_public": is_public,
            "message_type": message_type,
            "ai_call_ids": ai_call_ids or []
        }
        self.logs.append(log_entry)

        # 打印日志（可选）
        print(f"[{log_entry['timestamp']}] [{self.current_day}天-{log_entry['phase']}] {source}: {message}")

    def get_alive_characters(self):
        """获取所有存活的角色"""
        return [c for c in self.characters if c.alive]

    def get_werewolves(self):
        """获取所有存活的狼人"""
        return [c for c in self.characters if c.alive and c.role == "werewolf"]

    def get_character_by_role(self, role):
        """获取指定身份的角色"""
        for character in self.characters:
            if character.alive and character.role == role:
                return character
        return None

    def to_dict(self):
        """将游戏转换为字典"""
        return {
            "characters": [c.to_dict() for c in self.characters],
            "phase": self.phase.value,
            "status": self.status.value,
            "current_day": self.current_day,
            "logs": self.logs
        }
