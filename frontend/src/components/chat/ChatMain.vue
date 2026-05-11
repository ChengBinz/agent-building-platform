<template>
  <div class="chat-main">
    <div v-if="!conversation" class="chat-placeholder">
      <div v-if="!currentAgent">
        <el-empty description="选择或创建一个智能体开始" />
      </div>
      <div v-else>
        <div class="agent-welcome">
          <el-avatar :size="64" :src="currentAgent.avatar">
            {{ currentAgent.name.charAt(0) }}
          </el-avatar>
          <h3>{{ currentAgent.name }}</h3>
          <p v-if="currentAgent.description">{{ currentAgent.description }}</p>
          <el-button type="primary" @click="$emit('createConv')">开始新对话</el-button>
        </div>
      </div>
    </div>
    <template v-else>
      <div class="chat-header">
        <div class="chat-header-left">
          <span class="chat-header-agent">{{ currentAgent?.name || '智能体' }}</span>
          <el-icon><ArrowRight /></el-icon>
          <span class="chat-header-title">{{ conversation.title }}</span>
        </div>
        <div class="chat-header-right">
          <el-button v-if="currentAgent" text size="small" @click="$emit('editAgent', currentAgent)">
            <el-icon><Setting /></el-icon>
            智能体设置
          </el-button>
        </div>
      </div>
      <div class="chat-messages" ref="msgContainer">
        <div v-for="(msg, idx) in messages" :key="idx" class="message" :class="msg.role">
          <div class="message-avatar">
            <el-avatar v-if="msg.role === 'user'" :icon="UserFilled" size="small" />
            <el-avatar v-else :icon="ChatDotRound" size="small" style="background-color: #409eff" />
          </div>
          <div class="message-content">
            <div class="message-role">{{ msg.role === 'user' ? '我' : currentAgent?.name || 'AI助手' }}</div>
            <div
              class="message-text"
              :class="{ 'is-streaming': msg.role === 'assistant' && sending && idx === (messages.length - 1) }"
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
          :disabled="sending"
        />
        <div class="chat-input-actions">
          <div class="model-selector">
            <span class="model-label">模型：</span>
            <el-select
              v-model="currentModel"
              placeholder="选择模型"
              size="small"
              style="width: 260px"
              :disabled="sending"
              @change="$emit('modelChange', $event)"
            >
              <el-option-group v-for="p in providers" :key="p.key" :label="p.name">
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
            <el-button v-if="sending" @click="$emit('cancel')" type="warning" plain size="small">
              停止生成
            </el-button>
            <el-button type="primary" :icon="Promotion" :loading="sending" @click="handleSend">
              发送
            </el-button>
          </div>
        </div>
      </div>
    </template>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch, nextTick } from "vue";
import { Promotion, UserFilled, ChatDotRound, Setting, ArrowRight } from "@element-plus/icons-vue";
import { marked } from "marked";
import type { Agent, Conversation, Message, ProviderWithKey } from "@/types";

const props = defineProps<{
  conversation: Conversation | null;
  currentAgent: Agent | null;
  messages: Message[];
  sending: boolean;
  providers: ProviderWithKey[];
  modelValue: string;
}>();

const emit = defineEmits<{
  createConv: [];
  editAgent: [agent: Agent];
  send: [text: string];
  cancel: [];
  modelChange: [value: string];
  "update:modelValue": [value: string];
}>();

const inputText = ref("");
const msgContainer = ref<HTMLElement>();

const currentModel = computed({
  get: () => props.modelValue,
  set: (v) => emit("update:modelValue", v),
});

// Sync model with conversation
watch(
  () => props.conversation,
  (conv) => {
    if (conv && conv.provider && conv.model_name) {
      currentModel.value = `${conv.provider}:${conv.model_name}`;
    } else {
      currentModel.value = "";
    }
  },
  { immediate: true },
);

// Auto-scroll on new messages
watch(
  () => props.messages.length,
  () => scrollToBottom(),
);

// Auto-scroll during streaming
watch(
  () => {
    const msgs = props.messages;
    if (!msgs.length) return "";
    return msgs[msgs.length - 1].content;
  },
  () => scrollToBottom(),
);

function scrollToBottom() {
  nextTick(() => {
    if (msgContainer.value) {
      msgContainer.value.scrollTop = msgContainer.value.scrollHeight;
    }
  });
}

function renderMarkdown(text: string): string {
  if (!text) return "";
  try {
    return marked.parse(text) as string;
  } catch {
    return text;
  }
}

function handleSend() {
  const text = inputText.value.trim();
  if (!text || props.sending) return;
  inputText.value = "";
  emit("send", text);
}
</script>

<style scoped>
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
</style>
