<template>
  <div class="model-list">
    <div class="page-header">
      <h3>AI模型管理</h3>
      <el-button type="primary" @click="$router.push('/model-config/models/add')">
        添加模型
      </el-button>
    </div>
    
    <el-table 
      :data="models" 
      border 
      style="width: 100%"
      v-loading="loading"
    >
      <el-table-column prop="name" label="模型名称" width="180" />
      <el-table-column prop="model_id" label="模型ID" width="150" />
      <el-table-column prop="provider.name" label="提供商" width="150" />
      <el-table-column prop="model_type" label="类型" width="100">
        <template #default="scope">
          <el-tag>{{ getModelTypeName(scope.row.model_type) }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="is_default" label="默认" width="80">
        <template #default="scope">
          <el-tag v-if="scope.row.is_default" type="success">默认</el-tag>
          <el-button 
            v-else 
            size="small" 
            type="text"
            @click="setAsDefault(scope.row)"
          >
            设为默认
          </el-button>
        </template>
      </el-table-column>
      <el-table-column prop="is_active" label="状态" width="80">
        <template #default="scope">
          <el-tag :type="scope.row.is_active ? 'success' : 'danger'">
            {{ scope.row.is_active ? '启用' : '禁用' }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column label="操作" width="200">
        <template #default="scope">
          <el-button 
            size="small" 
            @click="$router.push(`/model-config/models/edit/${scope.row.id}`)"
          >
            编辑
          </el-button>
          <el-button 
            size="small" 
            type="danger" 
            @click="handleDelete(scope.row)"
          >
            删除
          </el-button>
        </template>
      </el-table-column>
    </el-table>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue';
import { ElMessageBox, ElMessage } from 'element-plus';
import { useModelConfigStore } from '@/stores/modelConfig';

const modelConfigStore = useModelConfigStore();
const models = ref([]);
const loading = ref(false);

// 模型类型映射
const modelTypes = {
  'chat': '对话模型',
  'text': '文本生成',
  'embedding': '向量嵌入',
  'image': '图像生成',
  'audio': '语音处理'
};

// 获取模型类型名称
const getModelTypeName = (type) => {
  return modelTypes[type] || type;
};

// 加载模型列表
const loadModels = async () => {
  loading.value = true;
  try {
    models.value = await modelConfigStore.fetchModels();
  } catch (error) {
    ElMessage.error('加载模型列表失败');
  } finally {
    loading.value = false;
  }
};

// 设置为默认模型
const setAsDefault = async (model) => {
  try {
    await ElMessageBox.confirm(
      `确定要将 "${model.name}" 设置为默认模型吗？`,
      '提示',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'info'
      }
    );
    
    loading.value = true;
    await modelConfigStore.setDefaultModel(model.id);
    ElMessage.success('默认模型设置成功');
    await loadModels();
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('设置默认模型失败');
    }
  } finally {
    loading.value = false;
  }
};

// 删除模型
const handleDelete = async (model) => {
  try {
    await ElMessageBox.confirm(
      `确定要删除模型 "${model.name}" 吗？`,
      '警告',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    );
    
    loading.value = true;
    await modelConfigStore.deleteModel(model.id);
    ElMessage.success('模型删除成功');
    await loadModels();
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('删除模型失败');
    }
  } finally {
    loading.value = false;
  }
};

onMounted(() => {
  loadModels();
});
</script>

<style scoped>
.model-list {
  width: 100%;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}
</style> 