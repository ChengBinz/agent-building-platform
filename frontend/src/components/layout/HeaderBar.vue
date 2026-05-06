<template>
  <div class="header-bar">
    <el-button text @click="appStore.toggleSidebar()">
      <el-icon><Fold /></el-icon>
    </el-button>
    <div class="spacer"></div>
    <el-dropdown @command="handleCommand">
      <span class="user-info">
        <el-icon><UserFilled /></el-icon>
        <span>{{ auth.user?.display_name || auth.user?.username || '用户' }}</span>
      </span>
      <template #dropdown>
        <el-dropdown-menu>
          <el-dropdown-item>个人信息</el-dropdown-item>
          <el-dropdown-item command="logout" divided>退出登录</el-dropdown-item>
        </el-dropdown-menu>
      </template>
    </el-dropdown>
  </div>
</template>

<script setup lang="ts">
import { useRouter } from "vue-router";
import { useAppStore } from "@/stores/app";
import { useAuthStore } from "@/stores/auth";
import { Fold, UserFilled } from "@element-plus/icons-vue";

const router = useRouter();
const appStore = useAppStore();
const auth = useAuthStore();

function handleCommand(cmd: string) {
  if (cmd === "logout") {
    auth.logout();
    router.push("/login");
  }
}
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
