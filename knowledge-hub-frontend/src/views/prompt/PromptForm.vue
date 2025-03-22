<template>
  <div class="prompt-form">
    <el-form 
      ref="formRef"
      :model="form"
      :rules="rules"
      label-width="120px"
    >
      <el-form-item label="模板名称" prop="name">
        <el-input v-model="form.name" />
      </el-form-item>

      <el-form-item label="模板类型" prop="template_type">
        <el-select v-model="form.template_type">
          <el-option label="系统提示词" value="system" />
          <el-option label="用户提示词" value="user" />
        </el-select>
      </el-form-item>

      <el-form-item label="所属场景" prop="scene">
        <el-select 
          v-model="form.scene"
          clearable
          placeholder="选择场景"
          @change="handleSceneChange"
        >
          <el-option 
            v-for="scene in promptStore.scenes"
            :key="scene.id"
            :label="scene.name"
            :value="scene.id"
          />
        </el-select>
      </el-form-item>

      <el-form-item 
        v-if="form.template_type === 'user'"
        label="关联系统提示词" 
        prop="system_prompt"
      >
        <el-select 
          v-model="form.system_prompt"
          clearable
          placeholder="选择关联的系统提示词"
          filterable
        >
          <el-option-group label="当前场景">
            <el-option 
              v-for="template in currentSceneSystemPrompts"
              :key="template.id"
              :label="template.name"
              :value="template.id"
            >
              <div style="display: flex; flex-direction: column;">
                <span>{{ template.name }}</span>
                <small style="color: #909399; font-size: 12px;">{{ template.description }}</small>
              </div>
            </el-option>
          </el-option-group>
          <el-option-group label="其他场景">
            <el-option 
              v-for="template in otherSceneSystemPrompts"
              :key="template.id"
              :label="template.name"
              :value="template.id"
            >
              <div style="display: flex; flex-direction: column;">
                <span>{{ template.name }}</span>
                <small style="color: #909399; font-size: 12px;">
                  [{{ getSceneName(template.scene) }}] {{ template.description }}
                </small>
              </div>
            </el-option>
          </el-option-group>
        </el-select>
      </el-form-item>

      <el-form-item label="模板描述" prop="description">
        <el-input 
          v-model="form.description" 
          type="textarea" 
          :rows="2"
        />
      </el-form-item>

      <el-form-item label="模板内容" prop="content">
        <el-input 
          v-model="form.content" 
          type="textarea" 
          :rows="6"
          :placeholder="contentPlaceholder"
        />
      </el-form-item>

      <el-form-item label="关联模型">
        <el-select 
          v-model="form.model"
          clearable
          placeholder="选择特定模型或留空作为通用模板"
        >
          <el-option 
            v-for="model in modelStore.models"
            :key="model.id"
            :label="model.name"
            :value="model.id"
          />
        </el-select>
      </el-form-item>

      <el-form-item label="变量定义">
        <div v-for="(variable, index) in variables" :key="index" class="variable-item">
          <el-input v-model="variable.name" placeholder="变量名" />
          <el-input v-model="variable.description" placeholder="变量说明" />
          <el-input v-model="variable.example" placeholder="示例值" />
          <el-button type="danger" link @click="removeVariable(index)">删除</el-button>
        </div>
        <el-button type="primary" link @click="addVariable">添加变量</el-button>
      </el-form-item>

      <el-form-item label="是否公开">
        <el-switch v-model="form.is_public" />
      </el-form-item>

      <el-form-item>
        <el-button type="primary" @click="handleSubmit">保存</el-button>
        <el-button @click="$router.back()">取消</el-button>
      </el-form-item>
    </el-form>

    <div class="template-help">
      <h3>模板使用说明</h3>
      <el-divider />
      
      <h4>示例模板</h4>
      <pre class="example-template">
你是一个专业的{role}。请根据以下要求完成任务：

任务描述：{task}

要求：
1. {requirement_1}
2. {requirement_2}

请以专业的方式回答。
      </pre>
      
      <h4>变量说明</h4>
      <el-descriptions :column="1" border>
        <el-descriptions-item label="role">角色定义，如"程序员"、"翻译"等</el-descriptions-item>
        <el-descriptions-item label="task">具体任务描述</el-descriptions-item>
        <el-descriptions-item label="requirement_1">第一个具体要求</el-descriptions-item>
        <el-descriptions-item label="requirement_2">第二个具体要求</el-descriptions-item>
      </el-descriptions>
      
      <h4>使用提示</h4>
      <ul>
        <li>使用 {变量名} 格式定义模板变量</li>
        <li>每个变量需要在"变量定义"中声明并说明用途</li>
        <li>系统提示词通常用于设定AI的角色和行为规范</li>
        <li>用户提示词用于构建具体的问题模板</li>
        <li>场景模板适用于特定场景的完整对话流程</li>
      </ul>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, computed } from 'vue'
import { useModelConfigStore } from '@/stores/modelConfig'
import { usePromptStore } from '@/stores/prompt'
import { useAuthStore } from '@/stores/auth'
import { useRouter, useRoute } from 'vue-router'
import { ElMessage } from 'element-plus'

const router = useRouter()
const route = useRoute()
const modelStore = useModelConfigStore()
const promptStore = usePromptStore()
const authStore = useAuthStore()
const formRef = ref()

const isEdit = computed(() => route.params.id)

const form = reactive({
  name: '',
  template_type: 'user',
  scene: null,
  system_prompt: null,
  description: '',
  content: '',
  model: null,
  is_public: true
})

const variables = ref([])

const rules = {
  name: [{ required: true, message: '请输入模板名称', trigger: 'blur' }],
  template_type: [{ required: true, message: '请选择模板类型', trigger: 'change' }],
  content: [{ required: true, message: '请输入模板内容', trigger: 'blur' }]
}

const systemPrompts = computed(() => {
  return promptStore.templates.filter(t => t.template_type === 'system')
})

const currentSceneSystemPrompts = computed(() => {
  return promptStore.templates.filter(t => 
    t.template_type === 'system' && 
    t.scene === form.scene
  )
})

const otherSceneSystemPrompts = computed(() => {
  return promptStore.templates.filter(t => 
    t.template_type === 'system' && 
    t.scene !== form.scene
  )
})

const getSceneName = (sceneId) => {
  const scene = promptStore.scenes.find(s => s.id === sceneId)
  return scene?.name || '未知场景'
}

const handleSceneChange = () => {
  form.system_prompt = null
}

const addVariable = () => {
  variables.value.push({ name: '', description: '', example: '' })
}

const removeVariable = (index) => {
  variables.value.splice(index, 1)
}

const loadTemplate = async (id) => {
  try {
    const template = await promptStore.getTemplate(id)
    Object.assign(form, {
      name: template.name,
      template_type: template.template_type,
      scene: template.scene,
      system_prompt: template.system_prompt,
      description: template.description,
      content: template.content,
      model: template.model,
      is_public: template.is_public
    })
    
    if (template.variables) {
      variables.value = Object.entries(template.variables).map(([name, description]) => ({
        name,
        description,
        example: template.example_values?.[name] || ''
      }))
    }
  } catch (error) {
    console.error('获取模板失败:', error)
    ElMessage.error('获取模板数据失败')
  }
}

const handleSubmit = async () => {
  try {
    await formRef.value.validate()
    
    if (!authStore.user) {
      await authStore.checkAuth()
    }
    
    const variablesObj = {}
    const exampleValuesObj = {}
    variables.value.forEach(v => {
      if (v.name && v.description) {
        variablesObj[v.name] = v.description
        if (v.example) {
          exampleValuesObj[v.name] = v.example
        }
      }
    })
    
    const submitData = {
      name: form.name,
      template_type: form.template_type,
      scene: form.scene,
      system_prompt: form.system_prompt,
      description: form.description,
      content: form.content,
      model: form.model,
      is_public: form.is_public,
      variables: variablesObj,
      example_values: exampleValuesObj,
      created_by: authStore.user.id
    }
    
    if (isEdit.value) {
      await promptStore.updateTemplate(route.params.id, submitData)
    } else {
      await promptStore.createTemplate(submitData)
    }
    
    ElMessage.success('保存成功')
    router.push('/prompts')
  } catch (error) {
    console.error('保存失败:', error)
    ElMessage.error(error.response?.data?.message || '保存失败，请检查表单内容')
  }
}

onMounted(async () => {
  try {
    // 确保先加载场景数据
    await promptStore.fetchScenes()
    
    // 添加调试日志
    console.log('场景数据:', promptStore.scenes)
    
    // 如果场景数据为空，提示错误
    if (!promptStore.scenes.length) {
      ElMessage.warning('未找到场景数据，请先创建场景')
    }
    
    // 加载其他必要数据
    await Promise.all([
      modelStore.fetchModels(),
      promptStore.fetchTemplates()
    ])
    
    if (isEdit.value) {
      await loadTemplate(route.params.id)
    }
  } catch (error) {
    console.error('初始化失败:', error)
    ElMessage.error('加载数据失败')
  }
})

const contentPlaceholder = `你是一个专业的{role}。请根据以下要求完成任务：

任务描述：{task}

要求：
1. {requirement_1}
2. {requirement_2}

请以专业的方式回答。`
</script>

<style scoped>
.template-help {
  margin-top: 30px;
  padding: 20px;
  background-color: #f8f9fa;
  border-radius: 4px;
}

.example-template {
  background-color: #fff;
  padding: 15px;
  border-radius: 4px;
  border: 1px solid #dcdfe6;
  margin: 10px 0;
  white-space: pre-wrap;
}

.template-help h4 {
  margin: 15px 0 10px;
  color: #303133;
}

.template-help ul {
  padding-left: 20px;
  color: #606266;
}

.template-help ul li {
  margin: 5px 0;
}

.variable-item {
  display: flex;
  gap: 10px;
  margin-bottom: 10px;
}

.variable-item .el-input {
  flex: 1;
}

.el-select-dropdown__item small {
  display: block;
  margin-top: 4px;
}
</style> 