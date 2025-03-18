from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db.models import Q, QuerySet
from typing import Type, Union
from rest_framework.serializers import Serializer
from .models import Category, Tag, Conversation, Message, KnowledgePoint
from .serializers import (
    CategorySerializer, TagSerializer, 
    ConversationSerializer, ConversationDetailSerializer,
    MessageSerializer, KnowledgePointSerializer
)
from .tasks import process_conversation_knowledge
from django.utils import timezone
from datetime import timedelta
import hashlib
from django.db.models.signals import pre_save
from django.dispatch import receiver
from django.db.models import F
from django.db import transaction
from django.core.cache import cache
import traceback
import threading
import os

class CategoryViewSet(viewsets.ModelViewSet):
    serializer_class = CategorySerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):  # type: ignore
        return Category.objects.filter(user=self.request.user)
    
    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

class TagViewSet(viewsets.ModelViewSet):
    serializer_class = TagSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):  # type: ignore
        return Tag.objects.filter(user=self.request.user)
    
    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

class ConversationViewSet(viewsets.ModelViewSet):
    permission_classes = [permissions.IsAuthenticated]
    
    def get_serializer_class(self):  # type: ignore
        if self.action == 'retrieve':
            return ConversationDetailSerializer
        return ConversationSerializer
    
    def get_queryset(self):  # type: ignore
        return Conversation.objects.filter(user=self.request.user)
    
    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
    
    @action(detail=True, methods=['post'])
    def add_message(self, request, pk=None):
        # 在方法开始时记录调用堆栈
        stack_trace = ''.join(traceback.format_stack())
        print(f"[DEBUG-STACK] add_message 方法调用堆栈:\n{stack_trace}")
        
        conversation = self.get_object()
        print(f"[DEBUG-CALL] add_message 被调用，会话ID: {pk}, 请求ID: {request.META.get('HTTP_X_REQUEST_ID', 'unknown')}")
        
        print("请求数据类型:", type(request.data))
        print("请求数据:", request.data)
        
        # 处理请求数据
        try:
            if isinstance(request.data, dict):
                message_content = request.data.get('message', '')
                model_id = request.data.get('model_id')
                # 获取客户端时间戳（如果有）
                client_timestamp = request.data.get('client_timestamp')
                print(f"解析到消息: {message_content}, 模型ID: {model_id}")
            else:
                message_content = str(request.data)
                model_id = None
                client_timestamp = None
                print(f"收到纯文本消息: {message_content}")
        except Exception as e:
            print(f"解析请求数据出错: {e}")
            message_content = str(request.data)
            model_id = None
            client_timestamp = None
        
        # 验证消息内容
        if not message_content:
            return Response(
                {'detail': '消息内容不能为空'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # 生成唯一键
        message_hash = hashlib.md5(message_content.encode()).hexdigest()
        cache_key = f"message_{request.user.id}_{conversation.id}_{message_hash}"
        
        # 检查是否最近处理过相同消息
        if cache.get(cache_key):
            print(f"[DEBUG] 缓存命中，发现在短时间内处理过相同消息: {message_hash}")
            # 处理重复逻辑...
            # 可以返回已有的消息响应
            return Response({'detail': '重复消息检测到'}, status=status.HTTP_400_BAD_REQUEST)
        
        # 设置缓存标记这个消息正在处理
        cache.set(cache_key, True, timeout=60)  # 60秒内不允许重复处理
        
        # 创建消息前记录日志
        print(f"[DEBUG-CREATE] 即将创建用户消息, 会话ID: {conversation.id}, 内容: '{message_content[:30]}...'")
        print(f"[DEBUG-CREATE] 当前线程ID: {threading.get_ident()}, 进程ID: {os.getpid()}")
        
        # 1. 先检查重复
        if Message.objects.filter(
            conversation=conversation,
            role='user',
            content=message_content,
            timestamp__gte=timezone.now() - timedelta(seconds=30)
        ).exists():
            # 处理重复消息...
            return Response({'detail': '重复消息检测到'}, status=status.HTTP_400_BAD_REQUEST)
        
        # 2. 在短小的事务中创建用户消息
        with transaction.atomic():
            # 检查是否已存在相同消息
            existing_count = Message.objects.filter(
                conversation=conversation,
                role='user',
                content=message_content,
                timestamp__gte=timezone.now() - timedelta(seconds=1)
            ).count()
            print(f"[DEBUG-CREATE] 检查到过去1秒内相同内容的消息数量: {existing_count}")
            
            # 创建消息前捕获消息ID的最大值
            max_id_before = Message.objects.all().order_by('-id').first()
            max_id_before = max_id_before.id if max_id_before else 0
            print(f"[DEBUG-CREATE] 创建消息前的最大ID: {max_id_before}")
            
            message_hash = hashlib.md5(message_content.encode()).hexdigest()
            user_message, created = Message.objects.get_or_create(
                conversation=conversation,
                role='user',
                message_hash=message_hash,
                defaults={
                    'content': message_content,
                    'request_id': request.META.get('HTTP_X_REQUEST_ID', str(timezone.now().timestamp()))
                }
            )
            
            if created:
                print(f"[DEBUG] 创建了新消息，ID: {user_message.id}")
            else:
                print(f"[DEBUG] 找到现有消息，ID: {user_message.id}，不创建新消息")
            
            # 创建消息后再次检查
            new_messages = Message.objects.filter(
                conversation=conversation,
                role='user',
                content=message_content,
                timestamp__gte=timezone.now() - timedelta(seconds=1)
            ).order_by('id')
            print(f"[DEBUG-CREATE] 创建后检查到的消息: {[m.id for m in new_messages]}")
        
        # 3. 事务外处理AI响应
        try:
            from .models_service import get_ai_response
            ai_response = get_ai_response(
                conversation=conversation, 
                user_message=message_content, 
                model_id=model_id,
                user=request.user
            )
            
            # 获取AI回复
            assistant_message = conversation.messages.filter(role='assistant').latest('timestamp')
            
            # 更新对话时间 (短事务)
            with transaction.atomic():
                conversation.save()
            
            # 触发异步任务
            process_conversation_knowledge.delay(conversation.id)
            
            return Response({
                'user_message': MessageSerializer(user_message).data,
                'assistant_message': MessageSerializer(assistant_message).data
            })
        except Exception as e:
            print(f"AI响应处理错误: {e}")
            return Response({'detail': f'处理消息时出错: {str(e)}'}, 
                          status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @action(detail=False, methods=['get'])
    def search(self, request):
        query = request.query_params.get('q', '')
        if not query:
            return Response([])
            
        conversations = self.get_queryset().filter(
            Q(title__icontains=query) | 
            Q(summary__icontains=query) |
            Q(messages__content__icontains=query)
        ).distinct()
        
        return Response(ConversationSerializer(conversations, many=True).data)

    @action(detail=True, methods=['get'])
    def messages(self, request, pk=None):
        """获取指定对话的所有消息"""
        conversation = self.get_object()
        
        # 获取消息，按时间排序
        messages = conversation.messages.all().order_by('timestamp')  # type: ignore
        
        return Response(MessageSerializer(messages, many=True).data)

class KnowledgePointViewSet(viewsets.ModelViewSet):
    serializer_class = KnowledgePointSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):  # type: ignore
        return KnowledgePoint.objects.filter(user=self.request.user)
    
    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
    
    @action(detail=False, methods=['get'])
    def search(self, request):
        query = request.query_params.get('q', '')
        if not query:
            return Response([])
            
        knowledge_points = self.get_queryset().filter(
            Q(title__icontains=query) | 
            Q(content__icontains=query)
        )
        
        return Response(KnowledgePointSerializer(knowledge_points, many=True).data)

    @action(detail=False, methods=['get'])
    def stats(self, request):
        """返回知识库统计信息"""
        user = request.user
        
        # 计算各种统计数据
        stats_data = {
            'conversations': Conversation.objects.filter(user=user).count(),
            'knowledgePoints': KnowledgePoint.objects.filter(user=user).count(),
            'categories': Category.objects.filter(user=user).count(),
            'tags': Tag.objects.filter(user=user).count(),
        }
        
        # 获取最近的知识点和对话
        recent_knowledge = KnowledgePoint.objects.filter(user=user).order_by('-created_at')[:5]
        recent_conversations = Conversation.objects.filter(user=user).order_by('-updated_at')[:5]
        
        # 组织响应数据
        response_data = {
            'stats': stats_data,
            'recentKnowledge': KnowledgePointSerializer(recent_knowledge, many=True).data,
            'recentConversations': ConversationSerializer(recent_conversations, many=True).data
        }
        
        return Response(response_data)

    @action(detail=False, methods=['get'])
    def recommended(self, request):
        """返回推荐的知识点"""
        user = request.user
        
        # 这里可以实现各种推荐逻辑，例如:
        # - 最近创建的知识点
        # - 基于用户查询历史的推荐
        # - 基于内容相似度的推荐
        # 简单起见，我们暂时返回最近创建的知识点
        
        recommended_points = KnowledgePoint.objects.filter(user=user).order_by('-created_at')[:10]
        
        return Response(KnowledgePointSerializer(recommended_points, many=True).data)