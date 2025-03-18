<template>
    <div class="knowledge-tree">
      <h3>知识结构</h3>
      <el-tree
        :data="treeData"
        :props="defaultProps"
        @node-click="handleNodeClick"
        default-expand-all
        :highlight-current="true"
      >
        <template #default="{ node, data }">
          <div class="custom-node">
            <el-icon v-if="data.type === 'category'"><Folder /></el-icon>
            <el-icon v-else-if="data.type === 'tag'"><Collection /></el-icon>
            <el-icon v-else><Document /></el-icon>
            <span>{{ node.label }}</span>
            <el-tag v-if="data.count" size="small" type="info" class="count-tag">
              {{ data.count }}
            </el-tag>
          </div>
        </template>
      </el-tree>
    </div>
  </template>
  
  <script setup>
  import { ref, computed, onMounted } from 'vue';
  import { useKnowledgeStore } from '@/stores/knowledge';
  import { Folder, Collection, Document } from '@element-plus/icons-vue';
  
  const knowledgeStore = useKnowledgeStore();
  const emit = defineEmits(['node-selected']);
  
  const defaultProps = {
    children: 'children',
    label: 'label'
  };
  
  const treeData = computed(() => {
    const categories = knowledgeStore.categories.map(cat => ({
      id: cat.id,
      label: cat.name,
      type: 'category',
      count: cat.knowledge_count || 0,
      children: knowledgeStore.tags
        .filter(tag => tag.category_id === cat.id)
        .map(tag => ({
          id: tag.id,
          label: tag.name,
          type: 'tag',
          parentId: cat.id,
          count: tag.knowledge_count || 0
        }))
    }));
  
    return [
      {
        id: 'all',
        label: '全部知识',
        type: 'root',
        count: knowledgeStore.totalKnowledgeCount,
        children: categories
      }
    ];
  });
  
  const handleNodeClick = (data) => {
    emit('node-selected', {
      id: data.id,
      type: data.type,
      label: data.label,
      parentId: data.parentId
    });
  };
  
  onMounted(async () => {
    await Promise.all([
      knowledgeStore.fetchCategories(),
      knowledgeStore.fetchTags(),
      knowledgeStore.fetchKnowledgeStats()
    ]);
  });
  </script>
  
  <style scoped>
  .knowledge-tree {
    background-color: #fff;
    border-radius: 8px;
    padding: 16px;
    box-shadow: 0 2px 12px 0 rgba(0, 0, 0, 0.1);
  }
  
  .custom-node {
    display: flex;
    align-items: center;
    flex: 1;
  }
  
  .custom-node i {
    margin-right: 6px;
  }
  
  .count-tag {
    margin-left: auto;
  }
  </style>