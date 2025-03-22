<template>
    <div class="chat-window">
      <div class="main-content">
        <!-- 左侧聊天区域 -->
        <div class="chat-area">
          <!-- 消息列表区域 -->
          <div class="messages-container" ref="messagesContainer">
            <!-- 确保所有消息在同一个容器内顺序显示 -->
            <div class="messages-wrapper">
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
              
              <!-- 遍历所有消息并确保它们正确地一个接一个显示 -->
              <div 
                v-for="(message, index) in uniqueMessages" 
                :key="message.id || `temp-${index}`"
                :class="['message-item', message.role]"
              >
                <!-- 用户消息 -->
                <div v-if="message.role === 'user'" class="user-message">
                  <div class="message-content">
                    <div class="message-text">{{ message.content }}</div>
                  </div>
                  <div class="avatar user-avatar">
                    <span>用户</span>
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
          </div>
          
          <!-- 左侧输入区域 -->
          <div class="input-area">
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

            <!-- 用户输入框 -->
            <div class="input-container">
              <el-input
                v-model="userInput"
                type="textarea"
                :rows="3"
                placeholder="输入您的具体内容..."
                :disabled="sendingLock"
                @keydown.enter.prevent
                @keydown.ctrl.enter="handleSend"
              />
              <el-button 
                type="primary" 
                @click="handleSend"
                :loading="sendingLock"
                :disabled="!canSend">
                {{ sendingLock ? '发送中...' : '发送' }}
              </el-button>
            </div>
          </div>
        </div>

        <!-- 右侧提示词面板 -->
        <div class="prompt-panel">
          <div class="panel-header">
            <h3>提示词模板</h3>
          </div>
          
          <!-- 场景选择 -->
          <div class="scene-section">
            <div class="section-title">选择场景</div>
            <el-select 
              v-model="selectedScene"
              placeholder="选择场景"
              @change="handleSceneChange"
              class="scene-select"
              :loading="promptStore.loading"
            >
              <el-option
                v-for="scene in promptStore.scenes"
                :key="scene.id"
                :label="scene.name"
                :value="scene.id"
              />
            </el-select>
          </div>

          <!-- 模板列表 -->
          <div class="templates-section">
            <div class="section-title">
              可用模板
              <small v-if="!selectedScene" class="hint-text">请先选择场景</small>
            </div>
            <div class="templates-list" v-loading="promptStore.loading">
              <el-empty v-if="!filteredTemplates.length" description="暂无可用模板" />
              <el-card
                v-for="template in filteredTemplates"
                :key="template.id"
                class="template-card"
                @click="handleTemplateSelect(template)"
                :class="{ 
                  'has-system-prompt': template.system_prompt,
                  'active': selectedTemplate?.id === template.id 
                }"
              >
                <div class="template-name">{{ template.name }}</div>
                <div class="template-description">{{ template.description }}</div>
                <el-tag 
                  v-if="template.system_prompt" 
                  size="small" 
                  type="success"
                  class="system-prompt-tag"
                >
                  包含系统提示词
                </el-tag>
              </el-card>
            </div>
          </div>

          <!-- 模板预览部分 -->
          <div class="template-preview">
            <div class="preview-header">
              <span class="preview-title">模板预览</span>
              <div class="preview-actions">
                <el-button 
                  type="primary" 
                  link 
                  size="small"
                  @click="clearTemplate"
                  v-if="selectedTemplate"
                >
                  清除选择
                </el-button>
              </div>
            </div>
            
            <!-- 修改预览文本框 -->
            <el-input
              v-if="selectedTemplate"
              v-model="previewContent"
              type="textarea"
              :rows="6"
              resize="vertical"
              :placeholder="selectedTemplate?.content || '选择模板后在这里显示模板内容'"
              class="preview-textarea"
            />
            <el-input
              v-else
              type="textarea"
              :rows="6"
              placeholder="选择模板后在这里显示模板内容"
              readonly
              disabled
              class="preview-textarea"
            />

            <!-- 变量说明部分 -->
            <div class="variable-hints" v-if="templateVariables.length">
              <div class="hints-title">变量说明：</div>
              <div class="variable-tags">
                <el-tag 
                  v-for="variable in templateVariables" 
                  :key="variable"
                  class="variable-tag"
                  @click="insertVariable(variable)"
                >
                  {{ variable }}
                </el-tag>
              </div>
            </div>
          </div>
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
  import { usePromptStore } from '@/stores/prompt';
  import { ArrowDown, InfoFilled } from '@element-plus/icons-vue';
  import { useAuthStore } from '@/stores/auth';
  
  const props = defineProps({
    conversationId: {
      type: [String, Number],
      default: null
    }
  });
  
  const chatStore = useChatStore();
  const modelStore = useModelStore();
  const userInput = ref(''); // 用户输入内容
  const selectedTemplate = ref(null); // 当前选中的模板
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
    // 获取store中的消息
    const storeMessages = Array.isArray(messages.value) ? messages.value : [];
    // 获取临时消息
    const tempMsgs = Array.isArray(tempMessages.value) ? tempMessages.value : [];
    
    console.log('[DEBUG] Store消息数:', storeMessages.length);
    console.log('[DEBUG] 临时消息数:', tempMsgs.length);
    
    // 合并消息并返回
    return [...storeMessages, ...tempMsgs];
  });
  
  // 计算属性：去除重复消息
  const uniqueMessages = computed(() => {
    // 使用 displayMessages 而不是 messages.value
    const allMessages = displayMessages.value;
    
    if (!Array.isArray(allMessages)) {
      return [];
    }
    
    // 过滤掉无效消息
    const validMessages = allMessages.filter(msg => msg && (msg.content || msg.role || msg.isLoading));
    
    // 使用Map去重
    const uniqueMap = new Map();
    validMessages.forEach(msg => {
      const key = msg.id || msg.tempId || `${msg.role}-${msg.content}`;
      if (!uniqueMap.has(key)) {
        uniqueMap.set(key, msg);
      }
    });
    
    // 转回数组并确保按时间戳排序
    return Array.from(uniqueMap.values()).sort((a, b) => {
      // 确保时间戳比较不会出错
      const timeA = a.timestamp ? new Date(a.timestamp).getTime() : 0;
      const timeB = b.timestamp ? new Date(b.timestamp).getTime() : 0;
      return timeA - timeB;
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
      
      console.log(`[ChatWindow] 消息加载完成，共 ${messages.value.length} 条消息，ID列表:`, 
        messages.value.map(m => m.id));
      
      // 强制触发视图更新
      messages.value = [...messages.value];
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
  const sendMessage = async (content) => {
    if (!content.trim() || sendingLock.value) return;
    
    try {
      sendingLock.value = true;
      
      const messageData = {
        content: content,
        model_id: selectedModel.value,
        system_prompt: currentSystemPrompt.value // 添加系统提示词
      };
      
      // 记录当前正在发送的消息内容和时间
      messageBeingSent.value = content;
      lastSentTimestamp = Date.now();
      
      // 确保tempMessages是一个数组
      if (!Array.isArray(tempMessages.value)) {
        tempMessages.value = [];
      }
      
      // 创建临时用户消息
      const userMessage = {
        tempId: `temp-user-${Date.now()}`,
        role: 'user',
        content: content,
        timestamp: new Date().toISOString()
      };
      
      // 创建临时AI思考消息
      const thinkingMessage = {
        tempId: `temp-assistant-${Date.now()}`,
        role: 'assistant',
        isLoading: true,
        content: '正在思考中...',
        timestamp: new Date().toISOString()
      };
      
      // 添加临时消息
      tempMessages.value = [...tempMessages.value, userMessage, thinkingMessage];
      
      console.log('[DEBUG] 添加临时消息后数量:', tempMessages.value.length);
      
      // 强制更新视图
      await nextTick();
      scrollToBottom();
      
      console.log('[DEBUG] 发送单条消息:', messageData);
      
      // 发送到服务器
      const apiResponse = await chatStore.sendMessage(
        messageData.content,
        props.conversationId,
        messageData.model_id,
        messageData.system_prompt
      );
      
      // 发送成功后，清除临时消息
      tempMessages.value = [];
      
      // 确保加载完整的消息列表
      await loadMessages();
      
      // 确保视图更新和滚动到底部
      await nextTick();
      scrollToBottom();
      
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
      
      // 错误处理：保留用户消息，显示错误提示
      tempMessages.value = tempMessages.value.filter(msg => msg.role === 'user');
      tempMessages.value.push({
        tempId: `error-${Date.now()}`,
        role: 'assistant',
        content: '消息发送失败，请重试',
        isError: true,
        timestamp: new Date().toISOString()
      });
    } finally {
      // 延迟重置发送状态
      setTimeout(() => {
        sendingLock.value = false;
        if (messageBeingSent.value === userInput.value) {
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

  const promptStore = usePromptStore();

  const selectedScene = ref(null);
  const currentSystemPrompt = ref(null);

  const authStore = useAuthStore();

  // 修改场景变化处理函数
  const handleSceneChange = async (sceneId) => {
    try {
      // 检查认证状态
      if (!authStore.isAuthenticated) {
        ElMessage.error('请先登录');
        router.push('/login');
        return;
      }

      selectedScene.value = sceneId;
      userInput.value = '';
      currentSystemPrompt.value = null;
      selectedTemplate.value = null;
      
      if (sceneId) {
        await promptStore.fetchTemplates(sceneId);
        console.log('场景模板加载成功:', promptStore.templates);
      } else {
        promptStore.templates = [];
      }
    } catch (error) {
      console.error('获取场景模板失败:', error);
      if (error.response?.status === 401) {
        ElMessage.error('登录已过期，请重新登录');
        router.push('/login');
      } else {
        ElMessage.error('获取场景模板失败');
      }
      promptStore.templates = [];
    }
  };

  // 修改计算属性
  const filteredTemplates = computed(() => {
    if (!selectedScene.value) return [];
    // 确保返回数组
    return (promptStore.templates || []).filter(t => 
      t.scene === selectedScene.value && 
      t.template_type === 'user'
    );
  });

  // 修改计算属性，添加空值判断
  const templateVariables = computed(() => {
    if (!selectedTemplate.value?.content) return [];
    const matches = selectedTemplate.value.content.match(/\{([^}]+)\}/g);
    return matches ? matches.map(m => m.replace(/[{}]/g, '')) : [];
  });

  // 判断是否可以发送
  const canSend = computed(() => {
    return (userInput.value.trim() && selectedTemplate.value) || 
           (!selectedTemplate.value && userInput.value.trim());
  });

  // 修改模板选择处理函数
  const handleTemplateSelect = (template) => {
    if (!template) {
      selectedTemplate.value = null;
      currentSystemPrompt.value = null;
      return;
    }
    
    selectedTemplate.value = template;
    
    // 如果模板有关联的系统提示词，获取系统提示词内容
    if (template.system_prompt) {
      const systemTemplate = promptStore.templates.find(t => t.id === template.system_prompt);
      if (systemTemplate) {
        currentSystemPrompt.value = systemTemplate.content;
      }
    }
  };

  // 清除选中的模板
  const clearTemplate = () => {
    selectedTemplate.value = null;
    currentSystemPrompt.value = null;
  };

  // 添加预览内容的响应式变量
  const previewContent = ref('');

  // 监听选中模板的变化
  watch(() => selectedTemplate.value, (newTemplate) => {
    if (newTemplate) {
      previewContent.value = newTemplate.content;
    } else {
      previewContent.value = '';
    }
  });

  // 添加插入变量的方法
  const insertVariable = (variable) => {
    const textarea = document.querySelector('.preview-textarea textarea');
    if (textarea) {
      const start = textarea.selectionStart;
      const end = textarea.selectionEnd;
      const text = previewContent.value;
      const before = text.substring(0, start);
      const after = text.substring(end);
      previewContent.value = `${before}{${variable}}${after}`;
      
      // 设置光标位置
      nextTick(() => {
        textarea.focus();
        const newCursorPos = start + variable.length + 2;
        textarea.setSelectionRange(newCursorPos, newCursorPos);
      });
    }
  };

  // 修改发送逻辑，使用预览内容
  const handleSend = async () => {
    if (!canSend.value || sendingLock.value) return;

    try {
      let finalContent = userInput.value;

      // 如果有预览内容，使用预览内容作为模板
      if (previewContent.value) {
        finalContent = previewContent.value;
        // 替换模板中的变量
        templateVariables.value.forEach(variable => {
          finalContent = finalContent.replace(`{${variable}}`, userInput.value);
        });
      }

      // 发送消息
      await sendMessage(finalContent);
      
      // 发送成功后清空输入
      userInput.value = '';
      
    } catch (error) {
      console.error('发送失败:', error);
      ElMessage.error('发送失败，请重试');
    }
  };

  // 在组件挂载时检查认证状态
  onMounted(async () => {
    try {
      // 检查认证状态
      if (!authStore.isAuthenticated) {
        await authStore.checkAuth();
      }

      console.log('开始加载场景和模板数据');
      await Promise.all([
        loadModels(),
        promptStore.fetchScenes(),
        promptStore.fetchTemplates()
      ]);
      
    } catch (error) {
      console.error('初始化失败:', error);
      if (error.response?.status === 401) {
        ElMessage.error('请先登录');
        router.push('/login');
      } else {
        ElMessage.error('加载数据失败');
      }
    }
  });

  // 可以添加一些新的计算属性或方法
  const hasSystemPrompt = computed(() => {
    return (template) => Boolean(template.system_prompt);
  });
  </script>
  
  <style scoped>
  .chat-window {
    height: 100%;
    background-color: #f5f7fa;
  }

  .main-content {
    display: flex;
    height: 100%;
  }

  /* 左侧聊天区域样式 */
  .chat-area {
    flex: 1;
    display: flex;
    flex-direction: column;
    border-right: 1px solid #e4e7ed;
    background-color: #fff;
  }

  .messages-container {
    flex: 1;
    overflow-y: auto;
    padding: 15px;
    background-color: #f5f7fa;
  }

  .messages-wrapper {
    display: flex;
    flex-direction: column;
    gap: 20px;
  }

  /* 消息项样式 */
  .message-item {
    display: flex;
    margin-bottom: 20px;
    max-width: 95%;
  }

  /* 用户消息样式 */
  .message-item.user {
    margin-left: auto; /* 靠右对齐 */
    flex-direction: row-reverse;
  }

  .user-message {
    display: flex;
    flex-direction: row-reverse;
    align-items: flex-start;
    gap: 8px;
  }

  .user-message .message-content {
    background-color: #95ec69 !important; /* 使用!important确保优先级 */
    color: var(--el-text-color-primary);
    border-radius: 16px 4px 16px 16px;
    padding: 10px 12px;
    box-shadow: var(--el-box-shadow-lighter);
  }

  /* AI消息样式 */
  .message-item.assistant {
    margin-right: auto; /* 靠左对齐 */
  }

  .assistant-message {
    display: flex;
    align-items: flex-start;
    gap: 8px;
  }

  .assistant-message .message-content {
    background-color: #ffffff !important; /* 使用!important确保优先级 */
    color: var(--el-text-color-primary);
    border-radius: 4px 16px 16px 16px;
    padding: 10px 12px;
    box-shadow: var(--el-box-shadow-lighter);
  }

  /* 头像样式 */
  .avatar {
    width: 40px;
    height: 40px;
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: var(--el-font-size-base);
    flex-shrink: 0;
  }

  .user-avatar {
    background-color: #409eff !important; /* 使用!important确保优先级 */
    color: #ffffff;
  }

  .assistant-avatar {
    background-color: #67c23a !important; /* 使用!important确保优先级 */
    color: #ffffff;
  }

  /* 消息内容样式 */
  .message-content {
    position: relative;
    word-break: break-word;
    min-width: 100px;
    max-width: calc(100% - 45px);
  }

  .message-text {
    font-size: var(--el-font-size-base);
    line-height: var(--el-font-line-height-primary);
  }

  /* 模型信息样式 */
  .model-info {
    font-size: 12px;
    color: #999;
    margin-top: 4px;
    text-align: right;
  }

  /* 加载动画样式 */
  .thinking-dots {
    display: flex;
    gap: 4px;
    padding: 8px 0;
  }

  .thinking-dots span {
    width: 8px;
    height: 8px;
    background-color: #999;
    border-radius: 50%;
    animation: thinking 1.4s infinite ease-in-out both;
  }

  .thinking-dots span:nth-child(1) { animation-delay: -0.32s; }
  .thinking-dots span:nth-child(2) { animation-delay: -0.16s; }

  @keyframes thinking {
    0%, 80%, 100% { 
      transform: scale(0.6);
      opacity: 0.4;
    }
    40% { 
      transform: scale(1);
      opacity: 1;
    }
  }

  /* Markdown 内容样式 */
  .markdown-content {
    line-height: 1.6;
  }

  .markdown-content :deep(p) {
    margin: 0.5em 0;
  }

  .markdown-content :deep(pre) {
    background-color: #f8f9fa;
    padding: 12px;
    border-radius: 4px;
    overflow-x: auto;
  }

  .markdown-content :deep(code) {
    font-family: monospace;
    background-color: #f0f0f0;
    padding: 2px 4px;
    border-radius: 3px;
  }

  .markdown-content :deep(ul),
  .markdown-content :deep(ol) {
    padding-left: 1.5em;
    margin: 0.5em 0;
  }

  .markdown-content :deep(li) {
    margin: 0.3em 0;
  }

  .markdown-content :deep(blockquote) {
    border-left: 4px solid #ddd;
    padding-left: 1em;
    margin: 0.5em 0;
    color: #666;
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

  .markdown-content :deep(strong) {
    font-weight: 600;
  }

  .markdown-content :deep(hr) {
    border: 0;
    border-top: 1px solid #eee;
    margin: 1em 0;
  }

  .input-area {
    padding: 16px;
    border-top: 1px solid #e4e7ed;
    background-color: #fff;
  }

  .model-selector {
    margin-bottom: 12px;
  }

  .model-selector :deep(.el-select) {
    width: 100%;
  }

  .input-container {
    display: flex;
    gap: 8px;
  }

  .input-container .el-textarea {
    flex: 1;
  }

  /* 右侧提示词面板样式 */
  .prompt-panel {
    width: 300px;
    display: flex;
    flex-direction: column;
    background-color: #fff;
    border-left: 1px solid #e4e7ed;
  }

  .panel-header {
    padding: 16px;
    border-bottom: 1px solid #e4e7ed;
  }

  .panel-header h3 {
    margin: 0;
    font-size: 16px;
    color: #303133;
  }

  .scene-section {
    padding: 16px;
    border-bottom: 1px solid #e4e7ed;
  }

  .section-title {
    margin-bottom: 12px;
    font-size: 14px;
    color: #606266;
    display: flex;
    justify-content: space-between;
    align-items: center;
  }

  .hint-text {
    color: #909399;
    font-size: 12px;
  }

  .scene-select {
    width: 100%;
  }

  .templates-section {
    flex: 1;
    padding: 16px;
    overflow-y: auto;
  }

  .templates-list {
    display: flex;
    flex-direction: column;
    gap: 12px;
  }

  .template-card {
    cursor: pointer;
    transition: all 0.3s;
    position: relative;
    padding: 12px;
  }

  .template-card:hover {
    transform: translateY(-2px);
    box-shadow: 0 2px 12px 0 rgba(0,0,0,0.1);
  }

  .template-name {
    font-size: 14px;
    font-weight: 500;
    color: #303133;
    margin-bottom: 4px;
  }

  .template-description {
    font-size: 12px;
    color: #909399;
    margin-bottom: 4px;
  }

  .system-prompt-tag {
    position: absolute;
    top: 8px;
    right: 8px;
    font-size: 10px;
  }

  .has-system-prompt {
    border: 1px solid #67c23a;
  }

  /* 错误消息样式 */
  .message-text.error {
    background-color: #fef0f0;
    color: #f56c6c;
    border: 1px solid #fbc4c4;
  }

  /* 消息样式优化 */
  .message {
    display: flex;
    margin-bottom: 20px;
    align-items: flex-start;
  }

  .message.user {
    flex-direction: row-reverse;
  }

  .avatar {
    width: 40px;
    height: 40px;
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    margin: 0 10px;
    background: #f0f2f5;
  }

  .content {
    max-width: 70%;
    padding: 12px 16px;
    border-radius: 12px;
    background: #f0f2f5;
  }

  .message.user .content {
    background: #e3f2fd;
  }

  .message.assistant .content {
    background: #f5f5f5;
  }

  /* 确保下拉菜单样式正确 */
  :deep(.el-dropdown-menu) {
    max-height: 400px;
    overflow-y: auto;
  }

  :deep(.el-dropdown-menu__item) {
    display: flex;
    align-items: center;
    justify-content: space-between;
  }

  :deep(.el-dropdown-menu__item .el-icon) {
    margin-left: 8px;
    color: #909399;
  }

  .template-preview {
    padding: 20px;
    border-top: 1px solid #e4e7ed;
    background-color: #f8f9fa;
    height: auto;
    min-height: 300px;
    display: flex;
    flex-direction: column;
    gap: 16px;
  }

  .preview-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 12px;
  }

  .preview-title {
    font-size: 16px;
    font-weight: 500;
    color: #303133;
  }

  .preview-textarea {
    font-size: 14px;
    line-height: 1.6;
  }

  .preview-textarea :deep(.el-textarea__inner) {
    font-family: 'Courier New', Courier, monospace;
    font-size: 14px;
    line-height: 1.6;
    padding: 12px;
    min-height: 200px;
    background-color: #fff;
  }

  .variable-hints {
    margin-top: 16px;
  }

  .hints-title {
    font-size: 14px;
    color: #606266;
    margin-bottom: 8px;
    font-weight: 500;
  }

  .variable-tags {
    display: flex;
    flex-wrap: wrap;
    gap: 8px;
  }

  .variable-tag {
    cursor: pointer;
    padding: 6px 12px;
    font-size: 13px;
    transition: all 0.3s;
  }

  .variable-tag:hover {
    background-color: #409eff;
    color: #fff;
    transform: translateY(-1px);
  }

  /* 确保文本框在暗色主题下也清晰可见 */
  .preview-textarea :deep(.el-textarea__inner) {
    color: #303133;
    background-color: #ffffff;
    border: 1px solid #dcdfe6;
  }

  /* 添加文本框hover效果 */
  .preview-textarea :deep(.el-textarea__inner):hover {
    border-color: #c0c4cc;
  }

  /* 添加文本框focus效果 */
  .preview-textarea :deep(.el-textarea__inner):focus {
    border-color: #409eff;
  }
  </style>