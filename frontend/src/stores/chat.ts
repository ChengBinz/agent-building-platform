import { defineStore } from "pinia";
import { ref } from "vue";
import { ElMessage } from "element-plus";
import * as chatApi from "@/api/chat";
import type { Conversation, Message } from "@/types";

export const useChatStore = defineStore("chat", () => {
  const conversations = ref<Conversation[]>([]);
  const currentConversation = ref<Conversation | null>(null);
  const loading = ref(false);
  const sending = ref(false);

  async function fetchConversations() {
    loading.value = true;
    try {
      const { data } = await chatApi.listConversations();
      conversations.value = data;
    } catch (e: any) {
      ElMessage.error(e.response?.data?.detail || "获取对话列表失败");
    } finally {
      loading.value = false;
    }
  }

  async function createConversation(params?: {
    title?: string;
    model_name?: string;
    system_prompt?: string;
  }) {
    try {
      const { data } = await chatApi.createConversation(params || {});
      conversations.value.unshift(data);
      currentConversation.value = data;
      return data;
    } catch (e: any) {
      ElMessage.error(e.response?.data?.detail || "创建对话失败");
      return null;
    }
  }

  async function selectConversation(id: string) {
    loading.value = true;
    try {
      const { data } = await chatApi.getConversation(id);
      currentConversation.value = data;
    } catch (e: any) {
      ElMessage.error(e.response?.data?.detail || "获取对话失败");
    } finally {
      loading.value = false;
    }
  }

  async function deleteConversation(id: string) {
    try {
      await chatApi.deleteConversation(id);
      conversations.value = conversations.value.filter((c) => c.id !== id);
      if (currentConversation.value?.id === id) {
        currentConversation.value = null;
      }
      ElMessage.success("对话已删除");
    } catch (e: any) {
      ElMessage.error(e.response?.data?.detail || "删除对话失败");
    }
  }

  async function sendMessage(content: string) {
    if (!currentConversation.value) return;
    sending.value = true;
    try {
      // Optimistic: add user message
      currentConversation.value.messages = currentConversation.value.messages || [];
      currentConversation.value.messages.push({
        id: "",
        conversation_id: currentConversation.value.id,
        role: "user",
        content,
        created_at: new Date().toISOString(),
      });

      const { data } = await chatApi.sendMessage(currentConversation.value.id, content);

      // Add assistant reply
      currentConversation.value.messages.push({
        id: "",
        conversation_id: currentConversation.value.id,
        role: data.role,
        content: data.content,
        created_at: new Date().toISOString(),
      });

      currentConversation.value.message_count += 2;
    } catch (e: any) {
      ElMessage.error(e.response?.data?.detail || "发送消息失败");
    } finally {
      sending.value = false;
    }
  }

  return {
    conversations,
    currentConversation,
    loading,
    sending,
    fetchConversations,
    createConversation,
    selectConversation,
    deleteConversation,
    sendMessage,
  };
});
