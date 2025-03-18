import openai
from django.conf import settings

# 设置OpenAI API密钥
openai.api_key = settings.OPENAI_API_KEY

def get_ai_response(conversation, user_message):
    """从大模型获取回复"""
    # 构建对话历史
    messages = []
    
    # 添加系统信息
    messages.append({
        "role": "system",
        "content": "你是一个知识助手，帮助用户回答问题并提供准确的信息。"
    })
    
    # 添加历史消息（最多5条）
    history = conversation.messages.order_by('-timestamp')[:10]
    for msg in reversed(list(history)):
        messages.append({
            "role": msg.role,
            "content": msg.content
        })
    
    # 添加当前用户消息
    messages.append({
        "role": "user",
        "content": user_message
    })
    
    # 调用API
    try:
        response = openai.chat.completions.create(  # type: ignore
            model="gpt-3.5-turbo",  # 或其他模型
            messages=messages,
            max_tokens=1500,
            temperature=0.7
        )
        return response.choices[0].message.content
    except Exception as e:
        print(f"OpenAI API错误: {e}")
        return "抱歉，我现在无法回答这个问题。请稍后再试。"

def extract_knowledge_structure(conversation_id):
    """
    从对话中提取知识结构
    这个函数会在异步任务中被调用
    """
    from .models import Conversation, Category, Tag, KnowledgePoint
    
    try:
        conversation = Conversation.objects.get(id=conversation_id)
        
        # 获取对话内容
        messages = conversation.messages.all().order_by('timestamp')  # type: ignore
        conversation_text = "\n".join([f"{msg.role}: {msg.content}" for msg in messages])
        
        # 创建提示以提取知识结构
        prompt = f"""
        分析下面的对话，提取以下信息：
        1. 主要主题/领域
        2. 关键概念和定义
        3. 重要知识点（带标题和内容）
        4. 适合的标签（5个以内）
        5. 对话摘要（100字以内）
        
        以JSON格式返回，结构如下：
        {{
          "main_topic": "主题名称",
          "description": "主题描述",
          "knowledge_points": [
            {{
              "title": "知识点标题",
              "content": "知识点内容",
              "tags": ["标签1", "标签2"]
            }}
          ],
          "tags": ["标签1", "标签2", "标签3"],
          "summary": "摘要文本"
        }}
        
        对话内容：
        {conversation_text}
        """
        
        response = openai.chat.completions.create(  # type: ignore
            model="gpt-3.5-turbo",  # 或使用gpt-4获取更好的结果
            messages=[
                {"role": "system", "content": "你是一个知识分析专家，擅长从对话中提取知识结构。"},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3,
            max_tokens=2000
        )
        
        # 解析响应
        import json
        content = response.choices[0].message.content
        if content is None:
            content = "{}"
        analysis = json.loads(content)
        
        # 更新对话摘要
        conversation.summary = analysis.get('summary', '')
        conversation.save()
        
        # 处理主题/分类
        main_topic = analysis.get('main_topic', '未分类')
        category, created = Category.objects.get_or_create(
            name=main_topic,
            user=conversation.user,
            defaults={'description': analysis.get('description', '')}
        )
        
        # 更新对话分类
        conversation.category = category
        conversation.save()
        
        # 处理标签
        tags = []
        for tag_name in analysis.get('tags', []):
            tag, created = Tag.objects.get_or_create(
                name=tag_name,
                user=conversation.user
            )
            tags.append(tag)
        
        # 更新对话标签
        conversation.tags.set(tags)
        
        # 处理知识点
        for point_data in analysis.get('knowledge_points', []):
            # 创建知识点
            knowledge_point = KnowledgePoint.objects.create(
                title=point_data.get('title', '未命名知识点'),
                content=point_data.get('content', ''),
                category=category,
                user=conversation.user
            )
            
            # 添加标签
            point_tags = []
            for tag_name in point_data.get('tags', []):
                tag, created = Tag.objects.get_or_create(
                    name=tag_name,
                    user=conversation.user
                )
                point_tags.append(tag)
            
            knowledge_point.tags.set(point_tags)
        
        return True
    
    except Exception as e:
        print(f"知识提取错误: {e}")
        return False