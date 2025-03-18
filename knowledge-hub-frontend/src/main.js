import './assets/main.css'
import { createApp } from 'vue'
import { createPinia } from 'pinia'
import piniaPluginPersistedstate from 'pinia-plugin-persistedstate'
import ElementPlus from 'element-plus'
import 'element-plus/dist/index.css'
import App from './App.vue'
import router from './router'
import * as ElementPlusIconsVue from '@element-plus/icons-vue'
import axios from 'axios'
import { marked } from 'marked'
import DOMPurify from 'dompurify'
import requestControl from '@/utils/requestControl'

// 安全模式启动
try {
  // 应用初始化代码
  const app = createApp(App)
  const pinia = createPinia()
  pinia.use(piniaPluginPersistedstate)

  // 注册所有图标
  for (const [key, component] of Object.entries(ElementPlusIconsVue)) {
    app.component(key, component)
  }

  // 添加全局响应拦截器
  axios.interceptors.response.use(
    response => response,
    error => {
      if (error.response?.status === 401) {
        // 未授权响应 - 可能是token过期
        // 清除存储的token
        localStorage.removeItem('token')
        
        // 如果不是在登录页，则重定向到登录页
        if (router.currentRoute.value.path !== '/login') {
          router.push('/login')
        }
      }
      return Promise.reject(error)
    }
  )

  // 注册全局Markdown渲染指令
  app.directive('md-render', {
    mounted(el, binding) {
      if (binding.value) {
        const html = DOMPurify.sanitize(marked.parse(binding.value))
        el.innerHTML = html
      }
    },
    updated(el, binding) {
      if (binding.value) {
        const html = DOMPurify.sanitize(marked.parse(binding.value))
        el.innerHTML = html
      }
    }
  })

  // 配置marked选项
  marked.setOptions({
    breaks: true, // 将回车符转换为<br>
    gfm: true,    // 启用GitHub风格Markdown
    tables: true, // 支持表格
    smartLists: true // 优化列表输出
  })

  // 全局错误处理
  app.config.errorHandler = (err, vm, info) => {
    console.error('[全局错误]', err);
    console.error('组件:', vm);
    console.error('信息:', info);
  };

  // 添加全局错误处理
  window.addEventListener('error', (event) => {
    console.error('全局错误:', event.error);
  });

  window.addEventListener('unhandledrejection', (event) => {
    console.error('未处理的 Promise 错误:', event.reason);
    // 防止错误继续传播
    event.preventDefault();
  });

  // 在应用启动前重置所有锁和状态
  //requestControl.resetAllLocks()
  //requestControl.clearCache()

  app.use(pinia)
  app.use(router)
  app.use(ElementPlus)

  // 挂载应用
  app.mount('#app')
  
  console.log('应用启动成功');
} catch (error) {
  console.error('应用启动失败:', error);
  // 显示错误消息到页面
  document.body.innerHTML = `<div style="padding: 20px; color: red;">
    <h2>应用启动失败</h2>
    <p>${error.message}</p>
    <button onclick="location.reload()">重新加载</button>
  </div>`;
}
