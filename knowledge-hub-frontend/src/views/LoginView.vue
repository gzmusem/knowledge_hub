<template>
  <div class="login-container">
    <div class="login-box">
      <div class="logo">
        <h1>知识库</h1>
        <p>您的个人智能知识助手</p>
      </div>
      
      <el-alert
        v-if="authStore.error"
        :title="authStore.error"
        type="error"
        show-icon
        :closable="true"
        @close="authStore.error = null"
        style="margin-bottom: 15px;"
      />
      
      <el-form 
        ref="loginForm"
        :model="loginData"
        :rules="rules"
        label-position="top"
        class="login-form"
      >
        <el-form-item label="用户名" prop="username">
          <el-input 
            v-model="loginData.username"
            prefix-icon="User"
            placeholder="请输入用户名"
          />
        </el-form-item>
        
        <el-form-item label="密码" prop="password">
          <el-input 
            v-model="loginData.password" 
            prefix-icon="Lock" 
            type="password"
            placeholder="请输入密码"
            show-password
          />
        </el-form-item>
        
        <div class="form-actions">
          <el-checkbox v-model="loginData.remember">记住我</el-checkbox>
        </div>
        
        <el-form-item>
          <el-button 
            type="primary" 
            :loading="loading" 
            @click="handleLogin" 
            class="login-button"
          >
            登录
          </el-button>
        </el-form-item>
      </el-form>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive } from 'vue';
import { useRouter } from 'vue-router';
import { ElMessage } from 'element-plus';
import { User, Lock } from '@element-plus/icons-vue';
import { useAuthStore } from '../stores/auth';

const router = useRouter();
const loading = ref(false);
const loginForm = ref(null);
const authStore = useAuthStore();

const loginData = reactive({
  username: '',
  password: '',
  remember: false
});

const rules = {
  username: [
    { required: true, message: '请输入用户名', trigger: 'blur' }
  ],
  password: [
    { required: true, message: '请输入密码', trigger: 'blur' },
    { min: 6, message: '密码长度至少为6个字符', trigger: 'blur' }
  ]
};

const handleLogin = async () => {
  if (!loginForm.value) return;
  
  await loginForm.value.validate(async (valid) => {
    if (!valid) return;
    
    loading.value = true;
    
    try {
      const success = await authStore.login({
        username: loginData.username,
        password: loginData.password,
        remember: loginData.remember
      });
      
      if (success) {
        ElMessage.success('登录成功');
        router.push('/');
      }
    } finally {
      loading.value = false;
    }
  });
};
</script>

<style scoped>
.login-container {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 100vh;
  width: 100%;
  padding: 0;
  margin: 0;
  box-sizing: border-box;
  background-color: #f5f7fa;
}

.login-box {
  width: 400px;
  padding: 40px;
  background-color: #fff;
  border-radius: 8px;
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.1);
  position: relative;
  left: 0;
}

.logo {
  text-align: center;
  margin-bottom: 30px;
}

.logo h1 {
  margin: 0;
  color: #409eff;
  font-size: 28px;
}

.logo p {
  margin-top: 8px;
  color: #909399;
}

.login-form {
  margin-top: 20px;
}

.form-actions {
  display: flex;
  justify-content: space-between;
  margin-bottom: 16px;
}

.login-button {
  width: 100%;
}
</style>
