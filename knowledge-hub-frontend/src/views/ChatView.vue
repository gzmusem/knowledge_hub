<template>
  <div class="chat-view" :key="key">
    <div v-if="isDebugMode" style="position: fixed; top: 5px; right: 10px; background: #f0f0f0; padding: 5px; font-size: 12px; z-index: 9999;">
      路径: {{ route.path }} <br>
      ID: {{ conversationId }} <br>
      传递ID: {{ route.path === '/chat/new' ? 'null' : conversationId }}
    </div>
    <div class="chat-header">
      <h2 v-if="conversationId && conversationId !== 'new' && chatStore.currentConversation?.title">
        {{ chatStore.currentConversation.title }}
      </h2>
      <h2 v-else>新对话</h2>
      <div class="actions">
        <el-button v-if="conversationId && conversationId !== 'new'" icon="Delete" type="danger" plain size="small" @click="deleteConversation">
          删除对话
        </el-button>
      </div>
    </div>
    
    <chat-window 
      ref="chatWindowRef"
      :conversation-id="isNewChat ? 'new' : conversationId"
      :key="conversationId || 'new'"
      @debug="(msg) => console.log('[DEBUG] 从ChatWindow:', msg)" 
    />
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch, nextTick, onUnmounted, watchEffect, onBeforeUnmount, provide } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import { useChatStore } from '@/stores/chat';
import ChatWindow from '@/components/chat/ChatWindow.vue';
import { ElMessageBox, ElMessage } from 'element-plus';
import requestControl from '@/utils/requestControl';

const route = useRoute();
const router = useRouter();
const chatStore = useChatStore();

const conversationId = ref(null);
const conversation = ref(null);
const loading = ref(false);
const isLoading = ref(false);
const key = ref(0); // 添加key用于强制刷新组件
const messages = ref([]);
const loadCompleted = ref(false);

// 添加这个变量替代process.env检查
const isDebugMode = false; // 开发时可以设为true

// 监听路由变化
watch(() => route.params.id, (newId) => {
  console.log(`[ChatView] 路由ID变化: ${newId}`);
  conversationId.value = newId || null;
}, { immediate: true });

// 计算属性：是否新对话
const isNewChat = computed(() => {
  return !conversationId.value || conversationId.value === 'new';
});

// 强制终止所有加载的标志
const forceAbort = ref(false);

// 加载对话 - 只在组件挂载时执行一次
const loadConversation = async () => {
  if (forceAbort.value) return;
  
  const id = route.params.id;
  console.log('[DEBUG] 当前路径:', route.path);
  console.log('[DEBUG] 对话ID:', id);
  
  // 如果是新对话，不需要加载
  if (id === 'new') {
    console.log('[DEBUG] 新对话模式，不加载现有对话');
    conversationId.value = null;
    conversation.value = null;
    return;
  }
  
  conversationId.value = id;
  loading.value = true;
  
  try {
    if (id && id !== 'new' && id !== 'undefined') {
      conversation.value = await chatStore.getConversation(id);
    }
  } catch (error) {
    console.error('[ERROR] 加载对话失败:', error);
    ElMessage.error('加载对话失败');
  } finally {
    loading.value = false;
  }
};

// 路由切换前清理
onBeforeUnmount(() => {
  forceAbort.value = true;
  chatStore.clearCurrentConversation();
  console.log('[DEBUG] ChatView 组件卸载，清理当前对话数据');
});

// 传递 conversationId 给子组件
provide('conversationId', conversationId);

// 只有在组件挂载时加载一次
onMounted(() => {
  // 只执行一次loadConversation，避免重复请求
  loadConversation();
});

// 添加日志到标题计算属性
const chatTitle = computed(() => {
  console.log('[DEBUG] 计算对话标题...');
  console.log('[DEBUG] conversationId:', conversationId.value);
  console.log('[DEBUG] currentConversation:', chatStore.currentConversation);
  
  if (!conversationId.value || conversationId.value === 'new') {
    console.log('[DEBUG] 返回空标题 (新对话)');
    return '';
  }
  
  const title = chatStore.currentConversation?.title;
  console.log('[DEBUG] 获取到的标题:', title);
  return title;
});

// 删除对话添加日志
const deleteConversation = async () => {
  try {
    console.log('[DEBUG] 尝试删除对话:', conversationId.value);
    await ElMessageBox.confirm('确定要删除这个对话吗?', '提示', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    });
    
    await chatStore.deleteConversation(conversationId.value);
    ElMessage.success('对话已删除');
    router.push('/chat/new');
  } catch (error) {
    if (error !== 'cancel') {
      console.error('删除对话失败:', error);
      ElMessage.error('删除对话失败');
    }
  }
};

// 添加处理新对话创建的方法
const handleConversationCreated = (newId) => {
  console.log('[DEBUG] 新对话已创建:', newId);
  // 如果在"new"页面创建了新对话，更新路由
  if (conversationId.value === 'new' && newId) {
    router.replace(`/chat/${newId}`);
    conversationId.value = newId;
  }
};

// 获取对话窗口组件引用
const chatWindowRef = ref(null);

// 监听ID变化
watch(() => route.params.id, () => {
  // 使用暴露的方法更新消息
  if (chatWindowRef.value) {
    chatWindowRef.value.updateOnIdChange();
  }
}, { immediate: true });

onUnmounted(() => {
  loadCompleted.value = false;
});
</script>

<style scoped>
.chat-view {
  height: calc(100vh - 64px); /* 减去头部高度 */
  display: flex;
  flex-direction: column;
}

.chat-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.chat-header h2 {
  margin: 0;
  color: #343a40;
}

.actions {
  display: flex;
  gap: 10px;
}
</style>
