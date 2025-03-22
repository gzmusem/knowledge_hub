<template>
  <div class="model-list">
    <div class="header">
      <h2>AI模型管理</h2>
      <el-button 
        link
        :icon="Plus"
        @click="$router.push('/model-config/models/add')"
      >
        添加模型
      </el-button>
    </div>

    <el-table 
      :data="modelConfigStore.models"
      v-loading="loading"
      style="width: 100%"
    >
      <el-table-column
        prop="name"
        label="模型名称"
        min-width="150"
      />
      <el-table-column
        prop="model_id"
        label="模型ID"
        min-width="150"
      />
      <el-table-column
        prop="provider_name"
        label="提供商"
        min-width="120"
      >
        <template #default="{ row }">
          {{ row.provider_name || '-' }}
        </template>
      </el-table-column>
      <el-table-column
        prop="type"
        label="类型"
        min-width="100"
      >
        <template #default="{ row }">
          <el-tag>对话模型</el-tag>
        </template>
      </el-table-column>
      <el-table-column
        label="默认"
        width="80"
      >
        <template #default="{ row }">
          <el-switch
            v-model="row.is_default"
            disabled
          />
        </template>
      </el-table-column>
      <el-table-column
        label="状态"
        width="100"
      >
        <template #default="{ row }">
          <el-tag :type="row.is_active ? 'success' : 'info'">
            {{ row.is_active ? '已启用' : '已禁用' }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column
        label="操作"
        width="250"
        fixed="right"
      >
        <template #default="{ row }">
          <el-button
            link
            type="primary"
            @click="handleToggleStatus(row)"
          >
            {{ row.is_active ? '禁用' : '启用' }}
          </el-button>
          <el-button
            link
            type="primary"
            @click="$router.push(`/model-config/models/edit/${row.id}`)"
          >
            编辑
          </el-button>
          <el-button
            link
            type="danger"
            @click="handleDelete(row)"
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
import { useModelConfigStore } from '@/stores/modelConfig';
import { ElMessage, ElMessageBox } from 'element-plus';
import { Plus } from '@element-plus/icons-vue';

const modelConfigStore = useModelConfigStore();
const loading = ref(false);

// 获取模型列表
const fetchModels = async () => {
  try {
    loading.value = true;
    await modelConfigStore.fetchModels();
  } catch (error) {
    console.error('[ModelList] 获取模型列表失败:', error);
    ElMessage.error('获取模型列表失败');
  } finally {
    loading.value = false;
  }
};

// 处理删除
const handleDelete = async (model) => {
  try {
    await ElMessageBox.confirm(
      `确定要删除模型 ${model.name} 吗？`,
      '删除确认',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning',
      }
    );
    
    await modelConfigStore.deleteModel(model.id);
    ElMessage.success('删除成功');
    await fetchModels();
  } catch (error) {
    if (error !== 'cancel') {
      console.error('[ModelList] 删除模型失败:', error);
      ElMessage.error('删除失败');
    }
  }
};

// 处理启用/禁用
const handleToggleStatus = async (model) => {
  try {
    const action = model.is_active ? '禁用' : '启用';
    console.log('[ModelList] 切换模型状态:', model.id, !model.is_active);
    
    // 先获取完整的模型数据
    const currentModel = await modelConfigStore.getModel(model.id);
    
    // 只更新 is_active 字段
    const updatedData = {
      ...currentModel,
      is_active: !model.is_active
    };
    
    await modelConfigStore.updateModel(model.id, updatedData);
    ElMessage.success(`${action}成功`);
  } catch (error) {
    console.error('[ModelList] 更新模型状态失败:', error);
    ElMessage.error(`${action}失败`);
  }
};

onMounted(() => {
  fetchModels();
});
</script>

<style scoped>
.model-list {
  padding: 20px;
}

.header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.header h2 {
  margin: 0;
}
</style> 