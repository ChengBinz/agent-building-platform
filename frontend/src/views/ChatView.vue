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
import { listModels } from "@/api/models";
import ChatSidebar from "@/components/chat/ChatSidebar.vue";
import ChatMain from "@/components/chat/ChatMain.vue";
import AgentDialog from "@/components/chat/AgentDialog.vue";
import type { Agent, ProviderInfo, ProviderWithKey } from "@/types";

const chatStore = useChatStore();
const agentStore = useAgentStore();

const providers = ref<ProviderInfo[]>([]);
const currentModel = ref("");

const configuredProviders = computed<ProviderWithKey[]>(() => {
  const result: ProviderWithKey[] = [];
  for (const p of providers.value) {
    if (p.configured) {
      const key = p.models[0]?.provider || "";
      result.push({ ...p, key });
    }
  }
  return result;
});

const msgs = computed(() => chatStore.currentConversation?.messages || []);

const showAgentDialog = ref(false);
const editingAgent = ref<Agent | null>(null);

onMounted(async () => {
  agentStore.fetchAgents();
  try {
    const { data } = await listModels();
    providers.value = data;
  } catch { /* ignore */ }
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

async function handleSend(text: string) {
  await chatStore.sendMessage(text);
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
