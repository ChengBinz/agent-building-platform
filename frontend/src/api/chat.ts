import apiClient from "./client";

export async function listConversations() {
  return apiClient.get("/conversations");
}

export async function createConversation(data: {
  title?: string;
  model_name?: string;
  system_prompt?: string;
}) {
  return apiClient.post("/conversations", data);
}

export async function getConversation(id: string) {
  return apiClient.get(`/conversations/${id}`);
}

export async function deleteConversation(id: string) {
  return apiClient.delete(`/conversations/${id}`);
}

export async function sendMessage(conversationId: string, content: string) {
  return apiClient.post(`/conversations/${conversationId}/send`, { content });
}
