<template>
  <div class="provider-form">
    <div class="page-header">
      <h3>{{ isEdit ? '编辑提供商' : '添加提供商' }}</h3>
      <el-button @click="$router.push('/model-config/providers')">返回列表</el-button>
    </div>
    
    <el-form 
      ref="formRef" 
      :model="form" 
      :rules="rules" 
      label-width="120px"
      v-loading="loading"
    >
      <el-form-item label="提供商名称" prop="name">
        <el-input v-model="form.name" placeholder="例如：OpenAI" />
      </el-form-item>
      
      <el-form-item label="提供商标识" prop="slug">
        <el-input v-model="form.slug" placeholder="例如：openai" />
        <div class="form-tip">唯一标识，只能包含小写字母、数字和连字符</div>
      </el-form-item>
      
      <el-form-item label="API基础URL" prop="api_base">
        <el-input v-model="form.api_base" placeholder="例如：https://api.openai.com/v1" />
      </el-form-item>
      
      <el-form-item label="API版本" prop="api_version">
        <el-input v-model="form.api_version" placeholder="例如：v1" />
      </el-form-item>
      
      <el-form-item label="是否需要认证" prop="auth_required">
        <el-switch v-model="form.auth_required" />
      </el-form-item>
      
      <el-form-item label="API密钥" prop="api_key" v-if="form.auth_required">
        <el-input 
          v-model="form.api_key" 
          placeholder="API密钥" 
          show-password
        />
      </el-form-item>
      
      <el-form-item label="API密钥2" prop="api_secret" v-if="form.auth_required">
        <el-input 
          v-model="form.api_secret" 
          placeholder="API密钥2（如果需要）" 
          show-password
        />
      </el-form-item>
      
      <el-form-item label="是否启用" prop="is_active">
        <el-switch v-model="form.is_active" />
      </el-form-item>
      
      <el-form-item label="提供商描述" prop="description">
        <el-input 
          v-model="form.description" 
          type="textarea" 
          :rows="4" 
          placeholder="提供商描述信息"
        />
      </el-form-item>
      
      <el-form-item>
        <el-button type="primary" @click="submitForm">保存</el-button>
        <el-button @click="resetForm">重置</el-button>
      </el-form-item>
    </el-form>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, computed } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import { ElMessage } from 'element-plus';
import { useModelConfigStore } from '@/stores/modelConfig';

const route = useRoute();
const router = useRouter();
const modelConfigStore = useModelConfigStore();

const formRef = ref(null);
const loading = ref(false);
const isEdit = computed(() => route.params.id !== undefined);

// 表单数据
const form = reactive({
  name: '',
  slug: '',
  api_base: '',
  api_version: '',
  is_active: true,
  auth_required: true,
  api_key: '',
  api_secret: '',
  description: ''
});

// 表单验证规则
const rules = {
  name: [
    { required: true, message: '请输入提供商名称', trigger: 'blur' },
    { min: 2, max: 50, message: '长度在2到50个字符之间', trigger: 'blur' }
  ],
  slug: [
    { required: true, message: '请输入提供商标识', trigger: 'blur' },
    { pattern: /^[a-z0-9-]+$/, message: '只能包含小写字母、数字和连字符', trigger: 'blur' }
  ],
  api_base: [
    { required: true, message: '请输入API基础URL', trigger: 'blur' }
  ]
};

// 加载提供商数据（编辑模式）
const loadProvider = async () => {
  if (!isEdit.value) return;
  
  loading.value = true;
  try {
    const provider = await modelConfigStore.getProvider(route.params.id);
    Object.assign(form, provider);
  } catch (error) {
    ElMessage.error('加载提供商数据失败');
    router.push('/model-config/providers');
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
      if (isEdit.value) {
        await modelConfigStore.updateProvider(route.params.id, form);
        ElMessage.success('提供商更新成功');
      } else {
        await modelConfigStore.createProvider(form);
        ElMessage.success('提供商添加成功');
      }
      router.push('/model-config/providers');
    } catch (error) {
      ElMessage.error(isEdit.value ? '更新提供商失败' : '添加提供商失败');
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
    loadProvider();
  }
};

onMounted(() => {
  loadProvider();
});
</script>

<style scoped>
.provider-form {
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