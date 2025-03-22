from rest_framework import serializers
from knowledge.ai_models import ModelProvider, AIModel, TokenUsage, PromptTemplate, PromptScene

class ModelProviderSerializer(serializers.ModelSerializer):
    class Meta:
        model = ModelProvider
        fields = '__all__'
        extra_kwargs = {
            'api_key': {'write_only': True},
            'api_secret': {'write_only': True}
        }

class AIModelSerializer(serializers.ModelSerializer):
    provider_name = serializers.SerializerMethodField()
    
    class Meta:
        model = AIModel
        fields = '__all__'
        
    def get_provider_name(self, obj):
        return obj.provider.name if obj.provider else None

class TokenUsageSerializer(serializers.ModelSerializer):
    user_name = serializers.SerializerMethodField()
    model_name = serializers.SerializerMethodField()
    
    class Meta:
        model = TokenUsage
        fields = '__all__'
        
    def get_user_name(self, obj):
        return obj.user.username if obj.user else None
        
    def get_model_name(self, obj):
        return obj.model.name if obj.model else None

class ModelStatSerializer(serializers.Serializer):
    """用于模型使用统计的序列化器"""
    period = serializers.CharField()
    days = serializers.IntegerField()
    start_date = serializers.DateTimeField()
    end_date = serializers.DateTimeField()
    usage_stats = serializers.ListField(child=serializers.DictField())
    model_stats = serializers.ListField(child=serializers.DictField())
    user_stats = serializers.ListField(child=serializers.DictField())
    totals = serializers.DictField()

class PromptSceneSerializer(serializers.ModelSerializer):
    """提示词场景序列化器"""
    template_count = serializers.SerializerMethodField()

    class Meta:
        model = PromptScene
        fields = [
            'id', 'name', 'code', 'description', 'icon', 
            'order', 'is_active', 'created_at', 'updated_at',
            'template_count'
        ]
        read_only_fields = ['created_at', 'updated_at']

    def get_template_count(self, obj):
        """获取场景下的模板数量"""
        return obj.templates.count()

    def validate_code(self, value):
        """验证场景代码格式"""
        if not value.isascii() or not value.islower():
            raise serializers.ValidationError("场景代码只能包含小写字母、数字和下划线")
        return value

class PromptTemplateSerializer(serializers.ModelSerializer):
    """提示词模板序列化器"""
    scene_name = serializers.CharField(source='scene.name', read_only=True)
    
    class Meta:
        model = PromptTemplate
        fields = [
            'id', 'name', 'description', 'content', 
            'scene', 'scene_name', 'template_type',
            'system_prompt', 'model', 'variables',
            'example_values', 'is_public', 'created_by',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']
        
    def validate_variables(self, value):
        """验证变量字段格式"""
        if not isinstance(value, dict):
            raise serializers.ValidationError("变量必须是字典格式")
        return value