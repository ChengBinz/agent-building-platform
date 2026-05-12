import apiClient from "./client";

export function listSystemSkills() {
  return apiClient.get("/skills/system");
}

export function listUserSkills() {
  return apiClient.get("/skills/user");
}

export function createSkill(data: {
  name: string;
  description?: string;
  skill_type?: string;
  content?: string;
  version?: string;
}) {
  return apiClient.post("/skills", data);
}

export function updateSkill(
  id: string,
  data: {
    name?: string;
    description?: string;
    skill_type?: string;
    content?: string;
    version?: string;
    is_active?: boolean;
  }
) {
  return apiClient.put(`/skills/${id}`, data);
}

export function deleteSkill(id: string) {
  return apiClient.delete(`/skills/${id}`);
}

export function toggleSkill(id: string, is_active: boolean) {
  return apiClient.put(`/skills/${id}/toggle`, { is_active });
}
