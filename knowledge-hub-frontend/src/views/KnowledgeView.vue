<template>
  <div class="knowledge-view">
    <el-row :gutter="20">
      <el-col :span="6">
        <knowledge-tree @node-selected="handleNodeSelected" />
        
        <div class="filter-section">
          <h3>筛选</h3>
          <el-input v-model="searchQuery" placeholder="搜索知识点..." clearable>
            <template #prefix>
              <el-icon><Search /></el-icon>
            </template>
          </el-input>
          
          <div class="date-filter">
            <h4>创建日期</h4>
            <el-date-picker
              v-model="dateRange"
              type="daterange"
              range-separator="至"
              start-placeholder="开始日期"
              end-placeholder="结束日期"
              format="YYYY-MM-DD"
              value-format="YYYY-MM-DD"
              style="width: 100%"
            />
          </div>
        </div>
      </el-col>
      
      <el-col :span="18">
        <div class="content-section">
          <div class="header">
            <h2>{{ currentViewTitle }}</h2>
            <div class="actions">
              <el-button type="primary" @click="createKnowledge" plain>新建知识点</el-button>
            </div>
          </div>
          
          <el-empty v-if="filteredKnowledge.length === 0" description="暂无知识点" />
          
          <div v-else class="knowledge-grid">
            <knowledge-card
              v-for="item in filteredKnowledge"
              :key="item.id"
              :knowledge="item"
              @edit="editKnowledge"
              @delete="deleteKnowledge"
              @view-source="viewSource"
            />
          </div>
        </div>
      </el-col>
    </el-row>
    
    <!-- 知识点编辑对话框 -->
    <el-dialog v-model="dialogVisible" :title="isEdit ? '编辑知识点' : '新建知识点'" width="50%">
      <el-form :model="knowledgeForm" label-width="100px">
        <el-form-item label="标题">
          <el-input v-model="knowledgeForm.title" />
        </el-form-item>
        <el-form-item label="内容">
          <el-input v-model="knowledgeForm.content" type="textarea" :rows="6" />
        </el-form-item>
        <el-form-item label="分类">
          <el-select v-model="knowledgeForm.category" placeholder="选择分类" style="width: 100%">
            <el-option
              v-for="category in categories"
              :key="category.id"
              :label="category.name"
              :value="category.id"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="标签">
          <el-select
            v-model="knowledgeForm.tags"
            multiple
            placeholder="选择标签"
            style="width: 100%"
          >
            <el-option
              v-for="tag in tags"
              :key="tag.id"
              :label="tag.name"
              :value="tag.id"
            />
          </el-select>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" @click="saveKnowledge">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import { Search } from '@element-plus/icons-vue';
import KnowledgeTree from '@/components/knowledge/KnowledgeTree.vue';
import KnowledgeCard from '@/components/knowledge/KnowledgeCard.vue';
import { useKnowledgeStore } from '@/stores/knowledge';

const route = useRoute();
const router = useRouter();
const knowledgeStore = useKnowledgeStore();

// 数据状态
const knowledgeItems = ref([]);
const categories = ref([]);
const tags = ref([]);
const searchQuery = ref('');
const dateRange = ref([]);
const currentNode = ref({ type: 'all', id: 'all', label: '全部知识点' });

// 编辑状态
const dialogVisible = ref(false);
const isEdit = ref(false);
const knowledgeForm = ref({
  id: null,
  title: '',
  content: '',
  category: null,
  tags: []
});

// 计算属性
const currentViewTitle = computed(() => {
  return currentNode.value?.label || '全部知识点';
});

// 筛选知识点
const filteredKnowledge = computed(() => {
  let result = [...knowledgeItems.value];
  
  // 按分类或标签筛选
  if (currentNode.value.type === 'category' && currentNode.value.id !== 'all') {
    result = result.filter(item => item.category.id === currentNode.value.id);
  } else if (currentNode.value.type === 'tag') {
    result = result.filter(item => 
      item.tags.some(tag => tag.id === currentNode.value.id)
    );
  }
  
  // 搜索筛选
  if (searchQuery.value) {
    const query = searchQuery.value.toLowerCase();
    result = result.filter(item => 
      item.title.toLowerCase().includes(query) || 
      item.content.toLowerCase().includes(query)
    );
  }
  
  // 日期筛选
  if (dateRange.value && dateRange.value.length === 2) {
    const startDate = new Date(dateRange.value[0]);
    const endDate = new Date(dateRange.value[1]);
    endDate.setHours(23, 59, 59);
    
    result = result.filter(item => {
      const itemDate = new Date(item.created_at);
      return itemDate >= startDate && itemDate <= endDate;
    });
  }
  
  return result;
});

// 加载数据
const loadData = async () => {
  try {
    const [knowledgeData, categoriesData, tagsData] = await Promise.all([
      knowledgeStore.fetchKnowledgePoints(),
      knowledgeStore.fetchCategories(),
      knowledgeStore.fetchTags()
    ]);
    
    knowledgeItems.value = knowledgeData;
    categories.value = categoriesData;
    tags.value = tagsData;
  } catch (error) {
    console.error('加载知识库数据失败:', error);
  }
};

// 事件处理
const handleNodeSelected = (node) => {
  currentNode.value = node;
};

const createKnowledge = () => {
  isEdit.value = false;
  knowledgeForm.value = {
    id: null,
    title: '',
    content: '',
    category: currentNode.value.type === 'category' ? currentNode.value.id : null,
    tags: currentNode.value.type === 'tag' ? [currentNode.value.id] : []
  };
  dialogVisible.value = true;
};

const editKnowledge = (knowledge) => {
  isEdit.value = true;
  knowledgeForm.value = {
    id: knowledge.id,
    title: knowledge.title,
    content: knowledge.content,
    category: knowledge.category.id,
    tags: knowledge.tags.map(tag => tag.id)
  };
  dialogVisible.value = true;
};

const saveKnowledge = async () => {
  try {
    if (isEdit.value) {
      await knowledgeStore.updateKnowledgePoint(knowledgeForm.value);
    } else {
      await knowledgeStore.createKnowledgePoint(knowledgeForm.value);
    }
    dialogVisible.value = false;
    loadData();
  } catch (error) {
    console.error('保存知识点失败:', error);
  }
};

const deleteKnowledge = async (id) => {
  try {
    await knowledgeStore.deleteKnowledgePoint(id);
    loadData();
  } catch (error) {
    console.error('删除知识点失败:', error);
  }
};

const viewSource = (conversationId) => {
  if (conversationId) {
    router.push(`/chat/${conversationId}`);
  }
};

// 监听路由变化
watch(
  () => route.params,
  (params) => {
    if (params.id) {
      if (route.path.includes('/category/')) {
        currentNode.value = { 
          type: 'category', 
          id: params.id,
          label: categories.value.find(c => c.id === params.id)?.name || '分类'
        };
      } else if (route.path.includes('/tag/')) {
        currentNode.value = { 
          type: 'tag', 
          id: params.id,
          label: tags.value.find(t => t.id === params.id)?.name || '标签'
        };
      }
    }
  },
  { immediate: true }
);

// 初始化
onMounted(async () => {
  await loadData();
});
</script>

<style scoped>
.knowledge-view {
  padding: 20px;
}

.filter-section {
  background-color: #fff;
  border-radius: 8px;
  padding: 16px;
  margin-top: 20px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.1);
}

.date-filter {
  margin-top: 16px;
}

.date-filter h4 {
  margin-top: 0;
  margin-bottom: 8px;
  font-weight: 500;
  color: #343a40;
}

.content-section {
  background-color: #fff;
  border-radius: 8px;
  padding: 20px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.1);
}

.header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
  padding-bottom: 16px;
  border-bottom: 1px solid #e9ecef;
}

.header h2 {
  margin: 0;
  color: #343a40;
}

.knowledge-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
  gap: 20px;
}
</style>
