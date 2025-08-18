#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
AI调用记录管理器
用于管理所有角色的AI调用记录，独立于角色记忆系统
"""

class AICallManager:
    """AI调用记录管理器，单例模式"""
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(AICallManager, cls).__new__(cls)
            cls._instance.ai_call_records = {}
        return cls._instance
    
    def get_ai_calls_by_ids(self, character_name, call_ids):
        """
        根据调用ID获取AI调用记录
        
        Args:
            character_name: 角色名称
            call_ids: AI调用记录ID列表
            
        Returns:
            list: AI调用记录列表
        """
        if character_name not in self.ai_call_records:
            return []
        
        character_calls = self.ai_call_records[character_name]
        return [call for call in character_calls if call["call_id"] in call_ids]
    
    def get_all_ai_calls(self, character_name):
        """
        获取角色的所有AI调用记录
        
        Args:
            character_name: 角色名称
            
        Returns:
            list: AI调用记录列表
        """
        return self.ai_call_records.get(character_name, [])
    
    def add_ai_call_record(self, character_name, record):
        """
        添加AI调用记录
        
        Args:
            character_name: 角色名称
            record: AI调用记录
        """
        if character_name not in self.ai_call_records:
            self.ai_call_records[character_name] = []
        
        self.ai_call_records[character_name].append(record)
        
        # 只保留最近30次调用记录
        if len(self.ai_call_records[character_name]) > 30:
            self.ai_call_records[character_name] = self.ai_call_records[character_name][-30:]
    
    def clear_records(self, character_name=None):
        """
        清空AI调用记录
        
        Args:
            character_name: 角色名称，如果为None则清空所有记录
        """
        if character_name is None:
            self.ai_call_records.clear()
        else:
            self.ai_call_records.pop(character_name, None)

# 全局实例
ai_call_manager = AICallManager()
