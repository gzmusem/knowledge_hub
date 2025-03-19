<template>
  <div class="token-usage">
    <!-- 查询条件 -->
    <div class="query-section">
      <el-date-picker
        v-model="startDate"
        type="date"
        placeholder="开始日期"
        value-format="YYYY-MM-DD"
      />
      <span class="separator">至</span>
      <el-date-picker
        v-model="endDate"
        type="date"
        placeholder="结束日期"
        value-format="YYYY-MM-DD"
      />
      <el-select 
        v-model="selectedModel" 
        placeholder="选择模型"
        clearable
      >
        <el-option
          v-for="model in modelStore.availableModels"
          :key="model.model_id"
          :label="model.name"
          :value="model.model_id"
        />
      </el-select>
      <el-button 
        type="primary" 
        @click="handleQuery"
        :loading="loading"
      >
        查询
      </el-button>
    </div>

    <!-- 统计卡片 -->
    <div class="stats-cards">
      <el-card class="stats-card">
        <template #header>总Token使用量</template>
        {{ totalTokens.toLocaleString() }}
      </el-card>
      <el-card class="stats-card">
        <template #header>总费用(USD)</template>
        ${{ totalCostUSD.toFixed(4) }}
      </el-card>
      <el-card class="stats-card">
        <template #header>总费用(RMB)</template>
        ¥{{ totalCostRMB.toFixed(2) }}
      </el-card>
    </div>

    <!-- 数据表格 -->
    <el-table
      :data="usageData"
      style="width: 100%; margin-top: 20px"
      v-loading="loading"
    >
      <el-table-column
        prop="request_time"
        label="请求时间"
        width="180"
        :formatter="(row) => formatDate(row.request_time)"
      />
      <el-table-column
        prop="model_name"
        label="模型"
        width="180"
      />
      <el-table-column
        prop="total_tokens"
        label="Token数量"
      />
      <el-table-column
        prop="cost_usd"
        label="费用(USD)"
        :formatter="(row) => row.cost_usd ? `$${row.cost_usd.toFixed(4)}` : '-'"
      />
      <el-table-column
        prop="cost_rmb"
        label="费用(RMB)"
        :formatter="(row) => row.cost_rmb ? `¥${row.cost_rmb.toFixed(2)}` : '-'"
      />
    </el-table>

    <!-- 分页 -->
    <div class="pagination">
      <el-pagination
        v-model:current-page="currentPage"
        v-model:page-size="pageSize"
        :page-sizes="[10, 20, 50, 100]"
        layout="total, sizes, prev, pager, next"
        :total="total"
        @size-change="handleSizeChange"
        @current-change="handleCurrentChange"
      />
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue';
import { ElMessage } from 'element-plus';
import { useModelStore } from '@/stores/models';
import { useModelConfigStore } from '@/stores/modelConfig';

const modelStore = useModelStore();
const modelConfigStore = useModelConfigStore();

// 定义响应式变量
const startDate = ref('');
const endDate = ref('');
const selectedModel = ref('');
const loading = ref(false);
const currentPage = ref(1);
const pageSize = ref(20);
const total = ref(0);
const usageData = ref([]);

// 添加统计数据的响应式变量
const totalTokens = ref(0);
const totalCostUSD = ref(0);
const totalCostRMB = ref(0);

// 更新统计数据
const updateStats = () => {
  const stats = usageData.value.reduce((acc, item) => {
    acc.totalTokens += item.total_tokens || 0;
    acc.totalCostUSD += item.cost_usd || 0;
    acc.totalCostRMB += item.cost_rmb || 0;
    return acc;
  }, { totalTokens: 0, totalCostUSD: 0, totalCostRMB: 0 });

  totalTokens.value = stats.totalTokens;
  totalCostUSD.value = stats.totalCostUSD;
  totalCostRMB.value = stats.totalCostRMB;
};

// 日期格式化函数
const formatDate = (date) => {
  if (!date) return '';
  if (typeof date === 'string') {
    return date.replace('T', ' ').split('.')[0];
  }
  return new Date(date).toLocaleString();
};

// 获取使用数据
const fetchUsageData = async () => {
  try {
    loading.value = true;
    
    const params = {
      page: currentPage.value,
      page_size: pageSize.value
    };

    if (startDate.value) {
      params.start_date = formatDateForAPI(startDate.value);
    }
    if (endDate.value) {
      params.end_date = formatDateForAPI(endDate.value);
    }
    if (selectedModel.value) {
      params.model_id = selectedModel.value;
    }

    console.log('[DEBUG] 请求Token使用数据，参数:', params);

    const data = await modelConfigStore.fetchTokenUsage(params);
    console.log('[DEBUG] Token使用数据响应:', data);

    if (data) {
      usageData.value = Array.isArray(data) ? data : (data.items || []);
      total.value = data.total || usageData.value.length;
      updateStats();
    }
  } catch (error) {
    console.error('[ERROR] 获取Token使用数据失败:', error);
    ElMessage.error('获取使用数据失败，请检查网络连接');
    usageData.value = [];
    total.value = 0;
  } finally {
    loading.value = false;
  }
};

// 处理查询
const handleQuery = () => {
  currentPage.value = 1;
  fetchUsageData();
};

// 处理分页
const handleSizeChange = (val) => {
  pageSize.value = val;
  fetchUsageData();
};

const handleCurrentChange = (val) => {
  currentPage.value = val;
  fetchUsageData();
};

// 日期格式化
const formatDateForAPI = (date) => {
  if (!date) return '';
  if (typeof date === 'string') {
    date = new Date(date);
  }
  return date.toISOString().split('T')[0];
};

// 在组件挂载时获取数据
onMounted(async () => {
  try {
    await modelStore.fetchAvailableModels();
    await fetchUsageData();
  } catch (error) {
    console.error('初始化数据加载失败:', error);
  }
});
</script>

<style scoped>
.token-usage {
  padding: 20px;
}

.query-section {
  display: flex;
  gap: 10px;
  align-items: center;
  margin-bottom: 20px;
}

.stats-cards {
  display: flex;
  gap: 20px;
  margin-bottom: 20px;
}

.stats-card {
  flex: 1;
  text-align: center;
  font-size: 24px;
}

.pagination {
  margin-top: 20px;
  display: flex;
  justify-content: flex-end;
}

.separator {
  margin: 0 8px;
}
</style> 