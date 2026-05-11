// Shared TypeScript type definitions

export interface User {
  id: string;
  username: string;
  email: string;
  display_name?: string;
  is_active: boolean;
  is_superuser: boolean;
  created_at?: string;
  updated_at?: string;
}

export interface Agent {
  id: string;
  user_id: string;
  name: string;
  description?: string;
  avatar?: string;
  system_prompt?: string;
  model_name: string;
  provider: string;
  tools?: string[];
  kb_ids?: string[];
  conversation_count?: number;
  created_at: string;
  updated_at: string;
}

export interface AgentCreate {
  name?: string;
  description?: string;
  avatar?: string;
  system_prompt?: string;
  model_name?: string;
  provider?: string;
  tools?: string[];
  kb_ids?: string[];
}

export interface AgentUpdate {
  name?: string;
  description?: string;
  avatar?: string;
  system_prompt?: string;
  model_name?: string;
  provider?: string;
  tools?: string[];
  kb_ids?: string[];
}

export interface Conversation {
  id: string;
  agent_id?: string;
  title: string;
  model_name: string;
  provider: string;
  message_count: number;
  total_tokens: number;
  created_at: string;
  updated_at: string;
  messages?: Message[];
}

export interface Message {
  id: string;
  conversation_id: string;
  role: "user" | "assistant" | "system" | "tool";
  content: string;
  token_count?: number;
  created_at: string;
}

export interface KnowledgeBase {
  id: string;
  name: string;
  description?: string;
  embedding_model: string;
  embedding_api_key_masked?: string;
  embedding_base_url?: string;
  chunk_count: number;
  document_count: number;
  created_at: string;
  updated_at: string;
  documents?: Document[];
}

export interface Document {
  id: string;
  filename: string;
  file_type: string;
  file_size: number;
  status: string;
  chunk_count: number;
  error_message?: string;
}

export interface ModelConfig {
  name: string;
  provider: string;
  available: boolean;
}

export interface ProviderInfo {
  name: string;
  configured: boolean;
  models: ModelConfig[];
}

// ── New RAGFlow-style model catalog ──

export interface FactoryModelInfo {
  llm_name: string;
  tags?: string;
  max_tokens?: number;
  model_type: string;
  is_tools: boolean;
}

export interface FactoryInfo {
  name: string;
  logo?: string;
  tags: string;
  status: string;
  rank: string;
  url?: string;
  llm: FactoryModelInfo[];
}

export interface LLMModel {
  id: string;
  factory: string;
  model_type: string;
  model_name: string;
  api_key_masked?: string;
  base_url?: string;
  max_tokens?: number;
  is_tools: boolean;
  tags?: string;
  is_active: boolean;
  is_default: boolean;
}

export interface LLMModelCreate {
  factory: string;
  model_name: string;
  model_type: string;
  api_key?: string;
  base_url?: string;
  max_tokens?: number;
  is_tools?: boolean;
  tags?: string;
  extra?: string;
}

export interface LLMModelUpdate {
  model_name?: string;
  api_key?: string;
  base_url?: string;
  max_tokens?: number;
  is_tools?: boolean;
  is_active?: boolean;
  extra?: string;
}

export interface DefaultModel {
  model_type: string;
  llm_model_id: string;
  factory: string;
  model_name: string;
}

export interface UsageSummary {
  total_conversations: number;
  total_messages: number;
  total_tokens: number;
  total_documents: number;
  active_users: number;
}

export interface UsageByModel {
  model_name: string;
  total_tokens: number;
  request_count: number;
}

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  page_size: number;
}

export interface SystemStats {
  user_count: number;
  conversation_count: number;
  knowledge_base_count: number;
  document_count: number;
  total_tokens: number;
}

export interface ApiKeyInfo {
  id: string;
  provider: string;
  api_key_masked: string;
  base_url?: string;
  is_active: boolean;
  created_at: string;
}
