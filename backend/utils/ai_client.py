#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import json
import requests
import uuid
from datetime import datetime
from dotenv import load_dotenv
from openai import OpenAI
from backend.utils.ai_call_manager import ai_call_manager

# 加载环境变量
load_dotenv()

class AIClient:
    """AI模型客户端基类"""

    def __init__(self):
        """初始化AI客户端"""
        # 用于存储AI调用记录的独立存储，不放在角色记忆中
        self.ai_call_records = {}

    def generate_response(self, prompt, character=None):
        """
        生成AI响应

        Args:
            prompt (str): 提示词
            character (Character, optional): 角色对象. 默认为None.

        Returns:
            str: AI生成的响应
        """
        raise NotImplementedError("子类必须实现此方法")

    def _record_ai_call(self, character, system_prompt, user_prompt, response, model_name, call_type="general", status="success", action_type=None):
        """
        记录AI调用信息

        Args:
            character: 角色对象
            system_prompt: 系统提示词
            user_prompt: 用户提示词
            response: AI响应
            model_name: 模型名称
            call_type: 调用类型
            status: 调用状态 (success/error)
            action_type: 行为类型，用于关联特定行为
            
        Returns:
            str: AI调用记录的唯一ID
        """
        if character:
            call_id = str(uuid.uuid4())
            ai_call_record = {
                "call_id": call_id,
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "model": model_name,
                "call_type": call_type,
                "action_type": action_type,  # 新增字段，用于关联特定行为
                "input": {
                    "system_prompt": system_prompt,
                    "user_prompt": user_prompt
                },
                "output": response,
                "character": character.name,
                "role": character.role,
                "status": status
            }

            # 使用全局AI调用记录管理器
            ai_call_manager.add_ai_call_record(character.name, ai_call_record)
            
            # 仍然在character.memory中记录最新的AI调用ID，用于关联
            if hasattr(character, 'memory'):
                character.memory["latest_ai_call_id"] = call_id
            
            # 推送模型调用状态到前端
            self._emit_model_call_status(character, call_type, status, response)
                
            return call_id
        return None



    def _emit_model_call_status(self, character, call_type, status, response_text):
        """
        向前端推送模型调用状态
        
        Args:
            character: 角色对象
            call_type: 调用类型
            status: 调用状态 (success/error/loading)
            response_text: 响应文本
        """
        try:
            # 导入socketio (这里用延迟导入避免循环依赖)
            from backend.app import socketio
            
            # 构建状态文本
            if status == "success":
                status_text = f"成功调用{character.model}模型"
            elif status == "error":
                status_text = f"调用{character.model}模型失败"
            else:
                status_text = f"正在调用{character.model}模型..."
            
            # 推送到前端
            socketio.emit('model_call', {
                'character': character.name,
                'call_type': call_type,
                'status': status,
                'status_text': status_text,
                'model': character.model,
                'timestamp': datetime.now().strftime("%H:%M:%S")
            })
        except Exception as e:
            print(f"推送模型调用状态失败: {str(e)}")

class DeepseekClient(AIClient):
    """Deepseek模型客户端 - 通过阿里百炼服务调用"""

    def __init__(self, model_name="deepseek-chat"):
        """初始化Deepseek客户端"""
        super().__init__()
        # 优先使用阿里百炼API调用DeepSeek模型
        self.api_key = os.getenv("DASHSCOPE_API_KEY") or os.getenv("QWEN_API_KEY")
        if not self.api_key:
            # 如果没有百炼API密钥，回退到DeepSeek官方API
            self.api_key = os.getenv("DEEPSEEK_API_KEY")
            if not self.api_key:
                raise ValueError("未设置DASHSCOPE_API_KEY、QWEN_API_KEY或DEEPSEEK_API_KEY环境变量")
            self.use_dashscope = False
            self.api_url = "https://api.deepseek.com/v1/chat/completions"
        else:
            self.use_dashscope = True
            self.api_url = "https://dashscope.aliyuncs.com/api/v1/services/aigc/text-generation/generation"

        self.model_name = model_name  # 支持不同的DeepSeek模型

    def generate_response(self, prompt, character=None, call_type="general", action_type=None):
        """
        生成Deepseek模型响应

        Args:
            prompt (str): 提示词
            character (Character, optional): 角色对象. 默认为None.
            call_type (str): 调用类型，用于调试
            action_type (str): 行为类型，用于关联特定行为

        Returns:
            str: AI生成的响应
        """
        # 构建角色提示词
        if character:
            system_prompt = f"你是一名叫{character.name}的{character.gender}性角色，性格{character.style}。"
            if character.role == "werewolf":
                system_prompt += "你是一名狼人，你的目标是消灭所有好人。"
            elif character.role == "seer":
                system_prompt += "你是一名预言家，你可以查验玩家的身份。"
            elif character.role == "witch":
                system_prompt += "你是一名女巫，你有一瓶解药和一瓶毒药。"

            elif character.role == "villager":
                system_prompt += "你是一名普通村民，你的目标是找出并消灭所有狼人。"
        else:
            system_prompt = "你是狼人杀游戏中的一名角色。"

        # 根据服务类型选择模型名称映射
        if self.use_dashscope:
            # 阿里百炼服务中的DeepSeek模型名称
            model_mapping = {
                "deepseek-r1": "deepseek-r1",
                "deepseek-v3": "deepseek-v3", 
                "deepseek-chat": "deepseek-v3"
            }
        else:
            # DeepSeek官方API的模型名称
            model_mapping = {
                "deepseek-r1": "deepseek-reasoner",
                "deepseek-v3": "deepseek-chat", 
                "deepseek-chat": "deepseek-chat"
            }
        
        # 使用映射后的模型名称
        actual_model = model_mapping.get(self.model_name, "deepseek-v3" if self.use_dashscope else "deepseek-chat")
        
        # 根据服务类型构建请求数据
        if self.use_dashscope:
            # 阿里百炼API格式
            data = {
                "model": actual_model,
                "input": {
                    "messages": [
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": prompt}
                    ]
                },
                "parameters": {
                    "temperature": 0.7,
                    "max_tokens": 500,
                    "result_format": "message"
                }
            }
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.api_key}"
            }
        else:
            # DeepSeek官方API格式
            data = {
                "model": actual_model,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": prompt}
                ],
                "temperature": 0.7,
                "max_tokens": 500
            }
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.api_key}"
            }

        # 发送调用开始状态
        if character:
            self._emit_model_call_status(character, call_type, "loading", "")
        
        try:
            response = requests.post(self.api_url, headers=headers, json=data, timeout=30)
            response.raise_for_status()
            result = response.json()
            
            # 根据服务类型解析响应
            if self.use_dashscope:
                # 阿里百炼API响应格式
                if "output" not in result:
                    raise Exception("阿里百炼API返回格式错误：缺少output字段")
                
                output = result["output"]
                choices = output.get("choices", [])
                if choices:
                    ai_response = choices[0].get("message", {}).get("content", "")
                else:
                    ai_response = output.get("text", "")
            else:
                # DeepSeek官方API响应格式
                if "choices" not in result or not result["choices"]:
                    raise Exception("DeepSeek API返回格式错误：缺少choices字段")
                
                ai_response = result["choices"][0]["message"]["content"]
            
            if not ai_response:
                raise Exception("API返回了空响应")

            # 记录成功的AI调用
            self._record_ai_call(character, system_prompt, prompt, ai_response, self.model_name, call_type, "success", action_type)

            return ai_response
        except requests.exceptions.RequestException as e:
            service_name = "阿里百炼" if self.use_dashscope else "DeepSeek官方"
            print(f"{service_name} API网络请求失败: {str(e)}")
            print(f"使用服务: {service_name}, 模型: {actual_model}")
            print(f"请求数据: {data}")
            fallback_response = f"这是{character.name if character else '某角色'}的回应：根据当前情况，我认为我们应该仔细思考..."
            self._record_ai_call(character, system_prompt, prompt, f"[{service_name}网络错误] {fallback_response}", self.model_name, call_type, "error", action_type)
            return fallback_response
        except Exception as e:
            service_name = "阿里百炼" if self.use_dashscope else "DeepSeek官方"
            print(f"{service_name} API调用失败: {str(e)}")
            print(f"使用服务: {service_name}, 模型: {actual_model}")
            fallback_response = f"这是{character.name if character else '某角色'}的回应：根据当前情况，我认为我们应该仔细思考..."
            self._record_ai_call(character, system_prompt, prompt, f"[{service_name}API调用失败] {fallback_response}", self.model_name, call_type, "error", action_type)
            return fallback_response

class QwenClient(AIClient):
    """通义千问模型客户端"""

    def __init__(self, model_name="qwen-turbo-latest"):
        """初始化通义千问客户端"""
        super().__init__()
        self.api_key = os.getenv("DASHSCOPE_API_KEY")
        if not self.api_key:
            raise ValueError("未设置DASHSCOPE_API_KEY环境变量")

        self.api_url = "https://dashscope.aliyuncs.com/api/v1/services/aigc/text-generation/generation"
        self.model_name = model_name  # 支持不同的Qwen模型

    def generate_response(self, prompt, character=None, call_type="general", action_type=None):
        """
        生成通义千问模型响应

        Args:
            prompt (str): 提示词
            character (Character, optional): 角色对象. 默认为None.
            call_type (str): 调用类型，用于调试
            action_type (str): 行为类型，用于关联特定行为

        Returns:
            str: AI生成的响应
        """
        # 构建角色提示词
        if character:
            system_prompt = f"你是一名叫{character.name}的{character.gender}性角色，性格{character.style}。"
            if character.role == "werewolf":
                system_prompt += "你是一名狼人，你的目标是消灭所有好人。"
            elif character.role == "seer":
                system_prompt += "你是一名预言家，你可以查验玩家的身份。"
            elif character.role == "witch":
                system_prompt += "你是一名女巫，你有一瓶解药和一瓶毒药。"

            elif character.role == "villager":
                system_prompt += "你是一名普通村民，你的目标是找出并消灭所有狼人。"
        else:
            system_prompt = "你是狼人杀游戏中的一名角色。"

        # 构建请求数据 - 使用指定的Qwen模型
        data = {
            "model": self.model_name,
            "input": {
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": prompt}
                ]
            },
            "parameters": {
                "temperature": 0.7,
                "max_tokens": 500,
                "result_format": "message"
            }
        }

        # 发送请求
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }

        try:
            response = requests.post(self.api_url, headers=headers, json=data)
            response.raise_for_status()
            result = response.json()
            
            # 检查响应是否包含error字段
            if "error" in result:
                error_msg = result.get('error', {}).get('message', '未知错误')
                raise Exception(f"API返回错误: {error_msg}")
            
            # 解析正常响应
            output = result.get("output", {})
            choices = output.get("choices", [])
            if choices:
                ai_response = choices[0].get("message", {}).get("content", "")
            else:
                ai_response = output.get("text", "")
            
            if not ai_response:
                raise Exception("API返回了空响应")

            # 记录AI调用
            self._record_ai_call(character, system_prompt, prompt, ai_response, self.model_name, call_type, "success", action_type)

            return ai_response
        except requests.exceptions.RequestException as e:
            print(f"通义千问API网络请求失败: {str(e)}")
            fallback_response = f"这是{character.name if character else '某角色'}的回应：我认为我们应该仔细分析每个人的发言..."

            # 记录失败的调用
            self._record_ai_call(character, system_prompt, prompt, f"[API调用失败] {fallback_response}", self.model_name, call_type, "error", action_type)

            return fallback_response
        except Exception as e:
            print(f"通义千问API调用失败: {str(e)}")
            fallback_response = f"这是{character.name if character else '某角色'}的回应：我认为我们应该仔细分析每个人的发言..."

            # 记录失败的调用
            self._record_ai_call(character, system_prompt, prompt, f"[API调用失败] {fallback_response}", self.model_name, call_type, "error", action_type)

            return fallback_response

class DoubaoClient(AIClient):
    """豆包模型客户端（火山方舟 - 使用OpenAI SDK）"""

    def __init__(self, model_name="doubao-seed-1-6-250615"):
        """初始化豆包客户端"""
        super().__init__()
        self.api_key = os.getenv("ARK_API_KEY")
        if not self.api_key:
            raise ValueError("未设置ARK_API_KEY环境变量")

        # 使用OpenAI客户端连接火山方舟
        self.client = OpenAI(
            base_url="https://ark.cn-beijing.volces.com/api/v3",
            api_key=self.api_key
        )
        
        # 豆包模型名称映射（兼容旧格式）
        self.model_mapping = {
            "Doubao-Seed-1.6": "doubao-seed-1-6-250615",
            "Doubao-Seed-1.6-thinking": "doubao-seed-1-6-thinking-250715",
            "doubao-seed-1.6": "doubao-seed-1-6-250615",
            "doubao-seed-1-6-thinking": "doubao-seed-1-6-thinking-250715",
            # 如果直接是正确格式，保持不变
            "doubao-seed-1-6-250615": "doubao-seed-1-6-250615",
            "doubao-seed-1-6-thinking-250715": "doubao-seed-1-6-thinking-250715"
        }
        
        # 获取实际的模型名称
        self.model_name = self.model_mapping.get(model_name, model_name)

    def generate_response(self, prompt, character=None, call_type="general", action_type=None):
        """
        生成豆包模型响应

        Args:
            prompt (str): 提示词
            character (Character, optional): 角色对象. 默认为None.
            call_type (str): 调用类型，用于调试
            action_type (str): 行为类型，用于关联特定行为

        Returns:
            str: AI生成的响应
        """
        # 构建角色提示词
        if character:
            system_prompt = f"你是一名叫{character.name}的{character.gender}性角色，性格{character.style}。"
            if character.role == "werewolf":
                system_prompt += "你是一名狼人，你的目标是消灭所有好人。"
            elif character.role == "seer":
                system_prompt += "你是一名预言家，你可以查验玩家的身份。"
            elif character.role == "witch":
                system_prompt += "你是一名女巫，你有一瓶解药和一瓶毒药。"
            elif character.role == "villager":
                system_prompt += "你是一名普通村民，你的目标是找出并消灭所有狼人。"
        else:
            system_prompt = "你是狼人杀游戏中的一名角色。"

        # 发送调用开始状态
        if character:
            self._emit_model_call_status(character, call_type, "loading", "")
            
        try:
            # 针对inner_decision调用增加超时时间和token限制
            timeout_duration = 90 if call_type == "inner_decision" else 45
            max_tokens = 300 if call_type == "inner_decision" else 500
            
            # 使用OpenAI SDK调用火山方舟API
            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=max_tokens,
                timeout=timeout_duration
            )
            
            # 获取AI响应
            ai_response = response.choices[0].message.content
            if not ai_response:
                raise Exception("API返回了空响应")

            # 记录AI调用
            self._record_ai_call(character, system_prompt, prompt, ai_response, self.model_name, call_type, "success", action_type)

            return ai_response
            
        except Exception as e:
            print(f"豆包API调用失败: {str(e)}")
            fallback_response = f"这是{character.name if character else '某角色'}的回应：我认为我们应该仔细分析每个人的发言..."
            self._record_ai_call(character, system_prompt, prompt, f"[API调用失败] {fallback_response}", self.model_name, call_type, "error", action_type)
            return fallback_response

def get_ai_client(model_name):
    """
    获取指定模型的AI客户端

    Args:
        model_name (str): 模型名称

    Returns:
        AIClient: AI客户端对象
    """
    # 根据模型名称选择对应的客户端
    if model_name.startswith("deepseek"):
        return DeepseekClient(model_name)
    elif model_name.startswith("qwen"):
        return QwenClient(model_name)
    elif model_name.startswith("Doubao") or model_name.startswith("doubao"):
        return DoubaoClient(model_name)
    else:
        # 默认使用通义千问客户端
        print(f"未知模型 {model_name}，使用默认的通义千问客户端")
        return QwenClient("qwen-turbo-latest")
