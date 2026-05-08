<template>
  <div class="knowledge-view">
    <div class="page-header">
      <h3>知识库管理</h3>
      <el-button type="primary" @click="dialogVisible = true" :icon="Plus">
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
    <el-dialog v-model="dialogVisible" title="新建知识库" width="500px">
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
        <el-form-item label="嵌入模型">
          <el-select v-model="form.embedding_model" style="width: 100%">
            <el-option label="text-embedding-3-small" value="text-embedding-3-small" />
            <el-option label="text-embedding-3-large" value="text-embedding-3-large" />
          </el-select>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handleCreate" :loading="creating">确定</el-button>
      </template>
    </el-dialog>

    <!-- Detail Drawer -->
    <el-drawer v-model="drawerVisible" title="知识库详情" size="500px">
      <template v-if="kbStore.currentKB">
        <el-descriptions :column="1" border>
          <el-descriptions-item label="名称">{{ kbStore.currentKB.name }}</el-descriptions-item>
          <el-descriptions-item label="描述">{{ kbStore.currentKB.description || '-' }}</el-descriptions-item>
          <el-descriptions-item label="嵌入模型">{{ kbStore.currentKB.embedding_model }}</el-descriptions-item>
          <el-descriptions-item label="分块数">{{ kbStore.currentKB.chunk_count }}</el-descriptions-item>
          <el-descriptions-item label="文档数">{{ kbStore.currentKB.document_count }}</el-descriptions-item>
          <el-descriptions-item label="创建时间">{{ formatDateTime(kbStore.currentKB.created_at) }}</el-descriptions-item>
        </el-descriptions>

        <h4 style="margin-top: 24px">文档列表</h4>
        <el-table :data="kbStore.currentKB.documents || []" size="small" style="margin-top: 12px">
          <el-table-column prop="filename" label="文件名" min-width="150" />
          <el-table-column prop="file_type" label="类型" width="80" />
          <el-table-column prop="status" label="状态" width="90">
            <template #default="{ row }">
              <el-tag :type="row.status === 'completed' ? 'success' : 'warning'" size="small">
                {{ row.status }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="chunk_count" label="分块数" width="80" />
        </el-table>
        <el-empty v-if="(kbStore.currentKB.documents || []).length === 0" description="暂无文档" />
      </template>
    </el-drawer>
  </div>
</template>

<script setup lang="ts">
import { reactive, ref, onMounted } from "vue";
import { ElMessageBox } from "element-plus";
import { Plus } from "@element-plus/icons-vue";
import { useKnowledgeStore } from "@/stores/knowledge";
import { formatDateTime } from "@/utils/format";

const kbStore = useKnowledgeStore();
const dialogVisible = ref(false);
const drawerVisible = ref(false);
const creating = ref(false);

const form = reactive({
  name: "",
  description: "",
  embedding_model: "text-embedding-3-small",
});

onMounted(() => {
  kbStore.fetchKnowledgeBases();
});

async function handleCreate() {
  if (!form.name.trim()) return;
  creating.value = true;
  const result = await kbStore.createKnowledgeBase({
    name: form.name,
    description: form.description || undefined,
    embedding_model: form.embedding_model,
  });
  creating.value = false;
  if (result) {
    dialogVisible.value = false;
    form.name = "";
    form.description = "";
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
