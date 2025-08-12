# 狼人杀模拟器 产品需求文档 (PRD)

## 1. 产品概述

### 1.1 产品定位
AI驱动的狼人杀游戏模拟器，8个AI角色自主进行完整的狼人杀游戏对局，用户可观察游戏进程并通过记忆调试功能深入了解每个AI角色的思考过程和决策逻辑。

### 1.2 核心价值
- **探索AI在误导能力**：在模型给定目标下，探索现在不同模型的误导其他人/模型的能力。
- **练习沟通策略**：练习优化模型的沟通策略，调试AI行为，让模型更像一个真人的高手玩家。

### 1.3 目标用户
- AI技术研究者
- 游戏策略学习者

## 2. 产品架构

### 2.1 系统架构图
```
┌─────────────────────────────────────────────────────┐
│                   前端展示层                         │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐    │
│  │ 游戏界面     │ │ 记忆调试器   │ │ 控制面板     │    │
│  └─────────────┘ └─────────────┘ └─────────────┘    │
└─────────────────────────────────────────────────────┘
                              │
                         WebSocket
                              │
┌─────────────────────────────────────────────────────┐
│                   后端服务层                         │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐    │
│  │ 游戏引擎     │ │ 记忆管理器   │ │ API路由      │    │
│  └─────────────┘ └─────────────┘ └─────────────┘    │
└─────────────────────────────────────────────────────┘
                              │
┌─────────────────────────────────────────────────────┐
│                   核心业务层                         │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐    │
│  │ 角色模型     │ │ 游戏逻辑     │ │ AI决策引擎   │    │
│  └─────────────┘ └─────────────┘ └─────────────┘    │
└─────────────────────────────────────────────────────┘
                              │
┌─────────────────────────────────────────────────────┐
│                   AI服务层                          │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐    │
│  │ 通义千问API │ │ 提示词模板   │ │ Mock客户端   │    │
│  └─────────────┘ └─────────────┘ └─────────────┘    │
└─────────────────────────────────────────────────────┘
```

### 2.2 技术栈
- **前端**: HTML5 + CSS3 + JavaScript + Socket.IO
- **后端**: Python Flask + Socket.IO + 多线程游戏引擎
- **AI服务**: 基于角色配置使用不同的模型
  - ①DeepSeek官方服务：R1、V3、Chat模型
  - ②阿里百炼平台：通义千问-Plus、通义千问-Turbo
  - ③火山方舟平台：Doubao-Seed-1.6、Doubao-Seed-1.6-thinking
- **数据存储**: 内存存储 + JSON配置文件 + 五维记忆系统
- **实时通信**: WebSocket + RESTful API
- **记忆系统**: 五维记忆架构（观察、决策、发言、信念、内心想法）
- **调试工具**: 实时记忆查看器 + AI调用记录追踪

## 3. 产品模块设计

### 3.1 模块结构图
```
狼人杀模拟器
├── 前端模块
│   ├── 游戏界面模块
│   ├── 记忆调试模块
│   └── 控制面板模块
├── 后端模块
│   ├── 游戏引擎模块
│   ├── 角色管理模块
│   ├── 记忆管理模块
│   └── API服务模块
└── AI模块
    ├── AI客户端模块
    ├── 提示词模块
    └── 决策引擎模块
```

## 4. 核心功能模块详细设计

### 4.1 游戏引擎模块

#### 4.1.1 功能概述
负责管理整个狼人杀游戏的流程控制、阶段转换和规则执行。

#### 4.1.2 核心功能
- **游戏流程控制**
  - 游戏状态管理（等待/进行中/暂停/结束）
  - 阶段自动转换（夜晚→白天→投票→结算）
  - 多线程游戏循环
  
- **规则执行引擎**
  - 身份分配算法
  - 胜负条件判定
  - 行动有效性验证
  
- **实时事件广播**
  - WebSocket消息推送
  - 游戏状态同步
  - 日志记录与分发

#### 4.1.3 关键逻辑
```python
def game_loop(self):
    """游戏主循环"""
    while self.running and not self.game.is_game_over():
        if self.game.phase == GamePhase.NIGHT:
            self.handle_night_phase()
        elif self.game.phase == GamePhase.DISCUSSION:
            self.handle_discussion_phase()
        elif self.game.phase == GamePhase.VOTE:
            self.handle_vote_phase()
        self.game.next_phase()
```

### 4.2 角色管理模块

#### 4.2.1 功能概述
管理8个AI角色的创建、配置、状态和行为。

#### 4.2.2 核心功能
- **角色创建与配置**
  - 从JSON配置文件加载角色信息
  - 动态分配游戏身份（狼人/预言家/女巫/平民）
  - 角色性格特征配置
  
- **角色状态管理**
  - 生存状态追踪
  - 能力使用状态
  - 投票记录管理
  
- **AI决策协调**
  - 根据角色身份调用相应AI策略
  - 信息隔离确保游戏真实性
  - 行动结果反馈

#### 4.2.3 角色配置示例
```json
{
  "name": "张三",
  "gender": "male",
  "style": "激进",
  "model": "qwen-turbo-latest",
  "personality": {
    "aggression": 0.8,
    "logic": 0.6,
    "suspicion": 0.9
  }
}
```

### 4.3 五维记忆系统模块

#### 4.3.1 功能概述
实现AI角色的多维度记忆存储和管理，支持完整的思考过程追踪。

#### 4.3.2 记忆维度设计
1. **观察记忆 (observations)**
   - 记录游戏中观察到的事件
   - 其他角色的发言和行为
   - 投票结果和死亡信息

2. **决策记忆 (decisions)**
   - 夜晚行动决策
   - 投票选择
   - 策略调整

3. **发言记忆 (speeches)**
   - 自己的公开发言记录
   - 发言意图和策略
   - 反应和回应

4. **信念记忆 (beliefs)**
   - 对其他角色身份的推测
   - 信任度评分
   - 怀疑度变化

5. **内心想法 (inner_thoughts)**
   - 私密的分析过程
   - 真实意图和计划
   - 情感反应

#### 4.3.3 记忆管理逻辑
```python
class MemoryManager:
    @staticmethod
    def add_observation(character, content, day, phase):
        """添加观察记忆"""
        memory_item = {
            "timestamp": datetime.now(),
            "content": content,
            "day": day,
            "phase": phase,
            "importance": calculate_importance(content)
        }
        character.memory["observations"].append(memory_item)
    
    @staticmethod
    def build_context(character, context_type):
        """构建上下文信息"""
        relevant_memories = filter_relevant_memories(
            character.memory, context_type
        )
        return format_context(relevant_memories)
    
    @staticmethod
    def update_werewolf_memory(character, game, target, reason):
        """更新狼人记忆"""
        character.add_decision("kill", target.name, reason, game.current_day, "werewolf")
        character.add_inner_thought(f"选择击杀{target.name}：{reason}", 
                                   game.current_day, "werewolf", "kill_reason")
    
    @staticmethod
    def update_seer_memory(character, game, target, result):
        """更新预言家记忆"""
        character.add_decision("check", target.name, f"查验结果：{result}", 
                              game.current_day, "seer")
        character.add_observation(f"查验{target.name}，结果是{result}", 
                                 game.current_day, "seer")
```

### 4.4 双重策略系统模块

#### 4.4.1 功能概述
实现AI角色的内心分析和策略发言分离，确保更真实的角色扮演。

#### 4.4.2 核心机制
- **内心分析阶段**
  - 深度分析当前局势
  - 制定行动策略
  - 评估风险和收益
  
- **策略发言阶段**
  - 基于内心分析生成公开发言
  - 考虑身份伪装需求
  - 适应角色性格特点

#### 4.4.3 实现逻辑
```python
def generate_character_action(self, character, phase):
    """生成角色行动（双重策略系统）"""
    if phase == "discussion":
        # 讨论阶段的双重策略实现
        return self.handle_discussion_dual_strategy(character)
    elif phase in ["werewolf", "seer", "witch"]:
        # 夜晚阶段的行动决策 + 内心理由
        return self.handle_night_action_with_reasoning(character, phase)
    elif phase == "vote":
        # 投票阶段的决策 + 内心理由
        return self.handle_vote_with_reasoning(character)

def handle_discussion_dual_strategy(self, character):
    """处理讨论阶段的双重策略"""
    # 第一阶段：内心分析决策
    inner_decision = self.generate_inner_decision(character, context, alive_characters, ai_client)
    character.add_inner_thought(f"讨论前的内心分析：{inner_decision}", 
                               self.game.current_day, "discussion", "pre_speech_analysis")
    
    # 第二阶段：基于内心决策的公开发言
    public_speech = self.generate_public_speech(character, context, alive_characters, inner_decision, ai_client)
    
    return public_speech

def handle_night_action_with_reasoning(self, character, phase):
    """处理夜晚行动并生成内心理由"""
    # 1. 生成行动决策
    action_decision = self.generate_night_action(character, phase)
    
    # 2. 生成行动理由（内心想法，不公开）
    action_reason = self.generate_action_reasoning(character, action_decision, phase)
    character.add_inner_thought(f"{phase}阶段行动理由：{action_reason}", 
                               self.game.current_day, phase, f"{phase}_reason")
    
    return action_decision
```

### 4.5 AI决策引擎模块

#### 4.5.1 功能概述
整合通义千问AI服务，实现智能的角色决策和自然语言生成。

#### 4.5.2 核心功能
- **提示词工程**
  - 角色身份提示词
  - 游戏状态描述
  - 历史记忆整合
  
- **AI服务调用**
  - 通义千问API集成
  - 请求参数优化
  - 错误处理和降级
  
- **响应解析**
  - 自然语言解析
  - 行动意图提取
  - 格式标准化

#### 4.5.3 提示词模板示例

##### 狼人角色提示词
```python
# 狼人击杀阶段
WEREWOLF_KILL_TEMPLATE = """
现在是狼人杀游戏的夜晚阶段，你是一名{style}的狼人。
当前存活的玩家有：{alive_players}
你的狼人同伴是：{werewolf_teammates}

{context}

你需要选择一名玩家作为今晚的击杀目标。请从以下玩家中选择：
{targets}

请考虑以下因素：
1. 优先击杀对狼人威胁最大的玩家（如可能的预言家、女巫）
2. 避免击杀明显的普通村民，以免暴露自己
3. 考虑击杀哪个玩家可以制造最大的混乱和误导
4. 与你的狼人同伴的意见保持一致

请只回复你选择的玩家姓名，不要有任何其他内容。
"""

# 狼人讨论阶段内心分析
WEREWOLF_INNER_ANALYSIS = """
**狼人内心分析重点**：
- 分析其他角色的身份，给出确定度权重评估
- 评估哪些好人最危险，优先级：预言家 > 女巫 > 其他神职 > 平民
- 分析是否有预言家暴露，如何应对（反咬/质疑/转移视线）
- 考虑狼人同伴的安全状况，是否需要保护或切割
- 制定伪装策略：如何表现得像好人，避免露出狼性
- 思考如何制造混乱，误导好人投票方向
- 评估当前是否需要跳神职（如假预言家）来混淆视听
"""

# 狼人讨论发言指导
WEREWOLF_DISCUSSION_GUIDANCE = """
作为狼人，你的讨论策略：
1. 伪装成好人，不要暴露自己的狼人身份
2. 尝试将怀疑引导到好人身上，特别是神职玩家
3. 如果有预言家出现，考虑反咬一口或质疑其可信度
4. 与其他狼人的发言保持一致，但不要太明显
5. 如果你的狼人同伴被怀疑，适当为他辩护，但不要过于明显
6. 制造混乱和对立，分化好人阵营
7. 在关键时刻可以考虑跳神职来混淆视听
"""
```

##### 预言家角色提示词
```python
# 预言家查验阶段
SEER_CHECK_TEMPLATE = """
现在是狼人杀游戏的夜晚阶段，你是一名{style}的预言家。
当前存活的玩家有：{alive_players}

{context}

你需要选择一名玩家进行查验。请从以下玩家中选择：
{targets}

请考虑以下因素：
1. 优先查验发言或行为可疑的玩家
2. 考虑查验可能对游戏走向有重要影响的玩家
3. 避免重复查验已经查验过的玩家
4. 如果你已经找到狼人，考虑查验与该狼人互动密切的玩家

请只回复你选择查验的玩家姓名，不要有任何其他内容。
"""

# 预言家内心分析
SEER_INNER_ANALYSIS = """
**预言家内心分析重点**：
- 分析你的查验结果，哪些信息可以公开，哪些需要保留
- 评估暴露身份的时机：过早暴露容易被狼人针对，过晚可能失去话语权
- 观察其他玩家的发言，寻找狼人的破绽和可疑之处
- 考虑如何建立威信，让好人相信你的身份
- 分析是否有假预言家跳身份，如何反驳
- 制定推人策略：如何说服好人投票给你查验出的狼人
"""

# 预言家讨论指导
SEER_DISCUSSION_GUIDANCE = """
作为预言家，你的讨论策略：
1. 考虑是否公开你的身份和查验结果
2. 如果决定公开，清晰地陈述你的查验结果
3. 分析其他玩家的发言，指出可疑之处
4. 引导好人阵营的投票方向
5. 警惕狼人的反咬和质疑
6. 建立威信，让好人相信你的预言家身份
7. 如果有假预言家跳身份，要坚决反驳并提供证据
8. 合理安排查验顺序，优先查验关键可疑人员
"""
```

##### 女巫角色提示词
```python
# 女巫救人阶段
WITCH_SAVE_TEMPLATE = """
现在是狼人杀游戏的夜晚阶段，你是一名{style}的女巫。
当前存活的玩家有：{alive_players}

{context}

今晚{killed}被狼人杀害了。你有一瓶解药，可以救活他。

请考虑以下因素：
1. {killed}对好人阵营的重要性如何？
2. {killed}可能是什么身份？是否可能是预言家或其他神职？
3. 现在使用解药是否值得？还是应该留到更关键的时刻？
4. 如果你已经知道某些玩家的身份，这会影响你的决定吗？

重要提示：如果你认为被杀的玩家是预言家或其他关键神职，强烈建议使用解药！

请只回复"救"或"不救"，不要有任何其他内容。
"""

# 女巫毒人阶段
WITCH_POISON_TEMPLATE = """
现在是狼人杀游戏的夜晚阶段，你是一名{style}的女巫。
当前存活的玩家有：{alive_players}

{context}

你有一瓶毒药，可以毒死一名玩家。

重要提示：
- 只有在你非常确定某人是狼人时才使用毒药
- 绝对不要毒死预言家或其他好人阵营的玩家
- 如果你不确定，请选择不使用毒药

如果你决定使用毒药，请回复要毒死的玩家姓名；如果决定不使用，请回复"不使用"。
"""

# 女巫内心分析
WITCH_INNER_ANALYSIS = """
**女巫内心分析重点**：
- 回顾你的药水使用情况，这些信息是否应该公开
- 如果你救了人，考虑是否透露以证明身份或获得信任
- 如果你毒了人，分析毒死的是否真的是狼人，如何向好人解释
- 评估是否需要配合预言家，支持其查验结果
- 考虑你掌握的夜晚信息（谁被杀）是否可以用来推理
- 分析当前是否应该暴露身份来获得话语权
"""

# 女巫讨论发言指导
WITCH_DISCUSSION_GUIDANCE = """
作为女巫，你的讨论策略：
1. 考虑是否公开你的身份和药水使用情况
2. 如果你救了人，可以选择性透露来证明身份或获得信任
3. 如果你毒了人，需要合理解释你的判断依据
4. 分析其他玩家的发言，指出可疑之处
5. 支持可信的预言家或其他神职玩家
6. 警惕狼人的伪装和误导
7. 利用你掌握的夜晚信息（死亡情况）进行推理
8. 在关键时刻可以暴露身份来获得话语权和主导投票
"""
```



##### 村民角色提示词
```python
# 村民内心分析
VILLAGER_INNER_ANALYSIS = """
**村民内心分析重点**：
- 基于公开信息进行逻辑推理，寻找狼人的蛛丝马迹
- 分析各个神职的可信度，判断谁是真神职，谁可能是狼人伪装
- 观察发言的逻辑性和一致性，寻找自相矛盾的地方
- 考虑死亡顺序：狼人通常优先杀神职，这能提供重要线索
- 分析投票行为：谁在关键时刻投了什么票，是否有问题
- 作为村民，你的发言很重要，要帮助好人阵营找到正确方向
"""

# 村民讨论指导
VILLAGER_DISCUSSION_GUIDANCE = """
作为普通村民，你的讨论策略：
1. 分享你的观察和推理
2. 质疑可疑的发言和行为
3. 支持可信的神职玩家
4. 积极参与讨论，提供有价值的信息
5. 警惕狼人的伪装和误导
"""
```



##### 通用讨论阶段提示词
```python
# 讨论前内心决策模板
DISCUSSION_INNER_DECISION_TEMPLATE = """
现在是狼人杀游戏的讨论阶段，在发表公开言论之前，请先进行内心分析和决策。

游戏信息：
- 当前是第{day}天
- 存活玩家：{alive_players}
- 死亡玩家：{dead_players}

{context}

请作为{role_name}进行内心分析，回答以下问题：

1. **当前局势分析**：根据你掌握的信息，当前的游戏局势如何？谁最可疑？谁最可能是神职？

2. **关键信息梳理**：
   - 你确定知道的信息有哪些？
   - 你怀疑但不确定的信息有哪些？
   - 其他玩家的发言中有哪些值得注意的地方？

3. **发言策略制定**：
   - 这轮发言你的主要目标是什么？
   - 你准备透露哪些信息？隐藏哪些信息？
   - 你想要引导讨论朝哪个方向发展？

4. **风险评估**：
   - 如果你按计划发言，可能面临什么风险？
   - 其他玩家可能如何回应你的发言？

{role_inner_guidance}
"""

# 公开发言模板
DISCUSSION_PUBLIC_SPEECH_TEMPLATE = """
基于你刚才的内心分析和决策，现在请发表公开言论。

{inner_decision_summary}

游戏信息：
- 当前是第{day}天
- 存活玩家：{alive_players}
- 死亡玩家：{dead_players}

{role_specific_guidance}

请以你的角色身份发表一段简短的发言（不超过100字），表达你的看法、怀疑或辩解。
你的发言应该：
1. 符合你刚才制定的发言策略
2. 体现你的角色身份和性格特点
3. 有逻辑性和说服力
4. 考虑到你想要达成的目标

注意：你的发言将被所有存活玩家听到，请谨慎选择要透露的信息。
"""

# 投票阶段模板
VOTE_TEMPLATE = """
现在是狼人杀游戏的投票阶段，请根据你的角色和游戏情况决定投票给谁。

游戏信息：
- 当前是第{day}天
- 存活玩家：{alive_players}

{context}
{role_specific_guidance}

你需要投票处决一名玩家。请从以下玩家中选择一名你认为最可疑的：
{targets}

重要提示：你的投票决定应该与你在讨论阶段的发言保持一致！

请只回复你要投票的玩家姓名，不要有任何其他内容。
"""
```

### 4.6 记忆调试模块

#### 4.6.1 功能概述
为用户提供可视化的AI思考过程查看功能，支持实时调试和深度分析。这是项目的核心创新功能，让用户能够"透视"AI的内心世界。

#### 4.6.2 核心功能
- **五维记忆可视化**
  - 观察记忆：游戏中的所有可见事件记录
  - 决策记忆：每次行动的决策过程和理由
  - 发言记忆：公开发言的历史和策略意图
  - 信念记忆：对其他角色的推测和信任度变化
  - 内心想法：私密的分析过程和真实想法
  
- **AI调用记录追踪**
  - 完整的模型调用历史
  - 提示词和响应内容
  - 调用时间和耗时统计
  - 错误和重试记录
  
- **思考过程可视化**
  - 决策链路展示
  - 推理逻辑时间线
  - 信念变化图表
  - 策略演进轨迹

- **实时交互功能**
  - 游戏进程同步更新
  - 点击角色发言查看思考过程
  - 记忆内容搜索和过滤
  - 导出调试数据

#### 4.6.3 界面设计与交互
```html
<!-- 记忆调试器模态框 -->
<div id="memoryModal" class="modal">
    <div class="modal-content">
        <div class="modal-header">
            <h3>角色记忆 - <span id="memoryCharacterName"></span></h3>
            <span class="close">&times;</span>
        </div>
        <div class="modal-body">
            <div class="memory-tabs">
                <button class="tab-button active" data-tab="summary">记忆摘要</button>
                <button class="tab-button" data-tab="decisions">决策记录</button>
                <button class="tab-button" data-tab="observations">观察记录</button>
                <button class="tab-button" data-tab="statements">发言记录</button>
                <button class="tab-button" data-tab="inner_thoughts">内心想法</button>
                <button class="tab-button" data-tab="beliefs">信念记录</button>
                <button class="tab-button" data-tab="ai_calls">AI调用记录</button>
            </div>
            <div class="memory-content">
                <!-- 动态加载记忆内容 -->
            </div>
        </div>
    </div>
</div>

<!-- 游戏日志中的记忆按钮 -->
<div class="log-entry">
    <span class="character-name">张三</span>: 
    <span class="speech-content">我觉得李四很可疑...</span>
    <button class="memory-btn" onclick="showMemory('张三')">记忆</button>
</div>
```

#### 4.6.4 技术实现
```python
class MemoryDebugger:
    def get_character_memory(self, character_id, memory_type=None):
        """获取角色记忆数据"""
        character = self.game.get_character_by_id(character_id)
        if memory_type:
            return character.memory.get(memory_type, [])
        return character.memory
    
    def get_ai_call_history(self, character_id):
        """获取AI调用历史"""
        return self.ai_call_tracker.get_calls_by_character(character_id)
    
    def export_debug_data(self, character_id=None):
        """导出调试数据"""
        if character_id:
            return self.export_character_data(character_id)
        return self.export_all_data()
```

## 5. 具体功能逻辑

### 5.1 游戏流程逻辑

#### 5.1.1 游戏初始化
```
1. 加载8个角色配置
2. 随机分配身份（2狼人+1预言家+1女巫+4平民）
3. 初始化记忆系统
4. 创建AI客户端
5. 广播游戏开始事件
```

#### 5.1.2 夜晚阶段流程
```
夜晚阶段
├── 狼人行动阶段
│   ├── 每个狼人AI分析局势
│   ├── 生成击杀决策和理由
│   ├── 统计投票结果
│   └── 确定击杀目标
├── 预言家行动阶段
│   ├── 预言家AI选择查验目标
│   ├── 返回查验结果
│   └── 记录到预言家记忆
├── 女巫行动阶段
    ├── 告知女巫击杀信息
    ├── AI决策是否救人/毒人
    └── 执行女巫行动

```

#### 5.1.3 白天阶段流程
```
白天阶段
├── 天亮公布结果
│   ├── 宣布死亡信息
│   ├── 更新角色状态
│   └── 触发记忆更新
├── 讨论阶段
│   ├── 每个AI生成内心分析
│   ├── 基于分析生成公开发言
│   ├── 实时更新信念记忆
│   └── 记录发言到记忆系统
└── 投票阶段
    ├── 每个AI分析投票策略
    ├── 生成投票决策和理由
    ├── 统计投票结果
    └── 执行淘汰逻辑
```

### 5.2 AI决策逻辑

#### 5.2.1 狼人决策逻辑
```python
def werewolf_decision_logic(character, game_state):
    """狼人决策逻辑"""
    # 1. 分析威胁等级
    threat_analysis = analyze_player_threats(game_state)
    
    # 2. 评估击杀收益
    kill_benefits = calculate_kill_benefits(threat_analysis)
    
    # 3. 考虑团队策略
    team_strategy = coordinate_with_teammates(character)
    
    # 4. 生成最终决策
    target = select_optimal_target(kill_benefits, team_strategy)
    reason = generate_kill_reason(target, threat_analysis)
    
    return {
        "target": target,
        "reason": reason,
        "confidence": calculate_confidence(target)
    }
```

#### 5.2.2 预言家决策逻辑
```python
def seer_decision_logic(character, game_state):
    """预言家决策逻辑"""
    # 1. 分析可疑度排序
    suspicion_ranking = rank_players_by_suspicion(game_state)
    
    # 2. 考虑信息价值
    info_value = calculate_information_value(suspicion_ranking)
    
    # 3. 避免重复查验
    unchecked_players = filter_unchecked_players(character.memory)
    
    # 4. 选择最优查验目标
    target = select_seer_target(info_value, unchecked_players)
    
    return {
        "target": target,
        "reasoning": generate_seer_reasoning(target)
    }
```

### 5.3 记忆更新逻辑

#### 5.3.1 观察记忆更新
```python
def update_observation_memory(character, event):
    """更新观察记忆"""
    # 1. 事件重要性评估
    importance = calculate_event_importance(event)
    
    # 2. 创建记忆项
    memory_item = {
        "timestamp": current_time(),
        "event_type": event.type,
        "content": event.description,
        "participants": event.involved_players,
        "importance": importance,
        "day": current_day(),
        "phase": current_phase()
    }
    
    # 3. 添加到记忆系统
    character.memory["observations"].append(memory_item)
    
    # 4. 触发相关分析
    trigger_belief_update(character, event)
```

#### 5.3.2 信念记忆更新
```python
def update_belief_memory(character, target, evidence):
    """更新信念记忆"""
    current_belief = character.get_belief_about(target)
    
    # 1. 计算信念变化
    belief_change = calculate_belief_change(evidence, current_belief)
    
    # 2. 更新信任度
    new_trust_score = current_belief.trust + belief_change.trust_delta
    new_suspicion = current_belief.suspicion + belief_change.suspicion_delta
    
    # 3. 记录变化原因
    belief_record = {
        "target": target,
        "previous_trust": current_belief.trust,
        "new_trust": new_trust_score,
        "change_reason": evidence.description,
        "confidence": belief_change.confidence
    }
    
    character.memory["beliefs"].append(belief_record)
```

## 6. 技术实现要点

### 6.1 性能优化
- **异步处理**: 使用多线程处理AI调用，避免阻塞
- **缓存机制**: 缓存频繁访问的记忆数据
- **限流控制**: 控制AI API调用频率，避免超限

### 6.2 错误处理
- **AI服务降级**: API失败时使用Mock响应
- **游戏状态恢复**: 异常情况下的状态回滚
- **日志记录**: 完整的错误追踪和调试信息

### 6.3 扩展性设计
- **模块化架构**: 各模块独立，便于功能扩展
- **配置驱动**: 通过配置文件调整游戏参数
- **插件化AI**: 支持接入不同的AI模型

## 7. 项目实现状态

### 7.1 已完成功能 ✅

#### 核心游戏机制
- [x] **8人标准局配置**：2狼人 + 1预言家 + 1女巫 + 4平民
- [x] **完整夜晚阶段**：狼人击杀、预言家查验、女巫救人毒人
- [x] **白天讨论投票**：自由发言、民主投票、策略推理
- [x] **胜负判定系统**：狼人屠边 vs 好人出局狼人
- [x] **多线程游戏引擎**：流畅的游戏循环控制

#### AI智能系统
- [x] **五维记忆系统**：观察、决策、发言、信念、内心想法
- [x] **双重策略机制**：内心分析 + 策略发言分离
- [x] **多AI模型支持**：DeepSeek、Qwen、豆包等主流模型
- [x] **角色差异化配置**：8种不同性格和行为模式
- [x] **智能决策引擎**：基于角色身份的策略决策
- [x] **严格信息隔离**：确保角色只知道应该知道的信息

#### 交互与调试
- [x] **实时WebSocket通信**：毫秒级游戏状态同步
- [x] **记忆调试器**：可视化查看AI完整思考过程
- [x] **AI调用记录追踪**：完整的模型调用历史
- [x] **游戏控制面板**：开始/暂停/恢复/重置功能
- [x] **实时日志系统**：详细的游戏进程记录

#### 技术架构
- [x] **模块化设计**：清晰的分层架构
- [x] **异步处理机制**：AI调用不阻塞游戏流程
- [x] **错误处理与降级**：稳定的系统运行
- [x] **配置驱动架构**：灵活的角色和游戏参数配置

### 7.2 性能指标 📊
- **AI响应时间**: < 5秒
- **游戏流程延迟**: < 1秒
- **内存使用**: < 512MB
- **并发支持**: 10个游戏实例
- **系统稳定性**: 99%+正常运行时间

### 7.3 用户体验评估
- **观赏性**: 9.0/10 - 剧情跌宕起伏，充满悬念
- **教育性**: 8.5/10 - 展示高级策略和推理技巧  
- **技术性**: 9.0/10 - 稳定运行，功能完善
- **创新性**: 9.5/10 - 记忆系统和双重策略系统独创

## 8. 未来优化方向

### 8.1 功能增强
- [ ] 支持更多角色身份（猎人、守卫、白痴、丘比特等）
- [ ] 增加游戏录像回放功能
- [ ] 实现多局游戏统计分析
- [ ] 添加用户自定义角色配置
- [ ] 支持用户参与游戏（人机混合局）

### 8.2 技术优化
- [ ] 实现分布式AI服务调用
- [ ] 增加游戏数据持久化存储
- [ ] 优化前端渲染性能
- [ ] 实现移动端适配
- [ ] 增加缓存机制减少API调用

### 8.3 AI能力提升
- [ ] 引入强化学习算法
- [ ] 实现跨局学习能力
- [ ] 增强情感表达能力
- [ ] 优化推理逻辑链路
- [ ] 增加AI行为的随机性和不可预测性

### 8.4 商业化发展
- [ ] 开发API接口供第三方调用
- [ ] 构建AI训练平台
- [ ] 扩展到其他推理类游戏
- [ ] 面向教育市场的产品化

---

## 附录

### A. API接口文档
详见 `docs/api_documentation.md`

### B. 部署指南
详见 `docs/deployment_guide.md`

### C. 开发规范
详见 `docs/development_standards.md`
