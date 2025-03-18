<template>
  <div class="chat-view">
    <div class="chat-header">
      <h2 v-if="conversationId">{{ conversationTitle }}</h2>
      <h2 v-else>新对话</h2>
      <div class="actions">
        <el-button v-if="conversationId" icon="Delete" type="danger" plain size="small" @click="deleteConversation">
          删除对话
        </el-button>
      </div>
    </div>
    
    <chat-window :conversation-id="conversationId" />
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import { ElMessageBox } from 'element-plus';
import ChatWindow from '@/components/chat/ChatWindow.vue';
import { useChatStore } from '@/stores/chat';

const route = useRoute();
const router = useRouter();
const chatStore = useChatStore();

const conversationId = computed(() => route.params.id);
const conversationTitle = ref('未命名对话');

onMounted(async () => {
  if (conversationId.value) {
    try {
      const conversation = await chatStore.loadConversation(conversationId.value);
      conversationTitle.value = conversation?.title || '未命名对话';
    } catch (error) {
      console.error('加载对话失败:', error);
    }
  }
});

const deleteConversation = async () => {
  try {
    await ElMessageBox.confirm('确定要删除这个对话吗?', '警告', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    });
    
    await chatStore.deleteConversation(conversationId.value);
    router.push('/chat');
  } catch (e) {
    // 用户取消删除
  }
};
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