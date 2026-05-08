import { defineStore } from "pinia";
import { ref } from "vue";
import { ElMessage } from "element-plus";
import * as kbApi from "@/api/knowledge";
import type { KnowledgeBase } from "@/types";

export const useKnowledgeStore = defineStore("knowledge", () => {
  const knowledgeBases = ref<KnowledgeBase[]>([]);
  const currentKB = ref<KnowledgeBase | null>(null);
  const loading = ref(false);

  async function fetchKnowledgeBases() {
    loading.value = true;
    try {
      const { data } = await kbApi.listKnowledgeBases();
      knowledgeBases.value = data;
    } catch (e: any) {
      ElMessage.error(e.response?.data?.detail || "获取知识库列表失败");
    } finally {
      loading.value = false;
    }
  }

  async function createKnowledgeBase(params: {
    name: string;
    description?: string;
    embedding_model?: string;
  }) {
    try {
      const { data } = await kbApi.createKnowledgeBase(params);
      knowledgeBases.value.unshift(data);
      ElMessage.success("知识库创建成功");
      return data;
    } catch (e: any) {
      ElMessage.error(e.response?.data?.detail || "创建知识库失败");
      return null;
    }
  }

  async function selectKnowledgeBase(id: string) {
    loading.value = true;
    try {
      const { data } = await kbApi.getKnowledgeBase(id);
      currentKB.value = data;
    } catch (e: any) {
      ElMessage.error(e.response?.data?.detail || "获取知识库失败");
    } finally {
      loading.value = false;
    }
  }

  async function updateKnowledgeBase(
    id: string,
    params: { name?: string; description?: string }
  ) {
    try {
      const { data } = await kbApi.updateKnowledgeBase(id, params);
      const idx = knowledgeBases.value.findIndex((k) => k.id === id);
      if (idx !== -1) {
        knowledgeBases.value[idx] = { ...knowledgeBases.value[idx], ...data };
      }
      if (currentKB.value?.id === id) {
        currentKB.value = { ...currentKB.value, ...data };
      }
      ElMessage.success("知识库更新成功");
      return data;
    } catch (e: any) {
      ElMessage.error(e.response?.data?.detail || "更新知识库失败");
      return null;
    }
  }

  async function deleteKnowledgeBase(id: string) {
    try {
      await kbApi.deleteKnowledgeBase(id);
      knowledgeBases.value = knowledgeBases.value.filter((k) => k.id !== id);
      if (currentKB.value?.id === id) {
        currentKB.value = null;
      }
      ElMessage.success("知识库已删除");
    } catch (e: any) {
      ElMessage.error(e.response?.data?.detail || "删除知识库失败");
    }
  }

  return {
    knowledgeBases,
    currentKB,
    loading,
    fetchKnowledgeBases,
    createKnowledgeBase,
    selectKnowledgeBase,
    updateKnowledgeBase,
    deleteKnowledgeBase,
  };
});
