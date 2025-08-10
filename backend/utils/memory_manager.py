#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
记忆系统管理工具，用于帮助管理角色记忆
"""

class MemoryManager:
    """记忆系统管理工具类"""

    @staticmethod
    def update_werewolf_memory(werewolf, game, target=None, reason=None):
        """
        更新狼人的记忆

        Args:
            werewolf: 狼人角色
            game: 游戏对象
            target: 击杀目标
            reason: 击杀理由
        """
        # 添加狼人同伴信息
        werewolves = game.get_werewolves()
        werewolf_teammates = [w.name for w in werewolves if w.id != werewolf.id]

        # 记录同伴信息
        if werewolf_teammates:
            werewolf.add_observation(
                f"你的狼人同伴是：{', '.join(werewolf_teammates)}",
                game.current_day,
                "werewolf"
            )

        # 记录击杀决策
        if target:
            werewolf.add_decision("kill", target.name, reason, game.current_day, "werewolf")
            werewolf.add_observation(
                f"你投票击杀{target.name}" + (f"，理由：{reason}" if reason else ""),
                game.current_day,
                "werewolf"
            )

            # 记录最终决策
            werewolf.add_observation(
                f"狼人团队最终决定击杀{target.name}",
                game.current_day,
                "werewolf"
            )

    @staticmethod
    def update_seer_memory(seer, game, target, result):
        """
        更新预言家的记忆

        Args:
            seer: 预言家角色
            game: 游戏对象
            target: 查验目标
            result: 查验结果
        """
        # 记录查验决策
        seer.add_decision("check", target.name, f"查验结果：{result}", game.current_day, "seer")

        # 添加预言家的观察记录
        seer.add_observation(
            f"你查验了{target.name}，结果是{result}",
            game.current_day,
            "seer"
        )

        # 更新预言家对目标的看法
        if result == "狼人":
            seer.update_belief(target.name, "是狼人", 1.0)  # 100%确定
        else:
            seer.update_belief(target.name, "是好人", 1.0)  # 100%确定

    @staticmethod
    def update_witch_memory(witch, game, killed=None, saved=False, poisoned=None):
        """
        更新女巫的记忆

        Args:
            witch: 女巫角色
            game: 游戏对象
            killed: 被杀的角色
            saved: 是否使用解药
            poisoned: 被毒的角色
        """
        # 记录被杀信息
        if killed:
            witch.add_observation(
                f"你看到{killed.name}被狼人杀害",
                game.current_day,
                "witch"
            )

        # 记录救人决策
        if saved and killed:
            witch.add_decision("save", killed.name, None, game.current_day, "witch")
            witch.add_observation(
                f"你使用解药救了{killed.name}",
                game.current_day,
                "witch"
            )
        elif killed:
            witch.add_observation(
                f"你选择不使用解药救{killed.name}",
                game.current_day,
                "witch"
            )

        # 记录毒人决策
        if poisoned:
            witch.add_decision("poison", poisoned.name, None, game.current_day, "witch")
            witch.add_observation(
                f"你使用毒药毒死了{poisoned.name}",
                game.current_day,
                "witch"
            )

    @staticmethod
    def update_guard_memory(guard, game, target):
        """
        更新守卫的记忆

        Args:
            guard: 守卫角色
            game: 游戏对象
            target: 保护目标
        """
        # 记录保护决策
        guard.add_decision("protect", target.name, None, game.current_day, "guard")
        guard.add_observation(
            f"你保护了{target.name}",
            game.current_day,
            "guard"
        )

    @staticmethod
    def update_discussion_memory(character, game, statement, alive_characters):
        """
        更新讨论阶段的记忆

        Args:
            character: 角色
            game: 游戏对象
            statement: 发言内容
            alive_characters: 存活角色列表
        """
        # 记录自己的发言
        character.add_statement(statement, game.current_day, "discussion")

        # 分析发言，更新对其他角色的看法
        for other in alive_characters:
            if other.id != character.id and other.name in statement:
                # 简单的情感分析，检测是否表达了怀疑
                if any(word in statement for word in ["怀疑", "可疑", "狼人", "不信任"]):
                    character.update_belief(other.name, "可能是狼人", 0.6)
                elif any(word in statement for word in ["信任", "好人", "相信"]):
                    character.update_belief(other.name, "可能是好人", 0.6)

    @staticmethod
    def update_vote_memory(voter, game, target, reason):
        """
        更新投票阶段的记忆

        Args:
            voter: 投票者
            game: 游戏对象
            target: 投票目标
            reason: 投票理由
        """
        # 记录投票决策
        voter.add_decision("vote", target.name, reason, game.current_day, "vote")
        voter.add_observation(
            f"你投票给了{target.name}" + (f"，理由：{reason}" if reason else ""),
            game.current_day,
            "vote"
        )

    @staticmethod
    def get_role_specific_context(character, game):
        """
        获取角色特定的上下文信息

        Args:
            character: 角色
            game: 游戏对象

        Returns:
            str: 角色特定的上下文信息
        """
        context = ""

        if character.role == "werewolf":
            # 狼人知道其他狼人
            werewolves = [c.name for c in game.get_werewolves() if c.id != character.id]
            context += f"- 你的狼人同伴是：{', '.join(werewolves) if werewolves else '没有其他狼人'}\n"

            # 添加之前的击杀记录
            wolf_kills = [d for d in character.memory["decisions"] if d["type"] == "kill"]
            if wolf_kills:
                context += "- 你们之前的击杀记录：\n"
                for kill in wolf_kills:
                    context += f"  - 第{kill['day']}天击杀{kill['target']}：{kill['reason'] if kill['reason'] else '无理由'}\n"

        elif character.role == "seer":
            # 添加预言家的查验历史
            seer_checks = [d for d in character.memory["decisions"] if d["type"] == "check"]
            if seer_checks:
                context += "- 你的查验历史：\n"
                for check in seer_checks:
                    context += f"  - 第{check['day']}天查验{check['target']}：{check['reason']}\n"

        elif character.role == "witch":
            # 添加女巫的使用药水历史和状态
            witch_saves = [d for d in character.memory["decisions"] if d["type"] == "save"]
            witch_poisons = [d for d in character.memory["decisions"] if d["type"] == "poison"]
            context += f"- 你已使用解药：{'是' if game.witch_used_save else '否'}\n"
            context += f"- 你已使用毒药：{'是' if game.witch_used_poison else '否'}\n"
            if witch_saves:
                context += f"- 你在第{witch_saves[0]['day']}天使用解药救了{witch_saves[0]['target']}\n"
            if witch_poisons:
                context += f"- 你在第{witch_poisons[0]['day']}天使用毒药毒死了{witch_poisons[0]['target']}\n"

        elif character.role == "guard":
            # 添加守卫的保护历史
            guard_protects = [d for d in character.memory["decisions"] if d["type"] == "protect"]
            if guard_protects:
                context += "- 你的保护历史：\n"
                for protect in guard_protects:
                    context += f"  - 第{protect['day']}天保护了{protect['target']}\n"

        return context
