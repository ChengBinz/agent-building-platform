<template>
  <div class="side-nav">
    <div class="logo">
      <span v-if="!collapsed">AI Agent Platform</span>
      <span v-else>AI</span>
    </div>
    <el-menu
      :default-active="currentRoute"
      :collapse="collapsed"
      background-color="#1e1e2d"
      text-color="#9899ac"
      active-text-color="#409eff"
      router
    >
      <el-menu-item index="/chat">
        <el-icon><ChatDotRound /></el-icon>
        <span>对话</span>
      </el-menu-item>
      <el-menu-item index="/knowledge">
        <el-icon><Folder /></el-icon>
        <span>知识库</span>
      </el-menu-item>
      <el-menu-item index="/models">
        <el-icon><Setting /></el-icon>
        <span>模型配置</span>
      </el-menu-item>
      <el-menu-item index="/monitoring">
        <el-icon><DataAnalysis /></el-icon>
        <span>监控面板</span>
      </el-menu-item>
      <el-menu-item index="/admin/users">
        <el-icon><UserFilled /></el-icon>
        <span>系统管理</span>
      </el-menu-item>
    </el-menu>
  </div>
</template>

<script setup lang="ts">
import { computed } from "vue";
import { useRoute } from "vue-router";
import { useAppStore } from "@/stores/app";

const route = useRoute();
const appStore = useAppStore();

const collapsed = computed(() => appStore.sidebarCollapsed);
const currentRoute = computed(() => route.path);
</script>

<style scoped>
.side-nav {
  height: 100%;
}
.logo {
  height: 60px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #fff;
  font-size: 16px;
  font-weight: bold;
  border-bottom: 1px solid rgba(255, 255, 255, 0.1);
}
.el-menu {
  border-right: none;
}
</style>
