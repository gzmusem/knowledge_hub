<template>
  <div class="model-config-container">
    <el-card class="config-card">
      <template #header>
        <div class="card-header">
          <h2>{{ getPageTitle }}</h2>
          <div class="header-actions">
            <el-button 
              v-if="currentRoute === 'ProviderList'" 
              type="primary" 
              @click="router.push('/model-config/providers/add')"
            >
              添加提供商
            </el-button>
            <el-button 
              v-if="currentRoute === 'ModelList'" 
              type="primary" 
              @click="router.push('/model-config/models/add')"
            >
              添加模型
            </el-button>
          </div>
        </div>
      </template>
      
      <el-tabs v-model="activeTab" @tab-click="handleTabClick">
        <el-tab-pane label="提供商管理" name="providers"></el-tab-pane>
        <el-tab-pane label="模型管理" name="models"></el-tab-pane>
        <el-tab-pane label="使用统计" name="usage"></el-tab-pane>
      </el-tabs>
      
      <div class="config-content">
        <router-view></router-view>
      </div>
    </el-card>
  </div>
</template>

<script setup>
import { ref, computed, watch } from 'vue';
import { useRoute, useRouter } from 'vue-router';

const route = useRoute();
const router = useRouter();

// 根据当前路由设置活动标签
const activeTab = ref('providers');

// 获取当前路由名称
const currentRoute = computed(() => route.name);

// 根据当前路由设置页面标题
const getPageTitle = computed(() => {
  switch (route.name) {
    case 'ProviderList':
      return '提供商管理';
    case 'AddProvider':
      return '添加提供商';
    case 'EditProvider':
      return '编辑提供商';
    case 'ModelList':
      return '模型管理';
    case 'AddModel':
      return '添加模型';
    case 'EditModel':
      return '编辑模型';
    case 'TokenUsage':
      return 'Token使用统计';
    default:
      return '模型配置';
  }
});

// 处理标签点击
const handleTabClick = (tab) => {
  router.push(`/model-config/${tab.props.name}`);
};

// 监听路由变化，更新活动标签
watch(
  () => route.path,
  (path) => {
    if (path.includes('/model-config/providers')) {
      activeTab.value = 'providers';
    } else if (path.includes('/model-config/models')) {
      activeTab.value = 'models';
    } else if (path.includes('/model-config/usage')) {
      activeTab.value = 'usage';
    }
  },
  { immediate: true }
);
</script>

<style scoped>
.model-config-container {
  padding: 20px;
}

.config-card {
  margin-bottom: 20px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.config-content {
  min-height: 500px;
  margin-top: 20px;
}
</style> 