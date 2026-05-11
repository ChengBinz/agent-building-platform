import apiClient from "./client";

export async function listKnowledgeBases() {
  return apiClient.get("/knowledge-bases");
}

export async function createKnowledgeBase(data: {
  name: string;
  description?: string;
  embedding_model?: string;
  embedding_api_key?: string;
  embedding_base_url?: string;
}) {
  return apiClient.post("/knowledge-bases", data);
}

export async function getKnowledgeBase(id: string) {
  return apiClient.get(`/knowledge-bases/${id}`);
}

export async function updateKnowledgeBase(
  id: string,
  data: {
    name?: string;
    description?: string;
    embedding_model?: string;
    embedding_api_key?: string;
    embedding_base_url?: string;
  }
) {
  return apiClient.put(`/knowledge-bases/${id}`, data);
}

export async function deleteKnowledgeBase(id: string) {
  return apiClient.delete(`/knowledge-bases/${id}`);
}

export async function uploadDocument(kbId: string, file: File) {
  const formData = new FormData();
  formData.append("file", file);
  return apiClient.post(`/knowledge-bases/${kbId}/documents`, formData, {
    headers: { "Content-Type": "multipart/form-data" },
  });
}

export async function listDocuments(kbId: string) {
  return apiClient.get(`/knowledge-bases/${kbId}/documents`);
}

export async function deleteDocument(kbId: string, documentId: string) {
  return apiClient.delete(`/knowledge-bases/${kbId}/documents/${documentId}`);
}
