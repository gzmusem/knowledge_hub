import { defineStore } from 'pinia';
import api from '@/api/api';
import requestControl from '@/utils/requestControl';

export const useChatStore = defineStore('chat', {
  state: () => ({
    conversations: [],
    currentConversation: null,
    currentMessages: [],
    loading: false,
    error: null,
    pendingRequests: new Map(),
    lastLoadedConversationId: null
  }),
  
  actions: {
    async getConversations() {
      try {
        const response = await api.getConversations();
        this.conversations = response;
        return response;
      } catch (error) {
        console.error('获取对话列表失败:', error);
        this.error = error.message;
        return [];
      }
    },
    
    async getConversation(id) {
      if (!id || id === 'new') {
        this.currentConversation = null;
        return null;
      }
      
      try {
        console.log(`[Store] 获取对话: ${id}`);
        const response = await api.chat.getConversation(id);
        this.currentConversation = response;
        return response;
      } catch (error) {
        console.error(`[Store] 获取对话失败:`, error);
        this.error = error.message;
        return null;
      }
    },
    
    async getMessages(conversationId) {
      if (!conversationId || conversationId === 'new') {
        this.currentMessages = [];
        return [];
      }
      
      try {
        console.log(`[Store] 获取消息: ${conversationId}`);
        const response = await api.chat.getMessages(conversationId);
        this.currentMessages = Array.isArray(response) ? response : [];
        return this.currentMessages;
      } catch (error) {
        console.error(`[Store] 获取消息失败:`, error);
        this.error = error.message;
        return [];
      }
    },
    
    async sendMessage(content, conversationId = null, modelId = null) {
      try {
        this.loading = true;
        
        // 确保content是字符串
        let contentStr;
        if (typeof content === 'object') {
          contentStr = String(content.content || '');
          console.warn('[Store] 警告：传入了对象类型的content，已提取内容字段');
        } else {
          contentStr = String(content || '');
        }
        
        console.log(`[Store] 发送消息: "${contentStr}" 到对话: ${conversationId || '新对话'}`);
        
        // 处理会话ID
        let targetId = conversationId;
        
        if (!targetId || targetId === 'new') {
          // 创建新对话
          const title = contentStr.length > 0 
            ? contentStr.substring(0, 30) + (contentStr.length > 30 ? '...' : '') 
            : '新对话';
            
          console.log(`[Store] 创建新对话，标题: "${title}"`);
          
          const newConversation = await api.chat.createConversation({ title });
          
          targetId = newConversation.id;
          this.currentConversation = newConversation;
          console.log(`[Store] 创建了新对话，ID: ${targetId}`);
        }
        
        // 发送消息并获取响应
        console.log(`[Store] 发送消息到API，内容: "${contentStr}", ID: ${targetId}`);
        
        const response = await api.chat.sendMessage(targetId, {
          content: contentStr,
          role: 'user',
          model_id: modelId
        });
        
        // 关键修改：正确处理接收到的数据
        if (response && response.data) {
          console.log('[Store] 收到API响应数据:', response.data);
          
          // 确保当前消息列表是数组
          if (!Array.isArray(this.currentMessages)) {
            this.currentMessages = [];
          }
          
          // 添加用户消息到列表
          if (response.data.user_message) {
            console.log('[Store] 添加用户消息到列表:', response.data.user_message);
            this.currentMessages.push(response.data.user_message);
          }
          
          // 添加AI回复到列表
          if (response.data.assistant_message) {
            console.log('[Store] 添加AI回复到列表:', response.data.assistant_message);
            this.currentMessages.push(response.data.assistant_message);
          }
          
          // 确保视图更新
          this.currentMessages = [...this.currentMessages];
        } else {
          console.warn('[Store] API响应没有返回预期的数据结构:', response);
        }
        
        return {
          success: true,
          conversationId: targetId
        };
      } catch (error) {
        console.error('[Store] 发送消息失败:', error);
        this.error = error.message;
        return {
          success: false,
          error: error.message
        };
      } finally {
        this.loading = false;
      }
    },
    
    async searchConversations(query) {
      try {
        this.loading = true;
        const response = await api.searchConversations(query);
        return response.data;
      } catch (error) {
        console.error('搜索对话失败:', error);
        this.error = error.response?.data?.detail || error.message;
        return [];
      } finally {
        this.loading = false;
      }
    },
    
    async deleteConversation(conversationId) {
      try {
        this.loading = true;
        await api.chat.deleteConversation(conversationId);
        return true;
      } catch (error) {
        console.error('删除对话失败:', error);
        this.error = error.response?.data?.detail || error.message;
        throw error;
      } finally {
        this.loading = false;
      }
    },
    
    setConversations(conversations) {
      this.conversations = conversations;
    },
    
    clearCurrentConversation() {
      requestControl.reset();
      this.currentConversation = null;
      this.currentMessages = [];
      this.lastLoadedConversationId = null;
    },
    
    clearError() {
      this.error = null;
    },
    
    async fetchRecentConversations(params = { page: 1, pageSize: 10 }) {
      try {
        console.log('[Store] 获取最近对话列表, 参数:', params);
        const response = await api.chat.getConversations(params);
        
        // 记录原始响应数据
        console.log('[Store] 获取对话列表响应:', response);
        
        // 确保数据是数组
        const conversationsData = Array.isArray(response) ? response : 
                                 (Array.isArray(response.data) ? response.data : []);
        
        // 更新 store 状态
        this.conversations = [...conversationsData];
        console.log('[Store] 更新对话列表完成, 数量:', this.conversations.length);
        
        return {
          data: conversationsData,
          total: conversationsData.length,
          page: params.page
        };
      } catch (error) {
        console.error('[Store] 获取对话列表失败:', error);
        // 返回空数组而不是undefined
        return {
          data: [],
          total: 0,
          page: params.page
        };
      }
    }
  }
});
