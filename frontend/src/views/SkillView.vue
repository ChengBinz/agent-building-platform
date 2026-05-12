<template>
  <div class="skill-view">
    <div class="page-header">
      <h2>技能管理</h2>
      <p class="page-desc">管理系统内置技能和用户自定义技能</p>
    </div>
    <el-tabs v-model="activeTab" class="skill-tabs">
      <el-tab-pane label="系统内置" name="system">
        <SystemSkillTab />
      </el-tab-pane>
      <el-tab-pane label="自定义技能" name="user">
        <UserSkillTab />
      </el-tab-pane>
    </el-tabs>
  </div>
</template>

<script setup lang="ts">
import { ref } from "vue";
import SystemSkillTab from "@/components/skill/SystemSkillTab.vue";
import UserSkillTab from "@/components/skill/UserSkillTab.vue";

const activeTab = ref("system");
</script>

<style scoped>
.skill-view {
  padding: 20px;
  height: 100%;
  display: flex;
  flex-direction: column;
}

.page-header {
  margin-bottom: 20px;
}

.page-header h2 {
  margin: 0 0 8px 0;
  font-size: 20px;
  color: #303133;
}

.page-desc {
  margin: 0;
  font-size: 14px;
  color: #909399;
}

.skill-tabs {
  flex: 1;
  display: flex;
  flex-direction: column;
}

.skill-tabs :deep(.el-tabs__content) {
  flex: 1;
  overflow: auto;
}
</style>
