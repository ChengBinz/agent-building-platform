<template>
  <div class="knowledge-view">
    <div class="page-header">
      <h3>知识库管理</h3>
      <el-button type="primary" @click="openCreateDialog" :icon="Plus">
        新建知识库
      </el-button>
    </div>

    <el-table :data="kbStore.knowledgeBases" v-loading="kbStore.loading" stripe>
      <el-table-column prop="name" label="名称" min-width="180" />
      <el-table-column prop="description" label="描述" min-width="200">
        <template #default="{ row }">
          {{ row.description || '-' }}
        </template>
      </el-table-column>
      <el-table-column prop="embedding_model" label="嵌入模型" width="200" />
      <el-table-column prop="chunk_count" label="分块数" width="100" align="right" />
      <el-table-column prop="document_count" label="文档数" width="90" align="right" />
      <el-table-column prop="created_at" label="创建时间" width="170">
        <template #default="{ row }">
          {{ formatDateTime(row.created_at) }}
        </template>
      </el-table-column>
      <el-table-column label="操作" width="160" fixed="right">
        <template #default="{ row }">
          <el-button text type="primary" size="small" @click="handleView(row)">
            详情
          </el-button>
          <el-button text type="danger" size="small" @click="handleDelete(row.id)">
            删除
          </el-button>
        </template>
      </el-table-column>
    </el-table>

    <!-- Create Dialog -->
    <el-dialog v-model="dialogVisible" title="新建知识库" width="520px" @close="resetForm">
      <el-form :model="form" label-width="100px">
        <el-form-item label="名称">
          <el-input v-model="form.name" placeholder="请输入知识库名称" />
        </el-form-item>
        <el-form-item label="描述">
          <el-input
            v-model="form.description"
            type="textarea"
            placeholder="请输入描述（可选）"
          />
        </el-form-item>
        <el-divider content-position="left">Embedding 配置</el-divider>
        <el-form-item label="嵌入模型">
          <el-select v-model="form.embedding_model" style="width: 100%">
            <el-option label="text-embedding-v4" value="text-embedding-v4" />
          </el-select>
        </el-form-item>
        <el-form-item label="API Key">
          <el-input
            v-model="form.embedding_api_key"
            type="password"
            show-password
            placeholder="输入 Embedding API Key（留空使用全局配置）"
          />
        </el-form-item>
        <el-form-item label="Base URL">
          <el-input
            v-model="form.embedding_base_url"
            placeholder="留空使用默认地址"
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handleCreate" :loading="creating">确定</el-button>
      </template>
    </el-dialog>

    <!-- Edit Config Dialog -->
    <el-dialog v-model="editDialogVisible" title="编辑 Embedding 配置" width="520px">
      <el-form :model="editForm" label-width="100px">
        <el-form-item label="嵌入模型">
          <el-select v-model="editForm.embedding_model" style="width: 100%">
            <el-option label="text-embedding-v4" value="text-embedding-v4" />
          </el-select>
        </el-form-item>
        <el-form-item label="API Key">
          <el-input
            v-model="editForm.embedding_api_key"
            type="password"
            show-password
            :placeholder="kbStore.currentKB?.embedding_api_key_masked || '输入新的 API Key（留空不修改）'"
          />
        </el-form-item>
        <el-form-item label="Base URL">
          <el-input
            v-model="editForm.embedding_base_url"
            placeholder="可选，留空使用默认地址"
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="editDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handleUpdateConfig" :loading="updating">保存</el-button>
      </template>
    </el-dialog>

    <!-- Detail Drawer -->
    <el-drawer v-model="drawerVisible" title="知识库详情" size="500px" @close="stopPolling()">
      <template v-if="kbStore.currentKB">
        <el-descriptions :column="1" border>
          <el-descriptions-item label="名称">{{ kbStore.currentKB.name }}</el-descriptions-item>
          <el-descriptions-item label="描述">{{ kbStore.currentKB.description || '-' }}</el-descriptions-item>
          <el-descriptions-item label="嵌入模型">{{ kbStore.currentKB.embedding_model }}</el-descriptions-item>
          <el-descriptions-item label="API Key">
            {{ kbStore.currentKB.embedding_api_key_masked || '未配置' }}
          </el-descriptions-item>
          <el-descriptions-item label="Base URL">
            {{ kbStore.currentKB.embedding_base_url || '默认' }}
          </el-descriptions-item>
          <el-descriptions-item label="分块数">{{ kbStore.currentKB.chunk_count }}</el-descriptions-item>
          <el-descriptions-item label="文档数">{{ kbStore.currentKB.document_count }}</el-descriptions-item>
          <el-descriptions-item label="创建时间">{{ formatDateTime(kbStore.currentKB.created_at) }}</el-descriptions-item>
        </el-descriptions>

        <el-button style="margin-top: 16px" @click="openEditDialog" :icon="Edit">
          编辑 Embedding 配置
        </el-button>

        <h4 style="margin: 24px 0 12px">上传文档</h4>
        <el-upload
          :auto-upload="false"
          :on-change="handleFileChange"
          :show-file-list="false"
          accept=".txt,.md"
          drag
          v-loading="kbStore.uploading"
        >
          <el-icon class="el-icon--upload"><UploadFilled /></el-icon>
          <div class="el-upload__text">拖拽文件到此处，或 <em>点击选择</em></div>
          <template #tip>
            <div class="el-upload__tip">仅支持 .txt 和 .md 文件</div>
          </template>
        </el-upload>

        <h4 style="margin: 24px 0 12px">文档列表</h4>
        <el-table :data="kbStore.currentKB.documents || []" size="small" style="margin-top: 12px">
          <el-table-column prop="filename" label="文件名" min-width="150" />
          <el-table-column prop="file_type" label="类型" width="80" />
          <el-table-column prop="status" label="状态" width="90">
            <template #default="{ row }">
              <el-tag :type="statusType(row.status)" size="small">
                {{ statusLabel(row.status) }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="chunk_count" label="分块数" width="80" />
          <el-table-column label="操作" width="80">
            <template #default="{ row }">
              <el-button text type="danger" size="small" @click="handleDeleteDocument(row.id)">
                删除
              </el-button>
            </template>
          </el-table-column>
        </el-table>
        <el-empty v-if="(kbStore.currentKB.documents || []).length === 0" description="暂无文档" />
      </template>
    </el-drawer>
  </div>
</template>

<script setup lang="ts">
import { reactive, ref, onMounted, onUnmounted, watch } from "vue";
import { ElMessageBox, ElMessage } from "element-plus";
import { Plus, UploadFilled, Edit } from "@element-plus/icons-vue";
import { useKnowledgeStore } from "@/stores/knowledge";
import { formatDateTime } from "@/utils/format";
import * as kbApi from "@/api/knowledge";

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

onMounted(() => {
  kbStore.fetchKnowledgeBases();
});

onUnmounted(() => {
  stopPolling();
});

watch(drawerVisible, (val) => {
  if (!val) stopPolling();
});

function stopPolling() {
  if (pollTimer) {
    clearTimeout(pollTimer);
    pollTimer = null;
  }
}

function pollUntilDone(kbId: string) {
  stopPolling();
  pollTimer = setTimeout(async function poll() {
    try {
      const { data } = await kbApi.getKnowledgeBase(kbId);
      const allDone = !data.documents?.some(
        (d: any) => d.status === "pending" || d.status === "processing"
      );
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
    } catch {
      // stop on error
    }
  }, 3000);
}

function resetForm() {
  form.name = "";
  form.description = "";
  form.embedding_model = "text-embedding-v4";
  form.embedding_api_key = "";
  form.embedding_base_url = "https://dashscope.aliyuncs.com/compatible-mode/v1";
}

function openCreateDialog() {
  resetForm();
  dialogVisible.value = true;
}

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
    name: form.name,
    description: form.description || undefined,
    embedding_model: form.embedding_model,
    embedding_api_key: form.embedding_api_key || undefined,
    embedding_base_url: form.embedding_base_url || undefined,
  });
  creating.value = false;
  if (result) {
    dialogVisible.value = false;
  }
}

async function handleUpdateConfig() {
  if (!kbStore.currentKB) return;
  updating.value = true;
  const params: Record<string, string | undefined> = {
    embedding_model: editForm.embedding_model,
    embedding_base_url: editForm.embedding_base_url || undefined,
  };
  if (editForm.embedding_api_key) {
    params.embedding_api_key = editForm.embedding_api_key;
  }
  const result = await kbStore.updateKnowledgeBase(kbStore.currentKB.id, params);
  updating.value = false;
  if (result) {
    editDialogVisible.value = false;
  }
}

async function handleView(row: any) {
  await kbStore.selectKnowledgeBase(row.id);
  drawerVisible.value = true;
}

async function handleDelete(id: string) {
  try {
    await ElMessageBox.confirm("确定删除该知识库？删除后无法恢复。", "警告", {
      confirmButtonText: "确定",
      cancelButtonText: "取消",
      type: "warning",
    });
    await kbStore.deleteKnowledgeBase(id);
  } catch {
    // cancelled
  }
}

async function handleFileChange(file: any) {
  if (!kbStore.currentKB) return;
  await kbStore.uploadDocument(kbStore.currentKB.id, file.raw);
  pollUntilDone(kbStore.currentKB.id);
}

async function handleDeleteDocument(docId: string) {
  if (!kbStore.currentKB) return;
  try {
    await ElMessageBox.confirm("确定删除该文档？", "警告", {
      confirmButtonText: "确定",
      cancelButtonText: "取消",
      type: "warning",
    });
    await kbStore.deleteDocument(kbStore.currentKB.id, docId);
  } catch {
    // cancelled
  }
}

function statusType(status: string) {
  if (status === "completed") return "success";
  if (status === "failed") return "danger";
  return "warning";
}

function statusLabel(status: string) {
  const map: Record<string, string> = {
    pending: "等待中",
    processing: "处理中",
    completed: "已完成",
    failed: "失败",
  };
  return map[status] || status;
}
</script>

<style scoped>
.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}

.page-header h3 {
  margin: 0;
}
</style>
