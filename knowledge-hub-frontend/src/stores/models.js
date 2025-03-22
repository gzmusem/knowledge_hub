// src/stores/models.js
import { defineStore } from 'pinia';
import apiService from '@/api/api';

export const useModelStore = defineStore('models', {
  state: () => ({
    availableModels: [],
    preferredModel: null,
    loading: false,
    error: null
  }),
  
  getters: {
    modelOptions: (state) => {
      return state.availableModels.map(model => ({
        value: model.model_id,
        label: model.name,
        provider: model.provider
      }));
    },
    
    currentModel: (state) => {
      return state.preferredModel || 'openai:gpt-3.5-turbo';
    }
  },
  
  actions: {
    async fetchAvailableModels() {
      try {
        this.loading = true;
        console.log('[DEBUG] Store - 开始获取可用模型');
        
        // 调用API获取模型列表
        const response = await apiService.models.getAvailableModels();
        console.log('[DEBUG] Store - 获取模型响应:', response);
        
        if (response && response.data) {
          this.availableModels = response.data;
          console.log('[DEBUG] Store - 更新可用模型:', this.availableModels);
        } else {
          console.warn('[警告] 模型API返回空数据');
          // 提供默认模型防止UI为空
          this.availableModels = [
            { model_id: 'qwq-32b', name: '通义千问-QwQ-32B', is_default: true }
          ];
        }
        
        // 从localStorage获取用户偏好
        const savedModel = localStorage.getItem('preferredModel');
        if (savedModel) {
          this.preferredModel = savedModel;
        } else if (this.availableModels.length > 0) {
          // 设置默认模型
          const defaultModel = this.availableModels.find(m => m.is_default) || this.availableModels[0];
          this.preferredModel = defaultModel.model_id;
        }
        
        return this.availableModels;
      } catch (error) {
        console.error('[ERROR] 获取模型列表失败:', error);
        this.error = error.message;
        // 提供默认值防止UI为空
        this.availableModels = [
          { model_id: 'qwq-32b', name: '通义千问-QwQ-32B', is_default: true }
        ];
        return this.availableModels;
      } finally {
        this.loading = false;
      }
    },
    
    setPreferredModel(modelId) {
      this.preferredModel = modelId;
      // 保存到本地存储
      localStorage.setItem('preferredModel', modelId);
    },

    async updateModelStatus(modelId, isActive) {
      try {
        await apiService.models.updateStatus(modelId, isActive);
        const model = this.availableModels.find(m => m.model_id === modelId);
        if (model) {
          model.is_active = isActive;
        }
      } catch (error) {
        console.error('[Store] 更新模型状态失败:', error);
        throw error;
      }
    }
  },
  
  // 启用持久化
  persist: {
    enabled: true,
    strategies: [
      {
        key: 'model-preferences',
        storage: localStorage,
        paths: ['preferredModel']
      }
    ]
  }
});