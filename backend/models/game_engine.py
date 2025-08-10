#!/usr/bin/env python
# -*- coding: utf-8 -*-

import time
import threading
import json
import random
from datetime import datetime

from backend.models.game import Game, GamePhase, GameStatus
from backend.models.character import Character
from backend.utils.ai_client import get_ai_client
from backend.utils.prompt_templates import *  # 导入提示词模板
from backend.utils.memory_manager import MemoryManager  # 导入记忆管理器

class GameEngine:
    """游戏引擎类，负责管理游戏流程和AI交互"""

    def __init__(self, socketio=None):
        """
        初始化游戏引擎

        Args:
            socketio: SocketIO实例，用于实时通信
        """
        self.game = Game()
        self.socketio = socketio
        self.game_thread = None
        self.running = False
        self.ai_clients = {}  # 存储角色的AI客户端

    def load_characters_from_config(self, config_file):
        """
        从配置文件加载角色

        Args:
            config_file (str): 配置文件路径
        """
        try:
            with open(config_file, 'r', encoding='utf-8') as f:
                characters_data = json.load(f)

            for data in characters_data:
                character = Character.from_dict(data)
                self.game.add_character(character)
                # 为每个角色创建AI客户端
                self.ai_clients[character.id] = get_ai_client(character.model)

            return True
        except Exception as e:
            print(f"加载角色配置失败: {str(e)}")
            return False

    def start_game(self):
        """启动游戏"""
        if self.game.status != GameStatus.WAITING:
            return False

        try:
            self.game.start_game()
            self.running = True
            # 在新线程中运行游戏循环
            self.game_thread = threading.Thread(target=self.game_loop)
            self.game_thread.daemon = True
            self.game_thread.start()
            return True
        except Exception as e:
            print(f"启动游戏失败: {str(e)}")
            return False

    def pause_game(self):
        """暂停游戏"""
        if self.game.status != GameStatus.RUNNING:
            return False

        self.game.status = GameStatus.PAUSED
        self.running = False
        self.emit_game_update("游戏已暂停")
        return True

    def resume_game(self):
        """恢复游戏"""
        if self.game.status != GameStatus.PAUSED:
            return False

        self.game.status = GameStatus.RUNNING
        self.running = True
        # 在新线程中运行游戏循环
        self.game_thread = threading.Thread(target=self.game_loop)
        self.game_thread.daemon = True
        self.game_thread.start()
        self.emit_game_update("游戏已恢复")
        return True

    def reset_game(self):
        """重置游戏"""
        self.running = False
        if self.game_thread and self.game_thread.is_alive():
            self.game_thread.join(timeout=1.0)

        self.game = Game()
        self.emit_game_update("游戏已重置")
        return True

    def game_loop(self):
        """游戏主循环"""
        while self.running and self.game.status == GameStatus.RUNNING:
            # 处理当前阶段
            self.handle_current_phase()

            # 检查游戏是否结束
            if self.game.phase == GamePhase.END:
                self.running = False
                self.emit_game_update("游戏结束")
                break

            # 进入下一阶段
            next_phase = self.game.next_phase()
            self.emit_game_update(f"进入{next_phase.value}阶段")

            # 根据阶段设置等待时间
            if next_phase in [GamePhase.NIGHT, GamePhase.DAWN]:
                time.sleep(2)  # 短暂过渡
            elif next_phase == GamePhase.DISCUSSION:
                time.sleep(5)  # 讨论阶段较长
            else:
                time.sleep(3)  # 其他阶段

    def handle_current_phase(self):
        """处理当前游戏阶段"""
        phase = self.game.phase

        if phase == GamePhase.NIGHT:
            self.handle_night_phase()
        elif phase == GamePhase.WEREWOLF:
            self.handle_werewolf_phase()
        elif phase == GamePhase.SEER:
            self.handle_seer_phase()
        elif phase == GamePhase.WITCH:
            self.handle_witch_phase()
        elif phase == GamePhase.GUARD:
            self.handle_guard_phase()
        elif phase == GamePhase.DAWN:
            self.handle_dawn_phase()
        elif phase == GamePhase.DISCUSSION:
            self.handle_discussion_phase()
        elif phase == GamePhase.VOTE:
            self.handle_vote_phase()

    def handle_night_phase(self):
        """处理夜晚阶段"""
        self.game.log("系统", f"第{self.game.current_day}天夜晚开始，天黑请闭眼")
        self.emit_game_update("夜晚开始，天黑请闭眼")

        # 重置夜晚状态
        self.game.killed_at_night = None
        self.game.saved_by_witch = False
        self.game.poisoned_by_witch = None
        self.game.protected_by_guard = None

    def handle_werewolf_phase(self):
        """处理狼人行动阶段"""
        werewolves = self.game.get_werewolves()
        if not werewolves:
            return

        # 获取所有存活的非狼人角色
        targets = [c for c in self.game.get_alive_characters() if c.role != "werewolf"]
        if not targets:
            return

        # 狼人讨论决定击杀目标
        # 收集每个狼人的意见
        wolf_votes = {}
        wolf_reasons = {}

        for werewolf in werewolves:
            # 构建狼人的上下文信息
            context = self.build_character_context(werewolf)

            werewolf_teammates = [w.name for w in werewolves if w.id != werewolf.id]

            if wolf_votes:
                context += "\n你的狼人同伴已经投票：\n"
                for target_name, votes in wolf_votes.items():
                    context += f"- {target_name}：{votes}票\n"
                if wolf_reasons:
                    for target_name, reason in wolf_reasons.items():
                        context += f"- 击杀{target_name}的理由：{reason}\n"

            # 使用新的提示词模板
            prompt = WEREWOLF_KILL_TEMPLATE.format(
                alive_players=', '.join([c.name for c in self.game.get_alive_characters()]),
                werewolf_teammates=', '.join(werewolf_teammates) if werewolf_teammates else "没有其他狼人",
                targets=', '.join([c.name for c in targets]),
                context=context
            )

            try:
                ai_client = self.ai_clients.get(werewolf.id)
                if ai_client:
                    # 获取狼人的击杀决策
                    kill_decision = ai_client.generate_response(prompt, werewolf, "werewolf_kill").strip()

                    # 解析击杀决策，找到对应的目标角色
                    target = None
                    for t in targets:
                        if t.name in kill_decision:
                            target = t
                            break

                    # 如果无法解析或没有找到匹配的目标，随机选择一个
                    if not target:
                        target = random.choice(targets)
                        print(f"警告: {werewolf.name}的击杀决策'{kill_decision}'无法解析，随机选择了{target.name}")

                    # 记录狼人投票
                    if target.name not in wolf_votes:
                        wolf_votes[target.name] = 0
                    wolf_votes[target.name] += 1

                    # 生成击杀理由
                    reason_prompt = WEREWOLF_KILL_REASON_TEMPLATE.format(target=target.name)

                    try:
                        kill_reason = ai_client.generate_response(reason_prompt, werewolf, "werewolf_kill_reason")
                        wolf_reasons[target.name] = kill_reason

                        # 更新狼人记忆
                        MemoryManager.update_werewolf_memory(werewolf, self.game, target, kill_reason)
                    except Exception as e:
                        print(f"生成击杀理由失败: {str(e)}")
            except Exception as e:
                print(f"生成狼人决策失败: {str(e)}")

        # 确定最终击杀目标（得票最多的）
        if wolf_votes:
            max_votes = max(wolf_votes.values())
            candidates = [name for name, votes in wolf_votes.items() if votes == max_votes]
            target_name = random.choice(candidates)
            target = next((t for t in targets if t.name == target_name), None)

            if target:
                self.game.killed_at_night = target

                # 记录狼人行动
                for werewolf in werewolves:
                    self.game.log(werewolf.name, f"狼人选择了{target.name}作为击杀目标")

                    # 如果有该目标的理由，记录理由
                    if target.name in wolf_reasons:
                        self.game.log(werewolf.name, wolf_reasons[target.name])

        self.emit_game_update("狼人正在行动")

    def handle_seer_phase(self):
        """处理预言家行动阶段"""
        seer = self.game.get_character_by_role("seer")
        if not seer or not seer.alive:
            # 不要公开说"预言家不在场或已死亡"
            return

        # 获取所有存活的角色（除了预言家自己）
        targets = [c for c in self.game.get_alive_characters() if c.id != seer.id]
        if not targets:
            return

        # 构建预言家的上下文信息
        context = self.build_character_context(seer)

        # 添加预言家特有的信息：之前的查验结果
        seer_checks = [d for d in seer.memory["decisions"] if d["type"] == "check"]
        if seer_checks:
            context += "\n你之前的查验结果：\n"
            for check in seer_checks:
                context += f"- 第{check['day']}天查验{check['target']}：{check['reason']}\n"

        # 排除已经查验过的目标
        checked_targets = [d["target"] for d in seer_checks]
        unchecked_targets = [t for t in targets if t.name not in checked_targets]

        # 如果所有人都查验过了，允许重复查验
        if not unchecked_targets:
            unchecked_targets = targets
            context += "\n你已经查验过所有存活的玩家，可以选择重新查验某人。\n"
        else:
            context += "\n你还没有查验过以下玩家：" + ", ".join([t.name for t in unchecked_targets]) + "\n"

        # 使用新的提示词模板
        prompt = SEER_CHECK_TEMPLATE.format(
            alive_players=', '.join([c.name for c in self.game.get_alive_characters()]),
            targets=', '.join([t.name for t in unchecked_targets]),
            context=context
        )

        try:
            ai_client = self.ai_clients.get(seer.id)
            if ai_client:
                # 获取预言家的查验决策
                check_decision = ai_client.generate_response(prompt, seer, "seer_check").strip()

                # 解析查验决策，找到对应的目标角色
                target = None
                for t in unchecked_targets:
                    if t.name in check_decision:
                        target = t
                        break

                # 如果无法解析或没有找到匹配的目标，随机选择一个
                if not target:
                    target = random.choice(unchecked_targets)
                    print(f"警告: {seer.name}的查验决策'{check_decision}'无法解析，随机选择了{target.name}")

                # 执行查验
                is_werewolf = target.role == "werewolf"
                result = "狼人" if is_werewolf else "好人"

                # 只记录预言家自己的日志，不公开
                self.game.log(seer.name, f"预言家查验了{target.name}，结果是{result}")

                # 更新预言家记忆
                MemoryManager.update_seer_memory(seer, self.game, target, result)

                # 生成查验理由
                reason_prompt = SEER_CHECK_REASON_TEMPLATE.format(target=target.name, result=result)

                try:
                    check_reason = ai_client.generate_response(reason_prompt, seer, "seer_check_reason")
                    self.game.log(seer.name, check_reason)

                    # 更新决策原因
                    for decision in seer.memory["decisions"]:
                        if (decision["type"] == "check" and
                            decision["target"] == target.name and
                            decision["day"] == self.game.current_day):
                            decision["reason"] = f"查验结果：{result}，理由：{check_reason}"
                            break
                except Exception as e:
                    print(f"生成查验理由失败: {str(e)}")
        except Exception as e:
            print(f"生成预言家决策失败: {str(e)}")

        self.emit_game_update("预言家正在行动")

    def handle_witch_phase(self):
        """处理女巫行动阶段"""
        witch = self.game.get_character_by_role("witch")
        if not witch or not witch.alive:
            return

        # 获取夜晚被杀的角色
        killed = self.game.killed_at_night

        # 构建女巫的上下文信息
        context = self.build_character_context(witch)

        # 女巫决定是否使用解药
        if killed and not self.game.witch_used_save:
            # 添加女巫特有的信息：她知道谁被杀了
            context += f"\n今晚{killed.name}被狼人杀害了。你可以选择使用解药救活他，或者不使用解药。\n"

            # 使用新的提示词模板
            save_prompt = WITCH_SAVE_TEMPLATE.format(
                alive_players=', '.join([c.name for c in self.game.get_alive_characters()]),
                killed=killed.name,
                context=context
            )

            try:
                ai_client = self.ai_clients.get(witch.id)
                if ai_client:
                    # 获取女巫的救人决策
                    save_decision = ai_client.generate_response(save_prompt, witch, "witch_save").strip().lower()

                    # 解析救人决策
                    use_save = "救" in save_decision

                    if use_save:
                        self.game.saved_by_witch = True
                        self.game.witch_used_save = True  # 标记解药已使用
                        self.game.log(witch.name, f"女巫使用解药救了{killed.name}")

                        # 更新女巫记忆
                        MemoryManager.update_witch_memory(witch, self.game, killed, True)

                        # 生成救人理由
                        reason_prompt = WITCH_SAVE_REASON_TEMPLATE.format(target=killed.name)

                        try:
                            save_reason = ai_client.generate_response(reason_prompt, witch, "witch_save_reason")
                            self.game.log(witch.name, save_reason)

                            # 更新决策原因
                            for decision in witch.memory["decisions"]:
                                if (decision["type"] == "save" and
                                    decision["target"] == killed.name and
                                    decision["day"] == self.game.current_day):
                                    decision["reason"] = save_reason
                                    break
                        except Exception as e:
                            print(f"生成救人理由失败: {str(e)}")
                    else:
                        # 即使不救，女巫也知道谁被杀了
                        MemoryManager.update_witch_memory(witch, self.game, killed, False)
            except Exception as e:
                print(f"生成女巫救人决策失败: {str(e)}")

        # 女巫决定是否使用毒药
        if not self.game.witch_used_poison:
            # 使用新的提示词模板
            poison_prompt = WITCH_POISON_TEMPLATE.format(
                alive_players=', '.join([c.name for c in self.game.get_alive_characters()]),
                context=context
            )

            try:
                ai_client = self.ai_clients.get(witch.id)
                if ai_client:
                    # 获取女巫的毒人决策
                    poison_decision = ai_client.generate_response(poison_prompt, witch, "witch_poison").strip()

                    # 解析毒人决策
                    if "不使用" not in poison_decision:
                        # 获取所有存活的角色（除了女巫自己）
                        targets = [c for c in self.game.get_alive_characters() if c.id != witch.id]

                        # 查找目标
                        target = None
                        for t in targets:
                            if t.name in poison_decision:
                                target = t
                                break

                        if target:
                            # 安全检查：确保女巫不会毒死预言家或其他好人阵营的关键角色
                            if target.role == "seer":
                                self.game.log("系统", "女巫犹豫了，决定不使用毒药")
                                print(f"警告: 女巫试图毒死预言家{target.name}，系统阻止了这一行为")
                            elif target.role != "werewolf" and random.random() < 0.8:  # 80%的概率阻止毒死好人
                                self.game.log("系统", "女巫犹豫了，决定不使用毒药")
                                print(f"警告: 女巫试图毒死好人{target.name}，系统阻止了这一行为")
                            else:
                                self.game.poisoned_by_witch = target
                                self.game.witch_used_poison = True  # 标记毒药已使用
                                self.game.log(witch.name, f"女巫使用毒药毒死了{target.name}")

                                # 更新女巫记忆
                                MemoryManager.update_witch_memory(witch, self.game, None, False, target)

                                # 生成毒人理由
                                reason_prompt = WITCH_POISON_REASON_TEMPLATE.format(target=target.name)

                                try:
                                    poison_reason = ai_client.generate_response(reason_prompt, witch, "witch_poison_reason")
                                    self.game.log(witch.name, poison_reason)

                                    # 更新决策原因
                                    for decision in witch.memory["decisions"]:
                                        if (decision["type"] == "poison" and
                                            decision["target"] == target.name and
                                            decision["day"] == self.game.current_day):
                                            decision["reason"] = poison_reason
                                            break
                                except Exception as e:
                                    print(f"生成毒人理由失败: {str(e)}")
            except Exception as e:
                print(f"生成女巫毒人决策失败: {str(e)}")

        self.emit_game_update("女巫正在行动")

    def handle_guard_phase(self):
        """处理守卫行动阶段"""
        guard = self.game.get_character_by_role("guard")
        if not guard or not guard.alive:
            # 不要公开说"守卫不在场或已死亡"
            return

        # 获取所有存活的角色
        targets = self.game.get_alive_characters()
        if not targets:
            return

        # 构建守卫的上下文信息
        context = self.build_character_context(guard)

        # 使用新的提示词模板
        prompt = GUARD_PROTECT_TEMPLATE.format(
            alive_players=', '.join([c.name for c in self.game.get_alive_characters()]),
            targets=', '.join([c.name for c in targets]),
            context=context
        )

        try:
            ai_client = self.ai_clients.get(guard.id)
            if ai_client:
                # 获取守卫的保护决策
                protect_decision = ai_client.generate_response(prompt, guard, "guard_protect").strip()

                # 解析保护决策，找到对应的目标角色
                target = None
                for t in targets:
                    if t.name in protect_decision:
                        target = t
                        break

                # 如果无法解析或没有找到匹配的目标，随机选择一个
                if not target:
                    target = random.choice(targets)
                    print(f"警告: {guard.name}的保护决策'{protect_decision}'无法解析，随机选择了{target.name}")

                # 检查是否连续两晚保护同一个人
                last_protect = None
                for decision in reversed(guard.memory["decisions"]):
                    if decision["type"] == "protect" and decision["day"] == self.game.current_day - 1:
                        last_protect = decision["target"]
                        break

                # 如果连续两晚保护同一个人，随机选择另一个人
                if last_protect == target.name:
                    other_targets = [t for t in targets if t.name != target.name]
                    if other_targets:
                        target = random.choice(other_targets)
                        print(f"守卫不能连续两晚保护同一个人，改为保护{target.name}")

                self.game.protected_by_guard = target
                self.game.log(guard.name, f"守卫保护了{target.name}")

                # 更新守卫记忆
                MemoryManager.update_guard_memory(guard, self.game, target)

                # 生成保护理由
                reason_prompt = GUARD_PROTECT_REASON_TEMPLATE.format(target=target.name)

                try:
                    protect_reason = ai_client.generate_response(reason_prompt, guard, "guard_protect_reason")
                    self.game.log(guard.name, protect_reason)

                    # 更新决策原因
                    for decision in guard.memory["decisions"]:
                        if (decision["type"] == "protect" and
                            decision["target"] == target.name and
                            decision["day"] == self.game.current_day):
                            decision["reason"] = protect_reason
                            break
                except Exception as e:
                    print(f"生成保护理由失败: {str(e)}")
        except Exception as e:
            print(f"生成守卫决策失败: {str(e)}")

        self.emit_game_update("守卫正在行动")

    def handle_dawn_phase(self):
        """处理天亮阶段"""
        self.game.log("系统", f"第{self.game.current_day}天，天亮了")
        self.emit_game_update("天亮了")

        # 处理夜晚的结果
        killed = self.game.killed_at_night
        saved = self.game.saved_by_witch
        poisoned = self.game.poisoned_by_witch
        protected = self.game.protected_by_guard

        # 处理被杀角色
        if killed and not saved and killed != protected:
            killed.alive = False
            self.game.log("系统", f"{killed.name}在夜晚被杀害")
            self.emit_game_update(f"{killed.name}在夜晚被杀害")

        # 处理被毒角色
        if poisoned:
            poisoned.alive = False
            self.game.log("系统", f"{poisoned.name}被毒死")
            self.emit_game_update(f"{poisoned.name}被毒死")

        # 如果没有人死亡
        if (not killed or saved or killed == protected) and not poisoned:
            self.game.log("系统", "平安夜，没有人死亡")
            self.emit_game_update("平安夜，没有人死亡")

    def handle_discussion_phase(self):
        """处理讨论阶段"""
        self.game.log("系统", "开始讨论")
        self.emit_game_update("开始讨论")

        # 获取所有存活的角色
        alive_characters = self.game.get_alive_characters()

        # 确定发言顺序：从最近死亡的玩家的下一位开始
        start_index = 0

        # 获取最近死亡的玩家
        recent_deaths = [c for c in self.game.characters if not c.alive]
        if recent_deaths:
            # 找出最近一个死亡的玩家
            last_death = recent_deaths[-1]

            # 找出这个玩家在原始角色列表中的位置
            all_characters = self.game.characters
            for i, c in enumerate(all_characters):
                if c.id == last_death.id:
                    # 从死者的下一位开始
                    start_index = (i + 1) % len(all_characters)
                    break

        # 重新排序存活角色，从start_index开始
        all_characters = self.game.characters
        ordered_alive = []

        # 从start_index开始，按顺序添加存活角色
        for i in range(len(all_characters)):
            idx = (start_index + i) % len(all_characters)
            character = all_characters[idx]
            if character.alive:
                ordered_alive.append(character)

        # 每个角色按新顺序发表言论
        for character in ordered_alive:
            # 构建角色的上下文信息
            context = self.build_character_context(character)

            # 获取角色特定的讨论指导
            role_guidance = ROLE_DISCUSSION_GUIDANCE.get(character.role, ROLE_DISCUSSION_GUIDANCE["villager"])

            # 使用新的提示词模板
            prompt = DISCUSSION_TEMPLATE.format(
                day=self.game.current_day,
                alive_players=', '.join([c.name for c in alive_characters]),
                dead_players=', '.join([c.name for c in self.game.characters if not c.alive]),
                context=context,
                role_specific_guidance=role_guidance
            )

            try:
                ai_client = self.ai_clients.get(character.id)
                if ai_client:
                    response = ai_client.generate_response(prompt, character, "discussion")

                    # 记录角色发言到游戏日志
                    self.game.log(character.name, response)
                    self.emit_game_update(f"{character.name}发言: {response}")

                    # 更新角色记忆
                    MemoryManager.update_discussion_memory(character, self.game, response, alive_characters)

                    # 为其他角色添加观察记录
                    for observer in alive_characters:
                        if observer.id != character.id:
                            observer.add_observation(
                                f"{character.name}说：{response}",
                                self.game.current_day,
                                "discussion"
                            )

                    time.sleep(2)  # 角色发言间隔
            except Exception as e:
                print(f"生成角色发言失败: {str(e)}")
                self.game.log(character.name, "（发言系统故障）")

    def handle_vote_phase(self):
        """处理投票阶段"""
        self.game.log("系统", "开始投票")
        self.emit_game_update("开始投票")

        # 获取所有存活的角色
        alive_characters = self.game.get_alive_characters()
        if len(alive_characters) <= 2:
            self.game.log("系统", "存活角色不足，跳过投票")
            return

        # 清空投票记录
        self.game.votes = {}

        # 每个角色进行投票
        for voter in alive_characters:
            # 可投票的目标（除了自己）
            targets = [c for c in alive_characters if c.id != voter.id]

            # 构建角色的上下文信息
            context = self.build_character_context(voter)

            # 获取角色特定的投票指导
            role_guidance = ROLE_VOTE_GUIDANCE.get(voter.role, ROLE_VOTE_GUIDANCE["villager"])

            # 使用新的提示词模板
            prompt = VOTE_TEMPLATE.format(
                day=self.game.current_day,
                alive_players=', '.join([c.name for c in alive_characters]),
                targets=', '.join([c.name for c in targets]),
                context=context,
                role_specific_guidance=role_guidance
            )

            try:
                ai_client = self.ai_clients.get(voter.id)
                if ai_client:
                    # 获取AI的投票决策
                    vote_decision = ai_client.generate_response(prompt, voter, "vote").strip()

                    # 解析投票决策，找到对应的目标角色
                    target = None
                    for t in targets:
                        if t.name in vote_decision:
                            target = t
                            break

                    # 如果无法解析或没有找到匹配的目标，随机选择一个
                    if not target:
                        target = random.choice(targets)
                        print(f"警告: {voter.name}的投票决策'{vote_decision}'无法解析，随机选择了{target.name}")

                    # 狼人不应该投票给狼人同伴（除非是为了伪装）
                    if voter.role == "werewolf" and target.role == "werewolf" and random.random() < 0.8:  # 80%的概率阻止狼人互投
                        non_werewolf_targets = [t for t in targets if t.role != "werewolf"]
                        if non_werewolf_targets:
                            target = random.choice(non_werewolf_targets)
                            print(f"警告: 狼人{voter.name}试图投票给狼人同伴{target.name}，系统调整为投票给{target.name}")

                    # 记录投票
                    if target.id not in self.game.votes:
                        self.game.votes[target.id] = 0
                    self.game.votes[target.id] += 1

                    self.game.log(voter.name, f"投票给了{target.name}")
                    self.emit_game_update(f"{voter.name}投票给了{target.name}")

                    # 生成投票理由
                    reason_prompt = VOTE_REASON_TEMPLATE.format(target=target.name)

                    try:
                         vote_reason = ai_client.generate_response(reason_prompt, voter, "vote_reason")
                        self.game.log(voter.name, vote_reason)

                        # 更新投票记忆
                        MemoryManager.update_vote_memory(voter, self.game, target, vote_reason)

                        # 为其他角色添加观察记录
                        for observer in alive_characters:
                            if observer.id != voter.id:
                                observer.add_observation(
                                    f"{voter.name}投票给了{target.name}，理由：{vote_reason}",
                                    self.game.current_day,
                                    "vote"
                                )
                    except Exception as e:
                        print(f"生成投票理由失败: {str(e)}")

            except Exception as e:
                print(f"生成投票决策失败: {str(e)}")
                # 出错时随机选择
                target = random.choice(targets)
                if target.id not in self.game.votes:
                    self.game.votes[target.id] = 0
                self.game.votes[target.id] += 1
                self.game.log(voter.name, f"投票给了{target.name}")
                self.emit_game_update(f"{voter.name}投票给了{target.name}")

        # 计算投票结果
        if self.game.votes:
            # 找出得票最多的玩家
            max_votes = max(self.game.votes.values())
            candidates = [cid for cid, votes in self.game.votes.items() if votes == max_votes]

            # 如果有平票，随机选择一个
            voted_id = random.choice(candidates)
            voted_character = next((c for c in alive_characters if c.id == voted_id), None)

            if voted_character:
                voted_character.alive = False
                self.game.log("系统", f"{voted_character.name}被投票处决")
                self.emit_game_update(f"{voted_character.name}被投票处决，得票{max_votes}票")

                # 为所有角色添加观察记录
                for character in alive_characters:
                    character.add_observation(
                        f"{voted_character.name}被投票处决，得票{max_votes}票",
                        self.game.current_day,
                        "vote_result"
                    )

                # 如果被处决的是猎人，触发猎人技能
                if voted_character.role == "hunter":
                    self.handle_hunter_skill(voted_character)

    def handle_hunter_skill(self, hunter):
        """处理猎人技能"""
        self.game.log("系统", f"猎人{hunter.name}发动技能")
        self.emit_game_update(f"猎人{hunter.name}发动技能")

        # 获取所有存活的角色
        targets = self.game.get_alive_characters()
        if not targets:
            self.game.log("系统", "没有可带走的目标")
            return

        # 构建猎人的上下文信息
        context = self.build_character_context(hunter)

        # 使用新的提示词模板
        prompt = HUNTER_SKILL_TEMPLATE.format(
            alive_players=', '.join([c.name for c in targets]),
            context=context
        )

        try:
            ai_client = self.ai_clients.get(hunter.id)
            if ai_client:
                # 获取猎人的决策
                skill_decision = ai_client.generate_response(prompt, hunter, "hunter_skill").strip()

                # 解析决策，找到对应的目标角色
                target = None
                for t in targets:
                    if t.name in skill_decision:
                        target = t
                        break

                # 如果无法解析或没有找到匹配的目标，随机选择一个
                if not target:
                    target = random.choice(targets)
                    print(f"警告: {hunter.name}的技能决策'{skill_decision}'无法解析，随机选择了{target.name}")

                target.alive = False
                self.game.log(hunter.name, f"猎人带走了{target.name}")
                self.emit_game_update(f"猎人带走了{target.name}")

                # 生成决策理由
                reason_prompt = HUNTER_SKILL_REASON_TEMPLATE.format(target=target.name)

                try:
                    skill_reason = ai_client.generate_response(reason_prompt, hunter, "hunter_skill_reason")
                    self.game.log(hunter.name, skill_reason)
                except Exception as e:
                    print(f"生成猎人决策理由失败: {str(e)}")
        except Exception as e:
            print(f"生成猎人决策失败: {str(e)}")
            # 出错时随机选择
            target = random.choice(targets)
            target.alive = False
            self.game.log(hunter.name, f"猎人带走了{target.name}")
            self.emit_game_update(f"猎人带走了{target.name}")

    def build_character_context(self, character):
        """
        构建角色的上下文信息

        Args:
            character (Character): 角色对象

        Returns:
            str: 角色上下文信息
        """
        # 基本角色信息
        context = f"你的角色信息：\n- 姓名：{character.name}\n- 性别：{character.gender}\n- 性格：{character.style}\n"

        # 添加角色特定信息（只有自己知道自己的身份）
        if character.role == "werewolf":
            context += ROLE_DESCRIPTIONS["werewolf"] + "\n"
        elif character.role == "seer":
            context += ROLE_DESCRIPTIONS["seer"] + "\n"
        elif character.role == "witch":
            context += ROLE_DESCRIPTIONS["witch"] + "\n"
        elif character.role == "guard":
            context += ROLE_DESCRIPTIONS["guard"] + "\n"
        else:
            context += ROLE_DESCRIPTIONS["villager"] + "\n"

        # 添加角色特定的上下文信息
        role_context = MemoryManager.get_role_specific_context(character, self.game)
        if role_context:
            context += role_context

        # 添加角色记忆摘要（只包含自己的观察和决策）
        memory_summary = character.get_memory_summary()
        if memory_summary:
            context += f"\n你的记忆：\n{memory_summary}\n"

        # 添加公开信息（所有人都知道的信息）
        context += "\n游戏历史：\n"
        for log in self.game.logs[-10:]:
            # 只包含公开信息，不包含角色身份信息
            if log["source"] == "系统":
                # 过滤掉可能泄露身份的系统消息
                if not any(role in log["message"] for role in ["预言家", "女巫", "守卫", "猎人", "狼人"]):
                    context += f"- 系统：{log['message']}\n"
            else:
                context += f"- {log['source']}：{log['message']}\n"

        return context

    def emit_game_update(self, message):
        """
        发送游戏更新消息

        Args:
            message (str): 更新消息
        """
        if self.socketio:
            game_state = self.game.to_dict()
            game_state["message"] = message
            self.socketio.emit('game_update', game_state)
        print(f"游戏更新: {message}")

    def get_game_state(self):
        """
        获取当前游戏状态

        Returns:
            dict: 游戏状态字典
        """
        return self.game.to_dict()
