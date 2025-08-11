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
        content.style.display = 'flex';
        content.style.alignItems = 'center';
        content.style.justifyContent = 'space-between';

        const messageContainer = document.createElement('div');
        messageContainer.style.flex = '1';

        const source = document.createElement('span');
        source.className = `log-source log-source-${getSourceClass(log.source)}`;
        source.textContent = `${log.source}: `;

        const message = document.createElement('span');
        message.className = 'log-message';
        message.textContent = log.message;

        messageContainer.appendChild(source);
        messageContainer.appendChild(message);

        content.appendChild(messageContainer);

        // 添加记忆按钮（只为非系统消息添加）
        if (log.source !== '系统') {
            const memoryBtn = document.createElement('button');
            memoryBtn.className = 'memory-btn';
            memoryBtn.textContent = '记忆';
            memoryBtn.onclick = () => showCharacterMemory(log.source);
            content.appendChild(memoryBtn);
        }

        entry.appendChild(time);
        entry.appendChild(content);

        elements.gameLogs.appendChild(entry);
    });

    // 滚动到底部
    elements.gameLogs.scrollTop = elements.gameLogs.scrollHeight;
}

// 显示角色记忆
async function showCharacterMemory(characterName) {
    try {
        const response = await fetch(`/api/character/memory/${encodeURIComponent(characterName)}`);
        const data = await response.json();

        if (data.status === 'success') {
            displayMemoryModal(data.data);
        } else {
            addMessage(`获取角色记忆失败: ${data.message}`);
        }
    } catch (error) {
        console.error('获取角色记忆失败:', error);
        addMessage(`获取角色记忆失败: ${error.message}`);
    }
}

// 显示记忆浮窗
function displayMemoryModal(memoryData) {
    const modal = document.getElementById('memoryModal');
    const characterNameSpan = document.getElementById('memoryCharacterName');

    characterNameSpan.textContent = `${memoryData.name} (${getRoleText(memoryData.role)})`;

    // 填充记忆摘要
    const summarySec = document.getElementById('memorySummary');
    summarySec.innerHTML = memoryData.memory_summary ?
        `<div class="memory-item"><p>${memoryData.memory_summary.replace(/\n/g, '<br>')}</p></div>` :
        '<div class="empty-state">暂无记忆摘要</div>';

    // 填充决策记录
    const decisionsSec = document.getElementById('memoryDecisions');
    if (memoryData.memory.decisions && memoryData.memory.decisions.length > 0) {
        decisionsSec.innerHTML = memoryData.memory.decisions.map(decision => `
            <div class="memory-item">
                <h4>第${decision.day}天 - ${decision.type.toUpperCase()}</h4>
                <p><strong>目标:</strong> ${decision.target || '无'}</p>
                <p><strong>理由:</strong> ${decision.reason || '无理由记录'}</p>
                <p class="timestamp">阶段: ${decision.phase}</p>
            </div>
        `).join('');
    } else {
        decisionsSec.innerHTML = '<div class="empty-state">暂无决策记录</div>';
    }

    // 填充观察记录
    const observationsSec = document.getElementById('memoryObservations');
    if (memoryData.memory.observations && memoryData.memory.observations.length > 0) {
        observationsSec.innerHTML = memoryData.memory.observations.map(obs => `
            <div class="memory-item">
                <h4>第${obs.day}天观察</h4>
                <p>${obs.content}</p>
                <p class="timestamp">阶段: ${obs.phase}</p>
            </div>
        `).join('');
    } else {
        observationsSec.innerHTML = '<div class="empty-state">暂无观察记录</div>';
    }

    // 填充发言记录（仅公开发言）
    const statementsSec = document.getElementById('memoryStatements');
    if (memoryData.memory.statements && memoryData.memory.statements.length > 0) {
        statementsSec.innerHTML = memoryData.memory.statements.map(stmt => `
            <div class="memory-item">
                <h4>第${stmt.day}天公开发言</h4>
                <p>${stmt.content}</p>
                <p class="timestamp">阶段: ${stmt.phase}</p>
            </div>
        `).join('');
    } else {
        statementsSec.innerHTML = '<div class="empty-state">暂无公开发言记录</div>';
    }

    // 填充内心想法（私密思考）
    const innerThoughtsSec = document.getElementById('memoryInnerThoughts');
    if (memoryData.memory.inner_thoughts && memoryData.memory.inner_thoughts.length > 0) {
        innerThoughtsSec.innerHTML = memoryData.memory.inner_thoughts.map(thought => {
            const isPreSpeechAnalysis = thought.type === 'pre_speech_analysis';
            const itemClass = `memory-item inner-thought-item ${isPreSpeechAnalysis ? 'pre-speech-analysis' : ''}`;
            
            return `
                <div class="${itemClass}">
                    <h4>第${thought.day}天内心想法 <span class="thought-type">[${getThoughtTypeText(thought.type)}]</span></h4>
                    <p class="inner-thought-content">${escapeHtml(thought.content)}</p>
                    <p class="timestamp">阶段: ${thought.phase}</p>
                </div>
            `;
        }).join('');
    } else {
        innerThoughtsSec.innerHTML = '<div class="empty-state">暂无内心想法记录</div>';
    }

    // 填充信念记录
    const beliefsSec = document.getElementById('memoryBeliefs');
    if (memoryData.memory.beliefs && Object.keys(memoryData.memory.beliefs).length > 0) {
        beliefsSec.innerHTML = Object.entries(memoryData.memory.beliefs).map(([target, belief]) => `
            <div class="belief-item">
                <span class="belief-target">${target}</span>
                <span class="belief-description">${belief.description}</span>
                <span class="belief-confidence">${Math.round(belief.confidence * 100)}%</span>
            </div>
        `).join('');
    } else {
        beliefsSec.innerHTML = '<div class="empty-state">暂无信念记录</div>';
    }

    // 填充AI调用记录
    const aiCallsSec = document.getElementById('memoryAiCalls');
    if (memoryData.memory.ai_calls && memoryData.memory.ai_calls.length > 0) {
        aiCallsSec.innerHTML = memoryData.memory.ai_calls.map(call => `
            <div class="ai-call-item">
                <div class="ai-call-header">
                    <h4>${getCallTypeText(call.call_type)} - ${call.model}</h4>
                    <span class="timestamp">${call.timestamp}</span>
                </div>
                <div class="ai-call-input">
                    <h5>系统提示词：</h5>
                    <div class="prompt-content">${escapeHtml(call.input.system_prompt)}</div>
                </div>
                <div class="ai-call-input">
                    <h5>用户提示词：</h5>
                    <div class="prompt-content">${escapeHtml(call.input.user_prompt)}</div>
                </div>
                <div class="ai-call-output">
                    <h5>AI输出：</h5>
                    <div class="response-content">${escapeHtml(call.output)}</div>
                </div>
            </div>
        `).join('');
    } else {
        aiCallsSec.innerHTML = '<div class="empty-state">暂无AI调用记录</div>';
    }

    modal.style.display = 'block';
}

// 关闭记忆浮窗
function closeMemoryModal() {
    document.getElementById('memoryModal').style.display = 'none';
}

// 切换记忆标签页
function switchMemoryTab(tabName) {
    // 隐藏所有标签内容
    document.querySelectorAll('.tab-content').forEach(content => {
        content.classList.remove('active');
    });

    // 移除所有按钮的激活状态
    document.querySelectorAll('.tab-button').forEach(button => {
        button.classList.remove('active');
    });

    // 显示选中的标签内容
    document.getElementById(`memoryTab-${tabName}`).classList.add('active');

    // 激活选中的按钮
    document.querySelector(`[data-tab="${tabName}"]`).classList.add('active');
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

// 获取调用类型文本
function getCallTypeText(callType) {
    const typeMap = {
        'werewolf_kill': '狼人击杀',
        'werewolf_kill_reason': '狼人击杀理由',
        'seer_check': '预言家查验',
        'seer_check_reason': '预言家查验理由',
        'witch_save': '女巫救人',
        'witch_save_reason': '女巫救人理由',
        'witch_poison': '女巫毒人',
        'witch_poison_reason': '女巫毒人理由',
        'guard_protect': '守卫保护',
        'guard_protect_reason': '守卫保护理由',
        'discussion': '讨论发言',
        'vote': '投票决策',
        'vote_reason': '投票理由',
        'hunter_skill': '猎人技能',
        'hunter_skill_reason': '猎人技能理由',
        'general': '一般调用'
    };
    return typeMap[callType] || callType;
}

// 获取内心想法类型文本
function getThoughtTypeText(thoughtType) {
    const types = {
        'kill_reason': '击杀理由',
        'check_reason': '查验理由',
        'save_reason': '救人理由',
        'poison_reason': '毒人理由',
        'protect_reason': '保护理由',
        'vote_reason': '投票理由',
        'pre_speech_analysis': '发言前分析',
        'general': '一般想法'
    };
    return types[thoughtType] || thoughtType;
}

// HTML转义函数
function escapeHtml(text) {
    if (!text) return '';
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML.replace(/\n/g, '<br>');
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
document.addEventListener('DOMContentLoaded', () => {
    initializeGame();

    // 绑定记忆浮窗事件
    document.getElementById('closeMemoryModal').onclick = closeMemoryModal;

    // 点击浮窗外部关闭浮窗
    document.getElementById('memoryModal').onclick = function(event) {
        if (event.target === this) {
            closeMemoryModal();
        }
    };

    // 绑定标签页切换事件
    document.querySelectorAll('.tab-button').forEach(button => {
        button.onclick = () => switchMemoryTab(button.dataset.tab);
    });

    // ESC键关闭浮窗
    document.addEventListener('keydown', (event) => {
        if (event.key === 'Escape') {
            closeMemoryModal();
        }
    });
});
