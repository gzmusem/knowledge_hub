<template>
  <div class="chat-input">
    <div class="model-selector">
      <el-select 
        v-model="selectedModel" 
        placeholder="选择AI模型" 
        size="small"
      >
        <el-option
          v-for="model in availableModels"
          :key="model.model_id"
          :label="model.name"
          :value="model.model_id"
        />
      </el-select>
    </div>
    
    <el-input
      v-model="message"
      type="textarea"
      :rows="2"
      placeholder="输入您的问题..."
      @keyup.enter.ctrl="sendMessage"
    ></el-input>
    
    <el-button 
      type="primary" 
      :loading="loading" 
      @click="sendMessage"
    >发送</el-button>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue';
import { ElMessage } from 'element-plus';
import apiService from '@/api/api';

const props = defineProps({
  conversationId: String,
  loading: Boolean
});

const emit = defineEmits(['send']);

const message = ref('');
const selectedModel = ref('');
const availableModels = ref([]);

// 获取可用模型
const fetchAvailableModels = async () => {
  try {
    const response = await apiService.models.getAvailableModels();
    availableModels.value = response.data;
    
    // 设置默认选中的模型
    if (availableModels.value.length > 0) {
      const defaultModel = availableModels.value.find(m => m.is_default) || availableModels.value[0];
      selectedModel.value = defaultModel.model_id;
    }
  } catch (error) {
    console.error('获取模型列表失败:', error);
    ElMessage.error('加载模型列表失败');
  }
};

const sendMessage = () => {
  if (!message.value.trim()) return;
  
  // 确保发送一个对象，而不是直接的文本
  emit('send', {
    content: message.value,
    model_id: selectedModel.value
  });
  
  message.value = '';
};

onMounted(() => {
  fetchAvailableModels();
});
</script>
