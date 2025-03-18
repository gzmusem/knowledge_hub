<template>
    <div class="main-layout">
      <el-container>
        <el-aside width="260px">
          <sidebar />
        </el-aside>
        <el-container>
          <el-header height="60px">
            <header-component />
          </el-header>
          <el-main>
            <router-view />
          </el-main>
        </el-container>
      </el-container>
    </div>
  </template>
  
  <script setup>
  import Sidebar from './Sidebar.vue';
  import HeaderComponent from './Header.vue';
  </script>
  
  <style scoped>
  .main-layout {
    height: 100vh;
  }
  .el-aside {
    background-color: #f8f9fa;
    border-right: 1px solid #e9ecef;
  }
  .el-header {
    background-color: #fff;
    border-bottom: 1px solid #e9ecef;
    display: flex;
    align-items: center;
    padding: 0 20px;
  }
  .el-main {
    padding: 20px;
    background-color: #f8f9fa;
  }
  </style>