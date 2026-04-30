<template>
  <div class="header-bar">
    <el-button text @click="appStore.toggleSidebar()">
      <el-icon><Fold /></el-icon>
    </el-button>
    <div class="spacer"></div>
    <el-dropdown>
      <span class="user-info">
        <el-icon><UserFilled /></el-icon>
        <span>管理员</span>
      </span>
      <template #dropdown>
        <el-dropdown-menu>
          <el-dropdown-item>个人信息</el-dropdown-item>
          <el-dropdown-item divided>退出登录</el-dropdown-item>
        </el-dropdown-menu>
      </template>
    </el-dropdown>
  </div>
</template>

<script setup lang="ts">
import { useAppStore } from "@/stores/app";

const appStore = useAppStore();
</script>

<style scoped>
.header-bar {
  width: 100%;
  display: flex;
  align-items: center;
}
.spacer {
  flex: 1;
}
.user-info {
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 6px;
}
</style>
