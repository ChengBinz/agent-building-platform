<template>
  <div class="chat-view">
    <ChatSidebar
      :currentConvId="chatStore.currentConversation?.id"
      @createAgent="handleCreateAgent"
      @selectAgent="handleSelectAgent"
      @editAgent="openAgentConfig"
      @deleteAgent="handleDeleteAgent"
      @createConv="handleCreateConv"
      @selectConv="handleSelectConv"
      @deleteConv="handleDeleteConv"
    />
    <ChatMain
      :conversation="chatStore.currentConversation"
      :currentAgent="agentStore.currentAgent"
      :messages="msgs"
      :sending="chatStore.sending"
      :providers="configuredProviders"
      v-model="currentModel"
      @createConv="handleCreateConv"
      @editAgent="openAgentConfig"
      @send="handleSend"
      @cancel="chatStore.cancelStream()"
      @modelChange="handleModelChange"
    />
    <AgentDialog
      v-model:visible="showAgentDialog"
      :agent="editingAgent"
      :providers="configuredProviders"
      @save="handleSaveAgent"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from "vue";
import { ElMessageBox } from "element-plus";
import { useChatStore } from "@/stores/chat";
import { useAgentStore } from "@/stores/agent";
import { listLLMModels } from "@/api/models";
import ChatSidebar from "@/components/chat/ChatSidebar.vue";
import ChatMain from "@/components/chat/ChatMain.vue";
import AgentDialog from "@/components/chat/AgentDialog.vue";
import type { Agent, LLMModel } from "@/types";

const chatStore = useChatStore();
const agentStore = useAgentStore();

// Model selector: grouped by factory name, value is `provider:modelName` where
// provider is the lowercase factory alias compatible with chat_service backend.
const llmModels = ref<LLMModel[]>([]);
const currentModel = ref("");

// Factory name → lowercase provider alias (must stay in sync with backend
// _FACTORY_ALIASES in chat_service.py).
const FACTORY_TO_PROVIDER: Record<string, string> = {
  OpenAI: "openai",
  "OpenAI-API-Compatible": "openai",
  Anthropic: "anthropic",
  DeepSeek: "deepseek",
  "Tongyi-Qianwen": "dashscope",
  "ZHIPU-AI": "zhipu",
  Moonshot: "moonshot",
  xAI: "xai",
  Gemini: "gemini",
  Mistral: "mistral",
  "Azure-OpenAI": "azure",
  Ollama: "ollama",
  VLLM: "vllm",
  SILICONFLOW: "siliconflow",
  GiteeAI: "gitee",
  Groq: "groq",
  OpenRouter: "openrouter",
  "Tencent-Hunyuan": "hunyuan",
  MiniMax: "minimax",
  BaiChuan: "baichuan",
};

function factoryToProvider(factory: string): string {
  return FACTORY_TO_PROVIDER[factory] || factory.toLowerCase();
}

interface ProviderGroup {
  name: string;
  key: string;
  models: { name: string; provider: string }[];
}

const configuredProviders = computed<ProviderGroup[]>(() => {
  // Group chat models by factory
  const map = new Map<string, ProviderGroup>();
  for (const m of llmModels.value) {
    if (m.model_type !== "chat") continue;
    if (!m.is_active) continue;
    const providerKey = factoryToProvider(m.factory);
    if (!map.has(m.factory)) {
      map.set(m.factory, { name: m.factory, key: providerKey, models: [] });
    }
    map.get(m.factory)!.models.push({ name: m.model_name, provider: providerKey });
  }
  return [...map.values()];
});

const msgs = computed(() => chatStore.currentConversation?.messages || []);

const showAgentDialog = ref(false);
const editingAgent = ref<Agent | null>(null);

onMounted(async () => {
  agentStore.fetchAgents();
  try {
    const { data } = await listLLMModels();
    llmModels.value = data;
  } catch {
    // ignore
  }
});

// === Agent actions ===
function handleCreateAgent() {
  editingAgent.value = null;
  showAgentDialog.value = true;
}

function openAgentConfig(agent: Agent) {
  editingAgent.value = agent;
  showAgentDialog.value = true;
}

async function handleSaveAgent(data: any) {
  if (editingAgent.value) {
    await agentStore.updateAgent(editingAgent.value.id, data);
  } else {
    const agent = await agentStore.createAgent(data);
    if (agent) await agentStore.selectAgent(agent.id);
  }
  showAgentDialog.value = false;
}

async function handleSelectAgent(id: string) {
  chatStore.currentConversation = null;
  await agentStore.selectAgent(id);
}

async function handleDeleteAgent(id: string) {
  try {
    await ElMessageBox.confirm("确定删除该智能体及其所有对话？", "提示", {
      confirmButtonText: "确定",
      cancelButtonText: "取消",
      type: "warning",
    });
    await agentStore.deleteAgent(id);
    if (agentStore.currentAgent?.id !== id) chatStore.currentConversation = null;
  } catch { /* cancelled */ }
}

// === Conversation actions ===
async function handleCreateConv() {
  const conv = await agentStore.createConversation();
  if (conv) chatStore.currentConversation = conv;
}

function handleSelectConv(id: string) {
  chatStore.selectConversation(id);
}

async function handleDeleteConv(id: string) {
  try {
    await ElMessageBox.confirm("确定删除该对话？", "提示", {
      confirmButtonText: "确定",
      cancelButtonText: "取消",
      type: "warning",
    });
    await chatStore.deleteConversation(id);
    agentStore.conversations = agentStore.conversations.filter((c) => c.id !== id);
  } catch { /* cancelled */ }
}

async function handleModelChange(value: string) {
  if (!value || !chatStore.currentConversation) return;
  const [provider, modelName] = value.split(":");
  await chatStore.updateConversation(chatStore.currentConversation.id, { model_name: modelName, provider });
}

async function handleSend(text: string, enableSearch: boolean = false) {
  await chatStore.sendMessage(text, enableSearch);
}
</script>

<style scoped>
.chat-view {
  display: flex;
  height: calc(100vh - 100px);
  background: #fff;
  border-radius: 8px;
  overflow: hidden;
}
</style>
