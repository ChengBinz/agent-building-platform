import { defineStore } from "pinia";
import { ref } from "vue";
import { ElMessage } from "element-plus";
import * as agentApi from "@/api/agents";
import * as chatApi from "@/api/chat";
import type { Agent, Conversation } from "@/types";

export const useAgentStore = defineStore("agent", () => {
  const agents = ref<Agent[]>([]);
  const currentAgent = ref<Agent | null>(null);
  const conversations = ref<Conversation[]>([]);
  const loading = ref(false);

  async function fetchAgents() {
    loading.value = true;
    try {
      const { data } = await agentApi.listAgents();
      agents.value = data;
    } catch (e: any) {
      ElMessage.error(e.response?.data?.detail || "获取智能体列表失败");
    } finally {
      loading.value = false;
    }
  }

  async function createAgent(params?: {
    name?: string;
    description?: string;
    avatar?: string;
    system_prompt?: string;
    model_name?: string;
    provider?: string;
    tools?: string[];
    kb_ids?: string[];
  }) {
    const defaults = {
      name: "新的智能体",
    };
    try {
      const { data } = await agentApi.createAgent({ ...defaults, ...params });
      agents.value.unshift(data);
      return data as Agent;
    } catch (e: any) {
      ElMessage.error(e.response?.data?.detail || "创建智能体失败");
      return null;
    }
  }

  async function updateAgent(
    id: string,
    params: {
      name?: string;
      description?: string;
      avatar?: string;
      system_prompt?: string;
      model_name?: string;
      provider?: string;
      tools?: string[];
      kb_ids?: string[];
    }
  ) {
    try {
      const { data } = await agentApi.updateAgent(id, params);
      const idx = agents.value.findIndex((a) => a.id === id);
      if (idx !== -1) {
        agents.value[idx] = { ...agents.value[idx], ...data };
      }
      if (currentAgent.value?.id === id) {
        currentAgent.value = { ...currentAgent.value, ...data };
      }
      return data as Agent;
    } catch (e: any) {
      ElMessage.error(e.response?.data?.detail || "更新智能体失败");
      return null;
    }
  }

  async function selectAgent(id: string) {
    loading.value = true;
    try {
      const { data } = await agentApi.getAgent(id);
      currentAgent.value = data;
      // Also load conversations for this agent
      await fetchConversations(id);
    } catch (e: any) {
      ElMessage.error(e.response?.data?.detail || "获取智能体失败");
    } finally {
      loading.value = false;
    }
  }

  async function deleteAgent(id: string) {
    const removedAgent = agents.value.find((a) => a.id === id);
    const removedIdx = agents.value.findIndex((a) => a.id === id);

    // Determine next agent to switch to
    let nextId: string | null = null;
    if (currentAgent.value?.id === id && agents.value.length > 1) {
      if (removedIdx < agents.value.length - 1) {
        nextId = agents.value[removedIdx + 1].id;
      } else {
        nextId = agents.value[removedIdx - 1].id;
      }
    }

    agents.value = agents.value.filter((a) => a.id !== id);
    if (currentAgent.value?.id === id) {
      if (nextId) {
        await selectAgent(nextId);
      } else {
        currentAgent.value = null;
        conversations.value = [];
      }
    }

    try {
      await agentApi.deleteAgent(id);
      ElMessage.success("智能体已删除");
    } catch (e: any) {
      if (removedAgent) {
        agents.value.splice(removedIdx, 0, removedAgent);
      }
      if (currentAgent.value?.id === id) {
        currentAgent.value = removedAgent || null;
      }
      ElMessage.error(e.response?.data?.detail || "删除智能体失败");
    }
  }

  async function fetchConversations(agentId?: string) {
    try {
      const { data } = await chatApi.listConversations(agentId);
      conversations.value = data;
    } catch (e: any) {
      ElMessage.error(e.response?.data?.detail || "获取对话列表失败");
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
      const { data } = await chatApi.createConversation({
        ...defaults,
        ...params,
        agent_id: currentAgent.value?.id,
      });
      conversations.value.unshift(data);
      return data as Conversation;
    } catch (e: any) {
      ElMessage.error(e.response?.data?.detail || "创建对话失败");
      return null;
    }
  }

  return {
    agents,
    currentAgent,
    conversations,
    loading,
    fetchAgents,
    createAgent,
    updateAgent,
    selectAgent,
    deleteAgent,
    fetchConversations,
    createConversation,
  };
});
