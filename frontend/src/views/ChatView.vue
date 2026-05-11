<template>
  <div class="chat-view">
    <!-- Sidebar: Agents + Conversations -->
    <div class="chat-sidebar">
      <div class="sidebar-header">
        <el-button type="primary" @click="handleCreateAgent" :icon="Plus">
          新建智能体
        </el-button>
      </div>
      <div class="sidebar-body" v-loading="agentStore.loading">
        <!-- Agent list -->
        <div
          v-for="agent in agentStore.agents"
          :key="agent.id"
          class="agent-group"
          :class="{ expanded: agentStore.currentAgent?.id === agent.id }"
        >
          <div
            class="agent-item"
            @click="handleSelectAgent(agent.id)"
          >
            <div class="agent-avatar">
              <el-avatar :size="28" :src="agent.avatar">
                {{ agent.name.charAt(0) }}
              </el-avatar>
            </div>
            <div class="agent-info">
              <div class="agent-name">{{ agent.name }}</div>
              <div class="agent-meta">
                {{ agent.provider ? agent.provider + '/' + agent.model_name : '未配置模型' }}
              </div>
            </div>
            <div class="agent-actions" @click.stop>
              <el-button text size="small" @click="openAgentConfig(agent)">
                <el-icon><Setting /></el-icon>
              </el-button>
              <el-button text size="small" type="danger" @click="handleDeleteAgent(agent.id)">
                <el-icon><Delete /></el-icon>
              </el-button>
            </div>
          </div>
          <!-- Conversations for this agent -->
          <div v-if="agentStore.currentAgent?.id === agent.id" class="conv-sublist">
            <div class="conv-sublist-header">
              <span>对话列表</span>
              <el-button text size="small" type="primary" @click="handleCreateConv">
                <el-icon><Plus /></el-icon>
              </el-button>
            </div>
            <div
              v-for="conv in agentStore.conversations"
              :key="conv.id"
              class="conv-item"
              :class="{ active: chatStore.currentConversation?.id === conv.id }"
              @click="handleSelectConv(conv.id)"
            >
              <div class="conv-title">{{ conv.title }}</div>
              <div class="conv-meta">{{ conv.message_count }} 条消息</div>
              <span class="conv-delete" @click.stop>
                <el-button text type="danger" size="small" @click="handleDeleteConv(conv.id)">
                  <el-icon><Delete /></el-icon>
                </el-button>
              </span>
            </div>
            <el-empty v-if="agentStore.conversations.length === 0" description="暂无对话" :image-size="48" />
          </div>
        </div>
        <el-empty v-if="!agentStore.loading && agentStore.agents.length === 0" description="暂无智能体，点击上方按钮创建" />
      </div>
    </div>

    <!-- Main chat area -->
    <div class="chat-main">
      <div v-if="!chatStore.currentConversation" class="chat-placeholder">
        <div v-if="!agentStore.currentAgent">
          <el-empty description="选择或创建一个智能体开始" />
        </div>
        <div v-else>
          <div class="agent-welcome">
            <el-avatar :size="64" :src="agentStore.currentAgent.avatar">
              {{ agentStore.currentAgent.name.charAt(0) }}
            </el-avatar>
            <h3>{{ agentStore.currentAgent.name }}</h3>
            <p v-if="agentStore.currentAgent.description">{{ agentStore.currentAgent.description }}</p>
            <el-button type="primary" @click="handleCreateConv">开始新对话</el-button>
          </div>
        </div>
      </div>
      <template v-else>
        <div class="chat-header">
          <div class="chat-header-left">
            <span class="chat-header-agent">{{ agentStore.currentAgent?.name || '智能体' }}</span>
            <el-icon><ArrowRight /></el-icon>
            <span class="chat-header-title">{{ chatStore.currentConversation.title }}</span>
          </div>
          <div class="chat-header-right">
            <el-button
              v-if="agentStore.currentAgent"
              text
              size="small"
              @click="openAgentConfig(agentStore.currentAgent)"
            >
              <el-icon><Setting /></el-icon>
              智能体设置
            </el-button>
          </div>
        </div>
        <div class="chat-messages" ref="msgContainer">
          <div
            v-for="(msg, idx) in msgs"
            :key="idx"
            class="message"
            :class="msg.role"
          >
            <div class="message-avatar">
              <el-avatar v-if="msg.role === 'user'" :icon="UserFilled" size="small" />
              <el-avatar v-else :icon="ChatDotRound" size="small" style="background-color: #409eff" />
            </div>
            <div class="message-content">
              <div class="message-role">{{ msg.role === 'user' ? '我' : agentStore.currentAgent?.name || 'AI助手' }}</div>
              <div
                class="message-text"
                :class="{ 'is-streaming': msg.role === 'assistant' && chatStore.sending && idx === (msgs.length - 1) }"
                v-html="renderMarkdown(msg.content)"
              ></div>
            </div>
          </div>
        </div>
        <div class="chat-input">
          <el-input
            v-model="inputText"
            type="textarea"
            :rows="3"
            placeholder="输入消息，Shift+Enter 换行，Enter 发送"
            @keydown.enter.exact.prevent="handleSend"
            :disabled="chatStore.sending"
          />
          <div class="chat-input-actions">
            <div class="model-selector">
              <span class="model-label">模型：</span>
              <el-select
                v-model="currentModel"
                placeholder="选择模型"
                size="small"
                style="width: 260px"
                :disabled="chatStore.sending"
                @change="handleModelChange"
              >
                <el-option-group
                  v-for="p in configuredProviders"
                  :key="p.key"
                  :label="p.name"
                >
                  <el-option
                    v-for="m in p.models"
                    :key="`${p.key}:${m.name}`"
                    :label="`${p.name} - ${m.name}`"
                    :value="`${p.key}:${m.name}`"
                  />
                </el-option-group>
              </el-select>
            </div>
            <div class="actions-right">
              <el-button
                v-if="chatStore.sending"
                @click="chatStore.cancelStream()"
                type="warning"
                plain
                size="small"
              >
                停止生成
              </el-button>
              <el-button
                type="primary"
                :icon="Promotion"
                :loading="chatStore.sending"
                @click="handleSend"
              >
                发送
              </el-button>
            </div>
          </div>
        </div>
      </template>
    </div>

    <!-- Agent config / create dialog -->
    <el-dialog
      v-model="showAgentDialog"
      :title="editingAgent ? '编辑智能体' : '新建智能体'"
      width="560px"
      destroy-on-close
    >
      <el-form label-width="90px" :model="agentForm" class="agent-form">
        <el-form-item label="名称">
          <el-input v-model="agentForm.name" placeholder="智能体名称" />
        </el-form-item>
        <el-form-item label="描述">
          <el-input v-model="agentForm.description" type="textarea" :rows="2" placeholder="描述智能体的功能" />
        </el-form-item>
        <el-form-item label="头像URL">
          <el-input v-model="agentForm.avatar" placeholder="可选，头像图片链接" />
        </el-form-item>
        <el-form-item label="系统提示词">
          <el-input v-model="agentForm.system_prompt" type="textarea" :rows="4" placeholder="定义智能体的行为、角色和能力" />
        </el-form-item>
        <el-form-item label="默认模型">
          <el-select v-model="agentForm.modelSelect" placeholder="选择模型" style="width: 100%">
            <el-option-group
              v-for="p in configuredProviders"
              :key="p.key"
              :label="p.name"
            >
              <el-option
                v-for="m in p.models"
                :key="`${p.key}:${m.name}`"
                :label="`${p.name} - ${m.name}`"
                :value="`${p.key}:${m.name}`"
              />
            </el-option-group>
          </el-select>
        </el-form-item>
        <el-form-item label="知识库">
          <el-select v-model="agentForm.kb_ids" multiple collapse-tags collapse-tags-tooltip placeholder="选择关联知识库（可选）" style="width: 100%">
            <el-option v-for="kb in knowledgeBases" :key="kb.id" :label="kb.name" :value="kb.id" />
          </el-select>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showAgentDialog = false">取消</el-button>
        <el-button type="primary" @click="handleSaveAgent">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, nextTick, watch } from "vue";
import { ElMessageBox } from "element-plus";
import { Plus, Delete, Promotion, UserFilled, ChatDotRound, Setting, ArrowRight } from "@element-plus/icons-vue";
import { useChatStore } from "@/stores/chat";
import { useAgentStore } from "@/stores/agent";
import { listLLMModels } from "@/api/models";
import { listKnowledgeBases } from "@/api/knowledge";
import { marked } from "marked";
import type { Agent, LLMModel, KnowledgeBase } from "@/types";

const chatStore = useChatStore();
const agentStore = useAgentStore();
const inputText = ref("");
const msgContainer = ref<HTMLElement>();
const knowledgeBases = ref<KnowledgeBase[]>([]);

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

// Agent dialog
const showAgentDialog = ref(false);
const editingAgent = ref<Agent | null>(null);
const agentForm = ref({
  name: "",
  description: "",
  avatar: "",
  system_prompt: "",
  modelSelect: "",
  kb_ids: [] as string[],
});

const defaultAgentName = computed(() => "新的智能体");

// Current messages (safe accessor for template)
const msgs = computed(() => chatStore.currentConversation?.messages || []);

// Sync currentModel with conversation
watch(
  () => chatStore.currentConversation,
  (conv) => {
    if (conv && conv.provider && conv.model_name) {
      currentModel.value = `${conv.provider}:${conv.model_name}`;
    } else {
      currentModel.value = "";
    }
  },
  { immediate: true },
);

// Auto-scroll when new messages arrive
watch(
  () => chatStore.currentConversation?.messages?.length,
  () => {
    nextTick(() => {
      if (msgContainer.value) {
        msgContainer.value.scrollTop = msgContainer.value.scrollHeight;
      }
    });
  },
);

// Auto-scroll during streaming
watch(
  () => {
    const msgs = chatStore.currentConversation?.messages;
    if (!msgs?.length) return "";
    return msgs[msgs.length - 1].content;
  },
  () => {
    nextTick(() => {
      if (msgContainer.value) {
        msgContainer.value.scrollTop = msgContainer.value.scrollHeight;
      }
    });
  },
);

onMounted(() => {
  agentStore.fetchAgents();
  loadModels();
});

async function loadModels() {
  try {
    const { data } = await listLLMModels();
    llmModels.value = data;
  } catch {
    // ignore
  }
}

function renderMarkdown(text: string): string {
  if (!text) return "";
  try {
    return marked.parse(text) as string;
  } catch {
    return text;
  }
}

// === Agent actions ===
async function loadKnowledgeBases() {
  try {
    const { data } = await listKnowledgeBases();
    knowledgeBases.value = data;
  } catch {
    // ignore
  }
}

async function handleCreateAgent() {
  editingAgent.value = null;
  agentForm.value = {
    name: "",
    description: "",
    avatar: "",
    system_prompt: "",
    modelSelect: "",
    kb_ids: [],
  };
  await loadKnowledgeBases();
  showAgentDialog.value = true;
}

async function openAgentConfig(agent: Agent) {
  editingAgent.value = agent;
  agentForm.value = {
    name: agent.name,
    description: agent.description || "",
    avatar: agent.avatar || "",
    system_prompt: agent.system_prompt || "",
    modelSelect: agent.provider ? `${agent.provider}:${agent.model_name}` : "",
    kb_ids: agent.kb_ids ? [...agent.kb_ids] : [],
  };
  await loadKnowledgeBases();
  showAgentDialog.value = true;
}

async function handleSaveAgent() {
  const { name, description, avatar, system_prompt, modelSelect, kb_ids } = agentForm.value;
  const agentName = name.trim() || defaultAgentName.value;
  let provider = "";
  let modelName = "";
  if (modelSelect) {
    const [p, m] = modelSelect.split(":");
    provider = p;
    modelName = m;
  }

  if (editingAgent.value) {
    await agentStore.updateAgent(editingAgent.value.id, {
      name: agentName,
      description: description || undefined,
      avatar: avatar || undefined,
      system_prompt: system_prompt || undefined,
      model_name: modelName,
      provider,
      kb_ids: kb_ids.length > 0 ? kb_ids : undefined,
    });
  } else {
    const agent = await agentStore.createAgent({
      name: agentName,
      description: description || undefined,
      avatar: avatar || undefined,
      system_prompt: system_prompt || undefined,
      model_name: modelName,
      provider,
      kb_ids: kb_ids.length > 0 ? kb_ids : undefined,
    });
    if (agent) {
      await agentStore.selectAgent(agent.id);
    }
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
    if (agentStore.currentAgent?.id !== id) {
      chatStore.currentConversation = null;
    }
  } catch {
    // cancelled
  }
}

// === Conversation actions ===
async function handleCreateConv() {
  const conv = await agentStore.createConversation();
  if (conv) {
    chatStore.currentConversation = conv;
  }
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
    // Sync agentStore list
    agentStore.conversations = agentStore.conversations.filter((c) => c.id !== id);
  } catch {
    // cancelled
  }
}

async function handleModelChange(value: string) {
  if (!value || !chatStore.currentConversation) return;
  const [provider, modelName] = value.split(":");
  await chatStore.updateConversation(chatStore.currentConversation.id, {
    model_name: modelName,
    provider,
  });
}

async function handleSend() {
  const text = inputText.value.trim();
  if (!text || chatStore.sending) return;
  inputText.value = "";
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

/* === Sidebar === */
.chat-sidebar {
  width: 320px;
  border-right: 1px solid #e4e7ed;
  display: flex;
  flex-direction: column;
}

.sidebar-header {
  padding: 12px;
  border-bottom: 1px solid #e4e7ed;
}

.sidebar-header .el-button {
  width: 100%;
}

.sidebar-body {
  flex: 1;
  overflow-y: auto;
}

/* Agent items */
.agent-group {
  border-bottom: 1px solid #f0f2f5;
}

.agent-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px 12px;
  cursor: pointer;
  transition: background 0.15s;
}

.agent-item:hover {
  background: #f0f2f5;
}

.agent-group.expanded .agent-item {
  background: #ecf5ff;
}

.agent-avatar {
  flex-shrink: 0;
}

.agent-info {
  flex: 1;
  min-width: 0;
}

.agent-name {
  font-size: 14px;
  font-weight: 500;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.agent-meta {
  font-size: 12px;
  color: #909399;
  margin-top: 2px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.agent-actions {
  flex-shrink: 0;
  opacity: 0;
  display: flex;
  gap: 2px;
}

.agent-item:hover .agent-actions {
  opacity: 1;
}

/* Conversation sublist */
.conv-sublist {
  background: #fafbfc;
  padding: 0 0 8px 0;
}

.conv-sublist-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 6px 12px 6px 44px;
  font-size: 12px;
  color: #909399;
}

.conv-item {
  padding: 8px 12px 8px 44px;
  cursor: pointer;
  position: relative;
  font-size: 13px;
  transition: background 0.15s;
}

.conv-item:hover {
  background: #f0f2f5;
}

.conv-item.active {
  background: #d9ecff;
}

.conv-title {
  font-size: 13px;
  font-weight: 500;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  padding-right: 28px;
}

.conv-meta {
  font-size: 11px;
  color: #909399;
  margin-top: 2px;
}

.conv-delete {
  position: absolute;
  right: 4px;
  top: 50%;
  transform: translateY(-50%);
  opacity: 0;
}

.conv-item:hover .conv-delete {
  opacity: 1;
}

/* === Main Chat === */
.chat-main {
  flex: 1;
  display: flex;
  flex-direction: column;
  min-width: 0;
}

.chat-placeholder {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
}

.agent-welcome {
  text-align: center;
}

.agent-welcome h3 {
  margin: 16px 0 8px;
  font-size: 18px;
}

.agent-welcome p {
  color: #909399;
  margin-bottom: 20px;
  max-width: 400px;
}

.chat-header {
  padding: 10px 16px;
  border-bottom: 1px solid #e4e7ed;
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.chat-header-left {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 14px;
}

.chat-header-agent {
  color: #409eff;
  font-weight: 500;
}

.chat-header-title {
  color: #303133;
}

.chat-header-right {
  flex-shrink: 0;
}

.chat-messages {
  flex: 1;
  overflow-y: auto;
  padding: 16px;
}

.message {
  display: flex;
  gap: 8px;
  margin-bottom: 16px;
}

.message.user {
  flex-direction: row-reverse;
}

.message-avatar {
  flex-shrink: 0;
}

.message-content {
  max-width: 70%;
}

.message.user .message-content {
  text-align: right;
}

.message-role {
  font-size: 12px;
  color: #909399;
  margin-bottom: 4px;
}

.message-text {
  padding: 10px 14px;
  border-radius: 8px;
  background: #f0f2f5;
  font-size: 14px;
  line-height: 1.6;
  word-break: break-word;
}

.message-text.is-streaming {
  border-left: 2px solid #409eff;
}

.message.user .message-text {
  background: #409eff;
  color: #fff;
}

.message-text :deep(p) {
  margin: 0 0 8px;
}

.message-text :deep(p:last-child) {
  margin-bottom: 0;
}

.message-text :deep(pre) {
  background: #f5f7fa;
  padding: 12px;
  border-radius: 6px;
  overflow-x: auto;
  font-size: 13px;
}

.message-text :deep(code) {
  font-family: "Cascadia Code", "Fira Code", monospace;
  font-size: 13px;
}

.message-text :deep(code:not(pre code)) {
  background: #e8eaed;
  padding: 2px 6px;
  border-radius: 4px;
}

.message.user .message-text :deep(pre),
.message.user .message-text :deep(code:not(pre code)) {
  background: rgba(255, 255, 255, 0.2);
  color: #fff;
}

.message.user .message-text :deep(a) {
  color: #fff;
  text-decoration: underline;
}

/* === Chat Input === */
.chat-input {
  padding: 12px 16px;
  border-top: 1px solid #e4e7ed;
}

.chat-input-actions {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-top: 8px;
  gap: 12px;
}

.model-selector {
  display: flex;
  align-items: center;
  gap: 6px;
  flex-shrink: 0;
}

.model-label {
  font-size: 13px;
  color: #606266;
  white-space: nowrap;
}

.actions-right {
  display: flex;
  gap: 8px;
  align-items: center;
  margin-left: auto;
}

/* Agent form - prevent label wrapping */
.agent-form :deep(.el-form-item__label) {
  white-space: nowrap;
}
</style>
