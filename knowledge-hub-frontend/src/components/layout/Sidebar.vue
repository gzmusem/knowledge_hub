<template>
    <div class="sidebar">
      <div class="logo">
        <h2>知识库</h2>
      </div>
      <el-menu 
        :default-active="activeMenu" 
        :router="true"
        :default-openeds="defaultOpeneds"
        class="sidebar-menu"
        background-color="#f8f9fa"
        text-color="#343a40"
        active-text-color="#007bff">
        <el-menu-item index="/home" @click="navigateTo('/home')">
          <el-icon><HomeFilled /></el-icon>
          <span>首页</span>
        </el-menu-item>
        
        <!-- 将聊天菜单改为折叠式 -->
        <el-sub-menu index="/chat" :default-openeds="['/chat']">
          <template #title>
            <div style="display: flex; width: 100%; justify-content: space-between; align-items: center;">
              <div>
                <el-icon><ChatDotRound /></el-icon>
                <span>聊天</span>
              </div>
              <el-button 
                @click.stop="loadRecentChats" 
                size="small" 
                icon="RefreshRight"
                style="margin-right: 5px; padding: 2px 5px;">
              </el-button>
            </div>
          </template>
          
          <!-- 新对话选项 -->
          <el-menu-item index="/chat/new" @click.native="createNewChat">
            <el-icon><Plus /></el-icon>
            <span>新对话</span>
          </el-menu-item>
          
          <!-- 历史对话列表 -->
          <el-menu-item 
            v-for="chat in chatList" 
            :key="chat.id" 
            :index="`${chat.id}`"
            class="chat-history-item"
            @click="navigateToChat(chat.id)"
          >
            <div class="chat-item-content">
              <el-icon><ChatLineRound /></el-icon>
              <span class="chat-title">{{ chat.title || '未命名对话' }}</span>
              <el-icon class="delete-icon" @click.stop="confirmDeleteChat(chat.id)"><Delete /></el-icon>
            </div>
          </el-menu-item>
          
          <!-- 加载更多按钮 -->
          <div v-if="hasMoreChats" class="load-more" @click="loadMoreChats">
            <span>加载更多...</span>
          </div>
        </el-sub-menu>
        
        <el-menu-item index="/knowledge" @click="navigateTo('/knowledge')">
          <el-icon><Files /></el-icon>
          <span>知识库</span>
        </el-menu-item>
        
        
        <el-sub-menu index="/knowledge-category">
          <template #title>
            <el-icon><Folder /></el-icon>
            <span>知识分类</span>
          </template>
          <el-menu-item 
            v-for="category in categories" 
            :key="category.id" 
            :index="`/category/${category.id}`"
            @click="navigateTo(`/category/${category.id}`)"
          >
            {{ category.name }}
          </el-menu-item>
        </el-sub-menu>

        <!-- 修改为带有子菜单的模型配置 -->
        <el-sub-menu index="/model-config">
          <template #title>
            <el-icon><Setting /></el-icon>
            <span>模型配置</span>
          </template>
          
          <!-- 模型配置子菜单 -->
          <el-menu-item 
            index="/model-config/providers" 
            @click="navigateTo('/model-config/providers')"
          >
            <el-icon><Connection /></el-icon>
            <span>提供商管理</span>
          </el-menu-item>
          
          <el-menu-item 
            index="/model-config/models" 
            @click="navigateTo('/model-config/models')"
          >
            <el-icon><Monitor /></el-icon>
            <span>模型管理</span>
          </el-menu-item>
          
          <el-menu-item 
            index="/model-config/usage" 
            @click="navigateTo('/model-config/usage')"
          >
            <el-icon><DataAnalysis /></el-icon>
            <span>使用统计</span>
          </el-menu-item>
        </el-sub-menu>
      </el-menu>
    </div>
  </template>
  
  <script setup>
  import { ref, computed, onMounted } from 'vue';
  import { useRoute, useRouter } from 'vue-router';
  import { useKnowledgeStore } from '@/stores/knowledge';
  import { useChatStore } from '@/stores/chat';
  import { ElMessageBox, ElMessage } from 'element-plus';
  import { 
    HomeFilled, 
    ChatDotRound, 
    ChatLineRound,
    Files, 
    Folder, 
    Plus, 
    Delete,
    Setting,
    Connection,  // 添加新图标
    Monitor,     // 添加新图标
    DataAnalysis // 添加新图标
  } from '@element-plus/icons-vue';
  
  const route = useRoute();
  const router = useRouter();
  const knowledgeStore = useKnowledgeStore();
  const chatStore = useChatStore();
  
  const activeMenu = computed(() => route.path);
  const categories = computed(() => knowledgeStore.categories);
  
  // 聊天历史相关
  const recentChats = ref([]);
  const currentPage = ref(1);
  const pageSize = ref(10);
  const hasMoreChats = ref(false);
  
  // 加载历史对话列表
  const loadRecentChats = async () => {
    try {
      console.log('[Sidebar] 开始加载历史对话');
      const response = await chatStore.fetchRecentConversations({
        page: currentPage.value,
        pageSize: pageSize.value
      });
      
      console.log('[Sidebar] 服务器返回对话数据:', response);
      
      // 确保数据是数组，即使为空
      recentChats.value = Array.isArray(response.data) ? response.data : [];
      
      // 将结果同步到 store，确保是数组
      chatStore.conversations = [...recentChats.value];
      
      // 检查是否有更多数据
      hasMoreChats.value = Array.isArray(response.data) && response.data.length >= pageSize.value;
      
      console.log(`[Sidebar] 加载了 ${recentChats.value.length} 个对话:`, recentChats.value);
      
      // 强制触发UI更新
      if (recentChats.value.length > 0) {
        setTimeout(() => {
          console.log('[Sidebar] 强制刷新UI');
          recentChats.value = [...recentChats.value];
        }, 100);
      }
    } catch (error) {
      console.error('[Sidebar] 加载对话列表失败:', error);
      // 确保即使出错也将值设为空数组而非undefined
      recentChats.value = [];
      chatStore.conversations = [];
      hasMoreChats.value = false;
    }
  };
  
  // 加载更多历史对话
  const loadMoreChats = async () => {
    currentPage.value++;
    try {
      const response = await chatStore.fetchRecentConversations({
        page: currentPage.value,
        pageSize: pageSize.value
      });
      
      if (response.data && response.data.length > 0) {
        recentChats.value = [...recentChats.value, ...response.data];
        hasMoreChats.value = response.data.length >= pageSize.value;
      } else {
        hasMoreChats.value = false;
      }
    } catch (error) {
      console.error('加载更多对话失败:', error);
      currentPage.value--;
    }
  };
  
  // 创建新对话
  const createNewChat = async () => {
    try {
      console.log('[DEBUG] 确认为新对话，重置会话ID');
      // 先清空store中的对话信息
      chatStore.currentConversation = null;
      chatStore.currentMessages = [];
      
      // 使用更简单的方式导航
      router.push('/chat/new').catch(err => {
        console.error('导航到新对话失败，忽略:', err);
        // 忽略NavigationDuplicated错误
        if (err.name !== 'NavigationDuplicated') {
          ElMessage.error('导航到新对话页面失败');
        }
      });
    } catch (error) {
      console.error('创建新对话失败:', error);
      ElMessage.error('创建新对话失败');
    }
  };
  
  // 确认删除对话
  const confirmDeleteChat = async (chatId) => {
    try {
      await ElMessageBox.confirm('确定要删除这个对话吗?', '提示', {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      });
      
      await chatStore.deleteConversation(chatId);
      ElMessage.success('对话已删除');
      
      // 如果删除的是当前正在查看的对话，跳转到新对话页面
      if (route.params.id === chatId.toString()) {
        router.push('/chat/new');
      }
      
      // 刷新对话列表
      loadRecentChats();
    } catch (error) {
      if (error !== 'cancel') {
        console.error('删除对话失败:', error);
      }
    }
  };
  
  const chatList = computed(() => {
    return recentChats.value.map(conv => ({
      id: conv.id,
      title: conv.title || '未命名对话',
    }));
  });
  
  // 修改defaultOpeneds计算属性，确保聊天菜单始终展开
  const defaultOpeneds = computed(() => {
    // 始终包含聊天菜单
    const openeds = ['/chat'];
    
    const path = route.path;
    
    if (path.includes('/category/')) {
      openeds.push('/knowledge-category');
    }
    
    if (path.includes('/model-config/')) {
      openeds.push('/model-config');
    }
    
    console.log('[Sidebar] 默认展开菜单:', openeds);
    return openeds;
  });
  
  // 添加通用导航方法
  const navigateTo = (path) => {
    console.log('导航到:', path);
    try {
      router.push(path).catch(err => {
        console.error('导航错误，忽略:', err);
        // 忽略NavigationDuplicated错误
        if (err.name !== 'NavigationDuplicated') {
          throw err;
        }
      });
    } catch (error) {
      console.error('导航失败，使用备选方案:', error);
      // 备选：尝试直接修改路由，避免触发导航守卫
      if (router.currentRoute.value.path !== path) {
        window.location.href = path;
      }
    }
  };
  
  // 修改导航到聊天的方法
  const navigateToChat = (chatId) => {
    console.log('导航到聊天:', chatId);
    try {
      // 确保路由中使用的是原始 ID，不需要在这里处理
      // 因为我们已经在 API 调用中处理了 ID 格式
      router.push(`/chat/${chatId}`).catch(err => {
        console.error('导航错误，忽略:', err);
        if (err.name !== 'NavigationDuplicated') {
          throw err;
        }
      });
    } catch (error) {
      console.error('导航到聊天失败:', error);
      ElMessage.error('导航到聊天失败');
    }
  };
  
  onMounted(async () => {
    try {
      await knowledgeStore.fetchCategories();
      await loadRecentChats();
      
      // 为新对话按钮添加额外的原生事件监听器
      const newChatBtn = document.querySelector('.sidebar-menu [index="/chat/new"]');
      if (newChatBtn) {
        console.log('[DEBUG] 找到新对话按钮，添加额外监听器');
        newChatBtn.addEventListener('click', (e) => {
          console.log('[DEBUG] 原生点击事件触发');
          createNewChat();
        });
      } else {
        console.log('[DEBUG] 未找到新对话按钮元素');
      }
    } catch (error) {
      console.error('初始化侧边栏失败:', error);
      ElMessage.error('加载分类失败，请刷新页面重试');
    }
  });
  </script>
  
  <style scoped>
  .sidebar {
    height: 100%;
    display: flex;
    flex-direction: column;
  }
  .logo {
    padding: 20px;
    text-align: center;
  }
  .sidebar-menu {
    flex: 1;
    border-right: none;
  }
  .chat-history-item {
    padding-right: 16px;
    height: auto;
    line-height: 1.5;
    min-height: 40px;
  }
  .chat-item-content {
    display: flex;
    align-items: center;
    width: 100%;
  }
  .chat-title {
    flex: 1;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
    margin-left: 5px;
  }
  .delete-icon {
    display: none;
    margin-left: 8px;
    font-size: 14px;
    color: #909399;
  }
  .chat-history-item:hover .delete-icon {
    display: inline-flex;
  }
  .load-more {
    text-align: center;
    color: #909399;
    font-size: 13px;
    padding: 8px 0;
    cursor: pointer;
    margin-left: 32px;
  }
  .load-more:hover {
    color: #409EFF;
  }
  </style>