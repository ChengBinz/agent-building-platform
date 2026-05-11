import { defineStore } from "pinia";
import { ref } from "vue";
import { ElMessage } from "element-plus";
import * as kbApi from "@/api/knowledge";
import type { KnowledgeBase } from "@/types";

export const useKnowledgeStore = defineStore("knowledge", () => {
  const knowledgeBases = ref<KnowledgeBase[]>([]);
  const currentKB = ref<KnowledgeBase | null>(null);
  const loading = ref(false);
  const uploading = ref(false);

  let pollTimer: ReturnType<typeof setInterval> | null = null;

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
    embedding_api_key?: string;
    embedding_base_url?: string;
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
    params: {
      name?: string;
      description?: string;
      embedding_model?: string;
      embedding_api_key?: string;
      embedding_base_url?: string;
    }
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

  // ── Document actions ─────────────────────────────────────────

  async function uploadDocument(kbId: string, file: File) {
    uploading.value = true;
    try {
      const { data } = await kbApi.uploadDocument(kbId, file);
      await selectKnowledgeBase(kbId);
      ElMessage.success("文件上传成功，正在处理中");
      return data;
    } catch (e: any) {
      ElMessage.error(e.response?.data?.detail || "文件上传失败");
      return null;
    } finally {
      uploading.value = false;
    }
  }

  async function deleteDocument(kbId: string, documentId: string) {
    try {
      await kbApi.deleteDocument(kbId, documentId);
      await selectKnowledgeBase(kbId);
      ElMessage.success("文档已删除");
    } catch (e: any) {
      ElMessage.error(e.response?.data?.detail || "删除文档失败");
    }
  }

  function startStatusPolling(kbId: string) {
    stopStatusPolling();
    pollTimer = setInterval(async () => {
      await selectKnowledgeBase(kbId);
      if (!currentKB.value) {
        stopStatusPolling();
        return;
      }
      const hasProcessing = currentKB.value.documents?.some(
        (d: any) => d.status === "pending" || d.status === "processing"
      );
      if (!hasProcessing) {
        stopStatusPolling();
      }
    }, 3000);
  }

  function stopStatusPolling() {
    if (pollTimer) {
      clearInterval(pollTimer);
      pollTimer = null;
    }
  }

  return {
    knowledgeBases,
    currentKB,
    loading,
    uploading,
    fetchKnowledgeBases,
    createKnowledgeBase,
    selectKnowledgeBase,
    updateKnowledgeBase,
    deleteKnowledgeBase,
    uploadDocument,
    deleteDocument,
    startStatusPolling,
    stopStatusPolling,
  };
});
