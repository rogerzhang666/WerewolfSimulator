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
    """游戏类，管理游戏状态和流程"""

    def __init__(self):
        """初始化游戏"""
        self.characters = []          # 角色列表
        self.phase = GamePhase.SETUP  # 当前游戏阶段
        self.status = GameStatus.WAITING  # 当前游戏状态
        self.current_day = 0          # 当前天数
        self.logs = []                # 游戏日志
        self.killed_at_night = None   # 夜晚被杀的角色
        self.saved_by_witch = False   # 女巫是否使用了解药
        self.poisoned_by_witch = None # 女巫毒杀的角色
        self.protected_by_guard = None # 守卫保护的角色
        self.votes = {}               # 投票记录

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

    def log(self, source, message):
        """添加游戏日志"""
        log_entry = {
            "source": source,
            "message": message,
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "day": self.current_day,
            "phase": self.phase.value
        }
        self.logs.append(log_entry)
        return log_entry

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
