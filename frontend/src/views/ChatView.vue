<template>
  <div class="chat-view">
    <div class="chat-sidebar">
      <div class="sidebar-header">
        <el-button type="primary" @click="handleNewChat" :icon="Plus">
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
            <span>{{ conv.model_name }}</span>
            <span>{{ conv.message_count }} 条消息</span>
          </div>
          <el-button
            class="conv-delete"
            text
            type="danger"
            size="small"
            @click.stop="handleDelete(conv.id)"
          >
            <el-icon><Delete /></el-icon>
          </el-button>
        </div>
        <el-empty v-if="!chatStore.loading && chatStore.conversations.length === 0" description="暂无对话" />
      </div>
    </div>
    <div class="chat-main">
      <div v-if="!chatStore.currentConversation" class="chat-placeholder">
        <el-empty description="选择或创建一个对话开始" />
      </div>
      <template v-else>
        <div class="chat-messages" ref="msgContainer">
          <div
            v-for="msg in chatStore.currentConversation.messages"
            :key="msg.created_at"
            class="message"
            :class="msg.role"
          >
            <div class="message-avatar">
              <el-avatar v-if="msg.role === 'user'" :icon="UserFilled" size="small" />
              <el-avatar v-else :icon="ChatDotRound" size="small" style="background-color: #409eff" />
            </div>
            <div class="message-content">
              <div class="message-role">{{ msg.role === 'user' ? '我' : 'AI助手' }}</div>
              <div class="message-text">{{ msg.content }}</div>
            </div>
          </div>
          <div v-if="chatStore.sending" class="message assistant">
            <el-icon class="is-loading"><Loading /></el-icon>
            <span style="margin-left: 8px; color: #909399">思考中...</span>
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
          <el-button
            type="primary"
            :icon="Promotion"
            :loading="chatStore.sending"
            @click="handleSend"
            style="margin-top: 8px"
          >
            发送
          </el-button>
        </div>
      </template>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, nextTick } from "vue";
import { ElMessageBox } from "element-plus";
import { Plus, Delete, Promotion, UserFilled, ChatDotRound, Loading } from "@element-plus/icons-vue";
import { useChatStore } from "@/stores/chat";

const chatStore = useChatStore();
const inputText = ref("");
const msgContainer = ref<HTMLElement>();

onMounted(() => {
  chatStore.fetchConversations();
});

async function handleNewChat() {
  await chatStore.createConversation();
}

async function handleSend() {
  const text = inputText.value.trim();
  if (!text || chatStore.sending) return;
  inputText.value = "";
  await chatStore.sendMessage(text);
  await nextTick();
  if (msgContainer.value) {
    msgContainer.value.scrollTop = msgContainer.value.scrollHeight;
  }
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
  opacity: 0;
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
  white-space: pre-wrap;
  word-break: break-word;
}

.message.user .message-text {
  background: #409eff;
  color: #fff;
}

.chat-input {
  padding: 12px 16px;
  border-top: 1px solid #e4e7ed;
}
</style>
