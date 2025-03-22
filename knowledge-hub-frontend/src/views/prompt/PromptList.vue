<template>
  <div class="prompt-list">
    <div class="header">
      <h2>提示词模板管理</h2>
      <el-button 
        type="primary" 
        @click="$router.push('/prompts/add')"
      >
        新建模板
      </el-button>
    </div>

    <!-- 添加场景筛选 -->
    <div class="filter-bar">
      <el-select 
        v-model="selectedScene" 
        placeholder="选择场景"
        clearable
        @change="handleSceneChange"
      >
        <el-option 
          v-for="scene in promptStore.scenes"
          :key="scene.id"
          :label="scene.name"
          :value="scene.id"
        />
      </el-select>
    </div>

    <el-table 
      :data="promptStore.templates"
      v-loading="loading"
    >
      <el-table-column prop="name" label="模板名称" />
      <el-table-column prop="template_type" label="类型" width="120">
        <template #default="{ row }">
          <el-tag :type="row.template_type === 'system' ? 'success' : 'primary'">
            {{ getTemplateTypeName(row.template_type) }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column label="关联信息" width="200">
        <template #default="{ row }">
          <template v-if="row.template_type === 'system'">
            <div class="associated-info">
              <span class="label">关联用户提示词：</span>
              <el-tag v-if="getUserPrompts(row).length" type="info">
                {{ getUserPrompts(row).length }}个
                <el-tooltip placement="top">
                  <template #content>
                    <div v-for="prompt in getUserPrompts(row)" :key="prompt.id">
                      {{ prompt.name }}
                    </div>
                  </template>
                  <el-icon><InfoFilled /></el-icon>
                </el-tooltip>
              </el-tag>
              <span v-else>无</span>
            </div>
          </template>
          <template v-else>
            <div class="associated-info">
              <span class="label">关联系统提示词：</span>
              <template v-if="row.system_prompt">
                <el-tag type="success">
                  {{ getSystemPromptName(row.system_prompt) }}
                </el-tag>
              </template>
              <span v-else>无</span>
            </div>
          </template>
        </template>
      </el-table-column>
      <el-table-column prop="scene.name" label="所属场景" />
      <el-table-column prop="description" label="描述" show-overflow-tooltip />
      <el-table-column prop="is_public" label="是否公开" width="80">
        <template #default="{ row }">
          <el-switch v-model="row.is_public" disabled />
        </template>
      </el-table-column>
      <el-table-column label="操作" width="250" fixed="right">
        <template #default="{ row }">
          <el-button link @click="handlePreview(row)">预览</el-button>
          <el-button link @click="handleEdit(row)">编辑</el-button>
          <el-button 
            v-if="row.template_type === 'user'"
            link 
            type="primary" 
            @click="handleAssociate(row)"
          >
            关联系统提示词
          </el-button>
          <el-button link type="danger" @click="handleDelete(row)">删除</el-button>
        </template>
      </el-table-column>
    </el-table>

    <!-- 预览对话框 -->
    <el-dialog v-model="previewVisible" title="模板预览" width="600px">
      <template v-if="selectedTemplate">
        <div v-if="selectedTemplate.system_prompt" class="preview-section">
          <h4>系统提示词：</h4>
          <pre>{{ getSystemPromptContent(selectedTemplate.system_prompt) }}</pre>
        </div>
        <div class="preview-section">
          <h4>{{ selectedTemplate.template_type === 'system' ? '系统提示词' : '用户提示词' }}：</h4>
          <pre>{{ selectedTemplate.content }}</pre>
        </div>
        <div v-if="selectedTemplate.variables" class="preview-section">
          <h4>变量说明：</h4>
          <el-descriptions :column="1" border>
            <el-descriptions-item 
              v-for="(desc, key) in selectedTemplate.variables" 
              :key="key" 
              :label="key"
            >
              {{ desc }}
              <template v-if="selectedTemplate.example_values?.[key]">
                <br>
                <small class="example-value">示例：{{ selectedTemplate.example_values[key] }}</small>
              </template>
            </el-descriptions-item>
          </el-descriptions>
        </div>
      </template>
    </el-dialog>

    <!-- 关联系统提示词对话框 -->
    <el-dialog 
      v-model="associateDialogVisible" 
      title="关联系统提示词" 
      width="500px"
    >
      <el-form v-if="currentTemplate" :model="associateForm">
        <el-form-item label="选择系统提示词">
          <el-select v-model="associateForm.systemPromptId" style="width: 100%">
            <el-option
              v-for="prompt in getSystemPrompts()"
              :key="prompt.id"
              :label="prompt.name"
              :value="prompt.id"
            >
              <div style="display: flex; justify-content: space-between;">
                <span>{{ prompt.name }}</span>
                <small style="color: #999">{{ prompt.description }}</small>
              </div>
            </el-option>
          </el-select>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="associateDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handleAssociateSubmit">确定</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue'
import { usePromptStore } from '@/stores/prompt'
import { useRouter } from 'vue-router'
import { ElMessageBox, ElMessage } from 'element-plus'
import { InfoFilled } from '@element-plus/icons-vue'

const router = useRouter()
const promptStore = usePromptStore()
const loading = ref(false)
const previewVisible = ref(false)
const selectedTemplate = ref(null)
const selectedScene = ref(null)
const associateDialogVisible = ref(false)
const currentTemplate = ref(null)
const associateForm = ref({ systemPromptId: null })

const getTemplateTypeName = (type) => {
  const types = {
    system: '系统提示词',
    user: '用户提示词',
    scene: '场景模板'
  }
  return types[type] || type
}

const handlePreview = (template) => {
  selectedTemplate.value = template
  previewVisible.value = true
}

const handleEdit = (template) => {
  router.push(`/prompts/edit/${template.id}`)
}

const handleDelete = async (template) => {
  try {
    await ElMessageBox.confirm(
      '确定要删除这个模板吗？此操作不可恢复。',
      '提示',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )
    
    await promptStore.deleteTemplate(template.id)
    ElMessage.success('删除成功')
    await promptStore.fetchTemplates() // 刷新列表
  } catch (error) {
    if (error !== 'cancel') {
      console.error('删除失败:', error)
      ElMessage.error('删除失败')
    }
  }
}

// 获取系统提示词列表
const getSystemPrompts = () => {
  return promptStore.templates.filter(t => t.template_type === 'system')
}

// 获取关联的用户提示词
const getUserPrompts = (systemPrompt) => {
  return promptStore.templates.filter(t => t.system_prompt === systemPrompt.id)
}

// 获取系统提示词名称
const getSystemPromptName = (systemPromptId) => {
  const prompt = promptStore.templates.find(t => t.id === systemPromptId)
  return prompt?.name || '未知'
}

// 获取系统提示词内容
const getSystemPromptContent = (systemPromptId) => {
  const prompt = promptStore.templates.find(t => t.id === systemPromptId)
  return prompt?.content || ''
}

// 处理场景筛选
const handleSceneChange = () => {
  // 这里可以添加场景筛选逻辑
}

// 处理关联系统提示词
const handleAssociate = (template) => {
  currentTemplate.value = template
  associateForm.value.systemPromptId = template.system_prompt
  associateDialogVisible.value = true
}

// 提交关联
const handleAssociateSubmit = async () => {
  try {
    if (!currentTemplate.value) return
    
    await promptStore.updateTemplate(currentTemplate.value.id, {
      system_prompt: associateForm.value.systemPromptId
    })
    
    ElMessage.success('关联成功')
    associateDialogVisible.value = false
    await promptStore.fetchTemplates() // 刷新列表
  } catch (error) {
    console.error('关联失败:', error)
    ElMessage.error('关联失败')
  }
}

onMounted(async () => {
  loading.value = true
  try {
    await Promise.all([
      promptStore.fetchTemplates(),
      promptStore.fetchScenes()
    ])
  } finally {
    loading.value = false
  }
})
</script>

<style scoped>
.filter-bar {
  margin-bottom: 20px;
}

.associated-info {
  font-size: 13px;
  .label {
    color: #909399;
  }
}

.preview-section {
  margin-bottom: 20px;
  
  h4 {
    margin-bottom: 10px;
    color: #606266;
  }
  
  pre {
    background: #f8f9fa;
    padding: 12px;
    border-radius: 4px;
    white-space: pre-wrap;
  }
}

.example-value {
  color: #909399;
  font-style: italic;
}
</style> 