<template>
    <el-card class="knowledge-card">
      <template #header>
        <div class="card-header">
          <h3>{{ knowledge.title }}</h3>
          <div class="actions">
            <el-button type="text" @click="handleEdit">
              <el-icon><Edit /></el-icon>
            </el-button>
            <el-button type="text" @click="handleDelete">
              <el-icon><Delete /></el-icon>
            </el-button>
          </div>
        </div>
      </template>
      <div class="card-content" v-html="formattedContent"></div>
      <div class="card-footer">
        <div class="tags">
          <el-tag v-for="tag in knowledge.tags" :key="tag.id" size="small" effect="plain" class="tag">
            {{ tag.name }}
          </el-tag>
        </div>
        <div class="metadata">
          <span class="date">{{ formatDate(knowledge.created_at) }}</span>
          <el-button type="text" size="small" @click="handleViewSource">查看来源</el-button>
        </div>
      </div>
    </el-card>
  </template>
  
  <script setup>
  import { computed } from 'vue';
  import { Edit, Delete } from '@element-plus/icons-vue';
  import MarkdownIt from 'markdown-it';
  import { ElMessageBox } from 'element-plus';
  import { useKnowledgeStore } from '@/stores/knowledge';
  
  const props = defineProps({
    knowledge: {
      type: Object,
      required: true
    }
  });
  
  const emit = defineEmits(['edit', 'delete', 'view-source']);
  const knowledgeStore = useKnowledgeStore();
  
  const md = new MarkdownIt();
  const formattedContent = computed(() => {
    return md.render(props.knowledge.content);
  });
  
  const formatDate = (dateString) => {
    const date = new Date(dateString);
    return date.toLocaleDateString('zh-CN');
  };
  
  const handleEdit = () => {
    emit('edit', props.knowledge);
  };
  
  const handleDelete = async () => {
    try {
      await ElMessageBox.confirm('确定要删除这个知识点吗?', '警告', {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      });
      
      await knowledgeStore.deleteKnowledgePoint(props.knowledge.id);
      emit('delete', props.knowledge.id);
    } catch (e) {
      // 用户取消删除
    }
  };
  
  const handleViewSource = () => {
    emit('view-source', props.knowledge.conversation_id);
  };
  </script>
  
  <style scoped>
  .knowledge-card {
    margin-bottom: 20px;
    transition: transform 0.3s;
  }
  
  .knowledge-card:hover {
    transform: translateY(-5px);
  }
  
  .card-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
  }
  
  .card-header h3 {
    margin: 0;
    font-size: 18px;
    color: #343a40;
  }
  
  .card-content {
    padding: 10px 0;
    color: #495057;
  }
  
  .card-footer {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-top: 16px;
    padding-top: 16px;
    border-top: 1px solid #e9ecef;
  }
  
  .tags {
    display: flex;
    flex-wrap: wrap;
    gap: 8px;
  }
  
  .tag {
    cursor: pointer;
  }
  
  .metadata {
    display: flex;
    align-items: center;
    color: #6c757d;
    font-size: 12px;
  }
  
  .date {
    margin-right: 10px;
  }
  </style>