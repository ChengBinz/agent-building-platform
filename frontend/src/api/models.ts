import apiClient from "./client";
import type {
  FactoryInfo,
  LLMModel,
  LLMModelCreate,
  LLMModelUpdate,
  DefaultModel,
} from "@/types";

// ── Factory catalog ──

export async function listFactories() {
  return apiClient.get<FactoryInfo[]>("/llm/factories");
}

// ── User-added models ──

export async function listLLMModels(model_type?: string) {
  return apiClient.get<LLMModel[]>("/llm/models", {
    params: model_type ? { model_type } : undefined,
  });
}

export async function addLLMModel(data: LLMModelCreate) {
  return apiClient.post<LLMModel>("/llm/models", data);
}

export async function updateLLMModel(id: string, data: LLMModelUpdate) {
  return apiClient.put<LLMModel>(`/llm/models/${id}`, data);
}

export async function deleteLLMModel(id: string) {
  return apiClient.delete(`/llm/models/${id}`);
}

// ── Defaults ──

export async function getDefaultModels() {
  return apiClient.get<DefaultModel[]>("/llm/defaults");
}

export async function setDefaultModel(model_type: string, llm_model_id: string) {
  return apiClient.post("/llm/defaults", { model_type, llm_model_id });
}


// ── Fetch available models from provider ──

export async function fetchAvailableModels(api_key: string, base_url: string) {
  return apiClient.post<{ models: string[] }>("/llm/fetch-models", { api_key, base_url });
}

// ── Test model connectivity ──

export async function testModelConnection(api_key: string, base_url: string, model_name: string, model_type: string = "chat") {
  return apiClient.post<{ success: boolean; message: string; reply?: string }>("/llm/test-model", {
    api_key,
    base_url,
    model_name,
    model_type,
  });
}
