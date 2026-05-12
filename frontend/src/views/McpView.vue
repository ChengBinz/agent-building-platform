<template>
  <div class="mcp-view">
    <div class="page-header">
      <h2>MCP 管理</h2>
      <p class="page-desc">管理 MCP Server 连接配置和 MCP Tool 工具列表</p>
    </div>
    <el-tabs v-model="activeTab" class="mcp-tabs">
      <el-tab-pane label="MCP Server" name="server">
        <McpServerTab />
      </el-tab-pane>
      <el-tab-pane label="MCP Tool" name="tool">
        <McpToolTab />
      </el-tab-pane>
    </el-tabs>
  </div>
</template>

<script setup lang="ts">
import { ref } from "vue";
import McpServerTab from "@/components/mcp/McpServerTab.vue";
import McpToolTab from "@/components/mcp/McpToolTab.vue";

const activeTab = ref("server");
</script>

<style scoped>
.mcp-view {
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

.mcp-tabs {
  flex: 1;
  display: flex;
  flex-direction: column;
}

.mcp-tabs :deep(.el-tabs__content) {
  flex: 1;
  overflow: auto;
}
</style>
