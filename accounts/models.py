from django.db import models
from django.contrib.auth.models import AbstractUser

class User(AbstractUser):
    """扩展用户模型"""
    bio = models.TextField(blank=True)
    avatar = models.ImageField(upload_to='avatars/', null=True, blank=True)
    
    def __str__(self):
        return self.username