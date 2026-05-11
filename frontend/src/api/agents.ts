import apiClient from "./client";

export function listAgents() {
  return apiClient.get("/agents");
}

export function createAgent(data: {
  name?: string;
  description?: string;
  avatar?: string;
  system_prompt?: string;
  model_name?: string;
  provider?: string;
  tools?: string[];
  kb_ids?: string[];
}) {
  return apiClient.post("/agents", data);
}

export function getAgent(id: string) {
  return apiClient.get(`/agents/${id}`);
}

export function updateAgent(
  id: string,
  data: {
    name?: string;
    description?: string;
    avatar?: string;
    system_prompt?: string;
    model_name?: string;
    provider?: string;
    tools?: string[];
    kb_ids?: string[];
  }
) {
  return apiClient.patch(`/agents/${id}`, data);
}

export function deleteAgent(id: string) {
  return apiClient.delete(`/agents/${id}`);
}
