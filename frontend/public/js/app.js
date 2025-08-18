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
    modelCallLog: document.getElementById('modelCallLog'),
    characters: document.getElementById('characters'),
    gameLogs: document.getElementById('gameLogs')
};

// Socket.io连接
const socket = io('http://localhost:5003');

// 事件监听
socket.on('connect', () => {
    console.log('已连接到服务器');
    addModelCallRecord('系统', '连接状态', '已连接到服务器', 'success');
});

socket.on('disconnect', () => {
    console.log('与服务器断开连接');
    addModelCallRecord('系统', '连接状态', '与服务器断开连接', 'error');
});

socket.on('game_state', (data) => {
    console.log('收到游戏状态:', data);
    updateGameState(data);
});

socket.on('game_update', (data) => {
    console.log('收到游戏更新:', data);
    updateGameState(data);
});

socket.on('model_call', (data) => {
    console.log('收到模型调用记录:', data);
    addModelCallRecord(data.character, data.call_type, data.status_text, data.status);
});

socket.on('voice_play', (data) => {
    console.log('收到语音播放请求:', data);
    playCharacterVoice(data.character, data.text);
});

socket.on('error', (data) => {
    console.error('错误:', data.message);
    addModelCallRecord('系统', '错误', data.message, 'error');
});

// 按钮事件
elements.startBtn.addEventListener('click', () => {
    fetch('/api/game/start', {
        method: 'POST'
    })
    .then(response => response.json())
    .then(data => {
        if (data.status === 'success') {
            addModelCallRecord('系统', '游戏控制', '游戏开始请求已发送', 'success');
            updateButtonState('running');
        } else {
            addModelCallRecord('系统', '游戏控制', `错误: ${data.message}`, 'error');
        }
    })
    .catch(error => {
        console.error('启动游戏失败:', error);
        addModelCallRecord('系统', '游戏控制', `启动游戏失败: ${error.message}`, 'error');
    });
});

elements.pauseBtn.addEventListener('click', () => {
    fetch('/api/game/pause', {
        method: 'POST'
    })
    .then(response => response.json())
    .then(data => {
        if (data.status === 'success') {
            addModelCallRecord('系统', '游戏控制', '游戏暂停请求已发送', 'success');
            updateButtonState('paused');
        } else {
            addModelCallRecord('系统', '游戏控制', `错误: ${data.message}`, 'error');
        }
    })
    .catch(error => {
        console.error('暂停游戏失败:', error);
        addModelCallRecord('系统', '游戏控制', `暂停游戏失败: ${error.message}`, 'error');
    });
});

elements.resumeBtn.addEventListener('click', () => {
    fetch('/api/game/resume', {
        method: 'POST'
    })
    .then(response => response.json())
    .then(data => {
        if (data.status === 'success') {
            addModelCallRecord('系统', '游戏控制', '游戏恢复请求已发送', 'success');
            updateButtonState('running');
        } else {
            addModelCallRecord('系统', '游戏控制', `错误: ${data.message}`, 'error');
        }
    })
    .catch(error => {
        console.error('恢复游戏失败:', error);
        addModelCallRecord('系统', '游戏控制', `恢复游戏失败: ${error.message}`, 'error');
    });
});

elements.resetBtn.addEventListener('click', () => {
    fetch('/api/game/reset', {
        method: 'POST'
    })
    .then(response => response.json())
    .then(data => {
        if (data.status === 'success') {
            addModelCallRecord('系统', '游戏控制', '游戏重置请求已发送', 'success');
            updateButtonState('waiting');
        } else {
            addModelCallRecord('系统', '游戏控制', `错误: ${data.message}`, 'error');
        }
    })
    .catch(error => {
        console.error('重置游戏失败:', error);
        addModelCallRecord('系统', '游戏控制', `重置游戏失败: ${error.message}`, 'error');
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

// 添加模型调用记录
function addModelCallRecord(character, callType, statusText, status) {
    const timestamp = new Date().toLocaleTimeString();
    
    const recordElement = document.createElement('div');
    recordElement.className = `model-call-item ${status}`;
    
    recordElement.innerHTML = `
        <div class="call-status-icon ${status}"></div>
        <div class="call-content">
            <div class="call-info">
                <span class="call-character">${character}</span>
                <span class="call-type">${getCallTypeText(callType)}</span>
            </div>
            <div class="call-timestamp">${timestamp}</div>
        </div>
    `;
    
    elements.modelCallLog.appendChild(recordElement);
    elements.modelCallLog.scrollTop = elements.modelCallLog.scrollHeight;
    
    // 限制记录数量
    if (elements.modelCallLog.children.length > 15) {
        elements.modelCallLog.removeChild(elements.modelCallLog.firstChild);
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
            <div>模型: ${character.model || '未知'}</div>
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
            // 传递完整的日志条目，而不是仅传递角色名称
            memoryBtn.onclick = () => showSpeechMemory(log);
            content.appendChild(memoryBtn);
        }

        entry.appendChild(time);
        entry.appendChild(content);

        elements.gameLogs.appendChild(entry);
    });

    // 滚动到底部
    elements.gameLogs.scrollTop = elements.gameLogs.scrollHeight;
}

// 显示特定发言的记忆
async function showSpeechMemory(logEntry) {
    try {
        // 检查是否有AI调用记录ID
        if (logEntry.ai_call_ids && logEntry.ai_call_ids.length > 0) {
            // 调用新的API获取特定发言的AI调用记录
            const response = await fetch(`/api/character/memory/speech/${encodeURIComponent(logEntry.source)}`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    ai_call_ids: logEntry.ai_call_ids
                })
            });
            const data = await response.json();

            if (data.status === 'success') {
                displayMemoryModal(data.data, true, logEntry.message); // 传递额外参数指示这是特定发言的记忆
            } else {
                addModelCallRecord('系统', '记忆查询', `获取发言AI调用记录失败: ${data.message}`, 'error');
            }
        } else {
            // 回退到显示角色的完整记忆
            showCharacterMemory(logEntry.source);
        }
    } catch (error) {
        console.error('获取发言记忆失败:', error);
        addModelCallRecord('系统', '记忆查询', `获取发言记忆失败: ${error.message}`, 'error');
    }
}

// 显示角色记忆
async function showCharacterMemory(characterName) {
    try {
        const response = await fetch(`/api/character/memory/${encodeURIComponent(characterName)}`);
        const data = await response.json();

        if (data.status === 'success') {
            displayMemoryModal(data.data);
        } else {
            addModelCallRecord('系统', '记忆查询', `获取角色记忆失败: ${data.message}`, 'error');
        }
    } catch (error) {
        console.error('获取角色记忆失败:', error);
        addModelCallRecord('系统', '记忆查询', `获取角色记忆失败: ${error.message}`, 'error');
    }
}

// 显示记忆浮窗
function displayMemoryModal(memoryData, isSpecificSpeech = false, speechContent = '') {
    const modal = document.getElementById('memoryModal');
    const characterNameSpan = document.getElementById('memoryCharacterName');

    // 设置标题
    if (isSpecificSpeech && speechContent) {
        characterNameSpan.textContent = `${memoryData.name} (${getRoleText(memoryData.role)}) - 发言："${speechContent.substring(0, 30)}${speechContent.length > 30 ? '...' : ''}"`;
    } else {
        characterNameSpan.textContent = `${memoryData.name} (${getRoleText(memoryData.role)})`;
    }

    // 如果是特定发言的记忆，隐藏其他标签页，只显示AI调用记录
    const tabButtons = document.querySelectorAll('.tab-button');
    const tabContents = document.querySelectorAll('.tab-content');

    if (isSpecificSpeech) {
        // 隐藏所有标签按钮和内容
        tabButtons.forEach(btn => {
            if (btn.dataset.tab !== 'ai_calls') {
                btn.style.display = 'none';
            } else {
                btn.style.display = 'block';
                btn.classList.add('active');
            }
        });
        
        tabContents.forEach(content => {
            if (content.id !== 'memoryTab-ai_calls') {
                content.classList.remove('active');
            } else {
                content.classList.add('active');
            }
        });
    } else {
        // 显示所有标签
        tabButtons.forEach(btn => btn.style.display = 'block');
        
        // 重置为默认的第一个标签页（记忆摘要）
        tabButtons.forEach(btn => btn.classList.remove('active'));
        tabContents.forEach(content => content.classList.remove('active'));
        
        document.querySelector('[data-tab="summary"]').classList.add('active');
        document.getElementById('memoryTab-summary').classList.add('active');
    }

    // 仅在非特定发言模式下填充其他记忆内容
    if (!isSpecificSpeech) {
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
    }

    // 始终填充AI调用记录（这是核心功能）
    const aiCallsSec = document.getElementById('memoryAiCalls');
    if (memoryData.memory.ai_calls && memoryData.memory.ai_calls.length > 0) {
        let callsHtml = '';
        if (isSpecificSpeech) {
            callsHtml = `<div class="specific-speech-notice">
                <p><strong>以下是该发言相关的AI调用记录：</strong></p>
            </div>`;
        }
        
        callsHtml += memoryData.memory.ai_calls.map(call => `
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
        
        aiCallsSec.innerHTML = callsHtml;
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
                addModelCallRecord('系统', '状态查询', `获取游戏状态失败: ${data.message}`, 'error');
            }
        })
        .catch(error => {
            console.error('获取游戏状态失败:', error);
            addModelCallRecord('系统', '状态查询', `获取游戏状态失败: ${error.message}`, 'error');
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

// 语音队列管理器
class VoiceQueueManager {
    constructor() {
        this.queue = [];
        this.isPlaying = false;
        this.currentAudio = null;
    }
    
    // 添加语音到队列
    addToQueue(character, text) {
        this.queue.push({ character, text });
        console.log(`语音已加入队列: ${character} - ${text.substring(0, 30)}...`);
        
        // 如果当前没有播放，开始播放
        if (!this.isPlaying) {
            this.processQueue();
        }
    }
    
    // 处理语音队列
    async processQueue() {
        if (this.queue.length === 0 || this.isPlaying) {
            return;
        }
        
        this.isPlaying = true;
        const { character, text } = this.queue.shift();
        
        try {
            console.log(`开始播放队列中的语音: ${character} - ${text.substring(0, 50)}...`);
            
            // 调用语音合成API
            const response = await fetch('/api/voice/synthesize', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    text: text,
                    character: character
                })
            });
            
            if (!response.ok) {
                throw new Error(`语音合成失败: ${response.status}`);
            }
            
            // 获取音频数据
            const audioBlob = await response.blob();
            const audioUrl = URL.createObjectURL(audioBlob);
            
            // 创建音频对象
            const audio = new Audio(audioUrl);
            this.currentAudio = audio;
            
            audio.onloadeddata = () => {
                console.log(`开始播放${character}的语音`);
            };
            
            audio.onended = () => {
                console.log(`${character}的语音播放完成`);
                URL.revokeObjectURL(audioUrl); // 释放内存
                this.currentAudio = null;
                this.isPlaying = false;
                
                // 发送语音播放完成确认到后端
                this.sendVoiceCompletion(character, text);
                
                // 播放下一段语音
                this.processQueue();
            };
            
            audio.onerror = (error) => {
                console.error(`${character}的语音播放失败:`, error);
                URL.revokeObjectURL(audioUrl);
                this.currentAudio = null;
                this.isPlaying = false;
                
                // 播放下一段语音
                this.processQueue();
            };
            
            // 播放音频
            await audio.play();
            
        } catch (error) {
            console.error(`为${character}生成/播放语音失败:`, error);
            this.isPlaying = false;
            
            // 播放下一段语音
            this.processQueue();
        }
    }
    
    // 清空队列
    clearQueue() {
        this.queue = [];
        if (this.currentAudio) {
            this.currentAudio.pause();
            this.currentAudio = null;
        }
        this.isPlaying = false;
        console.log('语音队列已清空');
    }
    
    // 获取队列状态
    getQueueStatus() {
        return {
            queueLength: this.queue.length,
            isPlaying: this.isPlaying,
            currentCharacter: this.isPlaying ? this.queue[0]?.character : null
        };
    }
    
    // 发送语音播放完成确认
    sendVoiceCompletion(character, text) {
        try {
            socket.emit('voice_completed', {
                character: character,
                text: text,
                timestamp: Date.now()
            });
            console.log(`已发送语音完成确认: ${character}`);
        } catch (error) {
            console.error('发送语音完成确认失败:', error);
        }
    }
}

// 创建全局语音队列管理器
const voiceQueueManager = new VoiceQueueManager();

// 语音播放功能 - 现在使用队列管理
async function playCharacterVoice(character, text) {
    // 将语音添加到队列
    voiceQueueManager.addToQueue(character, text);
}
