<template>
  <div class="token-usage">
    <div class="page-header">
      <h3>Token使用统计</h3>
      <div class="filter-controls">
        <el-date-picker
          v-model="dateRange"
          type="daterange"
          range-separator="至"
          start-placeholder="开始日期"
          end-placeholder="结束日期"
          format="YYYY-MM-DD"
          value-format="YYYY-MM-DD"
          @change="handleDateChange"
        />
        <el-select 
          v-model="selectedModel" 
          placeholder="选择模型" 
          clearable
          @change="handleModelChange"
        >
          <el-option 
            v-for="model in models" 
            :key="model.id" 
            :label="model.name" 
            :value="model.id"
          />
        </el-select>
        <el-button type="primary" @click="fetchUsageData">查询</el-button>
      </div>
    </div>
    
    <!-- 统计卡片 -->
    <el-row :gutter="20" class="stat-cards">
      <el-col :span="8">
        <el-card shadow="hover">
          <template #header>
            <div class="card-header">
              <span>总Token数</span>
            </div>
          </template>
          <div class="stat-value">{{ formatNumber(totalStats.total_tokens) }}</div>
        </el-card>
      </el-col>
      <el-col :span="8">
        <el-card shadow="hover">
          <template #header>
            <div class="card-header">
              <span>总成本(美元)</span>
            </div>
          </template>
          <div class="stat-value">${{ formatNumber(totalStats.cost_usd, 4) }}</div>
        </el-card>
      </el-col>
      <el-col :span="8">
        <el-card shadow="hover">
          <template #header>
            <div class="card-header">
              <span>总成本(人民币)</span>
            </div>
          </template>
          <div class="stat-value">¥{{ formatNumber(totalStats.cost_rmb, 2) }}</div>
        </el-card>
      </el-col>
    </el-row>
    
    <!-- 使用趋势图 -->
    <el-card class="chart-card">
      <template #header>
        <div class="card-header">
          <span>Token使用趋势</span>
        </div>
      </template>
      <div id="usage-chart" style="width: 100%; height: 400px;"></div>
    </el-card>
    
    <!-- 使用明细表格 -->
    <el-card class="usage-table-card">
      <template #header>
        <div class="card-header">
          <span>使用明细</span>
        </div>
      </template>
      <el-table 
        :data="usageData" 
        border 
        style="width: 100%"
        v-loading="loading"
      >
        <el-table-column prop="request_time" label="请求时间" width="180" />
        <el-table-column prop="model.name" label="模型" width="150" />
        <el-table-column prop="prompt_tokens" label="提示词Token" width="120" />
        <el-table-column prop="completion_tokens" label="回复Token" width="120" />
        <el-table-column prop="total_tokens" label="总Token" width="120" />
        <el-table-column prop="cost_usd" label="成本(美元)" width="120">
          <template #default="scope">
            ${{ formatNumber(scope.row.cost_usd, 6) }}
          </template>
        </el-table-column>
        <el-table-column prop="cost_rmb" label="成本(人民币)" width="120">
          <template #default="scope">
            ¥{{ formatNumber(scope.row.cost_rmb, 4) }}
          </template>
        </el-table-column>
        <el-table-column prop="response_time" label="响应时间(秒)" width="120">
          <template #default="scope">
            {{ formatNumber(scope.row.response_time, 2) }}s
          </template>
        </el-table-column>
        <el-table-column prop="is_successful" label="状态" width="80">
          <template #default="scope">
            <el-tag :type="scope.row.is_successful ? 'success' : 'danger'">
              {{ scope.row.is_successful ? '成功' : '失败' }}
            </el-tag>
          </template>
        </el-table-column>
      </el-table>
      
      <!-- 分页 -->
      <div class="pagination-container">
        <el-pagination
          v-model:current-page="currentPage"
          v-model:page-size="pageSize"
          :page-sizes="[10, 20, 50, 100]"
          layout="total, sizes, prev, pager, next, jumper"
          :total="totalItems"
          @size-change="handleSizeChange"
          @current-change="handleCurrentChange"
        />
      </div>
    </el-card>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, watch } from 'vue';
import { ElMessage } from 'element-plus';
import { useModelConfigStore } from '@/stores/modelConfig';
import * as echarts from 'echarts';

const modelConfigStore = useModelConfigStore();
const loading = ref(false);
const models = ref([]);
const usageData = ref([]);
const totalItems = ref(0);
const currentPage = ref(1);
const pageSize = ref(20);
const selectedModel = ref(null);
const dateRange = ref([]);
const chart = ref(null);

// 总计统计
const totalStats = reactive({
  total_tokens: 0,
  cost_usd: 0,
  cost_rmb: 0
});

// 格式化数字
const formatNumber = (num, decimals = 0) => {
  if (num === undefined || num === null) return '0';
  return Number(num).toLocaleString(undefined, {
    minimumFractionDigits: decimals,
    maximumFractionDigits: decimals
  });
};

// 加载模型列表
const loadModels = async () => {
  try {
    models.value = await modelConfigStore.fetchModels();
  } catch (error) {
    ElMessage.error('加载模型列表失败');
  }
};

// 获取使用数据
const fetchUsageData = async () => {
  loading.value = true;
  try {
    const params = {
      page: currentPage.value,
      page_size: pageSize.value
    };
    
    if (selectedModel.value) {
      params.model_id = selectedModel.value;
    }
    
    if (dateRange.value && dateRange.value.length === 2) {
      params.start_date = dateRange.value[0];
      params.end_date = dateRange.value[1];
    }
    
    const response = await modelConfigStore.fetchTokenUsage(params);
    usageData.value = response.results || [];
    totalItems.value = response.count || 0;
    
    // 更新总计统计
    if (response.summary) {
      totalStats.total_tokens = response.summary.total_tokens || 0;
      totalStats.cost_usd = response.summary.cost_usd || 0;
      totalStats.cost_rmb = response.summary.cost_rmb || 0;
    }
    
    // 更新图表
    updateChart(response.chart_data || []);
  } catch (error) {
    ElMessage.error('获取Token使用数据失败');
  } finally {
    loading.value = false;
  }
};

// 初始化图表
const initChart = () => {
  if (chart.value) {
    chart.value.dispose();
  }
  
  const chartDom = document.getElementById('usage-chart');
  if (!chartDom) return;
  
  chart.value = echarts.init(chartDom);
  const option = {
    tooltip: {
      trigger: 'axis',
      axisPointer: {
        type: 'shadow'
      }
    },
    legend: {
      data: ['提示词Token', '回复Token', '成本(美元)']
    },
    grid: {
      left: '3%',
      right: '4%',
      bottom: '3%',
      containLabel: true
    },
    xAxis: {
      type: 'category',
      data: []
    },
    yAxis: [
      {
        type: 'value',
        name: 'Token数',
        position: 'left'
      },
      {
        type: 'value',
        name: '成本(美元)',
        position: 'right',
        axisLine: {
          show: true,
          lineStyle: {
            color: '#5470C6'
          }
        },
        axisLabel: {
          formatter: '${value}'
        }
      }
    ],
    series: [
      {
        name: '提示词Token',
        type: 'bar',
        stack: 'Token',
        emphasis: {
          focus: 'series'
        },
        data: []
      },
      {
        name: '回复Token',
        type: 'bar',
        stack: 'Token',
        emphasis: {
          focus: 'series'
        },
        data: []
      },
      {
        name: '成本(美元)',
        type: 'line',
        yAxisIndex: 1,
        data: []
      }
    ]
  };
  
  chart.value.setOption(option);
  
  // 窗口大小变化时自动调整图表大小
  window.addEventListener('resize', () => {
    chart.value && chart.value.resize();
  });
};

// 更新图表数据
const updateChart = (chartData) => {
  if (!chart.value) {
    initChart();
  }
  
  const dates = [];
  const promptTokens = [];
  const completionTokens = [];
  const costs = [];
  
  chartData.forEach(item => {
    dates.push(item.date);
    promptTokens.push(item.prompt_tokens);
    completionTokens.push(item.completion_tokens);
    costs.push(item.cost_usd);
  });
  
  chart.value.setOption({
    xAxis: {
      data: dates
    },
    series: [
      {
        name: '提示词Token',
        data: promptTokens
      },
      {
        name: '回复Token',
        data: completionTokens
      },
      {
        name: '成本(美元)',
        data: costs
      }
    ]
  });
};

// 处理日期变化
const handleDateChange = () => {
  currentPage.value = 1;
};

// 处理模型选择变化
const handleModelChange = () => {
  currentPage.value = 1;
};

// 处理页码变化
const handleCurrentChange = (page) => {
  currentPage.value = page;
  fetchUsageData();
};

// 处理每页条数变化
const handleSizeChange = (size) => {
  pageSize.value = size;
  currentPage.value = 1;
  fetchUsageData();
};

// 监听分页参数变化
watch([currentPage, pageSize], () => {
  fetchUsageData();
});

onMounted(async () => {
  await loadModels();
  await fetchUsageData();
  initChart();
});
</script>

<style scoped>
.token-usage {
  width: 100%;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.filter-controls {
  display: flex;
  gap: 10px;
}

.stat-cards {
  margin-bottom: 20px;
}

.stat-value {
  font-size: 24px;
  font-weight: bold;
  text-align: center;
  color: #409EFF;
}

.chart-card {
  margin-bottom: 20px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.pagination-container {
  margin-top: 20px;
  display: flex;
  justify-content: flex-end;
}
</style> 