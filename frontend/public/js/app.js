// 游戏状态管理
const gameState = {
    status: 'waiting',
    phase: '',
    day: 0,
    characters: [],
    logs: []
};

// DOM元素
const elements = {
    startBtn: document.getElementById('startBtn'),
    pauseBtn: document.getElementById('pauseBtn'),
    resumeBtn: document.getElementById('resumeBtn'),
    resetBtn: document.getElementById('resetBtn'),
    gameStatus: document.getElementById('gameStatus'),
    gamePhase: document.getElementById('gamePhase'),
    gameDay: document.getElementById('gameDay'),
    gameMessage: document.getElementById('gameMessage'),
    characters: document.getElementById('characters'),
    gameLogs: document.getElementById('gameLogs')
};

// Socket.io连接
const socket = io('http://localhost:5003');

// 事件监听
socket.on('connect', () => {
    console.log('已连接到服务器');
    addMessage('已连接到服务器');
});

socket.on('disconnect', () => {
    console.log('与服务器断开连接');
    addMessage('与服务器断开连接');
});

socket.on('game_state', (data) => {
    console.log('收到游戏状态:', data);
    updateGameState(data);
});

socket.on('game_update', (data) => {
    console.log('收到游戏更新:', data);
    updateGameState(data);
    if (data.message) {
        addMessage(data.message);
    }
});

socket.on('error', (data) => {
    console.error('错误:', data.message);
    addMessage(`错误: ${data.message}`);
});

// 按钮事件
elements.startBtn.addEventListener('click', () => {
    fetch('/api/game/start', {
        method: 'POST'
    })
    .then(response => response.json())
    .then(data => {
        if (data.status === 'success') {
            addMessage('游戏开始请求已发送');
            updateButtonState('running');
        } else {
            addMessage(`错误: ${data.message}`);
        }
    })
    .catch(error => {
        console.error('启动游戏失败:', error);
        addMessage(`启动游戏失败: ${error.message}`);
    });
});

elements.pauseBtn.addEventListener('click', () => {
    fetch('/api/game/pause', {
        method: 'POST'
    })
    .then(response => response.json())
    .then(data => {
        if (data.status === 'success') {
            addMessage('游戏暂停请求已发送');
            updateButtonState('paused');
        } else {
            addMessage(`错误: ${data.message}`);
        }
    })
    .catch(error => {
        console.error('暂停游戏失败:', error);
        addMessage(`暂停游戏失败: ${error.message}`);
    });
});

elements.resumeBtn.addEventListener('click', () => {
    fetch('/api/game/resume', {
        method: 'POST'
    })
    .then(response => response.json())
    .then(data => {
        if (data.status === 'success') {
            addMessage('游戏恢复请求已发送');
            updateButtonState('running');
        } else {
            addMessage(`错误: ${data.message}`);
        }
    })
    .catch(error => {
        console.error('恢复游戏失败:', error);
        addMessage(`恢复游戏失败: ${error.message}`);
    });
});

elements.resetBtn.addEventListener('click', () => {
    fetch('/api/game/reset', {
        method: 'POST'
    })
    .then(response => response.json())
    .then(data => {
        if (data.status === 'success') {
            addMessage('游戏重置请求已发送');
            updateButtonState('waiting');
        } else {
            addMessage(`错误: ${data.message}`);
        }
    })
    .catch(error => {
        console.error('重置游戏失败:', error);
        addMessage(`重置游戏失败: ${error.message}`);
    });
});

// 更新游戏状态
function updateGameState(data) {
    // 更新状态信息
    if (data.status) {
        gameState.status = data.status;
        elements.gameStatus.textContent = getStatusText(data.status);
        updateButtonState(data.status);
    }

    if (data.phase) {
        gameState.phase = data.phase;
        elements.gamePhase.textContent = getPhaseText(data.phase);
    }

    if (data.current_day !== undefined) {
        gameState.day = data.current_day;
        elements.gameDay.textContent = data.current_day;
    }

    // 更新角色信息
    if (data.characters) {
        gameState.characters = data.characters;
        renderCharacters();
    }

    // 更新日志
    if (data.logs) {
        gameState.logs = data.logs;
        renderLogs();
    }
}

// 添加消息到消息框
function addMessage(message) {
    const messageElement = document.createElement('div');
    messageElement.textContent = message;
    elements.gameMessage.appendChild(messageElement);
    elements.gameMessage.scrollTop = elements.gameMessage.scrollHeight;

    // 限制消息数量
    if (elements.gameMessage.children.length > 10) {
        elements.gameMessage.removeChild(elements.gameMessage.firstChild);
    }
}

// 渲染角色信息
function renderCharacters() {
    elements.characters.innerHTML = '';

    gameState.characters.forEach(character => {
        const card = document.createElement('div');
        card.className = `character-card ${!character.alive ? 'dead' : ''}`;

        const name = document.createElement('div');
        name.className = 'character-name';
        name.textContent = character.name;

        const role = document.createElement('div');
        role.className = `character-role role-${character.role || 'unknown'}`;
        role.textContent = getRoleText(character.role);

        const info = document.createElement('div');
        info.className = 'character-info';
        info.innerHTML = `
            <div>性别: ${character.gender}</div>
            <div>性格: ${character.style}</div>
            <div>状态: ${character.alive ? '存活' : '死亡'}</div>
        `;

        card.appendChild(name);
        card.appendChild(role);
        card.appendChild(info);

        elements.characters.appendChild(card);
    });
}

// 渲染游戏日志
function renderLogs() {
    elements.gameLogs.innerHTML = '';

    gameState.logs.forEach(log => {
        const entry = document.createElement('div');
        entry.className = 'log-entry';

        const time = document.createElement('div');
        time.className = 'log-time';
        time.textContent = `[${log.timestamp}] [${log.day}天-${log.phase}]`;

        const content = document.createElement('div');

        const source = document.createElement('span');
        source.className = `log-source log-source-${getSourceClass(log.source)}`;
        source.textContent = `${log.source}: `;

        const message = document.createElement('span');
        message.className = 'log-message';
        message.textContent = log.message;

        content.appendChild(source);
        content.appendChild(message);

        entry.appendChild(time);
        entry.appendChild(content);

        elements.gameLogs.appendChild(entry);
    });

    // 滚动到底部
    elements.gameLogs.scrollTop = elements.gameLogs.scrollHeight;
}

// 更新按钮状态
function updateButtonState(status) {
    switch (status) {
        case 'waiting':
            elements.startBtn.disabled = false;
            elements.pauseBtn.disabled = true;
            elements.resumeBtn.disabled = true;
            elements.resetBtn.disabled = true;
            break;
        case 'running':
            elements.startBtn.disabled = true;
            elements.pauseBtn.disabled = false;
            elements.resumeBtn.disabled = true;
            elements.resetBtn.disabled = false;
            break;
        case 'paused':
            elements.startBtn.disabled = true;
            elements.pauseBtn.disabled = true;
            elements.resumeBtn.disabled = false;
            elements.resetBtn.disabled = false;
            break;
        case 'finished':
            elements.startBtn.disabled = true;
            elements.pauseBtn.disabled = true;
            elements.resumeBtn.disabled = true;
            elements.resetBtn.disabled = false;
            break;
    }
}

// 获取状态文本
function getStatusText(status) {
    const statusMap = {
        'waiting': '等待开始',
        'running': '游戏进行中',
        'paused': '游戏已暂停',
        'finished': '游戏已结束'
    };
    return statusMap[status] || status;
}

// 获取阶段文本
function getPhaseText(phase) {
    const phaseMap = {
        'setup': '设置阶段',
        'night': '夜晚',
        'werewolf': '狼人行动',
        'seer': '预言家行动',
        'witch': '女巫行动',
        'guard': '守卫行动',
        'dawn': '天亮',
        'discussion': '讨论',
        'vote': '投票',
        'end': '游戏结束'
    };
    return phaseMap[phase] || phase;
}

// 获取角色文本
function getRoleText(role) {
    const roleMap = {
        'werewolf': '狼人',
        'seer': '预言家',
        'witch': '女巫',
        'guard': '守卫',
        'hunter': '猎人',
        'villager': '平民',
        '': '未分配'
    };
    return roleMap[role] || '未知';
}

// 获取日志源的CSS类
function getSourceClass(source) {
    if (source === '系统') {
        return 'system';
    }

    // 根据角色名查找对应的角色
    const character = gameState.characters.find(c => c.name === source);
    if (character && character.role) {
        return character.role;
    }

    return 'villager'; // 默认样式
}

// 初始化：获取当前游戏状态
function initializeGame() {
    fetch('/api/game/state')
        .then(response => response.json())
        .then(data => {
            if (data.status === 'success') {
                updateGameState(data.data);
            } else {
                addMessage(`获取游戏状态失败: ${data.message}`);
            }
        })
        .catch(error => {
            console.error('获取游戏状态失败:', error);
            addMessage(`获取游戏状态失败: ${error.message}`);
        });

    // 获取角色配置
    fetch('/api/characters')
        .then(response => response.json())
        .then(data => {
            if (data.status === 'success' && !gameState.characters.length) {
                gameState.characters = data.data;
                renderCharacters();
            }
        })
        .catch(error => {
            console.error('获取角色配置失败:', error);
        });
}

// 页面加载完成后初始化
document.addEventListener('DOMContentLoaded', initializeGame);
