import apiClient from "./client";

export async function listModels() {
  return apiClient.get("/models");
}
