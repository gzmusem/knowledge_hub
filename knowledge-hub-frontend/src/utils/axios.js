import axios from 'axios';
import { requestControl } from '@/utils/requestControl';

// 请求缓存
const cache = new Map();
const pendingRequests = new Map();

// 创建axios实例
const axiosInstance = axios.create({
  baseURL: 'http://localhost:8000',
  timeout: 10000
});

// 请求拦截器
axiosInstance.interceptors.request.use(
  config => {
    // 生成请求的唯一key
    const url = config.url;
    const method = config.method || 'get';
    const requestKey = `${method}_${url}`;
    
    // 将请求标记到config中，用于响应拦截器识别
    config.requestKey = requestKey;
    
    // 检查是否是重复请求
    if (requestControl.pendingRequests.has(requestKey)) {
      console.log(`[Axios] 检测到重复请求: ${requestKey}`);
      
      // 创建取消令牌
      const source = axios.CancelToken.source();
      config.cancelToken = source.token;
      
      // 立即取消请求
      source.cancel(`重复请求已被拦截: ${requestKey}`);
    }
    
    return config;
  },
  error => {
    return Promise.reject(error);
  }
);

// 响应拦截器
axiosInstance.interceptors.response.use(
  response => {
    // 从requestKey中移除已完成的请求
    const requestKey = response.config.requestKey;
    if (requestKey) {
      requestControl.pendingRequests.delete(requestKey);
    }
    
    return response;
  },
  error => {
    // 处理被取消的请求
    if (axios.isCancel(error)) {
      console.log('[Axios] 请求已被取消:', error.message);
      return Promise.reject(new Error('请求已被取消，避免重复'));
    }
    
    // 从requestKey中移除已失败的请求
    if (error.config && error.config.requestKey) {
      requestControl.pendingRequests.delete(error.config.requestKey);
    }
    
    return Promise.reject(error);
  }
);

export default axiosInstance; 