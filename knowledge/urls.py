from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import CategoryViewSet, TagViewSet, ConversationViewSet, KnowledgePointViewSet
from .views_model import ModelProviderViewSet, AIModelViewSet, TokenUsageViewSet, PromptTemplateViewSet, PromptSceneViewSet

router = DefaultRouter()
router.register(r'categories', CategoryViewSet, basename='category')
router.register(r'tags', TagViewSet, basename='tag')
router.register(r'conversations', ConversationViewSet, basename='conversation')
router.register(r'knowledge-points', KnowledgePointViewSet, basename='knowledge-point')

# 确保这些路径正确
router.register(r'model-providers', ModelProviderViewSet, basename='model-provider')
router.register(r'ai-models', AIModelViewSet, basename='ai-model')  # 注意这里是 ai-models
router.register(r'token-usage', TokenUsageViewSet, basename='token-usage')
router.register(r'prompt-templates', PromptTemplateViewSet, basename='prompt-template')
router.register(r'prompt-scenes', PromptSceneViewSet)

urlpatterns = [
    path('', include(router.urls)),
    # 其他路径...
]
