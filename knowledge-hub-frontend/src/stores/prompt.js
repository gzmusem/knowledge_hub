import { defineStore } from 'pinia';
import apiService from '@/api/api';

export const usePromptStore = defineStore('prompt', {
  state: () => ({
    templates: [],
    scenes: [],
    activeScene: null,
    loading: false,
    error: null
  }),

  getters: {
    // 获取当前场景下的模板
    currentSceneTemplates: (state) => {
      if (!state.activeScene) return state.templates;
      return state.templates.filter(template => template.scene === state.activeScene);
    },
    
    // 获取所有激活的场景
    activeScenes: (state) => {
      return state.scenes.filter(scene => scene.is_active);
    }
  },

  actions: {
    // 获取所有场景
    async fetchScenes() {
      try {
        this.loading = true;
        const response = await apiService.promptScenes.getScenes();
        console.log('获取场景列表响应:', response);
        // 更新 store 中的 scenes 状态
        this.scenes = response.data || [];
        return response.data || [];
      } catch (error) {
        console.error('获取场景列表失败:', error);
        this.error = error.message;
        return [];
      } finally {
        this.loading = false;
      }
    },

    // 设置当前活动场景
    setActiveScene(sceneId) {
      this.activeScene = sceneId;
      // 可选：重新获取该场景下的模板
      if (sceneId) {
        this.fetchTemplates(sceneId);
      }
    },

    // 创建新场景
    async createScene(data) {
      try {
        this.loading = true;
        const response = await apiService.promptScenes.createScene(data);
        await this.fetchScenes();
        return response.data;
      } catch (error) {
        this.error = error.message;
        throw error;
      } finally {
        this.loading = false;
      }
    },

    // 更新场景
    async updateScene(id, data) {
      try {
        this.loading = true;
        const response = await apiService.promptScenes.updateScene(id, data);
        await this.fetchScenes();
        return response.data;
      } catch (error) {
        this.error = error.message;
        throw error;
      } finally {
        this.loading = false;
      }
    },

    // 删除场景
    async deleteScene(id) {
      try {
        this.loading = true;
        await apiService.promptScenes.deleteScene(id);
        await this.fetchScenes();
        return true;
      } catch (error) {
        this.error = error.message;
        throw error;
      } finally {
        this.loading = false;
      }
    },

    // 更新场景排序
    async reorderScene(id, order) {
      try {
        this.loading = true;
        const response = await apiService.promptScenes.reorderScene(id, order);
        await this.fetchScenes();
        return response.data;
      } catch (error) {
        this.error = error.message;
        throw error;
      } finally {
        this.loading = false;
      }
    },

    // 修改现有的 fetchTemplates 方法，支持场景过滤
    async fetchTemplates(sceneId = null) {
      try {
        this.loading = true;
        // 构造查询参数
        const params = {};
        if (sceneId) {
          params.scene = sceneId;
        }
        const response = await apiService.prompts.getTemplates(params);
        this.templates = response.data || [];
      } catch (error) {
        console.error('获取模板失败:', error);
        this.error = error.message;
        this.templates = []; // 确保失败时设置为空数组
      } finally {
        this.loading = false;
      }
    },

    async createTemplate(data) {
      try {
        this.loading = true;
        const response = await apiService.prompts.createTemplate(data);
        await this.fetchTemplates();
        return response.data;
      } catch (error) {
        this.error = error.message;
        throw error;
      } finally {
        this.loading = false;
      }
    },

    // 添加获取单个模板的方法
    async getTemplate(id) {
      try {
        this.loading = true;
        const response = await apiService.prompts.getTemplate(id);
        return response.data;
      } catch (error) {
        this.error = error.message;
        throw error;
      } finally {
        this.loading = false;
      }
    },

    // 添加更新模板的方法
    async updateTemplate(id, data) {
      try {
        this.loading = true;
        const response = await apiService.prompts.updateTemplate(id, data);
        await this.fetchTemplates();
        return response.data;
      } catch (error) {
        this.error = error.message;
        throw error;
      } finally {
        this.loading = false;
      }
    },

    // 添加删除模板的方法
    async deleteTemplate(id) {
      try {
        this.loading = true;
        await apiService.prompts.deleteTemplate(id);
        await this.fetchTemplates();
        return true;
      } catch (error) {
        this.error = error.message;
        throw error;
      } finally {
        this.loading = false;
      }
    },

    // 添加复制模板的方法
    async duplicateTemplate(id) {
      try {
        this.loading = true;
        const response = await apiService.prompts.duplicateTemplate(id);
        await this.fetchTemplates();
        return response.data;
      } catch (error) {
        this.error = error.message;
        throw error;
      } finally {
        this.loading = false;
      }
    }
  }
}); 