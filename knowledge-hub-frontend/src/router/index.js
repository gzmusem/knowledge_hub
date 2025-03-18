import { createRouter, createWebHistory } from 'vue-router'
import MainLayout from '@/components/layout/MainLayout.vue'
import HomeView from '../views/HomeView.vue'
import ChatView from '../views/ChatView.vue'
import requestControl from '@/utils/requestControl';

// 导入组件
const ModelConfig = () => import('@/views/model/ModelConfig.vue');
const ProviderList = () => import('@/views/model/ProviderList.vue');
const ProviderForm = () => import('@/views/model/ProviderForm.vue');
const ModelList = () => import('@/views/model/ModelList.vue');
const ModelForm = () => import('@/views/model/ModelForm.vue');
const TokenUsage = () => import('@/views/model/TokenUsage.vue');

const routes = [
  {
    path: '/',
    component: MainLayout,
    children: [
      {
        path: '',
        redirect: '/home'
      },
      {
        path: 'home',
        name: 'Home',
        component: HomeView,
        meta: { title: '首页' }
      },
      {
        path: 'chat/:id',
        name: 'Chat',
        component: ChatView,
        meta: { title: '聊天', requiresAuth: true }
      },
      {
        path: 'chat/new',
        name: 'NewChat',
        component: ChatView,
        meta: { title: '新对话', requiresAuth: true }
      },
      {
        path: 'knowledge',
        name: 'Knowledge',
        component: () => import('../views/KnowledgeView.vue'),
        meta: { title: '知识库', requiresAuth: true }
      },
      {
        path: 'category/:id',
        name: 'Category',
        component: () => import('../views/KnowledgeView.vue'),
        meta: { title: '知识分类', requiresAuth: true }
      },
      {
        path: 'model-config/providers',
        name: 'ProviderList',
        component: ProviderList,
        meta: { 
          title: '提供商管理', 
          requiresAuth: true,
          adminOnly: true
        }
      },
      {
        path: 'model-config/providers/add',
        name: 'AddProvider',
        component: ProviderForm,
        meta: { 
          title: '添加提供商', 
          requiresAuth: true,
          adminOnly: true
        }
      },
      {
        path: 'model-config/providers/edit/:id',
        name: 'EditProvider',
        component: ProviderForm,
        meta: { 
          title: '编辑提供商', 
          requiresAuth: true,
          adminOnly: true
        }
      },
      {
        path: 'model-config/models',
        name: 'ModelList',
        component: ModelList,
        meta: { 
          title: '模型管理', 
          requiresAuth: true,
          adminOnly: true
        }
      },
      {
        path: 'model-config/models/add',
        name: 'AddModel',
        component: ModelForm,
        meta: { 
          title: '添加模型', 
          requiresAuth: true,
          adminOnly: true
        }
      },
      {
        path: 'model-config/models/edit/:id',
        name: 'EditModel',
        component: ModelForm,
        meta: { 
          title: '编辑模型', 
          requiresAuth: true,
          adminOnly: true
        }
      },
      {
        path: 'model-config/usage',
        name: 'TokenUsage',
        component: TokenUsage,
        meta: { 
          title: 'Token使用统计', 
          requiresAuth: true,
          adminOnly: true
        }
      }
    ]
  },
  {
    path: '/login',
    name: 'Login',
    component: () => import('../views/LoginView.vue'),
    meta: { requiresAuth: false, layout: 'none' }
  },
  {
    path: '/',
    component: MainLayout,
    children: [
      {
        path: 'home',
        name: 'Home',
        component: HomeView,
        meta: { requiresAuth: true }
      },
      {
        path: 'chat',
        name: 'Chat',
        component: () => import('@/views/ChatView.vue'),
        children: [
          {
            path: '',
            name: 'NewChat',
            component: () => import('@/views/ChatView.vue'),
            meta: {
              title: '新对话',
              requiresAuth: true
            }
          },
          {
            path: 'new',
            name: 'CreateChat',
            component: () => import('@/views/ChatView.vue')
          },
          {
            path: ':id',
            name: 'ChatDetail',
            component: () => import('@/views/ChatView.vue'),
            props: true
          }
        ]
      },
      {
        path: 'knowledge',
        name: 'Knowledge',
        component: () => import('../views/KnowledgeView.vue')
      },
      {
        path: 'knowledge/category/:id',
        name: 'CategoryKnowledge',
        component: () => import('../views/KnowledgeView.vue'),
        props: true
      },
      {
        path: 'knowledge/tag/:id',
        name: 'TagKnowledge',
        component: () => import('../views/KnowledgeView.vue'),
        props: true
      }
    ]
  },
  {
    path: '/login',
    name: 'Login',
    component: () => import('../views/LoginView.vue'),
    meta: { requiresAuth: false, layout: 'none' }
  },
]

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes
})

// 简化导航守卫以减少出错可能
router.beforeEach((to, from, next) => {
  const publicPages = ['/login'];
  const authRequired = !publicPages.includes(to.path);
  const loggedIn = localStorage.getItem('token');

  try {
    // 认证逻辑
    if (authRequired && !loggedIn) {
      return next('/login');
    } else if (to.path === '/login' && loggedIn) {
      return next('/home');
    }

    // 其他情况简单地调用next()，让导航继续
    return next();
  } catch (error) {
    console.error('导航守卫错误:', error);
    // 确保导航不会被阻塞
    return next();
  }
});

// 添加全局导航守卫
router.beforeEach((to, from, next) => {
  // 当路由发生变化时，重置请求控制器
  //requestControl.reset();
  console.log('[Router] 路由变化，重置请求控制状态');
  next();
});

export default router
