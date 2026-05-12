<template>
  <div class="mcp-tool-tab">
    <div class="tab-header">
      <el-input
        v-model="searchText"
        placeholder="搜索 MCP Tool"
        prefix-icon="Search"
        style="width: 300px"
        clearable
      />
      <el-select
        v-model="selectedServer"
        placeholder="筛选 MCP Server"
        clearable
        style="width: 200px"
        @change="handleServerFilter"
      >
        <el-option
          v-for="server in servers"
          :key="server.id"
          :label="server.name"
          :value="server.id"
        />
      </el-select>
    </div>

    <el-table :data="filteredTools" v-loading="loading" stripe style="width: 100%">
      <el-table-column prop="name" label="工具名称" min-width="150" />
      <el-table-column prop="description" label="描述" min-width="250" show-overflow-tooltip />
      <el-table-column prop="server_name" label="归属服务" width="150">
        <template #default="{ row }">
          <el-tag type="info" size="small">{{ row.server_name }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="is_active" label="状态" width="100" align="center">
        <template #default="{ row }">
          <el-switch
            v-model="row.is_active"
            @change="handleToggleActive(row)"
            size="small"
          />
        </template>
      </el-table-column>
      <el-table-column label="操作" width="100" align="center">
        <template #default="{ row }">
          <el-button type="primary" link size="small" @click="showDetail(row)">
            详情
          </el-button>
        </template>
      </el-table-column>
    </el-table>

    <!-- 工具详情对话框 -->
    <el-dialog
      v-model="detailVisible"
      :title="selectedTool?.name || '工具详情'"
      width="600px"
      destroy-on-close
    >
      <div v-if="selectedTool" class="tool-detail">
        <el-descriptions :column="1" border>
          <el-descriptions-item label="工具名称">{{ selectedTool.name }}</el-descriptions-item>
          <el-descriptions-item label="归属服务">{{ selectedTool.server_name }}</el-descriptions-item>
          <el-descriptions-item label="描述">{{ selectedTool.description || '-' }}</el-descriptions-item>
          <el-descriptions-item label="状态">
            <el-tag :type="selectedTool.is_active ? 'success' : 'danger'" size="small">
              {{ selectedTool.is_active ? '启用' : '禁用' }}
            </el-tag>
          </el-descriptions-item>
        </el-descriptions>
        <div v-if="selectedTool.input_schema" class="schema-section">
          <h4>输入参数 Schema</h4>
          <pre class="schema-code">{{ JSON.stringify(selectedTool.input_schema, null, 2) }}</pre>
        </div>
      </div>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from "vue";
import { useMcpStore } from "@/stores/mcp";
import type { MCPTool } from "@/types";

const mcpStore = useMcpStore();
const loading = computed(() => mcpStore.loading);
const tools = computed(() => mcpStore.tools);
const servers = computed(() => mcpStore.servers);

const searchText = ref("");
const selectedServer = ref("");
const detailVisible = ref(false);
const selectedTool = ref<MCPTool | null>(null);

const filteredTools = computed(() => {
  let result = tools.value;
  if (searchText.value) {
    const keyword = searchText.value.toLowerCase();
    result = result.filter(
      (t) =>
        t.name.toLowerCase().includes(keyword) ||
        (t.description && t.description.toLowerCase().includes(keyword))
    );
  }
  return result;
});

onMounted(() => {
  mcpStore.fetchTools();
  mcpStore.fetchServers();
});

function handleServerFilter() {
  mcpStore.fetchTools(selectedServer.value || undefined);
}

async function handleToggleActive(tool: MCPTool) {
  await mcpStore.toggleTool(tool.id, tool.is_active);
}

function showDetail(tool: MCPTool) {
  selectedTool.value = tool;
  detailVisible.value = true;
}
</script>

<style scoped>
.mcp-tool-tab {
  padding: 16px 0;
}

.tab-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}

.tool-detail {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.schema-section h4 {
  margin: 0 0 8px 0;
  font-size: 14px;
  color: #303133;
}

.schema-code {
  background: #f5f7fa;
  padding: 12px;
  border-radius: 6px;
  font-size: 13px;
  overflow-x: auto;
  margin: 0;
}
</style>
