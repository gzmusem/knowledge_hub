<template>
  <div class="home-view">
    <el-row :gutter="20">
      <el-col :span="24">
        <div class="welcome-section">
          <h1>欢迎使用个人智能知识库</h1>
          <p>通过AI助手学习和整理您的知识</p>
          <div class="action-buttons">
            <el-button type="primary" @click="$router.push('/chat')">开始新对话</el-button>
            <el-button @click="$router.push('/knowledge')">浏览知识库</el-button>
          </div>
        </div>
      </el-col>
    </el-row>
    
    <el-row :gutter="20" class="stats-row">
      <el-col :span="8">
        <el-card>
          <template #header>
            <div class="card-header">
              <span>对话数量</span>
            </div>
          </template>
          <div class="card-value">{{ stats.conversations || 0 }}</div>
        </el-card>
      </el-col>
      
      <el-col :span="8">
        <el-card>
          <template #header>
            <div class="card-header">
              <span>知识点</span>
            </div>
          </template>
          <div class="card-value">{{ stats.knowledgePoints || 0 }}</div>
        </el-card>
      </el-col>
      
      <el-col :span="8">
        <el-card>
          <template #header>
            <div class="card-header">
              <span>分类数量</span>
            </div>
          </template>
          <div class="card-value">{{ stats.categories || 0 }}</div>
        </el-card>
      </el-col>
    </el-row>
    
    <el-row :gutter="20">
      <el-col :span="12">
        <div class="section">
          <div class="section-header">
            <h2>最近对话</h2>
            <el-button size="small" @click="$router.push('/chat')">查看全部</el-button>
          </div>
          <el-empty v-if="recentConversations.length === 0" description="暂无对话"></el-empty>
          <div v-else class="recent-list">
            <div v-for="item in recentConversations" :key="item.id" class="recent-item" @click="$router.push(`/chat/${item.id}`)">
              <span class="title">{{ item.title || '无标题对话' }}</span>
              <span class="date">{{ formatDate(item.updated_at) }}</span>
            </div>
          </div>
        </div>
      </el-col>
      
      <el-col :span="12">
        <div class="section">
          <div class="section-header">
            <h2>知识点统计</h2>
            <el-button size="small" @click="$router.push('/knowledge')">查看全部</el-button>
          </div>
          <el-empty v-if="categories.length === 0" description="暂无分类"></el-empty>
          <div v-else class="category-stats">
            <div v-for="category in categories" :key="category.id" class="category-item">
              <span class="name">{{ category.name }}</span>
              <el-progress :percentage="getCategoryPercentage(category)" />
            </div>
          </div>
        </div>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue';
import { useChatStore } from '@/stores/chat';
import { useKnowledgeStore } from '@/stores/knowledge';

const chatStore = useChatStore();
const knowledgeStore = useKnowledgeStore();

const recentConversations = ref([]);
const categories = ref([]);
const stats = ref({
  conversations: 0,
  knowledgePoints: 0,
  categories: 0
});

// 计算分类百分比
const getCategoryPercentage = (category) => {
  const total = stats.value.knowledgePoints;
  if (!total) return 0;
  return Math.round((category.knowledge_count / total) * 100);
};

// 格式化日期
const formatDate = (dateString) => {
  const date = new Date(dateString);
  return date.toLocaleDateString('zh-CN');
};

// 加载数据
onMounted(async () => {
  try {
    // 加载统计数据
    const statsData = await knowledgeStore.fetchStats();
    stats.value = statsData;
    
    // 加载最近对话
    recentConversations.value = await chatStore.fetchRecentConversations();
    
    // 加载分类
    const categoriesData = await knowledgeStore.fetchCategories();
    categories.value = categoriesData;
  } catch (error) {
    console.error('加载首页数据失败:', error);
  }
});
</script>

<style scoped>
.home-view {
  padding: 20px;
}

.welcome-section {
  text-align: center;
  padding: 40px 20px;
  background-color: #fff;
  border-radius: 8px;
  margin-bottom: 30px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.1);
}

.welcome-section h1 {
  font-size: 28px;
  color: #343a40;
  margin-bottom: 10px;
}

.welcome-section p {
  color: #6c757d;
  margin-bottom: 24px;
}

.action-buttons {
  display: flex;
  justify-content: center;
  gap: 16px;
}

.stats-row {
  margin-bottom: 30px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.card-value {
  font-size: 36px;
  font-weight: bold;
  text-align: center;
  color: #343a40;
}

.section {
  background-color: #fff;
  border-radius: 8px;
  padding: 20px;
  margin-bottom: 20px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.1);
}

.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
  border-bottom: 1px solid #e9ecef;
  padding-bottom: 10px;
}

.section-header h2 {
  margin: 0;
  font-size: 18px;
}

.recent-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.recent-item {
  display: flex;
  justify-content: space-between;
  padding: 10px;
  border-radius: 4px;
  cursor: pointer;
  transition: background-color 0.2s;
}

.recent-item:hover {
  background-color: #f8f9fa;
}

.recent-item .title {
  font-weight: 500;
}

.recent-item .date {
  color: #6c757d;
  font-size: 0.9em;
}

.category-stats {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.category-item {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.category-item .name {
  font-weight: 500;
  color: #495057;
}
</style>
