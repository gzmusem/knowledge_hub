from rest_framework import serializers
from knowledge.ai_models import ModelProvider, AIModel, TokenUsage

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
