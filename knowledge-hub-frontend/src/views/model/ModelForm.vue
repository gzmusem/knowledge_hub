<template>
    <div class="model-form">
      <div class="page-header">
        <h3>{{ isEdit ? '编辑模型' : '添加模型' }}</h3>
        <el-button @click="$router.push('/model-config/models')">返回列表</el-button>
      </div>
      
      <el-form 
        ref="formRef" 
        :model="form" 
        :rules="rules" 
        label-width="140px"
        v-loading="loading"
      >
        <el-form-item label="模型名称" prop="name">
          <el-input v-model="form.name" placeholder="例如：GPT-4" />
        </el-form-item>
        
        <el-form-item label="模型ID" prop="model_id">
          <el-input v-model="form.model_id" placeholder="例如：gpt-4" />
        </el-form-item>
        
        <div class="form-tip">模型的唯一标识符，通常由提供商定义</div>
        
        <el-form-item label="提供商" prop="provider">
          <el-select v-model="form.provider" placeholder="选择提供商">
            <el-option 
              v-for="provider in providers" 
              :key="provider.id" 
              :label="provider.name" 
              :value="provider.id"
            />
          </el-select>
        </el-form-item>
        
        <el-form-item label="模型类型" prop="model_type">
          <el-select v-model="form.model_type" placeholder="选择模型类型">
            <el-option label="对话模型" value="chat" />
            <el-option label="文本生成" value="text" />
            <el-option label="向量嵌入" value="embedding" />
            <el-option label="图像生成" value="image" />
            <el-option label="语音处理" value="audio" />
          </el-select>
        </el-form-item>
        
        <el-divider>模型参数配置</el-divider>
        
        <el-form-item label="最大Token数" prop="max_tokens">
          <el-input-number v-model="form.max_tokens" :min="1" :max="100000" />
          <div class="form-tip">模型单次请求可以处理的最大token数量</div>
        </el-form-item>
        
        <el-form-item label="温度" prop="temperature">
          <el-slider 
            v-model="form.temperature" 
            :min="0" 
            :max="2" 
            :step="0.1" 
            show-input
          />
          <div class="form-tip">控制输出的随机性，值越高结果越随机，值越低结果越确定</div>
        </el-form-item>
        
        <el-form-item label="Top P" prop="top_p">
          <el-slider 
            v-model="form.top_p" 
            :min="0" 
            :max="1" 
            :step="0.05" 
            show-input
          />
          <div class="form-tip">核采样，控制模型考虑的词汇范围</div>
        </el-form-item>
        
        <el-form-item label="存在惩罚" prop="presence_penalty">
          <el-slider 
            v-model="form.presence_penalty" 
            :min="-2" 
            :max="2" 
            :step="0.1" 
            show-input
          />
          <div class="form-tip">对已出现过的词汇进行惩罚，避免重复</div>
        </el-form-item>
        
        <el-form-item label="频率惩罚" prop="frequency_penalty">
          <el-slider 
            v-model="form.frequency_penalty" 
            :min="-2" 
            :max="2" 
            :step="0.1" 
            show-input
          />
          <div class="form-tip">对高频词汇进行惩罚，增加多样性</div>
        </el-form-item>
        
        <el-divider>成本设置</el-divider>
        
        <el-form-item label="提示词成本" prop="cost_prompt">
          <el-input-number 
            v-model="form.cost_prompt" 
            :precision="6" 
            :step="0.000001" 
            :min="0"
          />
          <div class="form-tip">提示词每千Token的成本（美元）</div>
        </el-form-item>
        
        <el-form-item label="回复成本" prop="cost_completion">
          <el-input-number 
            v-model="form.cost_completion" 
            :precision="6" 
            :step="0.000001" 
            :min="0"
          />
          <div class="form-tip">回复每千Token的成本（美元）</div>
        </el-form-item>
        
        <el-divider>其他设置</el-divider>
        
        <el-form-item label="是否默认模型" prop="is_default">
          <el-switch v-model="form.is_default" />
          <div class="form-tip">设为默认后，新对话将默认使用此模型</div>
        </el-form-item>
        
        <el-form-item label="是否启用" prop="is_active">
          <el-switch v-model="form.is_active" />
        </el-form-item>
        
        <el-form-item label="显示顺序" prop="display_order">
          <el-input-number v-model="form.display_order" :min="0" :step="1" />
          <div class="form-tip">控制模型在列表中的显示顺序，数字越小越靠前</div>
        </el-form-item>
        
        <el-form-item label="上下文窗口大小" prop="context_window">
          <el-input-number v-model="form.context_window" :min="1" :step="1" />
          <div class="form-tip">模型能够处理的上下文窗口大小（token数）</div>
        </el-form-item>
        
        <el-form-item label="模型描述" prop="description">
          <el-input 
            v-model="form.description" 
            type="textarea" 
            :rows="4" 
            placeholder="模型描述信息"
          />
        </el-form-item>
        
        <el-form-item label="模型能力" prop="capabilities">
          <el-input 
            v-model="capabilitiesJson" 
            type="textarea" 
            :rows="6" 
            placeholder="JSON格式的模型能力描述"
          />
          <div class="form-tip">JSON格式，描述模型的特殊能力和限制</div>
        </el-form-item>
        
        <el-form-item>
          <el-button type="primary" @click="submitForm">保存</el-button>
          <el-button @click="resetForm">重置</el-button>
        </el-form-item>
      </el-form>
    </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted, watch } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import { ElMessage } from 'element-plus';
import { useModelConfigStore } from '@/stores/modelConfig';

const route = useRoute();
const router = useRouter();
const modelConfigStore = useModelConfigStore();

const formRef = ref(null);
const loading = ref(false);
const providers = ref([]);
const isEdit = computed(() => route.params.id !== undefined);

// 表单数据
const form = reactive({
  name: '',
  model_id: '',
  provider: null,
  model_type: 'chat',
  max_tokens: 2000,
  temperature: 0.7,
  top_p: 1.0,
  presence_penalty: 0.0,
  frequency_penalty: 0.0,
  cost_prompt: 0.0,
  cost_completion: 0.0,
  is_default: false,
  is_active: true,
  display_order: 0,
  context_window: 4096,
  description: '',
  capabilities: {}
});

// 模型能力JSON字符串
const capabilitiesJson = computed({
  get: () => {
    try {
      return JSON.stringify(form.capabilities, null, 2);
    } catch (e) {
      return '{}';
    }
  },
  set: (val) => {
    try {
      form.capabilities = JSON.parse(val);
    } catch (e) {
      ElMessage.warning('JSON格式不正确');
    }
  }
});

// 表单验证规则
const rules = {
  name: [
    { required: true, message: '请输入模型名称', trigger: 'blur' },
    { min: 2, max: 100, message: '长度在2到100个字符之间', trigger: 'blur' }
  ],
  model_id: [
    { required: true, message: '请输入模型ID', trigger: 'blur' }
  ],
  provider: [
    { required: true, message: '请选择提供商', trigger: 'change' }
  ],
  model_type: [
    { required: true, message: '请选择模型类型', trigger: 'change' }
  ]
};

// 加载提供商列表
const loadProviders = async () => {
  loading.value = true;
  try {
    providers.value = await modelConfigStore.fetchProviders();
  } catch (error) {
    ElMessage.error('加载提供商列表失败');
  } finally {
    loading.value = false;
  }
};

// 加载模型数据（编辑模式）
const loadModel = async () => {
  if (!isEdit.value) return;
  
  loading.value = true;
  try {
    const model = await modelConfigStore.getModel(route.params.id);
    // 处理provider字段，需要从对象转为ID
    if (model.provider && typeof model.provider === 'object') {
      model.provider = model.provider.id;
    }
    Object.assign(form, model);
  } catch (error) {
    ElMessage.error('加载模型数据失败');
    router.push('/model-config/models');
  } finally {
    loading.value = false;
  }
};

// 提交表单
const submitForm = async () => {
  if (!formRef.value) return;
  
  await formRef.value.validate(async (valid) => {
    if (!valid) return;
    
    loading.value = true;
    try {
      // 确保capabilities是有效的JSON对象
      try {
        if (typeof form.capabilities === 'string') {
          form.capabilities = JSON.parse(form.capabilities);
        }
      } catch (e) {
        form.capabilities = {};
      }
      
      if (isEdit.value) {
        await modelConfigStore.updateModel(route.params.id, form);
        ElMessage.success('模型更新成功');
      } else {
        await modelConfigStore.createModel(form);
        ElMessage.success('模型添加成功');
      }
      router.push('/model-config/models');
    } catch (error) {
      ElMessage.error(isEdit.value ? '更新模型失败' : '添加模型失败');
    } finally {
      loading.value = false;
    }
  });
};

// 重置表单
const resetForm = () => {
  if (!formRef.value) return;
  formRef.value.resetFields();
  
  // 如果是编辑模式，重新加载数据
  if (isEdit.value) {
    loadModel();
  }
};

onMounted(async () => {
  await loadProviders();
  await loadModel();
});
</script>

<style scoped>
.model-form {
  max-width: 800px;
  margin: 0 auto;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.form-tip {
  font-size: 12px;
  color: #909399;
  margin-top: 5px;
}
</style>