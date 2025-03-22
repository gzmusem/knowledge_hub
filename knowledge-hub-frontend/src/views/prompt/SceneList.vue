<template>
  <div class="scene-list">
    <div class="header">
      <h2>场景管理</h2>
      <el-button type="primary" @click="handleAdd">新建场景</el-button>
    </div>

    <el-table :data="scenes" border v-loading="loading" element-loading-text="加载中...">
      <el-table-column prop="name" label="场景名称" />
      <el-table-column prop="code" label="场景代码" />
      <el-table-column prop="description" label="描述" show-overflow-tooltip />
      
      <el-table-column prop="order" label="排序" width="80" align="center" />
      
      <el-table-column prop="is_active" label="状态" width="100">
        <template #default="{ row }">
          <el-switch
            v-model="row.is_active"
            @change="handleStatusChange(row)"
          />
        </template>
      </el-table-column>
      
      <el-table-column prop="icon" label="图标" width="100">
        <template #default="{ row }">
          <el-icon v-if="row.icon">
            <component :is="row.icon" />
          </el-icon>
          <span v-else>-</span>
        </template>
      </el-table-column>
      
      <el-table-column label="操作" width="200" fixed="right">
        <template #default="{ row }">
          <el-button link type="primary" @click="handleEdit(row)">
            编辑
          </el-button>
          <el-button link type="danger" @click="handleDelete(row)">
            删除
          </el-button>
        </template>
      </el-table-column>
    </el-table>

    <!-- 编辑对话框 -->
    <el-dialog
      v-model="dialogVisible"
      :title="isEdit ? '编辑场景' : '新建场景'"
      width="500px"
    >
      <el-form
        ref="formRef"
        :model="form"
        :rules="rules"
        label-width="100px"
      >
        <el-form-item label="场景名称" prop="name">
          <el-input v-model="form.name" />
        </el-form-item>
        
        <el-form-item label="场景代码" prop="code">
          <el-input 
            v-model="form.code"
            :disabled="isEdit"
            placeholder="必须以小写字母开头，可包含数字和下划线"
          />
          <small class="form-tip">例如：qa_system, code_review, translation</small>
        </el-form-item>
        
        <el-form-item label="场景描述" prop="description">
          <el-input
            v-model="form.description"
            type="textarea"
            :rows="3"
          />
        </el-form-item>
        
        <el-form-item label="图标" prop="icon">
          <el-select 
            v-model="form.icon" 
            placeholder="请选择图标"
            clearable
            filterable
          >
            <el-option
              v-for="icon in iconList"
              :key="icon.name"
              :label="icon.name"
              :value="icon.name"
            >
              <div style="display: flex; align-items: center;">
                <el-icon>
                  <component :is="icon.name" />
                </el-icon>
                <span style="margin-left: 8px">{{ icon.name }}</span>
              </div>
            </el-option>
          </el-select>
        </el-form-item>
        
        <el-form-item label="排序" prop="order">
          <el-input-number v-model="form.order" :min="0" />
        </el-form-item>
        
        <el-form-item label="是否启用" prop="is_active">
          <el-switch v-model="form.is_active" />
        </el-form-item>
      </el-form>
      
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handleSubmit">确定</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { usePromptStore } from '@/stores/prompt'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import * as ElementPlusIcons from '@element-plus/icons-vue'

const router = useRouter()
const promptStore = usePromptStore()
const scenes = ref([])
const dialogVisible = ref(false)
const isEdit = ref(false)
const formRef = ref(null)
const loading = ref(false)

const form = ref({
  name: '',
  code: '',
  description: '',
  icon: '',
  order: 0,
  is_active: true
})

const rules = {
  name: [{ required: true, message: '请输入场景名称', trigger: 'blur' }],
  code: [
    { required: true, message: '请输入场景代码', trigger: 'blur' },
    { 
      pattern: /^[a-z][a-z0-9_]*$/, 
      message: '场景代码必须以小写字母开头，只能包含小写字母、数字和下划线', 
      trigger: 'blur' 
    }
  ]
}

// 生成图标列表
const iconList = ref(
  Object.keys(ElementPlusIcons).map(name => ({
    name,
    component: ElementPlusIcons[name]
  }))
)

// 重置表单
const resetForm = () => {
  form.value = {
    name: '',
    code: '',
    description: '',
    icon: '',
    order: 0,
    is_active: true
  }
  if (formRef.value) {
    formRef.value.resetFields()
  }
}

// 处理新增场景
const handleAdd = () => {
  isEdit.value = false
  resetForm()
  dialogVisible.value = true
}

// 处理编辑场景
const handleEdit = (row) => {
  isEdit.value = true
  form.value = { ...row }
  dialogVisible.value = true
}

// 处理删除场景
const handleDelete = async (row) => {
  try {
    await ElMessageBox.confirm('确定要删除该场景吗？', '提示', {
      type: 'warning'
    })
    await promptStore.deleteScene(row.id)
    ElMessage.success('删除成功')
    loadScenes()
  } catch (error) {
    if (error !== 'cancel') {
      console.error('删除场景失败:', error)
      ElMessage.error('删除失败')
    }
  }
}

// 处理排序变更
const handleOrderChange = async (row) => {
  try {
    await promptStore.reorderScene(row.id, row.order)
    ElMessage.success('排序更新成功')
    loadScenes()
  } catch (error) {
    console.error('更新排序失败:', error)
    ElMessage.error('更新排序失败')
  }
}

// 处理状态变更
const handleStatusChange = async (row) => {
  try {
    await promptStore.updateScene(row.id, { is_active: row.is_active })
    ElMessage.success('状态更新成功')
    loadScenes()
  } catch (error) {
    console.error('更新状态失败:', error)
    ElMessage.error('更新状态失败')
    // 恢复原状态
    row.is_active = !row.is_active
  }
}

// 处理表单提交
const handleSubmit = async () => {
  if (!formRef.value) return
  
  try {
    await formRef.value.validate()
    
    if (isEdit.value) {
      await promptStore.updateScene(form.value.id, form.value)
      ElMessage.success('更新成功')
    } else {
      await promptStore.createScene(form.value)
      ElMessage.success('创建成功')
    }
    
    dialogVisible.value = false
    await loadScenes()
  } catch (error) {
    console.error('保存场景失败:', error)
    ElMessage.error('保存失败')
  }
}

// 加载场景列表
const loadScenes = async () => {
  loading.value = true
  try {
    const data = await promptStore.fetchScenes()
    scenes.value = Array.isArray(data) ? data : []
  } catch (error) {
    console.error('加载场景列表失败:', error)
    ElMessage.error('加载失败')
    scenes.value = []
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  console.log('组件挂载，开始加载场景列表');
  loadScenes()
})
</script>

<style scoped>
.scene-list {
  padding: 20px;
}

.header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.el-table {
  margin-top: 20px;
}

.el-select {
  width: 100%;
}

/* 可选：调整图标选项的样式 */
:deep(.el-select-dropdown__item) {
  padding: 0 12px;
  height: 34px;
  line-height: 34px;
}

.form-tip {
  color: #909399;
  font-size: 12px;
  margin-top: 4px;
  display: block;
}
</style> 