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
  let streamController: AbortController | null = null;

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
    provider?: string;
    system_prompt?: string;
  }) {
    const defaults = {
      title: new Date().toLocaleString("zh-CN", { hour12: false }) + " 对话",
    };
    try {
      const { data } = await chatApi.createConversation({ ...defaults, ...params });
      conversations.value.unshift(data);
      currentConversation.value = data;
      return data;
    } catch (e: any) {
      ElMessage.error(e.response?.data?.detail || "创建对话失败");
      return null;
    }
  }

  async function updateConversation(id: string, params: {
    title?: string;
    model_name?: string;
    provider?: string;
  }) {
    try {
      const { data } = await chatApi.updateConversation(id, params);
      // Update in list
      const idx = conversations.value.findIndex((c) => c.id === id);
      if (idx !== -1) {
        conversations.value[idx] = { ...conversations.value[idx], ...data };
      }
      // Update current if active
      if (currentConversation.value?.id === id) {
        currentConversation.value = { ...currentConversation.value, ...data };
      }
      return data;
    } catch (e: any) {
      ElMessage.error(e.response?.data?.detail || "更新对话失败");
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
    // Snapshot for rollback
    const wasCurrent = currentConversation.value?.id === id;
    const removedConv = conversations.value.find((c) => c.id === id);
    const removedIdx = conversations.value.findIndex((c) => c.id === id);

    // Determine next conversation to switch to
    let nextId: string | null = null;
    if (wasCurrent && conversations.value.length > 1) {
      if (removedIdx < conversations.value.length - 1) {
        nextId = conversations.value[removedIdx + 1].id;
      } else {
        nextId = conversations.value[removedIdx - 1].id;
      }
    }

    // Optimistic: remove from list immediately
    conversations.value = conversations.value.filter((c) => c.id !== id);
    if (wasCurrent) {
      if (nextId) {
        // Switch to next conversation (basic info, messages load in background)
        currentConversation.value = conversations.value.find((c) => c.id === nextId) || null;
        // Load full messages async - don't await, let it load in background
        selectConversation(nextId);
      } else {
        currentConversation.value = null;
      }
    }

    try {
      await chatApi.deleteConversation(id);
      ElMessage.success("对话已删除");
    } catch (e: any) {
      // Rollback
      if (removedConv) {
        conversations.value.splice(removedIdx, 0, removedConv);
      }
      if (wasCurrent) {
        currentConversation.value = removedConv || null;
      }
      ElMessage.error(e.response?.data?.detail || "删除对话失败");
    }
  }

  function cancelStream() {
    if (streamController) {
      streamController.abort();
      streamController = null;
      sending.value = false;
    }
  }

  async function sendMessage(content: string, enableSearch: boolean = false) {
    if (!currentConversation.value) return;

    // Cancel any existing stream before starting a new one
    cancelStream();
    sending.value = true;

    const conv = currentConversation.value;
    conv.messages = conv.messages || [];

    // Add user message optimistically
    conv.messages.push({
      id: "",
      conversation_id: conv.id,
      role: "user",
      content,
      created_at: new Date().toISOString(),
    });

    // Create placeholder for assistant reply - 通过数组索引访问确保响应式
    const assistantMsgIndex = conv.messages.length;
    conv.messages.push({
      id: "",
      conversation_id: conv.id,
      role: "assistant",
      content: "",
      thinking_content: "",
      created_at: new Date().toISOString(),
    });

    let hasError = false;

    streamController = chatApi.sendMessageStream(
      conv.id,
      content,
      () => {
        // onThinkingStart — placeholder already has thinking_content: ""
      },
      () => {
        // onThinkingStart — placeholder already has thinking_content: ""
      },
      (token: string) => {
        // onThinkingToken
        const messages = conv.messages;
        if (messages && messages[assistantMsgIndex]) {
          messages[assistantMsgIndex].thinking_content =
            (messages[assistantMsgIndex].thinking_content || "") + token;
        }
      },
      () => {
        // onThinkingEnd
      },
      (token: string) => {
        // onToken
        const messages = conv.messages;
        if (messages && messages[assistantMsgIndex]) {
          messages[assistantMsgIndex].content += token;
        }
      },
      async () => {
        streamController = null;
        try {
          const { data } = await chatApi.getConversation(conv.id);
          currentConversation.value = data;
          const idx = conversations.value.findIndex((c) => c.id === conv.id);
          if (idx !== -1) conversations.value[idx] = data;
        } catch { /* ignore */ }
        sending.value = false;
      },
      (err: string) => {
        const messages = conv.messages;
        if (messages && messages[assistantMsgIndex] && !messages[assistantMsgIndex].content) {
          messages[assistantMsgIndex].content = `发送失败: ${err}`;
        }
        hasError = true;
        ElMessage.error(`发送失败: ${err}`);
        sending.value = false;
        streamController = null;
      },
      enableSearch,
      (toolCall) => {
        const messages = conv.messages;
        if (messages && messages[assistantMsgIndex]) {
          messages[assistantMsgIndex].content += `\n\n🔧 调用工具: ${toolCall.name}(${JSON.stringify(toolCall.args)})\n`;
        }
      },
      (toolResult) => {
        const messages = conv.messages;
        if (messages && messages[assistantMsgIndex]) {
          messages[assistantMsgIndex].content += `📋 结果: ${toolResult.result}\n\n`;
        }
      },
    );
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
    updateConversation,
    sendMessage,
    cancelStream,
  };
});
