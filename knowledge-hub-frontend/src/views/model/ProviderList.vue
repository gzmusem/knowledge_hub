<template>
  <div class="provider-list-container">
    <el-card class="provider-card">
      <template #header>
        <div class="card-header">
          <h2>提供商管理</h2>
          <el-button type="primary" @click="$router.push('/model-config/providers/add')">
            添加提供商
          </el-button>
        </div>
      </template>
      
      <el-table 
        :data="providers" 
        border 
        style="width: 100%"
        v-loading="loading"
      >
        <el-table-column prop="name" label="提供商名称" width="180" />
        <el-table-column prop="slug" label="标识" width="150" />
        <el-table-column prop="api_base" label="API基础URL" />
        <el-table-column prop="is_active" label="状态" width="100">
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
              @click="$router.push(`/model-config/providers/edit/${scope.row.id}`)"
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
    </el-card>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue';
import { ElMessageBox, ElMessage } from 'element-plus';
import { useModelConfigStore } from '@/stores/modelConfig';

const modelConfigStore = useModelConfigStore();
const providers = ref([]);
const loading = ref(false);

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

// 删除提供商
const handleDelete = async (provider) => {
  try {
    await ElMessageBox.confirm(
      `确定要删除提供商 "${provider.name}" 吗？这将同时删除该提供商下的所有模型。`,
      '警告',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    );
    
    loading.value = true;
    await modelConfigStore.deleteProvider(provider.id);
    ElMessage.success('提供商删除成功');
    await loadProviders();
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('删除提供商失败');
    }
  } finally {
    loading.value = false;
  }
};

onMounted(() => {
  loadProviders();
});
</script>

<style scoped>
.provider-list-container {
  width: 100%;
}

.provider-card {
  margin-bottom: 20px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
</style> 