<template>
  <div class="knowledge-view">
    <div class="page-header">
      <h3>知识库管理</h3>
      <el-button type="primary" @click="openCreateDialog" :icon="Plus">新建知识库</el-button>
    </div>

    <el-table :data="kbStore.knowledgeBases" v-loading="kbStore.loading" stripe>
      <el-table-column prop="name" label="名称" min-width="180" />
      <el-table-column prop="description" label="描述" min-width="200">
        <template #default="{ row }">{{ row.description || '-' }}</template>
      </el-table-column>
      <el-table-column prop="embedding_model" label="嵌入模型" width="200" />
      <el-table-column prop="chunk_count" label="分块数" width="100" align="right" />
      <el-table-column prop="document_count" label="文档数" width="90" align="right" />
      <el-table-column prop="created_at" label="创建时间" width="170">
        <template #default="{ row }">{{ formatDateTime(row.created_at) }}</template>
      </el-table-column>
      <el-table-column label="操作" width="160" fixed="right">
        <template #default="{ row }">
          <el-button text type="primary" size="small" @click="handleView(row)">详情</el-button>
          <el-button text type="danger" size="small" @click="handleDelete(row.id)">删除</el-button>
        </template>
      </el-table-column>
    </el-table>

    <KbConfigDialog
      v-model:visible="dialogVisible"
      mode="create"
      :form="form"
      :loading="creating"
      @submit="handleCreate"
      @reset="resetForm"
    />

    <KbConfigDialog
      v-model:visible="editDialogVisible"
      mode="edit"
      :form="editForm"
      :loading="updating"
      :apiPlaceholder="kbStore.currentKB?.embedding_api_key_masked || '输入新的 API Key（留空不修改）'"
      @submit="handleUpdateConfig"
    />

    <KbDetailDrawer
      v-model:visible="drawerVisible"
      :kb="kbStore.currentKB"
      :uploading="kbStore.uploading"
      @close="stopPolling()"
      @editConfig="openEditDialog"
      @upload="handleFileChange"
      @deleteDoc="handleDeleteDocument"
    />
  </div>
</template>

<script setup lang="ts">
import { reactive, ref, onMounted, onUnmounted } from "vue";
import { ElMessageBox, ElMessage } from "element-plus";
import { Plus } from "@element-plus/icons-vue";
import { useKnowledgeStore } from "@/stores/knowledge";
import { formatDateTime } from "@/utils/format";
import * as kbApi from "@/api/knowledge";
import KbConfigDialog from "@/components/knowledge/KbConfigDialog.vue";
import KbDetailDrawer from "@/components/knowledge/KbDetailDrawer.vue";

const kbStore = useKnowledgeStore();
const dialogVisible = ref(false);
const drawerVisible = ref(false);
const editDialogVisible = ref(false);
const creating = ref(false);
const updating = ref(false);
let pollTimer: ReturnType<typeof setTimeout> | null = null;

const form = reactive({
  name: "",
  description: "",
  embedding_model: "text-embedding-v4",
  embedding_api_key: "",
  embedding_base_url: "https://dashscope.aliyuncs.com/compatible-mode/v1",
});

const editForm = reactive({
  embedding_model: "text-embedding-v4",
  embedding_api_key: "",
  embedding_base_url: "",
});

onMounted(() => kbStore.fetchKnowledgeBases());
onUnmounted(() => stopPolling());

function stopPolling() {
  if (pollTimer) { clearTimeout(pollTimer); pollTimer = null; }
}

function pollUntilDone(kbId: string) {
  stopPolling();
  pollTimer = setTimeout(async function poll() {
    try {
      const { data } = await kbApi.getKnowledgeBase(kbId);
      const allDone = !data.documents?.some((d: any) => d.status === "pending" || d.status === "processing");
      if (allDone) {
        await kbStore.selectKnowledgeBase(kbId);
        await kbStore.fetchKnowledgeBases();
        const failedDocs = data.documents?.filter((d: any) => d.status === "failed") || [];
        if (failedDocs.length > 0) {
          const errMsg = failedDocs[0].error_message || "未知错误";
          ElMessage.error(`文档解析失败: ${errMsg}`);
        } else {
          ElMessage.success("文档解析完成");
        }
        return;
      }
      pollTimer = setTimeout(poll, 3000);
    } catch { /* stop on error */ }
  }, 3000);
}

function resetForm() {
  Object.assign(form, { name: "", description: "", embedding_model: "text-embedding-v4", embedding_api_key: "", embedding_base_url: "https://dashscope.aliyuncs.com/compatible-mode/v1" });
}

function openCreateDialog() { resetForm(); dialogVisible.value = true; }

function openEditDialog() {
  if (!kbStore.currentKB) return;
  editForm.embedding_model = kbStore.currentKB.embedding_model;
  editForm.embedding_api_key = "";
  editForm.embedding_base_url = kbStore.currentKB.embedding_base_url || "";
  editDialogVisible.value = true;
}

async function handleCreate() {
  if (!form.name.trim()) return;
  creating.value = true;
  const result = await kbStore.createKnowledgeBase({
    name: form.name, description: form.description || undefined,
    embedding_model: form.embedding_model, embedding_api_key: form.embedding_api_key || undefined,
    embedding_base_url: form.embedding_base_url || undefined,
  });
  creating.value = false;
  if (result) dialogVisible.value = false;
}

async function handleUpdateConfig() {
  if (!kbStore.currentKB) return;
  updating.value = true;
  const params: Record<string, string | undefined> = {
    embedding_model: editForm.embedding_model,
    embedding_base_url: editForm.embedding_base_url || undefined,
  };
  if (editForm.embedding_api_key) params.embedding_api_key = editForm.embedding_api_key;
  const result = await kbStore.updateKnowledgeBase(kbStore.currentKB.id, params);
  updating.value = false;
  if (result) editDialogVisible.value = false;
}

async function handleView(row: any) {
  await kbStore.selectKnowledgeBase(row.id);
  drawerVisible.value = true;
}

async function handleDelete(id: string) {
  try {
    await ElMessageBox.confirm("确定删除该知识库？删除后无法恢复。", "警告", { confirmButtonText: "确定", cancelButtonText: "取消", type: "warning" });
    await kbStore.deleteKnowledgeBase(id);
  } catch { /* cancelled */ }
}

async function handleFileChange(file: any) {
  if (!kbStore.currentKB) return;
  await kbStore.uploadDocument(kbStore.currentKB.id, file.raw);
  pollUntilDone(kbStore.currentKB.id);
}

async function handleDeleteDocument(docId: string) {
  if (!kbStore.currentKB) return;
  try {
    await ElMessageBox.confirm("确定删除该文档？", "警告", { confirmButtonText: "确定", cancelButtonText: "取消", type: "warning" });
    await kbStore.deleteDocument(kbStore.currentKB.id, docId);
  } catch { /* cancelled */ }
}
</script>

<style scoped>
.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}
.page-header h3 { margin: 0; }
</style>
