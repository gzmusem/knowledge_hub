import { defineStore } from 'pinia';
import axios from 'axios';

// 假设有一个API服务
const api = axios.create({
  baseURL: 'http://localhost:8000/api',
  headers: {
    'Content-Type': 'application/json',
  },
});

export const useKnowledgeStore = defineStore('knowledge', {
  state: () => ({
    categories: [],
    tags: [],
    knowledgePoints: [],
    loading: false,
    error: null,
  }),
  
  actions: {
    // 获取分类列表
    async fetchCategories() {
      try {
        this.loading = true;
        // 暂时使用模拟数据，后续连接实际API
        // const response = await api.get('/categories/');
        const mockCategories = [
          { id: 1, name: '编程开发', knowledge_count: 5 },
          { id: 2, name: '数据科学', knowledge_count: 3 },
          { id: 3, name: '人工智能', knowledge_count: 7 },
        ];
        this.categories = mockCategories;
        return this.categories;
      } catch (error) {
        this.error = error.message;
        return [];
      } finally {
        this.loading = false;
      }
    },
    
    // 获取标签列表
    async fetchTags() {
      try {
        this.loading = true;
        // 暂时使用模拟数据，后续连接实际API
        // const response = await api.get('/tags/');
        const mockTags = [
          { id: 1, name: 'Python', category_id: 1, knowledge_count: 3 },
          { id: 2, name: 'JavaScript', category_id: 1, knowledge_count: 2 },
          { id: 3, name: '机器学习', category_id: 3, knowledge_count: 4 },
          { id: 4, name: '深度学习', category_id: 3, knowledge_count: 3 },
          { id: 5, name: '数据可视化', category_id: 2, knowledge_count: 2 },
        ];
        this.tags = mockTags;
        return this.tags;
      } catch (error) {
        this.error = error.message;
        return [];
      } finally {
        this.loading = false;
      }
    },
    
    // 获取知识点
    async fetchKnowledgePoints() {
      try {
        this.loading = true;
        // 暂时使用模拟数据，后续连接实际API
        // const response = await api.get('/knowledge-points/');
        const mockKnowledgePoints = [
          { 
            id: 1, 
            title: 'Python基础语法', 
            content: '# Python基础语法\n\nPython是一种简单易学的编程语言...',
            category: { id: 1, name: '编程开发' },
            tags: [{ id: 1, name: 'Python' }],
            created_at: '2023-01-15T08:30:00Z',
            conversation_id: 1
          },
          { 
            id: 2, 
            title: 'JavaScript闭包', 
            content: '# JavaScript闭包\n\n闭包是JavaScript中的一个重要概念...',
            category: { id: 1, name: '编程开发' },
            tags: [{ id: 2, name: 'JavaScript' }],
            created_at: '2023-01-20T10:15:00Z',
            conversation_id: 2
          },
          { 
            id: 3, 
            title: '机器学习模型评估', 
            content: '# 机器学习模型评估\n\n评估机器学习模型的性能是很重要的一步...',
            category: { id: 3, name: '人工智能' },
            tags: [{ id: 3, name: '机器学习' }],
            created_at: '2023-02-05T14:20:00Z',
            conversation_id: 3
          },
        ];
        this.knowledgePoints = mockKnowledgePoints;
        return this.knowledgePoints;
      } catch (error) {
        this.error = error.message;
        return [];
      } finally {
        this.loading = false;
      }
    },
    
    // 获取统计数据
    async fetchStats() {
      try {
        this.loading = true;
        // 暂时使用模拟数据
        return {
          conversations: 10,
          knowledgePoints: 15,
          categories: 3
        };
      } catch (error) {
        this.error = error.message;
        return {};
      } finally {
        this.loading = false;
      }
    },
    
    // 获取知识库统计
    async fetchKnowledgeStats() {
      try {
        this.loading = true;
        return { totalKnowledgeCount: 15 };
      } catch (error) {
        this.error = error.message;
        return { totalKnowledgeCount: 0 };
      } finally {
        this.loading = false;
      }
    },
    
    // 其他方法
    async createKnowledgePoint(data) {
      // 实现知识点创建逻辑
      console.log('创建知识点:', data);
      return { id: Date.now(), ...data };
    },
    
    async updateKnowledgePoint(data) {
      // 实现知识点更新逻辑
      console.log('更新知识点:', data);
      return data;
    },
    
    async deleteKnowledgePoint(id) {
      // 实现知识点删除逻辑
      console.log('删除知识点:', id);
      return true;
    },
  }
});
