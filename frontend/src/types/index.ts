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

export interface Conversation {
  id: string;
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
