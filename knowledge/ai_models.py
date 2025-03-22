# knowledge/models/ai_models.py
from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone
from knowledge.models import Conversation, Message
from django.conf import settings
from django.core.exceptions import ValidationError

User = get_user_model()

class ModelProvider(models.Model):
    """模型提供商"""
    name = models.CharField(max_length=50, unique=True, verbose_name="提供商名称")
    slug = models.SlugField(max_length=50, unique=True, verbose_name="提供商标识")
    api_base = models.URLField(max_length=255, blank=True, verbose_name="API基础URL")
    api_version = models.CharField(max_length=20, blank=True, verbose_name="API版本")
    is_active = models.BooleanField(default=True, verbose_name="是否启用")
    
    # 认证信息
    auth_required = models.BooleanField(default=True, verbose_name="是否需要认证")
    api_key = models.CharField(max_length=100, blank=True, verbose_name="API密钥")
    api_secret = models.CharField(max_length=100, blank=True, verbose_name="API密钥2")
    
    description = models.TextField(blank=True, verbose_name="提供商描述")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="创建时间")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="更新时间")
    
    class Meta:
        verbose_name = "模型提供商"
        verbose_name_plural = "模型提供商"
        
    def __str__(self):
        return self.name

class AIModel(models.Model):
    """AI模型定义"""
    MODEL_TYPES = (
        ('chat', '对话模型'),
        ('text', '文本生成'),
        ('embedding', '向量嵌入'),
        ('image', '图像生成'),
        ('audio', '语音处理'),
    )
    
    # 基本信息
    name = models.CharField(max_length=100, verbose_name="模型名称")
    model_id = models.CharField(max_length=100, unique=True, verbose_name="模型ID")
    provider = models.ForeignKey(ModelProvider, on_delete=models.CASCADE, verbose_name="提供商")
    model_type = models.CharField(max_length=20, choices=MODEL_TYPES, default='chat', verbose_name="模型类型")
    
    # 参数配置
    max_tokens = models.IntegerField(default=2000, verbose_name="最大Token数")
    temperature = models.FloatField(default=0.7, verbose_name="温度")
    top_p = models.FloatField(default=1.0, verbose_name="Top P")
    presence_penalty = models.FloatField(default=0.0, verbose_name="存在惩罚")
    frequency_penalty = models.FloatField(default=0.0, verbose_name="频率惩罚")
    
    # 费用设置
    cost_prompt = models.FloatField(default=0.0, verbose_name="提示词每千Token成本(美元)")
    cost_completion = models.FloatField(default=0.0, verbose_name="回复每千Token成本(美元)")
    
    # 状态
    is_default = models.BooleanField(default=False, verbose_name="是否默认模型")
    is_active = models.BooleanField(default=True, verbose_name="是否启用")
    display_order = models.IntegerField(default=0, verbose_name="显示顺序")
    context_window = models.IntegerField(default=4096, verbose_name="上下文窗口大小")
    
    # 其他信息
    description = models.TextField(blank=True, verbose_name="模型描述")
    capabilities = models.JSONField(default=dict, blank=True, verbose_name="模型能力")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="创建时间")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="更新时间")
    
    class Meta:
        verbose_name = "AI模型"
        verbose_name_plural = "AI模型"
        ordering = ['display_order', 'provider__name', 'name']
        
    def __str__(self):
        return f"{self.provider.name} - {self.name}"
    
    def save(self, *args, **kwargs):
        # 确保只有一个默认模型
        if self.is_default:
            AIModel.objects.filter(is_default=True).update(is_default=False)
        super().save(*args, **kwargs)

class TokenUsage(models.Model):
    """Token使用记录"""
    # 关联信息
    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="用户")
    model = models.ForeignKey(AIModel, on_delete=models.SET_NULL, null=True, verbose_name="模型")
    conversation = models.ForeignKey(Conversation, on_delete=models.SET_NULL, null=True, verbose_name="对话")
    message = models.ForeignKey(Message, on_delete=models.SET_NULL, null=True, verbose_name="消息")
    
    # Token统计
    prompt_tokens = models.IntegerField(default=0, verbose_name="提示词Token数")
    completion_tokens = models.IntegerField(default=0, verbose_name="回复Token数")
    total_tokens = models.IntegerField(default=0, verbose_name="总Token数")
    
    # 成本计算
    cost_usd = models.FloatField(default=0.0, verbose_name="成本(美元)")
    cost_rmb = models.FloatField(default=0.0, verbose_name="成本(人民币)")
    
    # 请求信息
    request_time = models.DateTimeField(default=timezone.now, verbose_name="请求时间")
    response_time = models.FloatField(default=0.0, verbose_name="响应时间(秒)")
    is_successful = models.BooleanField(default=True, verbose_name="请求是否成功")
    error_message = models.TextField(blank=True, verbose_name="错误信息")
    
    # 元数据
    session_id = models.CharField(max_length=100, blank=True, verbose_name="会话ID")
    metadata = models.JSONField(default=dict, blank=True, verbose_name="元数据")
    
    class Meta:
        verbose_name = "Token使用记录"
        verbose_name_plural = "Token使用记录"
        indexes = [
            models.Index(fields=['user', 'request_time']),
            models.Index(fields=['model', 'request_time']),
        ]
        
    def __str__(self):
        return f"{self.user.username} - {self.model.name} - {self.request_time}"

class PromptScene(models.Model):
    """提示词场景"""
    name = models.CharField(max_length=50, verbose_name="场景名称")
    code = models.CharField(
        max_length=50, 
        unique=True, 
        verbose_name="场景代码",
        help_text="场景的唯一标识符，如：code_review"
    )
    description = models.TextField(
        blank=True, 
        verbose_name="场景描述"
    )
    icon = models.CharField(
        max_length=50, 
        blank=True,
        verbose_name="场景图标",
        help_text="可选的图标标识"
    )
    order = models.IntegerField(
        default=0, 
        verbose_name="排序",
        help_text="数字越小越靠前"
    )
    is_active = models.BooleanField(
        default=True, 
        verbose_name="是否启用"
    )
    created_at = models.DateTimeField(
        auto_now_add=True, 
        verbose_name="创建时间"
    )
    updated_at = models.DateTimeField(
        auto_now=True, 
        verbose_name="更新时间"
    )

    class Meta:
        verbose_name = "提示词场景"
        verbose_name_plural = "提示词场景"
        ordering = ['order', 'created_at']

    def __str__(self):
        return self.name

class PromptTemplate(models.Model):
    """提示词模板"""
    name = models.CharField(max_length=100, verbose_name="模板名称")
    description = models.TextField(blank=True, verbose_name="模板描述")
    content = models.TextField(verbose_name="模板内容")
    
    # 添加场景分类
    SCENE_TYPES = (
        ('general', '通用'),
        ('code_review', '代码审查'),
        ('document', '文档生成'),
        ('translation', '翻译助手'),
        ('qa', '问答系统'),
        # 可以根据需要添加更多场景
    )
    scene = models.ForeignKey(
        PromptScene,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='templates',
        verbose_name="所属场景"
    )
    
    TEMPLATE_TYPES = (
        ('system', '系统提示词'),
        ('user', '用户提示词'),
    )
    template_type = models.CharField(
        max_length=20, 
        choices=TEMPLATE_TYPES, 
        default='user',
        verbose_name="模板类型"
    )
    
    # 关联系统提示词（只有用户提示词可以关联系统提示词）
    system_prompt = models.ForeignKey(
        'self',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        limit_choices_to={'template_type': 'system'},
        related_name='user_prompts',
        verbose_name="关联的系统提示词"
    )
    
    # 关联AI模型
    model = models.ForeignKey(
        AIModel,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        verbose_name="关联模型"
    )
    
    variables = models.JSONField(
        default=dict,
        blank=True,
        verbose_name="变量定义",
        help_text="定义模板中使用的变量，格式：{'变量名': '变量说明'}"
    )
    
    # 添加示例值字段
    example_values = models.JSONField(
        default=dict,
        blank=True,
        verbose_name="变量示例值",
        help_text="变量的示例值，格式：{'变量名': '示例值'}"
    )
    
    is_public = models.BooleanField(default=True, verbose_name="是否公开")
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        verbose_name="创建者"
    )
    
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="创建时间")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="更新时间")
    
    class Meta:
        verbose_name = "提示词模板"
        verbose_name_plural = "提示词模板"
        ordering = ['-created_at']
        
    def clean(self):
        """模型验证"""
        super().clean()
        # 系统提示词不能关联系统提示词
        if self.template_type == 'system' and self.system_prompt:
            raise ValidationError('系统提示词不能关联系统提示词')
        
        # 验证变量定义和示例值的对应关系
        if self.variables and self.example_values:
            if not all(key in self.variables for key in self.example_values):
                raise ValidationError('示例值中包含未定义的变量')
    
    def save(self, *args, **kwargs):
        """保存前进行验证"""
        self.clean()
        super().save(*args, **kwargs)

    @property
    def full_content(self):
        """获取完整的提示词内容（包含系统提示词）"""
        if self.template_type == 'user' and self.system_prompt:
            return {
                'system_prompt': self.system_prompt.content,
                'user_prompt': self.content
            }
        return {
            'system_prompt': None,
            'user_prompt': self.content
        }