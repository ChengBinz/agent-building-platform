import apiClient from "./client";

export async function listUsers(page = 1, pageSize = 20) {
  return apiClient.get("/admin/users", { params: { page, page_size: pageSize } });
}

export async function getUser(id: string) {
  return apiClient.get(`/admin/users/${id}`);
}

export async function updateUserStatus(
  id: string,
  data: { is_active?: boolean; is_superuser?: boolean }
) {
  return apiClient.put(`/admin/users/${id}/status`, null, { params: data });
}

export async function deleteUser(id: string) {
  return apiClient.delete(`/admin/users/${id}`);
}

export async function getSystemStats() {
  return apiClient.get("/admin/stats");
}

export async function getModels() {
  return apiClient.get("/models");
}

export async function getUsageSummary() {
  return apiClient.get("/monitoring/usage");
}

export async function getUsageByModel() {
  return apiClient.get("/monitoring/usage-by-model");
}

export async function listApiKeys() {
  return apiClient.get("/auth/api-keys");
}

export async function saveApiKey(data: { provider: string; api_key: string; base_url?: string }) {
  return apiClient.post("/auth/api-keys", data);
}

export async function deleteApiKey(id: string) {
  return apiClient.delete(`/auth/api-keys/${id}`);
}
