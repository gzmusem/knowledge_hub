import os
import json
import time
import requests
import tiktoken
import openai
from django.utils import timezone
from django.db import transaction
from typing import List, Dict, Any, Optional, Tuple

from knowledge.ai_models import ModelProvider, AIModel, TokenUsage

class TokenCounter:
    """Token计数工具"""
    @staticmethod
    def count_tokens(text: str, model_name: str) -> int:
        """计算文本的token数量"""
        try:
            encoding = tiktoken.encoding_for_model(model_name)
            return len(encoding.encode(text))
        except Exception:
            try:
                # 回退到cl100k_base编码
                encoding = tiktoken.get_encoding("cl100k_base")
                return len(encoding.encode(text))
            except Exception:
                # 最基础的近似算法：按中文字符和英文单词计算
                chinese_chars = sum(1 for c in text if '\u4e00' <= c <= '\u9fff')
                english_words = len([w for w in text.split() if all(c.isalpha() for c in w)])
                return chinese_chars + english_words

    @staticmethod
    def count_message_tokens(messages: List[Dict[str, str]], model_name: str) -> int:
        """计算消息列表的token数量"""
        total_tokens = 0
        for message in messages:
            # 每条消息的角色和内容
            role_tokens = TokenCounter.count_tokens(message.get('role', ''), model_name)
            content_tokens = TokenCounter.count_tokens(message.get('content', ''), model_name)
            # 每条消息额外计算4个tokens作为格式开销
            total_tokens += role_tokens + content_tokens + 4
        
        # 额外添加2个tokens作为格式开销
        return total_tokens + 2

class ModelService:
    """大模型服务基类"""
    def __init__(self, model_id: str):
        # 从数据库获取模型配置
        try:
            self.model_config = AIModel.objects.select_related('provider').get(model_id=model_id)
            self.model_name = self.model_config.name
            self.provider = self.model_config.provider
            self.is_active = self.model_config.is_active and self.provider.is_active
        except AIModel.DoesNotExist:
            raise ValueError(f"找不到模型配置: {model_id}")
        
    def generate_response(self, messages: List[Dict[str, str]], user=None, conversation=None, message=None) -> Tuple[str, Dict]:
        """生成响应，由子类实现"""
        raise NotImplementedError
        
    @staticmethod
    def get_service(model_id: str) -> 'ModelService':
        """工厂方法，根据模型ID返回对应的服务"""
        print(f"👉 尝试获取模型服务 - 模型ID: {model_id}")
        
        try:
            # 查询模型配置
            print(f"   查询数据库中的模型配置...")
            model_config = AIModel.objects.select_related('provider').get(model_id=model_id)
            print(f"   ✅ 找到模型配置: {model_config.name} (ID: {model_config.model_id})")
            
            # 根据提供商类型选择服务类
            provider_slug = model_config.provider.slug
            print(f"   📋 提供商信息: {model_config.provider.name} (slug: {provider_slug})")

            # 根据提供商类型创建相应的服务实例
            print(f"   🔧 准备创建模型服务实例 ({provider_slug})...")
            
            if provider_slug == 'openai':
                print(f"   🚀 创建 OpenAI 服务实例")
                return OpenAIService(model_id)
            elif provider_slug == 'aliyun':
                print(f"   🚀 创建阿里云服务实例")
                return AliyunService(model_id)
            elif provider_slug == 'deepseek':
                print(f"   🚀 创建 DeepSeek 服务实例")
                return DeepSeekService(model_id)
            else:
                print(f"   ❌ 不支持的提供商类型: {provider_slug}")
                raise ValueError(f"不支持的模型提供商: {provider_slug}")
                
        except AIModel.DoesNotExist:
            # 如果找不到模型，使用默认模型
            print(f"   ⚠️ 模型ID: {model_id} 在数据库中不存在")
            print(f"   🔍 尝试获取默认模型...")
            
            default_model = AIModel.objects.filter(is_default=True).first()
            if default_model:
                print(f"   📎 使用默认模型: {default_model.name} (ID: {default_model.model_id})")
                return ModelService.get_service(default_model.model_id)
            else:
                print(f"   ❌ 系统中没有设置默认模型")
                
                # 尝试获取任意活跃模型
                print(f"   🔍 尝试获取任意活跃模型...")
                any_model = AIModel.objects.filter(is_active=True).first()
                if any_model:
                    print(f"   📎 使用活跃模型: {any_model.name} (ID: {any_model.model_id})")
                    return ModelService.get_service(any_model.model_id)
                else:
                    print(f"   ❌ 系统中没有任何可用模型")
                    raise ValueError(f"未找到模型配置，且没有默认模型")
        except Exception as e:
            print(f"   ❌ 获取模型服务时发生异常: {str(e)}")
            raise
    
    @staticmethod
    def get_default_model() -> str:
        """获取默认模型ID"""
        default_model = AIModel.objects.filter(is_default=True).first()
        if default_model:
            return default_model.model_id
        else:
            # 如果没有设置默认模型，返回第一个活跃模型
            active_model = AIModel.objects.filter(is_active=True).first()
            if active_model:
                return active_model.model_id
            else:
                raise ValueError("系统中没有可用的模型")

    def record_token_usage(self, user, conversation, message, 
                          prompt_tokens, completion_tokens, 
                          response_time, is_successful=True, 
                          error_message="", metadata=None):
        """记录Token使用情况"""
        total_tokens = prompt_tokens + completion_tokens
        
        # 计算成本
        cost_prompt = (prompt_tokens / 1000) * self.model_config.cost_prompt
        cost_completion = (completion_tokens / 1000) * self.model_config.cost_completion
        cost_usd = cost_prompt + cost_completion
        cost_rmb = cost_usd * 7.2  # 美元到人民币的大致汇率
        
        # 创建使用记录
        TokenUsage.objects.create(
            user=user,
            model=self.model_config,
            conversation=conversation,
            message=message,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            total_tokens=total_tokens,
            cost_usd=cost_usd,
            cost_rmb=cost_rmb,
            request_time=timezone.now(),
            response_time=response_time,
            is_successful=is_successful,
            error_message=error_message,
            metadata=metadata or {}
        )

class OpenAIService(ModelService):
    """OpenAI模型服务"""
    def __init__(self, model_id: str):
        super().__init__(model_id)
        
    def generate_response(self, messages: List[Dict[str, str]], user=None, conversation=None, message=None) -> Tuple[str, Dict]:
        start_time = time.time()
        
        api_key = self.provider.api_key
        api_base = self.provider.api_base or "https://api.openai.com/v1"
        
        prompt_tokens = TokenCounter.count_message_tokens(messages, self.model_config.model_id)
        completion_tokens = 0
        usage_info = {"prompt_tokens": prompt_tokens, "completion_tokens": 0, "total_tokens": prompt_tokens}
        
        try:
            client = openai.OpenAI(
                api_key=api_key,
                base_url=api_base
            )
            
            response = client.chat.completions.create(
                model=self.model_config.model_id,
                messages=messages,
                max_tokens=self.model_config.max_tokens,
                temperature=self.model_config.temperature,
                top_p=self.model_config.top_p,
                presence_penalty=self.model_config.presence_penalty,
                frequency_penalty=self.model_config.frequency_penalty
            )
            
            content = response.choices[0].message.content or "无响应内容"
            
            # 获取Token使用情况
            if hasattr(response, 'usage') and response.usage:
                usage_info = {
                    "prompt_tokens": response.usage.prompt_tokens,
                    "completion_tokens": response.usage.completion_tokens,
                    "total_tokens": response.usage.total_tokens
                }
                completion_tokens = response.usage.completion_tokens
            else:
                # 如果OpenAI没有返回token使用情况，则计算回复文本的tokens
                completion_tokens = TokenCounter.count_tokens(content, self.model_config.model_id)
                usage_info["completion_tokens"] = completion_tokens
                usage_info["total_tokens"] = prompt_tokens + completion_tokens
            
            response_time = time.time() - start_time
            
            # 记录使用情况
            if user:
                self.record_token_usage(
                    user=user,
                    conversation=conversation,
                    message=message,
                    prompt_tokens=usage_info["prompt_tokens"],
                    completion_tokens=usage_info["completion_tokens"],
                    response_time=response_time,
                    metadata={"model_id": self.model_config.model_id}
                )
                
            return content, usage_info
            
        except Exception as e:
            response_time = time.time() - start_time
            error_message = str(e)
            
            # 记录失败的请求
            if user:
                self.record_token_usage(
                    user=user,
                    conversation=conversation,
                    message=message,
                    prompt_tokens=prompt_tokens,
                    completion_tokens=0,
                    response_time=response_time,
                    is_successful=False,
                    error_message=error_message
                )
                
            raise

class AliyunService(ModelService):
    """阿里云百炼模型服务"""
    def __init__(self, model_id: str):
        super().__init__(model_id)
        print(f"   🔧 初始化阿里云服务，模型ID: {model_id}")
        
    def generate_response(self, messages: List[Dict[str, str]], user=None, conversation=None, message=None) -> Tuple[str, Dict]:
        start_time = time.time()
        print(f"   🚀 开始调用阿里云模型: {self.model_config.name}")
        
        api_key = self.provider.api_key
        # 兼容模式的base_url
        base_url = "https://dashscope.aliyuncs.com/compatible-mode/v1"
        
        prompt_tokens = TokenCounter.count_message_tokens(messages, "qwen")
        completion_tokens = 0
        usage_info = {"prompt_tokens": prompt_tokens, "completion_tokens": 0, "total_tokens": prompt_tokens}
        
        try:
            print(f"   📡 使用OpenAI兼容模式连接阿里云API (流式模式)")
            # 使用OpenAI客户端连接阿里云
            from openai import OpenAI
            
            client = OpenAI(
                api_key=api_key,
                base_url=base_url
            )
            
            print(f"   📤 发送流式请求到阿里云，消息数: {len(messages)}")
            # 使用流式模式创建聊天完成请求
            completion = client.chat.completions.create(
                model=self.model_config.model_id,
                messages=messages,
                max_tokens=self.model_config.max_tokens,
                temperature=self.model_config.temperature,
                top_p=self.model_config.top_p,
                stream=True,  # 启用流式模式
                stream_options={"include_usage": True}  # 包含用量统计
            )
            
            # 收集完整响应
            full_content = ""
            reasoning_content = ""
            
            print(f"   📥 开始接收流式响应...")
            for chunk in completion:
                # 检查是否是用量信息
                if not hasattr(chunk, 'choices') or not chunk.choices:
                    if hasattr(chunk, 'usage') and chunk.usage:
                        usage_info = {
                            "prompt_tokens": chunk.usage.prompt_tokens,
                            "completion_tokens": chunk.usage.completion_tokens,
                            "total_tokens": chunk.usage.total_tokens
                        }
                        completion_tokens = chunk.usage.completion_tokens
                        print(f"   📊 Token使用情况: {usage_info}")
                    continue
                
                delta = chunk.choices[0].delta
                
                # 检查是否有思考过程内容
                if hasattr(delta, 'reasoning_content') and delta.reasoning_content is not None:
                    reasoning_content += delta.reasoning_content
                    print(f"   💭 接收思考内容: {len(reasoning_content)} 字符", end="\r")
                    
                # 检查是否有回复内容
                if hasattr(delta, 'content') and delta.content:
                    full_content += delta.content
                    print(f"   💬 接收回复内容: {len(full_content)} 字符", end="\r")
            
            # 如果没有获取到使用情况，估算一下
            if completion_tokens == 0:
                completion_tokens = TokenCounter.count_tokens(full_content, "qwen")
                usage_info["completion_tokens"] = completion_tokens
                usage_info["total_tokens"] = prompt_tokens + completion_tokens
                print(f"   📊 估算Token使用情况: {usage_info}")
            
            print(f"   ✅ 流式响应接收完成，总长度: {len(full_content)} 字符")
            
            response_time = time.time() - start_time
            print(f"   ⏱️ 响应时间: {response_time:.2f}秒")
            
            # 记录使用情况
            if user:
                print(f"   💾 记录Token使用情况")
                self.record_token_usage(
                    user=user,
                    conversation=conversation,
                    message=message,
                    prompt_tokens=usage_info["prompt_tokens"],
                    completion_tokens=usage_info["completion_tokens"],
                    response_time=response_time,
                    metadata={
                        "model_id": self.model_config.model_id,
                        "has_reasoning": len(reasoning_content) > 0
                    }
                )
            
            # 如果有思考内容，可以选择添加到元数据或直接合并到回复中
            if reasoning_content:
                print(f"   📝 模型提供了思考过程 ({len(reasoning_content)} 字符)")
                # 可以选择下面两种方式之一:
                
                # 1. 将思考过程添加到回复前面
                # full_content = f"思考过程：\n{reasoning_content}\n\n回答：\n{full_content}"
                
                # 2. 只保留回复内容，思考过程作为元数据记录
                if message:
                    try:
                        # 假设Message模型有一个metadata字段
                        message.metadata = message.metadata or {}
                        message.metadata['reasoning'] = reasoning_content
                        message.save(update_fields=['metadata'])
                        print(f"   ✅ 思考过程已保存到消息元数据")
                    except:
                        print(f"   ⚠️ 无法将思考过程保存到元数据")
                
            return full_content, usage_info
                
        except Exception as e:
            response_time = time.time() - start_time
            error_message = str(e)
            print(f"   ❌ 阿里云API错误: {error_message}")
            
            # 记录失败的请求
            if user:
                print(f"   💾 记录失败请求")
                self.record_token_usage(
                    user=user,
                    conversation=conversation,
                    message=message,
                    prompt_tokens=prompt_tokens,
                    completion_tokens=0,
                    response_time=response_time,
                    is_successful=False,
                    error_message=error_message
                )
                
            raise

class DeepSeekService(ModelService):
    """DeepSeek模型服务"""
    def __init__(self, model_id: str):
        super().__init__(model_id)
        
    def generate_response(self, messages: List[Dict[str, str]], user=None, conversation=None, message=None) -> Tuple[str, Dict]:
        start_time = time.time()
        
        api_key = self.provider.api_key
        api_base = self.provider.api_base or "https://api.deepseek.com/v1"
        
        prompt_tokens = TokenCounter.count_message_tokens(messages, "deepseek")
        completion_tokens = 0
        usage_info = {"prompt_tokens": prompt_tokens, "completion_tokens": 0, "total_tokens": prompt_tokens}
        
        try:
            client = openai.OpenAI(
                api_key=api_key,
                base_url=api_base
            )
            
            response = client.chat.completions.create(
                model=self.model_config.model_id,
                messages=messages,
                max_tokens=self.model_config.max_tokens,
                temperature=self.model_config.temperature,
                top_p=self.model_config.top_p
            )
            
            content = response.choices[0].message.content or "无响应内容"
            
            # 获取Token使用情况
            if hasattr(response, 'usage') and response.usage:
                usage_info = {
                    "prompt_tokens": response.usage.prompt_tokens,
                    "completion_tokens": response.usage.completion_tokens,
                    "total_tokens": response.usage.total_tokens
                }
                completion_tokens = response.usage.completion_tokens
            else:
                # 如果没有返回token使用情况，则计算回复文本的tokens
                completion_tokens = TokenCounter.count_tokens(content, "deepseek")
                usage_info["completion_tokens"] = completion_tokens
                usage_info["total_tokens"] = prompt_tokens + completion_tokens
            
            response_time = time.time() - start_time
            
            # 记录使用情况
            if user:
                self.record_token_usage(
                    user=user,
                    conversation=conversation,
                    message=message,
                    prompt_tokens=usage_info["prompt_tokens"],
                    completion_tokens=usage_info["completion_tokens"],
                    response_time=response_time,
                    metadata={"model_id": self.model_config.model_id}
                )
                
            return content, usage_info
            
        except Exception as e:
            response_time = time.time() - start_time
            error_message = str(e)
            
            # 记录失败的请求
            if user:
                self.record_token_usage(
                    user=user,
                    conversation=conversation,
                    message=message,
                    prompt_tokens=prompt_tokens,
                    completion_tokens=0,
                    response_time=response_time,
                    is_successful=False,
                    error_message=error_message
                )
                
            raise

def get_ai_response(conversation, user_message: str, model_id: str = None, user=None, existing_message_id=None) -> str:
    """统一接口，从指定大模型获取回复"""
    # 获取用户偏好的模型，如未指定则使用默认模型
    if not model_id:
        if user and hasattr(user, 'preferred_model'):
            model_id = user.preferred_model
        else:
            model_id = ModelService.get_default_model()
    
    # 构建对话历史
    messages = []
    
    # 添加系统信息
    messages.append({
        "role": "system",
        "content": "你是一个知识助手，帮助用户回答问题并提供准确的信息。"
    })
    
    # 添加历史消息
    history = conversation.messages.order_by('-timestamp')[:10]
    for msg in reversed(list(history)):
        messages.append({
            "role": msg.role,
            "content": msg.content
        })
    
    # 添加当前用户消息
    messages.append({
        "role": "user",
        "content": user_message
    })
    
    # 后备响应
    fallback_responses = [
        "抱歉，AI服务暂时不可用。请稍后再试。",
        "由于技术原因，无法处理您的请求。我们正在努力修复问题。",
        "连接AI服务时遇到问题。请稍后重试或尝试使用其他模型。"
    ]
    
    # 获取已存在的用户消息对象，而不是创建新的
    from knowledge.models import Message
    
    if existing_message_id:
        # 如果提供了现有消息ID，直接获取
        try:
            user_message_obj = Message.objects.get(id=existing_message_id)
            print(f"[DEBUG] 使用已存在的用户消息 ID: {existing_message_id}")
        except Message.DoesNotExist:
            print(f"[WARNING] 找不到指定ID的消息: {existing_message_id}，将创建新消息")
            user_message_obj = None
    else:
        # 尝试查找最近的匹配消息
        import hashlib
        message_hash = hashlib.md5(user_message.encode()).hexdigest()
        user_message_obj = Message.objects.filter(
            conversation=conversation,
            role='user',
            message_hash=message_hash
        ).order_by('-timestamp').first()
        
        print(f"[DEBUG] 查找匹配消息 hash: {message_hash[:8]}, 结果: {'找到' if user_message_obj else '未找到'}")
    
    # 只有在确实找不到现有消息时才创建新消息
    if not user_message_obj:
        print("[WARNING] 未找到匹配的用户消息，创建新消息")
        user_message_obj = Message.objects.create(
            conversation=conversation,
            role='user',
            content=user_message,
            message_hash=message_hash if 'message_hash' in locals() else None
        )
    
    try:
        # 只使用用户选择的模型，不再尝试备选模型
        service = ModelService.get_service(model_id)
        
        # 生成响应
        content, usage_info = service.generate_response(
            messages, 
            user=user or conversation.user, 
            conversation=conversation,
            message=user_message_obj
        )
        
        # 创建助手消息 - 不使用metadata参数
        assistant_message = Message.objects.create(
            conversation=conversation,
            role='assistant',
            content=content
        )
        
        return content
            
    except Exception as e:
        print(f"模型 {model_id} 调用失败: {e}")
        # 返回后备响应
        import random
        fallback_response = random.choice(fallback_responses)
        
        # 创建失败的助手消息 - 不使用metadata参数
        Message.objects.create(
            conversation=conversation,
            role='assistant',
            content=fallback_response
        )
        
        return fallback_response
