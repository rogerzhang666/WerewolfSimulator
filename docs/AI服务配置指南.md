# AI服务配置指南

## 概述

狼人杀模拟器支持多个AI服务平台，不同角色可以使用不同的模型，以体验各种AI模型在狼人杀游戏中的不同表现。

## 支持的AI服务平台

### 1. DeepSeek（智谱AI）
- **服务商**: DeepSeek AI
- **API端点**: `https://api.deepseek.com/v1/chat/completions`
- **支持模型**:
  - `deepseek-r1`: DeepSeek R1模型
  - `deepseek-v3`: DeepSeek V3模型
  - `deepseek-chat`: DeepSeek Chat模型

### 2. 阿里百炼（通义千问）
- **服务商**: 阿里云百炼平台
- **API端点**: `https://dashscope.aliyuncs.com/api/v1/services/aigc/text-generation/generation`
- **支持模型**:
  - `qwen-plus`: 通义千问Plus模型
  - `qwen-turbo`: 通义千问Turbo模型
  - `qwen-turbo-latest`: 通义千问Turbo最新版

### 3. 火山方舟（豆包）
- **服务商**: 字节跳动火山方舟
- **API端点**: `https://ark.cn-beijing.volces.com/api/v3/chat/completions`
- **支持模型**:
  - `Doubao-Seed-1.6`: 豆包Seed 1.6模型
  - `Doubao-Seed-1.6-thinking`: 豆包Seed 1.6 Thinking模型

## 环境变量配置

在`.env`文件中配置对应的API密钥：

```bash
# DeepSeek API密钥
DEEPSEEK_API_KEY=sk-your_deepseek_api_key_here

# 阿里百炼API密钥
DASHSCOPE_API_KEY=sk-your_dashscope_api_key_here

# 火山方舟API密钥
ARK_API_KEY=sk-your_ark_api_key_here
```

## 角色模型配置

在`config/characters.json`中为每个角色配置使用的模型：

```json
[
  {
    "id": 1,
    "name": "张三",
    "gender": "男",
    "style": "激进",
    "model": "deepseek-r1",
    "role": ""
  },
  {
    "id": 2,
    "name": "李四",
    "gender": "女",
    "style": "保守",
    "model": "qwen-plus",
    "role": ""
  }
]
```

## 当前角色分配

| 角色 | 性格 | AI模型 | 服务平台 |
|------|------|--------|----------|
| 张三 | 激进 | deepseek-r1 | DeepSeek |
| 李四 | 保守 | qwen-plus | 阿里百炼 |
| 王五 | 理性 | Doubao-Seed-1.6-thinking | 火山方舟 |
| 赵六 | 情绪化 | deepseek-v3 | DeepSeek |
| 钱七 | 冷静 | qwen-turbo | 阿里百炼 |
| 孙八 | 多疑 | Doubao-Seed-1.6 | 火山方舟 |
| 周九 | 沉默 | deepseek-chat | DeepSeek |
| 吴十 | 活跃 | qwen-plus | 阿里百炼 |

## 模型选择策略

### DeepSeek模型特点
- **deepseek-r1**: 推理能力强，适合逻辑性角色
- **deepseek-v3**: 对话流畅，适合表达型角色
- **deepseek-chat**: 均衡能力，适合通用角色

### 通义千问模型特点
- **qwen-plus**: 性能强劲，适合复杂策略角色
- **qwen-turbo**: 响应快速，适合活跃型角色

### 豆包模型特点
- **Doubao-Seed-1.6**: 创新思维，适合多变角色
- **Doubao-Seed-1.6-thinking**: 深度思考，适合分析型角色

## 故障排除

### 常见问题

1. **API密钥错误**
   - 检查`.env`文件中的密钥配置
   - 确认密钥格式正确

2. **网络连接问题**
   - 检查网络连接
   - 确认API端点可访问

3. **模型不存在**
   - 检查模型名称拼写
   - 确认模型在对应平台可用

### 降级策略

当某个模型不可用时，系统会自动降级到默认的通义千问模型，确保游戏正常进行。

## 扩展新的AI服务

要添加新的AI服务：

1. 在`backend/utils/ai_client.py`中创建新的客户端类
2. 继承`AIClient`基类
3. 实现`generate_response`方法
4. 在`get_ai_client`函数中添加新模型的识别逻辑
5. 更新配置文件中的可用模型列表

## 性能优化建议

1. **模型缓存**: 为每个角色创建固定的AI客户端实例
2. **负载均衡**: 将不同角色分配到不同的AI服务平台
3. **超时设置**: 为API调用设置合理的超时时间
4. **重试机制**: 实现API调用失败的重试逻辑

通过多AI服务平台的支持，狼人杀模拟器能够展示不同AI模型的独特特性，为用户提供更加丰富和有趣的游戏体验。
