import { defineStore } from 'pinia';
import apiService from '@/api/api';

export const useAuthStore = defineStore('auth', {
  state: () => ({
    user: null,
    token: localStorage.getItem('token') || null,
    loading: false,
    error: null
  }),
  
  getters: {
    isAuthenticated: (state) => !!state.token,
    username: (state) => state.user ? state.user.username : ''
  },
  
  actions: {
    async login(credentials) {
      try {
        this.loading = true;
        this.error = null;
        
        // 使用apiService调用登录API
        const response = await apiService.auth.login(credentials);
        
        // 检查是否成功且返回token
        if (response.data.token) {
          // 存储token
          localStorage.setItem('token', response.data.token);
          this.token = response.data.token;
          
          // 保存用户信息
          if (response.data.user) {
            this.user = response.data.user;
          } else {
            // 如果响应中没有用户信息，单独请求
            await this.fetchUserProfile();
          }
          
          return true;
        } else if (response.data.detail === '登录成功') {
          // 如果后端没有提供token但登录成功
          console.warn('登录成功但后端未提供token，使用临时token');
          const tempToken = 'temp-token-' + Date.now();
          localStorage.setItem('token', tempToken);
          this.token = tempToken;
          
          // 保存用户信息
          if (response.data.user) {
            this.user = response.data.user;
          }
          
          return true;
        } else {
          throw new Error(response.data.detail || '登录失败');
        }
      } catch (error) {
        console.error('登录失败:', error);
        this.error = error.response?.data?.detail || error.message || '登录失败';
        return false;
      } finally {
        this.loading = false;
      }
    },
    
    async logout() {
      try {
        this.loading = true;
        
        if (this.token) {
          await apiService.auth.logout();
        }
        
        // 清除本地存储
        localStorage.removeItem('token');
        this.token = null;
        this.user = null;
        
        return true;
      } catch (error) {
        console.error('登出错误:', error);
        // 即使API调用失败，仍然清除本地存储
        localStorage.removeItem('token');
        this.token = null;
        this.user = null;
        return true;
      } finally {
        this.loading = false;
      }
    },
    
    async fetchUserProfile() {
      try {
        if (!this.token) return null;
        
        this.loading = true;
        const response = await apiService.auth.getUser();
        
        this.user = response.data;
        return this.user;
      } catch (error) {
        console.error('获取用户信息失败:', error);
        this.error = error.response?.data?.detail || error.message || '获取用户信息失败';
        return null;
      } finally {
        this.loading = false;
      }
    },
    
    async checkAuth() {
      if (this.token && !this.user) {
        return await this.fetchUserProfile();
      }
      return this.user;
    }
  }
});
