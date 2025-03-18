import { defineStore } from 'pinia';
import apiService from '@/api/api';

export const useModelConfigStore = defineStore('modelConfig', {
  state: () => ({
    providers: [],
    models: [],
    tokenUsage: [],
    loading: false,
    error: null
  }),
  
  actions: {
    // 提供商相关操作
    async fetchProviders() {
      try {
        this.loading = true;
        const response = await apiService.models.getProviders();
        this.providers = response.data;
        return this.providers;
      } catch (error) {
        this.error = error.message;
        console.error('获取提供商列表失败:', error);
        throw error;
      } finally {
        this.loading = false;
      }
    },
    
    async getProvider(id) {
      try {
        this.loading = true;
        const response = await apiService.models.getProvider(id);
        return response.data;
      } catch (error) {
        this.error = error.message;
        console.error('获取提供商详情失败:', error);
        throw error;
      } finally {
        this.loading = false;
      }
    },
    
    async createProvider(data) {
      try {
        this.loading = true;
        const response = await apiService.models.createProvider(data);
        await this.fetchProviders(); // 刷新列表
        return response.data;
      } catch (error) {
        this.error = error.message;
        console.error('创建提供商失败:', error);
        throw error;
      } finally {
        this.loading = false;
      }
    },
    
    async updateProvider(id, data) {
      try {
        this.loading = true;
        const response = await apiService.models.updateProvider(id, data);
        await this.fetchProviders(); // 刷新列表
        return response.data;
      } catch (error) {
        this.error = error.message;
        console.error('更新提供商失败:', error);
        throw error;
      } finally {
        this.loading = false;
      }
    },
    
    async deleteProvider(id) {
      try {
        this.loading = true;
        await apiService.models.deleteProvider(id);
        await this.fetchProviders(); // 刷新列表
        return true;
      } catch (error) {
        this.error = error.message;
        console.error('删除提供商失败:', error);
        throw error;
      } finally {
        this.loading = false;
      }
    },
    
    // 模型相关操作
    async fetchModels() {
      try {
        this.loading = true;
        const response = await apiService.models.getModels();
        this.models = response.data;
        return this.models;
      } catch (error) {
        this.error = error.message;
        console.error('获取模型列表失败:', error);
        throw error;
      } finally {
        this.loading = false;
      }
    },
    
    async getModel(id) {
      try {
        this.loading = true;
        const response = await apiService.models.getModel(id);
        return response.data;
      } catch (error) {
        this.error = error.message;
        console.error('获取模型详情失败:', error);
        throw error;
      } finally {
        this.loading = false;
      }
    },
    
    async createModel(data) {
      try {
        this.loading = true;
        const response = await apiService.models.createModel(data);
        await this.fetchModels(); // 刷新列表
        return response.data;
      } catch (error) {
        this.error = error.message;
        console.error('创建模型失败:', error);
        throw error;
      } finally {
        this.loading = false;
      }
    },
    
    async updateModel(id, data) {
      try {
        this.loading = true;
        const response = await apiService.models.updateModel(id, data);
        await this.fetchModels(); // 刷新列表
        return response.data;
      } catch (error) {
        this.error = error.message;
        console.error('更新模型失败:', error);
        throw error;
      } finally {
        this.loading = false;
      }
    },
    
    async deleteModel(id) {
      try {
        this.loading = true;
        await apiService.models.deleteModel(id);
        await this.fetchModels(); // 刷新列表
        return true;
      } catch (error) {
        this.error = error.message;
        console.error('删除模型失败:', error);
        throw error;
      } finally {
        this.loading = false;
      }
    },
    
    async setDefaultModel(id) {
      try {
        this.loading = true;
        await apiService.models.setDefaultModel(id);
        await this.fetchModels(); // 刷新列表
        return true;
      } catch (error) {
        this.error = error.message;
        console.error('设置默认模型失败:', error);
        throw error;
      } finally {
        this.loading = false;
      }
    },
    
    // Token使用统计
    async fetchTokenUsage(params = {}) {
      try {
        this.loading = true;
        const response = await apiService.models.getTokenUsage(params);
        this.tokenUsage = response.data;
        return this.tokenUsage;
      } catch (error) {
        this.error = error.message;
        console.error('获取Token使用统计失败:', error);
        throw error;
      } finally {
        this.loading = false;
      }
    }
  }
});
