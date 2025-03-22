import axios from 'axios';
import router from '@/router';

// 检查 axios 基础配置，确保没有重复的 api 前缀
axios.defaults.baseURL = 'http://localhost:8000';  // 不要在这里加 /api

// 创建axios实例
const api = axios.create({
  baseURL: 'http://localhost:8000',  // 不要在这里加 /api
  headers: {
    'Content-Type': 'application/json',
  },
});

// 请求拦截器
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('token');
    if (token) {
      config.headers.Authorization = `Token ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// 响应拦截器
api.interceptors.response.use(
  (response) => {
    return response;
  },
  (error) => {
    // 处理401未授权错误
    if (error.response?.status === 401) {
      // 清除token
      localStorage.removeItem('token');
      
      // 如果不是在登录页，则重定向到登录页
      if (router.currentRoute.value.path !== '/login') {
        router.push('/login');
      }
    }
    
    return Promise.reject(error);
  }
);

// API路径封装
const apiService = {
  // 认证相关
  auth: {
    login: (credentials) => api.post('/api/auth/login/', credentials),
    logout: () => api.post('/api/auth/logout/'),
    getUser: () => api.get('/api/auth/user/'),
    register: (userData) => api.post('/api/auth/register/', userData),
    getProfile: () => api.get('/api/auth/profile/'),
    updateProfile: (data) => api.put('/api/auth/profile/', data),
    checkAuth: () => api.get('/api/auth/user/')
  },
  
  // 知识库相关
  knowledge: {
    getCategories: () => api.get('/api/categories/'),
    getTags: () => api.get('/api/tags/'),
    getKnowledgePoints: (params) => api.get('/api/knowledge-points/', { params }),
    createKnowledgePoint: (data) => api.post('/knowledge-points/', data),
    updateKnowledgePoint: (id, data) => api.put(`/knowledge-points/${id}/`, data),
    deleteKnowledgePoint: (id) => api.delete(`/knowledge-points/${id}/`),
  },
  
  // 对话相关
  chat: {
    async getConversations(params = { page: 1, pageSize: 10 }) {
      try {
        const response = await api.get('/api/conversations/', { params });
        // 确保返回数组，即使后端返回null或undefined
        return Array.isArray(response.data) ? response.data : [];
      } catch (error) {
        console.error('API 获取对话列表失败:', error);
        // 返回空数组而不是让错误传播
        return [];
      }
    },
    
    async getConversation(id) {
      try {
        const response = await api.get(`/api/conversations/${id}/`);
        return response.data; // 这通常是一个对象，不需要数组检查
      } catch (error) {
        console.error(`API 获取对话失败 (ID: ${id}):`, error);
        throw error; // 这里可以抛出错误，让调用者处理
      }
    },
    
    createConversation: async (data = { title: '新对话' }) => {
      console.log('[DEBUG] API - 创建对话:', data);
      const response = await api.post('/api/conversations/', data);
      console.log('[DEBUG] API - 创建对话响应:', response.data);
      return response.data; // 直接返回数据，不是整个response
    },
    
    sendMessage: (conversationId, data) => {
      const cleanId = typeof conversationId === 'string' && conversationId.startsWith('chat-') 
        ? conversationId.replace('chat-', '') 
        : conversationId;
      // 转换字段名以匹配后端期望
      const requestData = {
        message: data.content,  // 从 'content' 转为 'message'
        model_id: data.model_id,
        role: data.role
      };
      
      console.log('[API] 发送消息请求体:', requestData);
      
      return api.post(`/api/conversations/${cleanId}/add_message/`, requestData);
    },
    
    
    async getMessages(conversationId) {
      try {
        const response = await api.get(`/api/conversations/${conversationId}/messages/`);
        // 确保返回数组
        return Array.isArray(response.data) ? response.data : [];
      } catch (error) {
        console.error(`API 获取消息失败 (对话ID: ${conversationId}):`, error);
        return []; // 返回空数组
      }
    },
    searchConversations: (query) => api.get('/conversations/search/', { params: { q: query } }),
    deleteConversation: (id) => {
      const cleanId = typeof id === 'string' && id.startsWith('chat-') 
        ? id.replace('chat-', '') 
        : id;
      return api.delete(`/api/conversations/${cleanId}/`);
    },
    updateConversation: (id, data) => {
      const cleanId = typeof id === 'string' && id.startsWith('chat-') 
        ? id.replace('chat-', '') 
        : id;
      return api.put(`/api/conversations/${cleanId}/`, data);
    }
  },
  
  // 添加模型相关API
  models: {
    getProviders: () => api.get('/api/model-providers/'),
    getProvider: (id) => api.get(`/api/model-providers/${id}/`),
    createProvider: (data) => api.post('/api/model-providers/', data),
    updateProvider: (id, data) => api.put(`/api/model-providers/${id}/`, data),
    deleteProvider: (id) => api.delete(`/api/model-providers/${id}/`),
    
    getModels: () => api.get('/api/ai-models/'),
    getModel: (id) => api.get(`/api/ai-models/${id}/`),
    createModel: (data) => api.post('/api/ai-models/', data),
    updateModel: (id, data) => api.put(`/api/ai-models/${id}/`, data),
    deleteModel: (id) => api.delete(`/api/ai-models/${id}/`),
    setDefaultModel: (id) => api.post(`/api/ai-models/${id}/set_default/`),
    
    getAvailableModels: () => api.get('/api/ai-models/available/'),
    
    getTokenUsage: (params) => api.get('/api/token-usage/', { params }),
    getTokenUsageSummary: () => api.get('/api/token-usage/stats/', { params: { period: 'day', days: 30 } })
  },
  
  // 添加提示词场景相关API
  promptScenes: {
    // 获取所有场景
    getScenes: () => {
      console.log('调用获取场景列表API'); // 添加日志
      return api.get('/api/prompt-scenes/');
    },
    
    // 获取单个场景详情
    getScene: (id) => api.get(`/api/prompt-scenes/${id}/`),
    
    // 创建新场景
    createScene: (data) => api.post('/api/prompt-scenes/', data),
    
    // 更新场景
    updateScene: (id, data) => api.put(`/api/prompt-scenes/${id}/`, data),
    
    // 删除场景
    deleteScene: (id) => api.delete(`/api/prompt-scenes/${id}/`),
    
    // 获取场景下的所有模板
    getSceneTemplates: (id) => api.get(`/api/prompt-scenes/${id}/templates/`),
    
    // 更新场景排序
    reorderScene: (id, order) => api.post(`/api/prompt-scenes/${id}/reorder/`, { order }),
    
    // 获取所有可用（已激活）的场景
    getActiveScenes: () => api.get('/api/prompt-scenes/', { params: { is_active: true } })
  },
  
  // 修改现有的 prompts 对象，添加场景相关参数
  prompts: {
    getTemplates: (params = {}) => {
      return api.get('/api/prompt-templates/', { params });
    },
    getTemplate: (id) => api.get(`/api/prompt-templates/${id}/`),
    createTemplate: (data) => api.post('/api/prompt-templates/', data),
    updateTemplate: (id, data) => api.put(`/api/prompt-templates/${id}/`, data),
    deleteTemplate: (id) => api.delete(`/api/prompt-templates/${id}/`),
    getAvailableTemplates: (params = {}) => api.get('/api/prompt-templates/available/', { params }),
    duplicateTemplate: (id) => api.post(`/api/prompt-templates/${id}/duplicate/`)
  },
};

export default apiService;
export { api };  // 导出原始实例，以便需要时直接使用
