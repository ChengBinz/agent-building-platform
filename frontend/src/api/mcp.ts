import apiClient from "./client";

export function listMCPServers() {
  return apiClient.get("/mcp/servers");
}

export function createMCPServer(data: {
  name: string;
  url: string;
  transport?: string;
  auth_type?: string;
  auth_value?: string;
  is_active?: boolean;
}) {
  return apiClient.post("/mcp/servers", data);
}

export function updateMCPServer(
  id: string,
  data: {
    name?: string;
    url?: string;
    transport?: string;
    auth_type?: string;
    auth_value?: string;
    is_active?: boolean;
  }
) {
  return apiClient.put(`/mcp/servers/${id}`, data);
}

export function deleteMCPServer(id: string) {
  return apiClient.delete(`/mcp/servers/${id}`);
}

export function testMCPServer(id: string) {
  return apiClient.post(`/mcp/servers/${id}/test`);
}

export function listMCPTools(serverId?: string) {
  const params = serverId ? { server_id: serverId } : {};
  return apiClient.get("/mcp/tools", { params });
}

export function toggleMCPTool(id: string, is_active: boolean) {
  return apiClient.put(`/mcp/tools/${id}/toggle`, { is_active });
}
