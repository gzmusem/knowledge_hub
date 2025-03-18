import time
import json
from django.utils import timezone

class RequestLogMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # 请求开始时间
        start_time = time.time()
        
        # 记录请求信息
        request_data = {
            'path': request.path,
            'method': request.method,
            'user': str(request.user) if request.user.is_authenticated else 'Anonymous',
            'time': timezone.now().strftime('%Y-%m-%d %H:%M:%S'),
        }
        
        # 尝试记录请求体(POST/PUT)
        if request.method in ['POST', 'PUT', 'PATCH'] and request.content_type == 'application/json':
            try:
                request_data['body'] = json.loads(request.body)
            except:
                request_data['body'] = '无法解析JSON'
        
        # 记录查询参数
        if request.GET:
            request_data['query_params'] = dict(request.GET)
            
        # 打印请求信息
        print("\n---------------------------------------------------")
        print(f"➡️ 接收请求: {request.method} {request.path}")
        print(f"👤 用户: {request_data['user']}")
        print(f"⏰ 时间: {request_data['time']}")
        if 'query_params' in request_data:
            print(f"🔍 查询参数: {request_data['query_params']}")
        if 'body' in request_data:
            print(f"📦 请求体: {request_data['body']}")
        
        # 获取响应
        response = self.get_response(request)
        
        # 计算执行时间
        duration = time.time() - start_time
        
        # 记录响应信息
        response_data = {
            'status_code': response.status_code,
            'duration': f"{duration:.4f}s",
        }
        
        # 尝试记录响应内容(仅对JSON响应)
        if hasattr(response, 'data'):
            try:
                response_data['content'] = response.data
            except:
                response_data['content'] = '无法获取响应数据'
        
        # 打印响应信息
        print(f"⬅️ 发送响应: {response.status_code}")
        print(f"⏱️ 耗时: {response_data['duration']}")
        if 'content' in response_data:
            print(f"📄 响应内容: {response_data['content']}")
        print("---------------------------------------------------\n")
        
        return response
