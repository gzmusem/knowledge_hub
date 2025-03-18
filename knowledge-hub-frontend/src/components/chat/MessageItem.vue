<template>
    <div class="message" :class="`message-${message.role}`">
      <div class="avatar">
        <el-avatar 
          :icon="message.role === 'user' ? UserFilled : Service" 
          :size="36"
          :style="{ backgroundColor: message.role === 'user' ? '#007bff' : '#6f42c1' }"
        />
      </div>
      <div class="content">
        <div class="role">{{ message.role === 'user' ? '您' : 'AI助手' }}</div>
        <div class="text" v-html="formattedContent"></div>
      </div>
    </div>
  </template>
  
  <script setup>
  import { computed } from 'vue';
  import { UserFilled, Service } from '@element-plus/icons-vue';
  import MarkdownIt from 'markdown-it';
  import hljs from 'highlight.js';
  import 'highlight.js/styles/github.css';
  
  const props = defineProps({
    message: {
      type: Object,
      required: true
    }
  });
  
  const md = new MarkdownIt({
    highlight: function (str, lang) {
      if (lang && hljs.getLanguage(lang)) {
        try {
          return hljs.highlight(str, { language: lang }).value;
        } catch (__) {}
      }
      return '';
    }
  });
  
  const formattedContent = computed(() => {
    return md.render(props.message.content);
  });
  </script>
  
  <style scoped>
  .message {
    display: flex;
    margin-bottom: 16px;
  }
  
  .message-user {
    flex-direction: row-reverse;
  }
  
  .avatar {
    margin: 0 10px;
  }
  
  .content {
    max-width: 80%;
    padding: 12px 16px;
    border-radius: 8px;
  }
  
  .message-user .content {
    background-color: #e7f3ff;
    border-radius: 8px 0 8px 8px;
  }
  
  .message-assistant .content {
    background-color: #f5f5f5;
    border-radius: 0 8px 8px 8px;
  }
  
  .role {
    font-weight: bold;
    margin-bottom: 4px;
    color: #6c757d;
    font-size: 12px;
  }
  
  .text {
    word-break: break-word;
  }
  
  .text :deep(pre) {
    background-color: #f8f9fa;
    padding: 10px;
    border-radius: 4px;
    overflow-x: auto;
  }
  </style>