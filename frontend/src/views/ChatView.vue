<template>
  <div class="chat-view">
    <div class="chat-sidebar">
      <div class="sidebar-header">
        <el-button type="primary" @click="showNewChatDialog = true" :icon="Plus">
          新建对话
        </el-button>
      </div>
      <div class="conversation-list" v-loading="chatStore.loading">
        <div
          v-for="conv in chatStore.conversations"
          :key="conv.id"
          class="conv-item"
          :class="{ active: chatStore.currentConversation?.id === conv.id }"
          @click="chatStore.selectConversation(conv.id)"
        >
          <div class="conv-title">{{ conv.title }}</div>
          <div class="conv-meta">
            <span>{{ conv.provider }}/{{ conv.model_name }}</span>
            <span>{{ conv.message_count }} 条消息</span>
          </div>
          <span class="conv-delete" @click.stop>
            <el-button
              text
              type="danger"
              size="small"
              @click="handleDelete(conv.id)"
            >
              <el-icon><Delete /></el-icon>
            </el-button>
          </span>
        </div>
        <el-empty v-if="!chatStore.loading && chatStore.conversations.length === 0" description="暂无对话" />
      </div>
    </div>
    <div class="chat-main">
      <div v-if="!chatStore.currentConversation" class="chat-placeholder">
        <el-empty description="选择或创建一个对话开始" />
      </div>
      <template v-else>
        <div class="chat-header">
          <span class="chat-header-title">{{ chatStore.currentConversation.title }}</span>
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
              <div class="message-role">{{ msg.role === 'user' ? '我' : 'AI助手' }}</div>
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

    <!-- New chat naming dialog -->
    <el-dialog v-model="showNewChatDialog" title="新建对话" width="420px">
      <el-form label-width="80px">
        <el-form-item label="对话名称">
          <el-input
            v-model="newChatName"
            :placeholder="defaultChatName"
            @keydown.enter="handleCreateChat"
          />
        </el-form-item>
        <div class="dialog-hint">留空则使用默认名称：{{ defaultChatName }}</div>
      </el-form>
      <template #footer>
        <el-button @click="showNewChatDialog = false">取消</el-button>
        <el-button type="primary" @click="handleCreateChat">创建</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, nextTick, watch } from "vue";
import { ElMessageBox } from "element-plus";
import { Plus, Delete, Promotion, UserFilled, ChatDotRound } from "@element-plus/icons-vue";
import { useChatStore } from "@/stores/chat";
import { listModels } from "@/api/models";
import { marked } from "marked";
import type { ProviderInfo } from "@/types";

const chatStore = useChatStore();
const inputText = ref("");
const msgContainer = ref<HTMLElement>();

// Model selector
const providers = ref<ProviderInfo[]>([]);
const currentModel = ref("");

interface ProviderWithKey extends ProviderInfo {
  key: string;
}

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

// New chat dialog
const showNewChatDialog = ref(false);
const newChatName = ref("");

const defaultChatName = computed(() => {
  return new Date().toLocaleString("zh-CN", { hour12: false }) + " 对话";
});

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
  chatStore.fetchConversations();
  loadModels();
});

async function loadModels() {
  try {
    const { data } = await listModels();
    providers.value = data;
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

async function handleCreateChat() {
  const name = newChatName.value.trim() || defaultChatName.value;
  // Use first configured provider/model by default if no model selected
  let provider = "";
  let modelName = "";
  if (configuredProviders.value.length > 0) {
    const first = configuredProviders.value[0];
    provider = first.key;
    modelName = first.models[0]?.name || "";
  }

  const conv = await chatStore.createConversation({
    title: name,
    model_name: modelName,
    provider,
  });
  if (conv) {
    showNewChatDialog.value = false;
    newChatName.value = "";
    // Trigger model sync
    if (provider && modelName) {
      currentModel.value = `${provider}:${modelName}`;
    }
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

async function handleDelete(id: string) {
  try {
    await ElMessageBox.confirm("确定删除该对话？", "提示", {
      confirmButtonText: "确定",
      cancelButtonText: "取消",
      type: "warning",
    });
    await chatStore.deleteConversation(id);
  } catch {
    // cancelled
  }
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

.chat-sidebar {
  width: 280px;
  border-right: 1px solid #e4e7ed;
  display: flex;
  flex-direction: column;
}

.sidebar-header {
  padding: 12px;
  border-bottom: 1px solid #e4e7ed;
}

.conversation-list {
  flex: 1;
  overflow-y: auto;
  padding: 4px;
}

.conv-item {
  padding: 10px 12px;
  border-radius: 6px;
  cursor: pointer;
  position: relative;
  margin-bottom: 2px;
}

.conv-item:hover {
  background: #f0f2f5;
}

.conv-item.active {
  background: #ecf5ff;
}

.conv-title {
  font-size: 14px;
  font-weight: 500;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  padding-right: 24px;
}

.conv-meta {
  font-size: 12px;
  color: #909399;
  margin-top: 4px;
  display: flex;
  gap: 12px;
}

.conv-delete {
  position: absolute;
  right: 4px;
  top: 50%;
  transform: translateY(-50%);
  opacity: 0.45;
}

.conv-item:hover .conv-delete {
  opacity: 1;
}

.chat-main {
  flex: 1;
  display: flex;
  flex-direction: column;
}

.chat-placeholder {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
}

.chat-header {
  padding: 12px 16px;
  border-bottom: 1px solid #e4e7ed;
  display: flex;
  align-items: center;
  gap: 12px;
}

.chat-header-title {
  font-size: 15px;
  font-weight: 600;
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

.dialog-hint {
  font-size: 12px;
  color: #909399;
  margin-top: 4px;
}
</style>
