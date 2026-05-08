import apiClient from "./client";

export async function listKnowledgeBases() {
  return apiClient.get("/knowledge-bases");
}

export async function createKnowledgeBase(data: {
  name: string;
  description?: string;
  embedding_model?: string;
}) {
  return apiClient.post("/knowledge-bases", data);
}

export async function getKnowledgeBase(id: string) {
  return apiClient.get(`/knowledge-bases/${id}`);
}

export async function updateKnowledgeBase(
  id: string,
  data: { name?: string; description?: string }
) {
  return apiClient.put(`/knowledge-bases/${id}`, data);
}

export async function deleteKnowledgeBase(id: string) {
  return apiClient.delete(`/knowledge-bases/${id}`);
}
