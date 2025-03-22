<template>
  <router-view />
</template>

<script setup>
import { onMounted } from 'vue';
import { useAuthStore } from '@/stores/auth';
import { useRouter } from 'vue-router';

const authStore = useAuthStore();
const router = useRouter();

// 在应用启动时执行身份验证检查
onMounted(async () => {
  // 如果localStorage中有token，则验证其有效性
  if (localStorage.getItem('token')) {
    try {
      // 调用checkAuth验证token
      const isValid = await authStore.checkAuth();
      
      console.log('Token验证结果:', isValid);
      
      // 如果token无效，并且不在登录页，则重定向到登录页
      if (!isValid && router.currentRoute.value.path !== '/login') {
        router.push('/login');
      }
    } catch (error) {
      console.error('验证token时出错:', error);
      // 出错时也清除token并重定向
      authStore.clearAuth();
      if (router.currentRoute.value.path !== '/login') {
        router.push('/login');
      }
    }
  }
});
</script>

<style>
* {
  box-sizing: border-box;
}

body, html {
  margin: 0;
  padding: 0;
  height: 100%;
  width: 100%;
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, 'Open Sans', 'Helvetica Neue', sans-serif;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
  background-color: #f5f7fa;
}

#app {
  width: 100%;
  height: 100%;
  margin: 0;
  padding: 0;
  font-weight: normal;
}

a {
  text-decoration: none;
  color: #409EFF;
  transition: 0.3s;
}

a:hover {
  color: #66b1ff;
}
</style>
