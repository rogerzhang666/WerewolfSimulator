# 狼人杀模拟器 API 文档

## 1. API 概览

### 1.1 基础信息
- **Base URL**: `http://localhost:5003`
- **协议**: HTTP/HTTPS + WebSocket
- **数据格式**: JSON
- **字符编码**: UTF-8

### 1.2 认证方式
当前版本无需认证，后续版本可能添加API Key认证。

## 2. REST API 接口

### 2.1 游戏控制接口

#### 开始游戏
```http
POST /api/game/start
Content-Type: application/json

Response:
{
    "success": true,
    "message": "游戏开始成功",
    "game_id": "game_12345",
    "timestamp": "2025-01-11T10:30:00Z"
}
```

#### 暂停游戏
```http
POST /api/game/pause
Content-Type: application/json

Response:
{
    "success": true,
    "message": "游戏已暂停",
    "timestamp": "2025-01-11T10:35:00Z"
}
```

#### 恢复游戏
```http
POST /api/game/resume
Content-Type: application/json

Response:
{
    "success": true,
    "message": "游戏已恢复",
    "timestamp": "2025-01-11T10:36:00Z"
}
```

#### 重置游戏
```http
POST /api/game/reset
Content-Type: application/json

Response:
{
    "success": true,
    "message": "游戏已重置",
    "timestamp": "2025-01-11T10:40:00Z"
}
```

### 2.2 游戏状态接口

#### 获取游戏状态
```http
GET /api/game/state

Response:
{
    "status": "running",  // waiting/running/paused/ended
    "phase": "discussion", // night/discussion/vote
    "current_day": 2,
    "alive_count": 6,
    "werewolf_count": 1,
    "villager_count": 5,
    "game_log": [
        {
            "timestamp": "2025-01-11T10:30:00Z",
            "day": 1,
            "phase": "night",
            "speaker": "系统",
            "content": "游戏开始，当前为第1天夜晚",
            "type": "system"
        }
    ]
}
```

#### 获取角色列表
```http
GET /api/characters

Response:
{
    "characters": [
        {
            "id": "char_001",
            "name": "张三",
            "role": "werewolf",
            "gender": "male",
            "style": "激进",
            "alive": true,
            "model": "qwen-turbo-latest"
        },
        {
            "id": "char_002", 
            "name": "李四",
            "role": "seer",
            "gender": "male", 
            "style": "理性",
            "alive": true,
            "model": "qwen-turbo-latest"
        }
        // ... 其他角色
    ]
}
```

### 2.3 记忆调试接口

#### 获取角色记忆
```http
GET /api/character/memory/{character_name}
Example: GET /api/character/memory/张三

Response:
{
    "character_name": "张三",
    "character_role": "werewolf",
    "memory": {
        "observations": [
            {
                "timestamp": "2025-01-11T10:31:00Z",
                "day": 1,
                "phase": "discussion",
                "content": "李四跳预言家，声称验到王五是好人",
                "importance": 0.9
            }
        ],
        "decisions": [
            {
                "timestamp": "2025-01-11T10:32:00Z", 
                "day": 1,
                "phase": "night",
                "action": "kill",
                "target": "李四",
                "reasoning": "李四发言太强势，总带节奏，留着对我们不利"
            }
        ],
        "speeches": [
            {
                "timestamp": "2025-01-11T10:33:00Z",
                "day": 1, 
                "phase": "discussion",
                "content": "我觉得李四很可疑，他的发言有漏洞",
                "intent": "引导投票"
            }
        ],
        "beliefs": [
            {
                "target": "李四",
                "role_guess": "seer",
                "trust_score": 0.2,
                "suspicion_level": 0.8,
                "last_updated": "2025-01-11T10:34:00Z"
            }
        ],
        "inner_thoughts": [
            {
                "timestamp": "2025-01-11T10:35:00Z",
                "day": 1,
                "phase": "discussion", 
                "thought": "李四确实是预言家，我们必须今天票掉他",
                "emotion": "紧张",
                "confidence": 0.9
            }
        ]
    }
}
```

#### 获取特定类型记忆
```http
GET /api/character/memory/{character_name}/{memory_type}
Example: GET /api/character/memory/张三/beliefs

Response:
{
    "character_name": "张三",
    "memory_type": "beliefs",
    "data": [
        {
            "target": "李四",
            "role_guess": "seer", 
            "trust_score": 0.2,
            "suspicion_level": 0.8,
            "evidence": [
                "跳预言家",
                "验人准确",
                "发言逻辑性强"
            ],
            "last_updated": "2025-01-11T10:34:00Z"
        }
    ]
}
```

### 2.4 配置管理接口

#### 获取游戏配置
```http
GET /api/config

Response:
{
    "game": {
        "players": 8,
        "roles": {
            "werewolf": 2,
            "villager": 4, 
            "seer": 1,
            "witch": 1
        },
        "phases": {
            "night_duration": 60,
            "discussion_duration": 180,
            "vote_duration": 60
        }
    },
    "ai": {
        "default_model": "qwen-turbo-latest",
        "temperature": 0.7,
        "max_tokens": 500
    }
}
```

## 3. WebSocket 接口

### 3.1 连接信息
- **连接地址**: `ws://localhost:5003/socket.io/`
- **协议**: Socket.IO v4
- **命名空间**: `/` (默认)

### 3.2 客户端事件（发送到服务器）

#### 连接事件
```javascript
socket.emit('connect');
```

#### 开始游戏
```javascript
socket.emit('start_game');
```

#### 暂停游戏
```javascript
socket.emit('pause_game');
```

#### 恢复游戏
```javascript
socket.emit('resume_game');
```

#### 重置游戏
```javascript
socket.emit('reset_game');
```

### 3.3 服务器事件（从服务器接收）

#### 游戏更新
```javascript
socket.on('game_update', (data) => {
    console.log('游戏更新:', data);
    // data = {
    //     type: 'phase_change',
    //     message: '进入讨论阶段',
    //     phase: 'discussion',
    //     day: 2
    // }
});
```

#### 角色发言
```javascript
socket.on('character_speech', (data) => {
    console.log('角色发言:', data);
    // data = {
    //     character: '张三',
    //     content: '我觉得李四很可疑',
    //     day: 1,
    //     phase: 'discussion',
    //     timestamp: '2025-01-11T10:30:00Z'
    // }
});
```

#### 游戏日志
```javascript
socket.on('game_log', (data) => {
    console.log('游戏日志:', data);
    // data = {
    //     timestamp: '2025-01-11T10:30:00Z',
    //     day: 1,
    //     phase: 'night',
    //     speaker: '系统',
    //     content: '第1天夜晚开始，天黑请闭眼',
    //     type: 'system'
    // }
});
```

#### 投票结果
```javascript
socket.on('vote_result', (data) => {
    console.log('投票结果:', data);
    // data = {
    //     voted_out: '张三',
    //     votes: {
    //         '张三': 5,
    //         '李四': 2, 
    //         '王五': 1
    //     },
    //     day: 1
    // }
});
```

#### 游戏结束
```javascript
socket.on('game_end', (data) => {
    console.log('游戏结束:', data);
    // data = {
    //     winner: 'villagers', // 'werewolves' or 'villagers'
    //     reason: '所有狼人被淘汰',
    //     final_day: 3,
    //     survivors: ['李四', '王五', '钱七']
    // }
});
```

#### 错误处理
```javascript
socket.on('error', (data) => {
    console.error('错误:', data);
    // data = {
    //     message: '游戏状态异常',
    //     code: 'GAME_STATE_ERROR'
    // }
});
```

## 4. 错误码说明

### 4.1 HTTP 错误码
- **200**: 成功
- **400**: 请求参数错误
- **404**: 资源不存在
- **500**: 服务器内部错误

### 4.2 业务错误码
```json
{
    "GAME_NOT_FOUND": "游戏不存在",
    "GAME_ALREADY_STARTED": "游戏已经开始", 
    "GAME_NOT_RUNNING": "游戏未运行",
    "CHARACTER_NOT_FOUND": "角色不存在",
    "INVALID_PHASE": "无效的游戏阶段",
    "AI_SERVICE_ERROR": "AI服务调用失败",
    "MEMORY_ACCESS_ERROR": "记忆访问错误"
}
```

## 5. 使用示例

### 5.1 JavaScript 客户端示例
```javascript
// 连接 WebSocket
const socket = io('http://localhost:5003');

// 监听连接成功
socket.on('connect', () => {
    console.log('连接成功');
});

// 监听游戏更新
socket.on('game_update', (data) => {
    updateGameUI(data);
});

// 监听角色发言
socket.on('character_speech', (data) => {
    addSpeechToUI(data);
});

// 开始游戏
function startGame() {
    fetch('/api/game/start', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            console.log('游戏开始成功');
        }
    });
}

// 获取角色记忆
async function getCharacterMemory(characterName) {
    try {
        const response = await fetch(`/api/character/memory/${characterName}`);
        const data = await response.json();
        displayMemory(data);
    } catch (error) {
        console.error('获取记忆失败:', error);
    }
}
```

### 5.2 Python 客户端示例
```python
import requests
import socketio

# HTTP API 调用
def start_game():
    url = 'http://localhost:5003/api/game/start'
    response = requests.post(url)
    return response.json()

def get_game_state():
    url = 'http://localhost:5003/api/game/state'
    response = requests.get(url)
    return response.json()

# WebSocket 客户端
sio = socketio.Client()

@sio.on('connect')
def on_connect():
    print('连接成功')

@sio.on('game_update') 
def on_game_update(data):
    print(f'游戏更新: {data}')

@sio.on('character_speech')
def on_character_speech(data):
    print(f'{data["character"]}: {data["content"]}')

# 连接服务器
sio.connect('http://localhost:5003')
```

## 6. 性能和限制

### 6.1 API 限制
- **请求频率**: 100次/分钟
- **并发连接**: 最大50个WebSocket连接
- **响应大小**: 最大10MB
- **请求超时**: 30秒

### 6.2 数据限制
- **角色数量**: 固定8个
- **记忆条目**: 每个角色最多1000条
- **游戏日志**: 最多10000条记录
- **历史保留**: 内存中保留最近10局游戏

---

*API文档版本: v1.0*  
*最后更新: 2025-01-11*
