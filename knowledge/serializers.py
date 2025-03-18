from rest_framework import serializers
from .models import Category, Tag, Conversation, Message, KnowledgePoint

class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = ['id', 'name']

class CategorySerializer(serializers.ModelSerializer):
    parent_name = serializers.SerializerMethodField()
    
    class Meta:
        model = Category
        fields = ['id', 'name', 'description', 'parent', 'parent_name', 'created_at']
    
    def get_parent_name(self, obj):
        return obj.parent.name if obj.parent else None

class MessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = Message
        fields = ['id', 'role', 'content', 'timestamp']

class ConversationSerializer(serializers.ModelSerializer):
    tags = TagSerializer(many=True, read_only=True)
    category_name = serializers.SerializerMethodField()
    message_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Conversation
        fields = ['id', 'title', 'summary', 'category', 'category_name', 
                  'tags', 'created_at', 'updated_at', 'message_count']
        extra_kwargs = {
            'title': {'required': False, 'default': '未命名对话'}
        }
    
    def get_category_name(self, obj):
        return obj.category.name if obj.category else None
    
    def get_message_count(self, obj):
        return obj.messages.count()

class ConversationDetailSerializer(ConversationSerializer):
    messages = MessageSerializer(many=True, read_only=True)
    
    class Meta(ConversationSerializer.Meta):
        fields = ConversationSerializer.Meta.fields + ['messages']

class KnowledgePointSerializer(serializers.ModelSerializer):
    tags = TagSerializer(many=True, read_only=True)
    category_name = serializers.SerializerMethodField()
    
    class Meta:
        model = KnowledgePoint
        fields = ['id', 'title', 'content', 'category', 'category_name', 
                  'tags', 'created_at', 'updated_at']
    
    def get_category_name(self, obj):
        return obj.category.name if obj.category else None