<template>
    <div class="chat-window">
      <!-- 消息列表区域 -->
      <div class="messages-container" ref="messagesContainer">
        <div v-if="!uniqueMessages || uniqueMessages.length === 0" class="empty-state">
          <div class="empty-icon">
            <i class="el-icon-chat-dot-round"></i>
          </div>
          <div class="empty-text">开始一个新对话吧</div>
          <div class="debug-info" style="font-size:12px;color:#999;margin-top:10px;">
            会话ID: {{ props.conversationId }}<br>
            消息数: {{ messages.value ? messages.value.length : 0 }}<br>
            Store消息数: {{ chatStore.currentMessages ? chatStore.currentMessages.length : 0 }}<br>
            临时消息数: {{ tempMessages.value ? tempMessages.value.length : 0 }}
          </div>
        </div>
        
        <div 
          v-for="message in uniqueMessages" 
          :key="message.id"
          :class="['message-wrapper', message.role]"
        >
          <!-- 用户消息 -->
          <div v-if="message.role === 'user'" class="user-message">
            <div class="avatar user-avatar">
              <span>用户</span>
            </div>
            <div class="message-content">
              <div class="message-text">{{ message.content }}</div>
            </div>
          </div>

          <!-- AI回答 -->
          <div v-else-if="message.role === 'assistant'" class="assistant-message">
            <div class="avatar assistant-avatar">
              <span>AI</span>
            </div>
            <div class="message-content">
              <!-- 正在加载的消息显示动画效果 -->
              <div v-if="message.isLoading" class="message-text loading">
                <div class="thinking-dots">
                  <span></span>
                  <span></span>
                  <span></span>
                </div>
                <div>正在思考，请稍候...</div>
              </div>
              <!-- 使用v-html渲染Markdown内容 -->
              <div v-else class="message-text markdown-content" v-html="renderMarkdown(message.content)"></div>
              <div class="model-info" v-if="message.metadata?.model_id || selectedModel">
                {{ getModelName(message.metadata?.model_id || selectedModel) }}
              </div>
            </div>
          </div>
        </div>
      </div>
      
      <!-- 底部输入区域 -->
      <div class="input-area">
        <!-- 模型选择 -->
        <div class="model-selector">
          <el-select v-model="selectedModel" size="small">
            <el-option
              v-for="model in availableModels"
              :key="model.model_id"
              :label="model.name"
              :value="model.model_id"
            />
          </el-select>
        </div>

        <!-- 输入框和发送按钮 -->
        <div class="input-container">
          <el-input
            v-model="message"
            type="textarea"
            :rows="3"
            placeholder="输入您的问题..."
            :disabled="sendingLock"
            @keydown.enter.prevent
            @keydown.ctrl.enter="sendMessage"
          />
          <el-button 
            type="primary" 
            @click="sendMessage"
            :loading="sendingLock"
            :disabled="!message.trim() || sendingLock">
            {{ sendingLock ? '发送中...' : '发送' }}
          </el-button>
        </div>
      </div>
    </div>
  </template>
  
  <script setup>
  import { ref, onMounted, nextTick, watch, computed, onUnmounted, onBeforeUnmount, defineExpose } from 'vue';
  import { ElMessage } from 'element-plus';
  import { useChatStore } from '@/stores/chat';
  import { useModelStore } from '@/stores/models';
  import { v4 as uuidv4 } from 'uuid';
  import { marked } from 'marked';
  import DOMPurify from 'dompurify';
  import requestControl from '@/utils/requestControl';
  import { useRouter } from 'vue-router';
  
  const props = defineProps({
    conversationId: {
      type: [String, Number],
      default: null
    }
  });
  
  const chatStore = useChatStore();
  const modelStore = useModelStore();
  const message = ref('');
  const loading = ref(false);
  const messagesContainer = ref(null);
  const selectedModel = ref('');
  const availableModels = ref([]);
  
  // 添加更严格的防重发机制
  const messageBeingSent = ref('');
  const sendingLock = ref(false);
  let lastSentTimestamp = 0;
  
  // 添加一个临时消息数组，用于在UI中显示但还未从服务器确认的消息
  const tempMessages = ref([]);
  
  // 合并正式消息和临时消息以供显示
  const displayMessages = computed(() => {
    // 合并store中的消息和临时消息
    const storeMessages = chatStore.currentMessages || [];
    return [...storeMessages, ...tempMessages.value];
  });
  
  // 计算属性：去除重复消息
  const uniqueMessages = computed(() => {
    // 先检查是否使用临时消息
    if (tempMessages.value && tempMessages.value.length > 0) {
      return tempMessages.value;
    }
    
    // 然后检查chatStore中的消息
    if (Array.isArray(chatStore.currentMessages) && chatStore.currentMessages.length > 0) {
      return chatStore.currentMessages;
    }
    
    // 最后尝试使用本地messages变量
    if (!Array.isArray(messages.value)) {
      return [];
    }
    
    // 过滤掉无效消息
    const validMessages = messages.value.filter(msg => msg && (msg.content || msg.role));
    
    // 使用Map去重
    const uniqueMap = new Map();
    validMessages.forEach(msg => {
      const key = msg.id || `${msg.role}-${msg.content}`;
      if (!uniqueMap.has(key)) {
        uniqueMap.set(key, msg);
      }
    });
    
    // 转回数组并排序
    return Array.from(uniqueMap.values()).sort((a, b) => {
      return new Date(a.timestamp || 0) - new Date(b.timestamp || 0);
    });
  });
  
  // 获取模型名称
  const getModelName = (modelId) => {
    const model = availableModels.value.find(m => m.model_id === modelId);
    return model?.name || modelId;
  };
  
  // 模型选择
  watch(selectedModel, (newValue) => {
    if (newValue) {
      localStorage.setItem('preferredModel', newValue);
    }
  });
  
  // 修改模型加载逻辑
  const loadModels = async () => {
    try {
      console.log('[DEBUG] 开始加载可用模型列表');
      
      // 从服务器获取模型列表
      await modelStore.fetchAvailableModels();
      availableModels.value = modelStore.availableModels;
      
      console.log('[DEBUG] 加载到的模型列表:', availableModels.value);
      
      // 如果没有模型数据，尝试再次加载或提供默认值
      if (!availableModels.value || availableModels.value.length === 0) {
        console.warn('[警告] 没有加载到模型数据，使用默认模型');
        // 添加一个默认模型作为备选
        availableModels.value = [
          { model_id: 'qwq-32b', name: '通义千问-QwQ-32B', is_default: true }
        ];
      }
      
      // 设置选中模型
      // 优先使用localStorage保存的偏好
      const savedModel = localStorage.getItem('preferredModel');
      if (savedModel && availableModels.value.some(m => m.model_id === savedModel)) {
        selectedModel.value = savedModel;
      } else {
        // 否则使用默认模型或第一个模型
        const defaultModel = availableModels.value.find(m => m.is_default) || availableModels.value[0];
        if (defaultModel) {
          selectedModel.value = defaultModel.model_id;
          // 保存默认选择
          localStorage.setItem('preferredModel', defaultModel.model_id);
        }
      }
      
      console.log('[DEBUG] 已选择模型:', selectedModel.value);
    } catch (error) {
      console.error('[ERROR] 加载模型列表失败:', error);
      ElMessage.error('加载模型列表失败，使用默认模型');
      
      // 出错时提供默认模型
      availableModels.value = [
        { model_id: 'qwq-32b', name: '通义千问-QwQ-32B', is_default: true }
      ];
      selectedModel.value = 'qwq-32b';
    }
  };
  
  // 组件挂载时立即加载模型
  onMounted(() => {
    console.log('[DEBUG] ChatWindow组件挂载，加载模型');
    loadModels();
    
    // 禁用Enter键自动提交，改为完全由按钮控制
    const textarea = document.querySelector('.input-container textarea');
    if (textarea) {
      textarea.addEventListener('keydown', (e) => {
        // 阻止Enter键默认行为，除非按下Ctrl或Meta键
        if (e.key === 'Enter' && !e.ctrlKey && !e.metaKey) {
          e.preventDefault();
        }
      });
    }
  });
  
  // 定义emit
  const emit = defineEmits(['debug']);
  
  // 判断是否为新对话模式
  const isNewChat = computed(() => {
    return !props.conversationId || props.conversationId === 'new';
  });
  
  // 防止重复加载的标志
  const isLoading = ref(false);
  // 当前加载的对话ID
  const currentlyLoadingId = ref(null);
  
  // 1. 先定义所有需要的变量
  const messages = ref([]);
  const loadCompleted = ref(false);
  const shouldAbort = ref(false);
  
  // 3. 定义加载消息函数，确保它访问的变量都已定义
  const loadMessages = async () => {
    const id = props.conversationId;
    if (!id || id === 'new') {
      console.log('[ChatWindow] 无效ID，不加载消息');
      messages.value = [];
      return;
    }
    
    console.log(`[ChatWindow] 加载消息, ID: ${id}`);
    loading.value = true;
    
    try {
      // 先清空现有消息，避免闪烁
      messages.value = [];
      
      // 获取对话和消息
      await chatStore.getConversation(id);
      await chatStore.getMessages(id);
      
      // 获取消息并确保是数组
      messages.value = Array.isArray(chatStore.currentMessages) 
        ? [...chatStore.currentMessages] 
        : [];
      
      console.log(`[ChatWindow] 加载了 ${messages.value.length} 条消息`);
    } catch (error) {
      console.error('[ChatWindow] 加载消息失败:', error);
      
      // 确保发生错误时也设置为数组
      messages.value = [];
    } finally {
      loading.value = false;
    }
  };
  
  // 4. 设置 watch 监听器
  watch(() => props.conversationId, (newId, oldId) => {
    if (newId !== oldId) {
      console.log(`[ChatWindow] ID变化 ${oldId} -> ${newId}`);
      loadMessages();
    }
  }, { immediate: true });
  
  // 组件卸载时移除watch
  onBeforeUnmount(() => {
    console.log('[DEBUG] ChatWindow 组件卸载');
  });
  
  // 1. 在组件顶部定义router（setup作用域内）
  const router = useRouter();
  
  // 2. 修改sendMessage函数
  const sendMessage = async () => {
    // 确保 message 是字符串且不为空
    const currentContent = String(message.value || '').trim();
    if (!currentContent || sendingLock.value) return;
    
    // 记录当前正在发送的消息内容和时间
    messageBeingSent.value = currentContent;
    lastSentTimestamp = Date.now();
    sendingLock.value = true;
    message.value = ''; // 立即清空输入框
    
    // 确保tempMessages是一个数组
    if (!Array.isArray(tempMessages.value)) {
      tempMessages.value = [];
    }
    
    // 生成临时ID
    const tempUserMsgId = `temp-user-${Date.now()}`;
    const tempAssistantMsgId = `temp-assistant-${Date.now()}`;
    
    try {
      console.log('[DEBUG] 发送单条消息:', currentContent);
      
      // 显示临时用户消息
      tempMessages.value.push({
        tempId: tempUserMsgId,
        role: 'user',
        content: currentContent,
        timestamp: new Date().toISOString()
      });
      
      // 显示加载中的AI消息
      tempMessages.value.push({
        tempId: tempAssistantMsgId,
        role: 'assistant',
        isLoading: true,
        content: '',
        timestamp: new Date().toISOString()
      });
      
      // 滚动到底部
      await nextTick();
      if (messagesContainer.value) {
        messagesContainer.value.scrollTop = messagesContainer.value.scrollHeight;
      }
      
      // 发送到服务器
      const sendingContent = currentContent;
      const sendingId = props.conversationId;
      const sendingModel = selectedModel.value;
      
      console.log('[DEBUG] 实际发送参数:', {
        conversationId: sendingId,
        content: sendingContent,
        model_id: sendingModel
      });
      
      const apiResponse = await chatStore.sendMessage(
        sendingContent,
        sendingId,
        sendingModel
      );
      
      // 确保临时消息数组仍然是数组
      if (!Array.isArray(tempMessages.value)) {
        tempMessages.value = [];
      } else {
        // 清除临时消息
        tempMessages.value = [];
      }
      
      console.log('[DEBUG] API响应:', apiResponse);
      
      if (apiResponse && apiResponse.success) {
        // 如果是新会话，需要更新路由
        if (isNewChat.value && apiResponse.conversationId) {
          console.log(`[DEBUG] 新会话创建成功，更新路由到会话ID: ${apiResponse.conversationId}`);
          
          try {
            // 使用路径导航
            await router.push(`/chat/${apiResponse.conversationId}`);
            
            // 导航成功后立即加载消息
            console.log(`[DEBUG] 导航成功，立即加载消息 ID: ${apiResponse.conversationId}`);
            messages.value = []; // 先清空消息
            await chatStore.getMessages(apiResponse.conversationId);
            messages.value = Array.isArray(chatStore.currentMessages) 
              ? [...chatStore.currentMessages] 
              : [];
          } catch (navError) {
            console.error('[ERROR] 导航失败，使用备用方法', navError);
            // 备用方法：使用window.location
            window.location.href = `/chat/${apiResponse.conversationId}`;
          }
        } else {
          // 如果不是新会话，直接重新加载消息
          await loadMessages();
        }
      } else {
        console.error('[ERROR] API响应成功但没有消息数据:', apiResponse);
        ElMessage.warning('发送成功但未收到回复，请刷新页面');
      }
      
      // 再次滚动到底部
      await nextTick();
      if (messagesContainer.value) {
        messagesContainer.value.scrollTop = messagesContainer.value.scrollHeight;
      }
    } catch (error) {
      console.error('[ERROR] 发送消息失败:', error);
      ElMessage.error('发送消息失败，请稍后重试');
      
      // 确保tempMessages是数组
      if (!Array.isArray(tempMessages.value)) {
        tempMessages.value = [];
      }
      
      // 添加错误提示
      tempMessages.value.push({
        tempId: `error-${Date.now()}`,
        role: 'assistant',
        content: '消息发送失败，请重试或检查网络连接。',
        isError: true,
        timestamp: new Date().toISOString()
      });
    } finally {
      // 延迟重置发送状态
      setTimeout(() => {
        sendingLock.value = false;
        if (messageBeingSent.value === currentContent) {
          messageBeingSent.value = '';
        }
      }, 2000); // 设置更长的锁定时间
    }
  };

  // 创建简单的渲染函数
  const renderMarkdown = (content) => {
    if (!content) return '';
    try {
      return DOMPurify.sanitize(marked.parse(content));
    } catch (error) {
      console.error('Markdown渲染错误:', error);
      return content; // 如果渲染失败，返回原始内容
    }
  };

  // 滚动到底部
  const scrollToBottom = () => {
    if (messagesContainer.value) {
      setTimeout(() => {
        messagesContainer.value.scrollTop = messagesContainer.value.scrollHeight;
      }, 50);
    }
  };

  // 暴露方法给父组件
  defineExpose({
    updateOnIdChange: loadMessages
  });
  </script>
  
  <style scoped>
  .chat-window {
    display: flex;
    flex-direction: column;
    height: 100%;
    background-color: #f5f7fa;
  }
  
  .messages-container {
    flex: 1;
    overflow-y: auto;
    padding: 16px;
    min-height: 200px;
    background-color: #f0f2f5;
    border-bottom: 1px solid #e0e3e9;
  }
  
  .empty-state {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    height: 100%;
    color: #909399;
  }
  
  .empty-icon {
    font-size: 48px;
    margin-bottom: 16px;
  }
  
  .empty-text {
    font-size: 16px;
  }
  
  .message-wrapper {
    margin-bottom: 16px;
    display: flex;
    flex-direction: column;
  }
  
  /* 用户消息样式 */
  .user-message {
    display: flex;
    flex-direction: row-reverse;
    align-items: flex-start;
  }
  
  .user-message .message-content {
    margin-right: 12px;
    max-width: 80%;
  }
  
  .user-message .message-text {
    background-color: #95ec69;
    color: #000;
    border-radius: 16px 4px 16px 16px;
    padding: 10px 14px;
    position: relative;
    box-shadow: 0 1px 2px rgba(0,0,0,0.1);
  }
  
  /* AI回答样式 */
  .assistant-message {
    display: flex;
    align-items: flex-start;
  }
  
  .assistant-message .message-content {
    margin-left: 12px;
    max-width: 80%;
  }
  
  .assistant-message .message-text {
    background-color: #fff;
    color: #333;
    border-radius: 4px 16px 16px 16px;
    padding: 10px 14px;
    box-shadow: 0 1px 2px rgba(0,0,0,0.1);
  }
  
  /* 模型标签样式 */
  .model-info {
    font-size: 12px;
    color: #999;
    margin-top: 4px;
    padding-left: 4px;
  }
  
  /* 头像样式 */
  .avatar {
    width: 36px;
    height: 36px;
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 14px;
    color: white;
  }
  
  .user-avatar {
    background-color: #007fff;
  }
  
  .assistant-avatar {
    background-color: #6b7280;
  }
  
  /* 底部输入区域 */
  .input-area {
    padding: 16px;
    background-color: #ffffff;
    border-top: 1px solid #ebeef5;
  }
  
  .model-selector {
    margin-bottom: 12px;
  }
  
  .model-selector .el-select {
    width: 100%;
  }
  
  .input-container {
    display: flex;
    align-items: flex-end;
  }
  
  .input-container .el-textarea {
    flex: 1;
    margin-right: 8px;
  }
  
  .input-container .el-button {
    height: 40px;
  }
  
  /* 添加加载中动画样式 */
  .loading {
    display: flex;
    flex-direction: column;
    align-items: flex-start;
    gap: 8px;
  }
  
  .thinking-dots {
    display: flex;
    align-items: center;
    gap: 4px;
  }
  
  .thinking-dots span {
    display: inline-block;
    width: 8px;
    height: 8px;
    border-radius: 50%;
    background-color: #666;
    animation: thinking 1.4s infinite ease-in-out both;
  }
  
  .thinking-dots span:nth-child(1) {
    animation-delay: 0s;
  }
  
  .thinking-dots span:nth-child(2) {
    animation-delay: 0.2s;
  }
  
  .thinking-dots span:nth-child(3) {
    animation-delay: 0.4s;
  }
  
  @keyframes thinking {
    0%, 80%, 100% {
      transform: scale(0.6);
      opacity: 0.6;
    }
    40% {
      transform: scale(1);
      opacity: 1;
    }
  }
  
  /* 错误消息样式 */
  .message-text.error {
    background-color: #fef0f0;
    color: #f56c6c;
    border: 1px solid #fbc4c4;
  }

  /* 添加Markdown内容样式 */
  .markdown-content {
    line-height: 1.6;
  }

  .markdown-content :deep(h1),
  .markdown-content :deep(h2),
  .markdown-content :deep(h3),
  .markdown-content :deep(h4),
  .markdown-content :deep(h5),
  .markdown-content :deep(h6) {
    margin-top: 1em;
    margin-bottom: 0.5em;
    font-weight: 600;
  }

  .markdown-content :deep(h3) {
    font-size: 1.2em;
    color: #333;
  }

  .markdown-content :deep(p) {
    margin: 0.5em 0;
  }

  .markdown-content :deep(ul),
  .markdown-content :deep(ol) {
    padding-left: 1.5em;
    margin: 0.5em 0;
  }

  .markdown-content :deep(li) {
    margin: 0.3em 0;
  }

  .markdown-content :deep(strong) {
    font-weight: 600;
  }

  .markdown-content :deep(hr) {
    border: 0;
    border-top: 1px solid #eee;
    margin: 1em 0;
  }

  .markdown-content :deep(blockquote) {
    border-left: 4px solid #ddd;
    padding-left: 1em;
    margin: 0.5em 0;
    color: #666;
  }

  .markdown-content :deep(code) {
    background-color: #f5f5f5;
    padding: 0.2em 0.4em;
    border-radius: 3px;
    font-family: monospace;
  }

  .markdown-content :deep(pre) {
    background-color: #f5f5f5;
    padding: 1em;
    border-radius: 5px;
    overflow-x: auto;
  }
  </style>