<template>
  <div class="header">
    <div class="left">
      <h2 class="title">知识库</h2>
    </div>
    <div class="right">
      <el-input
        placeholder="搜索..."
        prefix-icon="Search"
        v-model="searchQuery"
        clearable
        @keyup.enter="handleSearch"
        class="search-input"
      />
      <el-dropdown trigger="click">
        <div class="user-info">
          <el-avatar 
            :size="32" 
            v-if="authStore.isAuthenticated && authStore.user?.avatar"
            :src="authStore.user.avatar"
          />
          <el-avatar 
            :size="32" 
            v-else-if="authStore.isAuthenticated"
            :style="{ 
              backgroundColor: getAvatarColor(authStore.username),
              color: '#ffffff'
            }"
          >
            {{ getInitials(authStore.username) }}
          </el-avatar>
          <el-avatar 
            :size="32" 
            :icon="User" 
            v-else
            style="background-color: #c0c4cc;"
          />
          <span class="username">{{ authStore.username || '用户' }}</span>
        </div>
        <template #dropdown>
          <el-dropdown-menu>
            <el-dropdown-item @click="goToProfile">个人设置</el-dropdown-item>
            <el-dropdown-item divided @click="handleLogout">退出登录</el-dropdown-item>
          </el-dropdown-menu>
        </template>
      </el-dropdown>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue';
import { Search, User } from '@element-plus/icons-vue';
import { useRouter } from 'vue-router';
import { ElMessageBox, ElMessage } from 'element-plus';
import { useAuthStore } from '@/stores/auth';

const router = useRouter();
const authStore = useAuthStore();
const searchQuery = ref('');

// 处理搜索
const handleSearch = () => {
  if (searchQuery.value.trim()) {
    router.push({
      path: '/knowledge',
      query: { q: searchQuery.value }
    });
    searchQuery.value = '';
  }
};

// 导航到个人设置页面
const goToProfile = () => {
  router.push('/profile');
};

// 处理登出
const handleLogout = async () => {
  try {
    await ElMessageBox.confirm('确定要退出登录吗?', '提示', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    });
    
    await authStore.logout();
    ElMessage.success('已成功退出登录');
    router.push('/login');
  } catch (e) {
    // 用户取消操作
  }
};

const getInitials = (name) => {
  if (!name) return '';
  return name.charAt(0).toUpperCase();
};

const getAvatarColor = (name) => {
  // 根据用户名生成一致的颜色
  const colors = [
    '#409EFF', // 蓝色
    '#67C23A', // 绿色
    '#E6A23C', // 橙色
    '#F56C6C', // 红色
    '#909399', // 灰色
    '#6B77E5', // 紫色
    '#31CCEC', // 青色
  ];
  
  if (!name) return colors[0];
  
  // 根据用户名字符计算颜色索引
  let sum = 0;
  for (let i = 0; i < name.length; i++) {
    sum += name.charCodeAt(i);
  }
  
  return colors[sum % colors.length];
};
</script>

<style scoped>
.header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  width: 100%;
  height: 100%;
}

.left {
  display: flex;
  align-items: center;
}

.title {
  margin: 0;
  font-size: 20px;
  color: #409eff;
}

.right {
  display: flex;
  align-items: center;
  gap: 20px;
}

.search-input {
  width: 220px;
}

.user-info {
  display: flex;
  align-items: center;
  cursor: pointer;
  padding: 2px 4px;
  border-radius: 4px;
  transition: background-color 0.3s;
}

.user-info:hover {
  background-color: #f5f7fa;
}

.username {
  margin-left: 8px;
  font-size: 14px;
  color: #606266;
}

/* 可以添加一个头像过渡效果 */
.el-avatar {
  transition: background-color 0.3s ease;
}

/* 或者使用更明显的有颜色头像样式 */
.user-info .el-avatar {
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}
</style>
