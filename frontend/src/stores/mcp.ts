import { defineStore } from "pinia";
import { ref } from "vue";
import { ElMessage } from "element-plus";
import * as mcpApi from "@/api/mcp";
import type { MCPServer, MCPTool } from "@/types";

export const useMcpStore = defineStore("mcp", () => {
  const servers = ref<MCPServer[]>([]);
  const tools = ref<MCPTool[]>([]);
  const loading = ref(false);

  async function fetchServers() {
    loading.value = true;
    try {
      const { data } = await mcpApi.listMCPServers();
      servers.value = data;
    } catch (e: any) {
      ElMessage.error(e.response?.data?.detail || "获取 MCP Server 列表失败");
    } finally {
      loading.value = false;
    }
  }

  async function createServer(params: {
    name: string;
    url: string;
    transport?: string;
    auth_type?: string;
    auth_value?: string;
    is_active?: boolean;
  }) {
    try {
      const { data } = await mcpApi.createMCPServer(params);
      servers.value.unshift(data);
      return data as MCPServer;
    } catch (e: any) {
      ElMessage.error(e.response?.data?.detail || "创建 MCP Server 失败");
      return null;
    }
  }

  async function updateServer(id: string, params: {
    name?: string;
    url?: string;
    transport?: string;
    auth_type?: string;
    auth_value?: string;
    is_active?: boolean;
  }) {
    try {
      const { data } = await mcpApi.updateMCPServer(id, params);
      const idx = servers.value.findIndex((s) => s.id === id);
      if (idx !== -1) {
        servers.value[idx] = { ...servers.value[idx], ...data };
      }
      return data as MCPServer;
    } catch (e: any) {
      ElMessage.error(e.response?.data?.detail || "更新 MCP Server 失败");
      return null;
    }
  }

  async function deleteServer(id: string) {
    try {
      await mcpApi.deleteMCPServer(id);
      servers.value = servers.value.filter((s) => s.id !== id);
      ElMessage.success("MCP Server 已删除");
    } catch (e: any) {
      ElMessage.error(e.response?.data?.detail || "删除 MCP Server 失败");
    }
  }

  async function testConnection(id: string) {
    try {
      const { data } = await mcpApi.testMCPServer(id);
      if (data.success) {
        ElMessage.success(data.message || "连接测试成功");
      } else {
        ElMessage.warning(data.message || "连接测试失败");
      }
      return data;
    } catch (e: any) {
      ElMessage.error(e.response?.data?.detail || "连接测试失败");
      return null;
    }
  }

  async function fetchTools(serverId?: string) {
    loading.value = true;
    try {
      const { data } = await mcpApi.listMCPTools(serverId);
      tools.value = data;
    } catch (e: any) {
      ElMessage.error(e.response?.data?.detail || "获取 MCP Tool 列表失败");
    } finally {
      loading.value = false;
    }
  }

  async function toggleTool(id: string, isActive: boolean) {
    try {
      const { data } = await mcpApi.toggleMCPTool(id, isActive);
      const idx = tools.value.findIndex((t) => t.id === id);
      if (idx !== -1) {
        tools.value[idx] = { ...tools.value[idx], ...data };
      }
      ElMessage.success(isActive ? "工具已启用" : "工具已禁用");
      return data as MCPTool;
    } catch (e: any) {
      ElMessage.error(e.response?.data?.detail || "更新工具状态失败");
      return null;
    }
  }

  return {
    servers,
    tools,
    loading,
    fetchServers,
    createServer,
    updateServer,
    deleteServer,
    testConnection,
    fetchTools,
    toggleTool,
  };
});
