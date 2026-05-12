<template>
  <div class="mcp-server-tab">
    <div class="tab-header">
      <el-input
        v-model="searchText"
        placeholder="搜索 MCP Server"
        prefix-icon="Search"
        style="width: 300px"
        clearable
      />
      <el-button type="primary" @click="openDialog()">
        <el-icon><Plus /></el-icon>
        新增 MCP Server
      </el-button>
    </div>

    <el-table :data="filteredServers" v-loading="loading" stripe style="width: 100%">
      <el-table-column prop="name" label="服务名称" min-width="150" />
      <el-table-column prop="url" label="连接地址" min-width="250" show-overflow-tooltip />
      <el-table-column prop="transport" label="传输协议" width="100">
        <template #default="{ row }">
          <el-tag size="small">{{ row.transport }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="auth_type" label="认证类型" width="100">
        <template #default="{ row }">
          <el-tag :type="row.auth_type === 'none' ? 'info' : 'warning'" size="small">
            {{ row.auth_type }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="tool_count" label="工具数" width="80" align="center" />
      <el-table-column prop="is_active" label="状态" width="80" align="center">
        <template #default="{ row }">
          <el-switch
            v-model="row.is_active"
            @change="handleToggleActive(row)"
            size="small"
          />
        </template>
      </el-table-column>
      <el-table-column label="操作" width="200" align="center">
        <template #default="{ row }">
          <el-button type="primary" link size="small" @click="handleTest(row)">
            测试连接
          </el-button>
          <el-button type="primary" link size="small" @click="openDialog(row)">
            编辑
          </el-button>
          <el-popconfirm title="确定删除该 MCP Server？" @confirm="handleDelete(row)">
            <template #reference>
              <el-button type="danger" link size="small">删除</el-button>
            </template>
          </el-popconfirm>
        </template>
      </el-table-column>
    </el-table>

    <!-- 新增/编辑对话框 -->
    <el-dialog
      v-model="dialogVisible"
      :title="editingServer ? '编辑 MCP Server' : '新增 MCP Server'"
      width="500px"
      destroy-on-close
    >
      <el-form :model="form" label-width="100px">
        <el-form-item label="服务名称" required>
          <el-input v-model="form.name" placeholder="输入服务名称" />
        </el-form-item>
        <el-form-item label="连接地址" required>
          <el-input v-model="form.url" placeholder="输入 MCP Server URL" />
        </el-form-item>
        <el-form-item label="传输协议">
          <el-select v-model="form.transport" style="width: 100%">
            <el-option label="SSE" value="sse" />
            <el-option label="STDIO" value="stdio" />
          </el-select>
        </el-form-item>
        <el-form-item label="认证类型">
          <el-select v-model="form.auth_type" style="width: 100%">
            <el-option label="无认证" value="none" />
            <el-option label="Token" value="token" />
            <el-option label="Header" value="header" />
          </el-select>
        </el-form-item>
        <el-form-item v-if="form.auth_type !== 'none'" label="认证凭据">
          <el-input
            v-model="form.auth_value"
            :placeholder="form.auth_type === 'token' ? '输入 Token' : '输入 Header 值'"
            type="password"
            show-password
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handleSave" :loading="saving">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from "vue";
import { Plus } from "@element-plus/icons-vue";
import { useMcpStore } from "@/stores/mcp";
import type { MCPServer } from "@/types";

const mcpStore = useMcpStore();
const loading = computed(() => mcpStore.loading);
const servers = computed(() => mcpStore.servers);

const searchText = ref("");
const dialogVisible = ref(false);
const editingServer = ref<MCPServer | null>(null);
const saving = ref(false);

const form = ref({
  name: "",
  url: "",
  transport: "sse",
  auth_type: "none",
  auth_value: "",
});

const filteredServers = computed(() => {
  if (!searchText.value) return servers.value;
  const keyword = searchText.value.toLowerCase();
  return servers.value.filter(
    (s) =>
      s.name.toLowerCase().includes(keyword) ||
      s.url.toLowerCase().includes(keyword)
  );
});

onMounted(() => {
  mcpStore.fetchServers();
});

function openDialog(server?: MCPServer) {
  editingServer.value = server || null;
  if (server) {
    form.value = {
      name: server.name,
      url: server.url,
      transport: server.transport,
      auth_type: server.auth_type,
      auth_value: server.auth_value || "",
    };
  } else {
    form.value = {
      name: "",
      url: "",
      transport: "sse",
      auth_type: "none",
      auth_value: "",
    };
  }
  dialogVisible.value = true;
}

async function handleSave() {
  if (!form.value.name || !form.value.url) {
    return;
  }
  saving.value = true;
  try {
    if (editingServer.value) {
      await mcpStore.updateServer(editingServer.value.id, form.value);
    } else {
      await mcpStore.createServer(form.value);
    }
    dialogVisible.value = false;
  } finally {
    saving.value = false;
  }
}

async function handleDelete(server: MCPServer) {
  await mcpStore.deleteServer(server.id);
}

async function handleTest(server: MCPServer) {
  await mcpStore.testConnection(server.id);
}

async function handleToggleActive(server: MCPServer) {
  await mcpStore.updateServer(server.id, { is_active: server.is_active });
}
</script>

<style scoped>
.mcp-server-tab {
  padding: 16px 0;
}

.tab-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}
</style>
