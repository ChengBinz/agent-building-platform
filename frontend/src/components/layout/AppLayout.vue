<template>
  <div class="app-layout">
    <el-container>
      <el-aside :width="sidebarCollapsed ? '64px' : '220px'">
        <SideNav />
      </el-aside>
      <el-container>
        <el-header>
          <HeaderBar />
        </el-header>
        <el-main>
          <router-view />
        </el-main>
      </el-container>
    </el-container>
  </div>
</template>

<script setup lang="ts">
import { computed } from "vue";
import { useAppStore } from "@/stores/app";
import SideNav from "./SideNav.vue";
import HeaderBar from "./HeaderBar.vue";

const appStore = useAppStore();
const sidebarCollapsed = computed(() => appStore.sidebarCollapsed);
</script>

<style scoped>
.app-layout {
  height: 100vh;
}
.el-container {
  height: 100%;
}
.el-aside {
  background-color: #1e1e2d;
  transition: width 0.3s;
  overflow: hidden;
}
.el-header {
  border-bottom: 1px solid #e4e7ed;
  padding: 0 16px;
  display: flex;
  align-items: center;
}
.el-main {
  background-color: #f5f7fa;
  padding: 16px;
}
</style>
