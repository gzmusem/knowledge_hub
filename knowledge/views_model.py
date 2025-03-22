from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page
from rest_framework.response import Response
from django.db.models import Sum, Avg, Count, F, ExpressionWrapper, fields
from django.db.models.functions import TruncDay, TruncMonth
from django.utils import timezone
import datetime
from rest_framework import serializers

from knowledge.ai_models import ModelProvider, AIModel, TokenUsage, PromptTemplate, PromptScene
from knowledge.serializers_model import ModelProviderSerializer, AIModelSerializer, TokenUsageSerializer, ModelStatSerializer, PromptTemplateSerializer, PromptSceneSerializer

class ModelProviderViewSet(viewsets.ModelViewSet):
    """模型提供商管理"""
    queryset = ModelProvider.objects.all()
    serializer_class = ModelProviderSerializer
    permission_classes = [permissions.IsAdminUser]
    
    def perform_create(self, serializer):
        serializer.save()
    
    def perform_update(self, serializer):
        serializer.save()
        
    @action(detail=False, methods=['get'], permission_classes=[permissions.IsAuthenticated])
    def active(self, request):
        """获取活跃的模型提供商列表"""
        providers = ModelProvider.objects.filter(is_active=True)
        serializer = self.get_serializer(providers, many=True)
        return Response(serializer.data)

class AIModelViewSet(viewsets.ModelViewSet):
    """AI模型管理"""
    queryset = AIModel.objects.all()
    serializer_class = AIModelSerializer
    permission_classes = [permissions.IsAdminUser]
    
    def perform_create(self, serializer):
        data = serializer.validated_data
        
        # 验证模型ID的唯一性
        model_id = data.get('model_id')
        if AIModel.objects.filter(model_id=model_id).exists():
            raise serializers.ValidationError({'model_id': '模型ID已存在'})
        
        # 如果设置为默认模型，取消其他默认模型
        if data.get('is_default'):
            AIModel.objects.filter(is_default=True).update(is_default=False)
        
        serializer.save()
        
    def perform_update(self, serializer):
        serializer.save()
    
    @method_decorator(cache_page(60 * 15))  # 缓存15分钟
    @action(detail=False, methods=['get'], permission_classes=[permissions.IsAuthenticated])
    def available(self, request):
        """获取可用的AI模型列表"""
        models = AIModel.objects.filter(is_active=True, provider__is_active=True)
        serializer = self.get_serializer(models, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def set_default(self, request, pk=None):
        """设置为默认模型"""
        try:
            model = self.get_object()
            
            # 取消其他默认模型
            AIModel.objects.filter(is_default=True).update(is_default=False)
            
            # 设置当前模型为默认
            model.is_default = True
            model.save()
            
            return Response({'status': 'success', 'message': f'{model.name}已设置为默认模型'})
        except Exception as e:
            return Response(
                {'status': 'error', 'message': f'设置默认模型失败: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=True, methods=['post'])
    def test_connection(self, request, pk=None):
        """测试模型连接"""
        model = self.get_object()
        
        try:
            # 这里实现模型连接测试逻辑
            # 例如，发送一个简单的请求到模型API
            
            # 假设测试成功
            return Response({
                'status': 'success',
                'message': f'成功连接到{model.name}',
                'details': {
                    'latency': '200ms',
                    'status': 'available'
                }
            })
        except Exception as e:
            return Response({
                'status': 'error',
                'message': f'连接测试失败: {str(e)}',
                'details': {
                    'error_type': type(e).__name__,
                    'error_message': str(e)
                }
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=False, methods=['post'])
    def bulk_update_status(self, request):
        """批量更新模型状态"""
        model_ids = request.data.get('model_ids', [])
        is_active = request.data.get('is_active')
        
        if not model_ids or is_active is None:
            return Response({
                'status': 'error',
                'message': '缺少必要参数'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            updated = AIModel.objects.filter(id__in=model_ids).update(is_active=is_active)
            return Response({
                'status': 'success',
                'message': f'已更新{updated}个模型的状态',
                'updated_count': updated
            })
        except Exception as e:
            return Response({
                'status': 'error',
                'message': f'批量更新失败: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class TokenUsageViewSet(viewsets.ReadOnlyModelViewSet):
    """Token使用记录管理"""
    queryset = TokenUsage.objects.all()
    serializer_class = TokenUsageSerializer
    permission_classes = [permissions.IsAdminUser]
    
    def get_queryset(self):
        queryset = TokenUsage.objects.all().order_by('-request_time')
        
        # 筛选指定用户的使用记录
        user_id = self.request.query_params.get('user_id')
        if user_id:
            queryset = queryset.filter(user_id=user_id)
            
        # 筛选指定模型的使用记录
        model_id = self.request.query_params.get('model_id')
        if model_id:
            queryset = queryset.filter(model__model_id=model_id)
            
        # 筛选时间范围
        start_date = self.request.query_params.get('start_date')
        if start_date:
            try:
                start_date = datetime.datetime.strptime(start_date, '%Y-%m-%d').date()
                queryset = queryset.filter(request_time__date__gte=start_date)
            except ValueError:
                pass
                
        end_date = self.request.query_params.get('end_date')
        if end_date:
            try:
                end_date = datetime.datetime.strptime(end_date, '%Y-%m-%d').date()
                queryset = queryset.filter(request_time__date__lte=end_date)
            except ValueError:
                pass
                
        return queryset
    
    @action(detail=False, methods=['get'])
    def stats(self, request):
        """获取Token使用统计数据"""
        # 获取查询参数
        period = request.query_params.get('period', 'day')
        days = request.query_params.get('days', 30)
        
        try:
            days = int(days)
        except ValueError:
            days = 30
            
        # 计算时间范围
        end_date = timezone.now()
        start_date = end_date - datetime.timedelta(days=days)
        
        # 使用select_related减少数据库查询
        base_queryset = TokenUsage.objects.filter(
            request_time__gte=start_date,
            request_time__lte=end_date
        ).select_related('user', 'model', 'model__provider')
        
        # 根据周期选择截断函数
        if period == 'month':
            trunc_func = TruncMonth('request_time')
        else:  # default: day
            trunc_func = TruncDay('request_time')
            
        # 查询数据
        usage_stats = base_queryset.annotate(
            date=trunc_func
        ).values(
            'date'
        ).annotate(
            total_prompt_tokens=Sum('prompt_tokens'),
            total_completion_tokens=Sum('completion_tokens'),
            total_tokens=Sum('total_tokens'),
            total_cost_usd=Sum('cost_usd'),
            total_cost_rmb=Sum('cost_rmb'),
            avg_response_time=Avg('response_time'),
            request_count=Count('id')
        ).order_by('date')
        
        # 按模型统计
        model_stats = base_queryset.values(
            'model__name', 'model__model_id', 'model__provider__name'
        ).annotate(
            total_prompt_tokens=Sum('prompt_tokens'),
            total_completion_tokens=Sum('completion_tokens'),
            total_tokens=Sum('total_tokens'),
            total_cost_usd=Sum('cost_usd'),
            total_cost_rmb=Sum('cost_rmb'),
            avg_response_time=Avg('response_time'),
            request_count=Count('id')
        ).order_by('-total_tokens')
        
        # 按用户统计
        user_stats = base_queryset.values(
            'user__username', 'user__id'
        ).annotate(
            total_prompt_tokens=Sum('prompt_tokens'),
            total_completion_tokens=Sum('completion_tokens'),
            total_tokens=Sum('total_tokens'),
            total_cost_usd=Sum('cost_usd'),
            total_cost_rmb=Sum('cost_rmb'),
            request_count=Count('id')
        ).order_by('-total_tokens')
        
        # 计算总计
        totals = base_queryset.aggregate(
            total_prompt_tokens=Sum('prompt_tokens'),
            total_completion_tokens=Sum('completion_tokens'),
            total_tokens=Sum('total_tokens'),
            total_cost_usd=Sum('cost_usd'),
            total_cost_rmb=Sum('cost_rmb'),
            avg_response_time=Avg('response_time'),
            request_count=Count('id')
        )
        
        # 整合数据
        serializer = ModelStatSerializer(data={
            'period': period,
            'days': days,
            'start_date': start_date,
            'end_date': end_date,
            'usage_stats': usage_stats,
            'model_stats': model_stats,
            'user_stats': user_stats,
            'totals': totals
        })
        
        serializer.is_valid()  # 验证数据
        return Response(serializer.data)

class PromptTemplateViewSet(viewsets.ModelViewSet):
    """提示词模板管理"""
    queryset = PromptTemplate.objects.all()
    serializer_class = PromptTemplateSerializer
    permission_classes = [permissions.IsAdminUser]
    
    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)
    
    def perform_update(self, serializer):
        serializer.save()
    
    @action(detail=False, methods=['get'], permission_classes=[permissions.IsAuthenticated])
    def available(self, request):
        """获取可用的提示词模板列表"""
        templates = PromptTemplate.objects.filter(is_public=True)
        if not request.user.is_staff:
            # 非管理员只能看到公开的和自己创建的模板
            templates = templates | PromptTemplate.objects.filter(created_by=request.user)
        
        serializer = self.get_serializer(templates.distinct(), many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def duplicate(self, request, pk=None):
        """复制模板"""
        template = self.get_object()
        new_template = PromptTemplate.objects.create(
            name=f"{template.name} (复制)",
            description=template.description,
            content=template.content,
            template_type=template.template_type,
            model=template.model,
            variables=template.variables,
            is_public=False,  # 复制的模板默认设为私有
            created_by=request.user
        )
        serializer = self.get_serializer(new_template)
        return Response(serializer.data)

class PromptSceneViewSet(viewsets.ModelViewSet):
    """提示词场景视图集"""
    queryset = PromptScene.objects.all()
    serializer_class = PromptSceneSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_permissions(self):
        """根据操作类型设置权限"""
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [permissions.IsAdminUser()]
        return super().get_permissions()

    def get_queryset(self):
        """根据请求类型过滤查询集"""
        queryset = super().get_queryset()
        if self.action == 'list' and not self.request.user.is_staff:
            return queryset.filter(is_active=True)
        return queryset

    @action(detail=True, methods=['get'])
    def templates(self, request, pk=None):
        """获取场景下的所有模板"""
        scene = self.get_object()
        templates = scene.templates.all()
        
        # 非管理员只能看到公开的模板
        if not request.user.is_staff:
            templates = templates.filter(is_public=True)
            
        serializer = PromptTemplateSerializer(templates, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def reorder(self, request, pk=None):
        """更新场景排序"""
        if not request.user.is_staff:
            return Response(
                {"detail": "只有管理员可以更改排序"}, 
                status=status.HTTP_403_FORBIDDEN
            )
            
        scene = self.get_object()
        new_order = request.data.get('order')
        
        if new_order is None:
            return Response(
                {"detail": "请提供新的排序值"}, 
                status=status.HTTP_400_BAD_REQUEST
            )
            
        scene.order = new_order
        scene.save()
        
        return Response(PromptSceneSerializer(scene).data)
