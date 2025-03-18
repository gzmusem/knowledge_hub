from celery import shared_task
from .utils import extract_knowledge_structure

@shared_task
def process_conversation_knowledge(conversation_id):
    """异步处理对话知识提取"""
    return extract_knowledge_structure(conversation_id)