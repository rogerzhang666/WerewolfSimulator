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
            self.game.log("系统", "没有存活的狼人")
            return

        # 获取所有存活的非狼人角色
        targets = [c for c in self.game.get_alive_characters() if c.role != "werewolf"]
        if not targets:
            self.game.log("系统", "没有可击杀的目标")
            return

        # 狼人讨论决定击杀目标
        # 收集每个狼人的意见
        wolf_votes = {}
        wolf_reasons = {}

        for werewolf in werewolves:
            # 构建狼人的上下文信息
            context = self.build_character_context(werewolf)

            # 使用AI生成狼人的决策
            prompt = f"""
            现在是狼人杀游戏的夜晚阶段，你是一名狼人。
            当前存活的玩家有：{', '.join([c.name for c in self.game.get_alive_characters()])}
            你的狼人同伴是：{', '.join([w.name for w in werewolves if w.id != werewolf.id])}

            {context}

            你需要选择一名玩家作为今晚的击杀目标。请从以下玩家中选择：
            {', '.join([c.name for c in targets])}

            请考虑以下因素：
            1. 哪个玩家可能是预言家、女巫等神职？
            2. 哪个玩家对狼人威胁最大？
            3. 击杀哪个玩家可以制造混乱，让好人互相猜疑？

            请只回复你选择的玩家姓名，不要有任何其他内容。
            """

            try:
                ai_client = self.ai_clients.get(werewolf.id)
                if ai_client:
                    # 获取狼人的击杀决策
                    kill_decision = ai_client.generate_response(prompt, werewolf).strip()

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
                    reason_prompt = f"""
                    你刚刚在狼人杀游戏中选择了{target.name}作为今晚的击杀目标。
                    请简短解释你为什么选择击杀这名玩家（不超过50字）。
                    """

                    try:
                        kill_reason = ai_client.generate_response(reason_prompt, werewolf)
                        wolf_reasons[target.name] = kill_reason

                        # 更新狼人记忆
                        werewolf.add_decision("kill", target.name, kill_reason, self.game.current_day, "werewolf")
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

                        # 为其他狼人添加观察记录
                        for other_wolf in werewolves:
                            if other_wolf.id != werewolf.id:
                                other_wolf.add_observation(
                                    f"{werewolf.name}想击杀{target.name}，理由：{wolf_reasons[target.name]}",
                                    self.game.current_day,
                                    "werewolf"
                                )

        self.emit_game_update("狼人正在行动")

    def handle_seer_phase(self):
        """处理预言家行动阶段"""
        seer = self.game.get_character_by_role("seer")
        if not seer or not seer.alive:
            self.game.log("系统", "预言家不在场或已死亡")
            return

        # 获取所有存活的角色（除了预言家自己）
        targets = [c for c in self.game.get_alive_characters() if c.id != seer.id]
        if not targets:
            self.game.log("系统", "没有可查验的目标")
            return

        # 构建预言家的上下文信息
        context = self.build_character_context(seer)

        # 使用AI生成预言家的决策
        prompt = f"""
        现在是狼人杀游戏的夜晚阶段，你是预言家。
        当前存活的玩家有：{', '.join([c.name for c in self.game.get_alive_characters()])}

        {context}

        你需要选择一名玩家进行查验。请从以下玩家中选择：
        {', '.join([c.name for c in targets])}

        请考虑以下因素：
        1. 哪个玩家的发言或行为最可疑？
        2. 哪个玩家可能对游戏走向有重要影响？
        3. 你之前查验过哪些玩家？（避免重复查验）

        请只回复你选择查验的玩家姓名，不要有任何其他内容。
        """

        try:
            ai_client = self.ai_clients.get(seer.id)
            if ai_client:
                # 获取预言家的查验决策
                check_decision = ai_client.generate_response(prompt, seer).strip()

                # 解析查验决策，找到对应的目标角色
                target = None
                for t in targets:
                    if t.name in check_decision:
                        target = t
                        break

                # 如果无法解析或没有找到匹配的目标，随机选择一个
                if not target:
                    target = random.choice(targets)
                    print(f"警告: {seer.name}的查验决策'{check_decision}'无法解析，随机选择了{target.name}")

                # 执行查验
                is_werewolf = target.role == "werewolf"
                result = "狼人" if is_werewolf else "好人"

                self.game.log(seer.name, f"预言家查验了{target.name}，结果是{result}")

                # 更新预言家记忆
                seer.add_decision("check", target.name, f"查验结果：{result}", self.game.current_day, "seer")

                # 更新预言家对目标的看法
                if is_werewolf:
                    seer.update_belief(target.name, "是狼人", 1.0)  # 100%确定
                else:
                    seer.update_belief(target.name, "是好人", 1.0)  # 100%确定

                # 生成查验理由
                reason_prompt = f"""
                你刚刚在狼人杀游戏中查验了{target.name}，查验结果是：{result}。
                请简短描述你为什么选择查验这名玩家，以及对查验结果的反应（不超过50字）。
                """

                try:
                    check_reason = ai_client.generate_response(reason_prompt, seer)
                    self.game.log(seer.name, check_reason)
                except Exception as e:
                    print(f"生成查验理由失败: {str(e)}")
        except Exception as e:
            print(f"生成预言家决策失败: {str(e)}")

        self.emit_game_update("预言家正在行动")

    def handle_witch_phase(self):
        """处理女巫行动阶段"""
        witch = self.game.get_character_by_role("witch")
        if not witch or not witch.alive:
            self.game.log("系统", "女巫不在场或已死亡")
            return

        # 获取夜晚被杀的角色
        killed = self.game.killed_at_night

        # 构建女巫的上下文信息
        context = self.build_character_context(witch)

        # 女巫决定是否使用解药
        if killed:
            save_prompt = f"""
            现在是狼人杀游戏的夜晚阶段，你是女巫。
            当前存活的玩家有：{', '.join([c.name for c in self.game.get_alive_characters()])}

            {context}

            今晚{killed.name}被狼人杀害了。你有一瓶解药，可以救活他。

            请考虑以下因素：
            1. {killed.name}对游戏的重要性如何？
            2. {killed.name}可能是什么身份？
            3. 现在使用解药是否值得？

            请只回复"救"或"不救"，不要有任何其他内容。
            """

            try:
                ai_client = self.ai_clients.get(witch.id)
                if ai_client:
                    # 获取女巫的救人决策
                    save_decision = ai_client.generate_response(save_prompt, witch).strip().lower()

                    # 解析救人决策
                    use_save = "救" in save_decision

                    if use_save:
                        self.game.saved_by_witch = True
                        self.game.log(witch.name, f"女巫使用解药救了{killed.name}")

                        # 更新女巫记忆
                        witch.add_decision("save", killed.name, None, self.game.current_day, "witch")

                        # 生成救人理由
                        reason_prompt = f"""
                        你刚刚在狼人杀游戏中使用解药救了{killed.name}。
                        请简短描述你为什么决定使用解药（不超过50字）。
                        """

                        try:
                            save_reason = ai_client.generate_response(reason_prompt, witch)
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
            except Exception as e:
                print(f"生成女巫救人决策失败: {str(e)}")

        # 女巫决定是否使用毒药
        poison_prompt = f"""
        现在是狼人杀游戏的夜晚阶段，你是女巫。
        当前存活的玩家有：{', '.join([c.name for c in self.game.get_alive_characters()])}

        {context}

        你有一瓶毒药，可以毒死一名玩家。

        请考虑以下因素：
        1. 你是否非常确定某人是狼人？
        2. 现在使用毒药是否值得？
        3. 是否应该保留毒药等待更关键的时刻？

        如果你决定使用毒药，请回复要毒死的玩家姓名；如果决定不使用，请回复"不使用"。
        """

        try:
            ai_client = self.ai_clients.get(witch.id)
            if ai_client:
                # 获取女巫的毒人决策
                poison_decision = ai_client.generate_response(poison_prompt, witch).strip()

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
                        self.game.poisoned_by_witch = target
                        self.game.log(witch.name, f"女巫使用毒药毒死了{target.name}")

                        # 更新女巫记忆
                        witch.add_decision("poison", target.name, None, self.game.current_day, "witch")

                        # 生成毒人理由
                        reason_prompt = f"""
                        你刚刚在狼人杀游戏中使用毒药毒死了{target.name}。
                        请简短描述你为什么选择毒死这名玩家（不超过50字）。
                        """

                        try:
                            poison_reason = ai_client.generate_response(reason_prompt, witch)
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
            self.game.log("系统", "守卫不在场或已死亡")
            return

        # 获取所有存活的角色
        targets = self.game.get_alive_characters()
        if not targets:
            self.game.log("系统", "没有可保护的目标")
            return

        # 构建守卫的上下文信息
        context = self.build_character_context(guard)

        # 使用AI生成守卫的决策
        prompt = f"""
        现在是狼人杀游戏的夜晚阶段，你是守卫。
        当前存活的玩家有：{', '.join([c.name for c in self.game.get_alive_characters()])}

        {context}

        你需要选择一名玩家进行保护，使其今晚不会被狼人杀害。请从以下玩家中选择：
        {', '.join([c.name for c in targets])}

        请考虑以下因素：
        1. 哪个玩家可能是重要角色（如预言家、女巫）？
        2. 哪个玩家最可能被狼人袭击？
        3. 你上一晚保护了谁？（守卫不能连续两晚保护同一个人）

        请只回复你选择保护的玩家姓名，不要有任何其他内容。
        """

        try:
            ai_client = self.ai_clients.get(guard.id)
            if ai_client:
                # 获取守卫的保护决策
                protect_decision = ai_client.generate_response(prompt, guard).strip()

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
                guard.add_decision("protect", target.name, None, self.game.current_day, "guard")

                # 生成保护理由
                reason_prompt = f"""
                你刚刚在狼人杀游戏中选择保护{target.name}。
                请简短描述你为什么选择保护这名玩家（不超过50字）。
                """

                try:
                    protect_reason = ai_client.generate_response(reason_prompt, guard)
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

        # 每个角色发表言论
        for character in alive_characters:
            # 构建角色的上下文信息
            context = self.build_character_context(character)

            # 使用AI生成角色发言
            prompt = f"""
            现在是狼人杀游戏的讨论阶段，请根据你的角色和游戏情况发表言论。

            游戏信息：
            - 当前是第{self.game.current_day}天
            - 存活玩家：{', '.join([c.name for c in alive_characters])}
            - 死亡玩家：{', '.join([c.name for c in self.game.characters if not c.alive])}

            {context}

            请以你的角色身份发表一段简短的发言（不超过100字），表达你的看法、怀疑或辩解。
            """

            try:
                ai_client = self.ai_clients.get(character.id)
                if ai_client:
                    response = ai_client.generate_response(prompt, character)

                    # 记录角色发言到游戏日志
                    self.game.log(character.name, response)
                    self.emit_game_update(f"{character.name}发言: {response}")

                    # 更新角色记忆
                    character.add_statement(response, self.game.current_day, "discussion")

                    # 分析发言，更新对其他角色的看法
                    for other in alive_characters:
                        if other.id != character.id and other.name in response:
                            # 简单的情感分析，检测是否表达了怀疑
                            if any(word in response for word in ["怀疑", "可疑", "狼人", "不信任"]):
                                character.update_belief(other.name, "可能是狼人", 0.6)
                            elif any(word in response for word in ["信任", "好人", "相信"]):
                                character.update_belief(other.name, "可能是好人", 0.6)

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

            # 使用AI生成角色投票决策
            prompt = f"""
            现在是狼人杀游戏的投票阶段，请根据你的角色和游戏情况决定投票给谁。

            游戏信息：
            - 当前是第{self.game.current_day}天
            - 存活玩家：{', '.join([c.name for c in alive_characters])}

            {context}

            你需要投票处决一名玩家。请从以下玩家中选择一名你认为最可疑的：
            {', '.join([c.name for c in targets])}

            请只回复你要投票的玩家姓名，不要有任何其他内容。
            """

            try:
                ai_client = self.ai_clients.get(voter.id)
                if ai_client:
                    # 获取AI的投票决策
                    vote_decision = ai_client.generate_response(prompt, voter).strip()

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

                    # 记录投票
                    if target.id not in self.game.votes:
                        self.game.votes[target.id] = 0
                    self.game.votes[target.id] += 1

                    self.game.log(voter.name, f"投票给了{target.name}")
                    self.emit_game_update(f"{voter.name}投票给了{target.name}")

                    # 更新角色记忆
                    voter.add_decision("vote", target.name, None, self.game.current_day, "vote")

                    # 生成投票理由
                    reason_prompt = f"""
                    你刚刚在狼人杀游戏中投票给了{target.name}。
                    请简短解释你为什么选择投票给这名玩家（不超过30字）。
                    """

                    try:
                        vote_reason = ai_client.generate_response(reason_prompt, voter)
                        self.game.log(voter.name, vote_reason)

                        # 更新投票决策的原因
                        for decision in voter.memory["decisions"]:
                            if (decision["type"] == "vote" and
                                decision["target"] == target.name and
                                decision["day"] == self.game.current_day):
                                decision["reason"] = vote_reason
                                break

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

        # 猎人选择带走目标
        # 在实际应用中，这里应该让AI猎人进行决策
        # 这里简化为随机选择一个目标
        target = random.choice(targets)
        target.alive = False

        self.game.log(hunter.name, f"猎人带走了{target.name}")
        self.emit_game_update(f"猎人带走了{target.name}")

        # 使用AI生成猎人的决策过程
        prompt = f"""
        你是猎人，你被投票处决了，可以发动技能带走一名玩家。
        当前存活的玩家有：{', '.join([c.name for c in targets])}
        你决定带走{target.name}。
        请简短描述你为什么选择带走这名玩家（不超过50字）。
        """

        try:
            ai_client = self.ai_clients.get(hunter.id)
            if ai_client:
                response = ai_client.generate_response(prompt, hunter)
                self.game.log(hunter.name, response)
        except Exception as e:
            print(f"生成猎人决策失败: {str(e)}")

    def build_character_context(self, character):
        """
        构建角色的上下文信息

        Args:
            character (Character): 角色对象

        Returns:
            str: 角色上下文信息
        """
        context = f"你的角色信息：\n- 姓名：{character.name}\n- 性别：{character.gender}\n- 性格：{character.style}\n"

        if character.role == "werewolf":
            # 狼人知道其他狼人
            werewolves = [c.name for c in self.game.get_werewolves() if c.id != character.id]
            context += f"- 你是狼人，你的同伴是：{', '.join(werewolves) if werewolves else '没有其他狼人'}\n"
            context += "- 你的目标是消灭所有好人\n"
        elif character.role == "seer":
            context += "- 你是预言家，你可以查验玩家的身份\n"
            # 添加预言家的查验历史
            # 这里需要实现查验历史的记录和获取
        elif character.role == "witch":
            context += "- 你是女巫，你有一瓶解药和一瓶毒药\n"
            # 添加女巫的使用药水历史
        elif character.role == "guard":
            context += "- 你是守卫，你可以保护一名玩家不被狼人杀害\n"
            # 添加守卫的保护历史
        else:
            context += "- 你是普通村民，你的目标是找出并消灭所有狼人\n"

        # 添加角色记忆摘要
        memory_summary = character.get_memory_summary()
        if memory_summary:
            context += f"\n你的记忆：\n{memory_summary}\n"

        # 添加游戏历史记录
        context += "\n游戏历史：\n"
        for log in self.game.logs[-10:]:  # 最近10条日志
            if log["source"] != "系统":
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
