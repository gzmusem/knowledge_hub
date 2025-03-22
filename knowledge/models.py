from django.db import models
from django.conf import settings

class Category(models.Model):
    """知识分类"""
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    parent = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='children')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "分类"
        verbose_name_plural = "分类"
        ordering = ['name']
    
    def __str__(self):
        return self.name

class Tag(models.Model):
    """标签"""
    name = models.CharField(max_length=50)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    
    class Meta:
        verbose_name = "标签"
        verbose_name_plural = "标签"
        unique_together = ['name', 'user']
    
    def __str__(self):
        return self.name

class Conversation(models.Model):
    """对话会话"""
    title = models.CharField(max_length=200)
    summary = models.TextField(blank=True)
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, blank=True)
    tags = models.ManyToManyField(Tag, blank=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "对话"
        verbose_name_plural = "对话"
        ordering = ['-updated_at']
    
    def __str__(self):
        return self.title

class Message(models.Model):
    """对话消息"""
    ROLE_CHOICES = [
        ('user', '用户'),
        ('assistant', '助手'),
        ('system', '系统')
    ]
    
    conversation = models.ForeignKey(Conversation, on_delete=models.CASCADE, related_name='messages')
    role = models.CharField(max_length=10, choices=ROLE_CHOICES)
    content = models.TextField()
    embedding = models.JSONField(null=True, blank=True)
    metadata = models.JSONField(null=True, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    
    # 添加一个指纹字段来防止重复
    message_hash = models.CharField(max_length=40, blank=True, null=True, db_index=True)
    # 或者添加一个请求ID字段
    request_id = models.CharField(max_length=100, blank=True, null=True)
    
    class Meta:
        verbose_name = "消息"
        verbose_name_plural = "消息"
        ordering = ['timestamp']
        # 添加一个约束，防止在短时间内创建相同内容的消息
        # 注意：这需要数据库支持（例如 PostgreSQL）
        constraints = [
            models.UniqueConstraint(
                fields=['conversation', 'role', 'message_hash'],
                name='unique_message_in_conversation'
            ),
        ]
    
    def save(self, *args, **kwargs):
        # 生成消息哈希值（如果未提供）
        if not self.message_hash and self.content:
            import hashlib
            self.message_hash = hashlib.md5(self.content.encode()).hexdigest()
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"{self.role}: {self.content[:50]}..."

class KnowledgePoint(models.Model):
    """知识点"""
    title = models.CharField(max_length=200)
    content = models.TextField()
    source_message = models.ForeignKey(Message, on_delete=models.SET_NULL, null=True, blank=True)
    category = models.ForeignKey(Category, on_delete=models.CASCADE)
    tags = models.ManyToManyField(Tag, blank=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "知识点"
        verbose_name_plural = "知识点"
        ordering = ['-updated_at']
    
    def __str__(self):
        return self.title

