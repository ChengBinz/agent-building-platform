<template>
  <el-drawer :model-value="visible" @update:model-value="$emit('update:visible', $event)" title="知识库详情" size="500px" @close="$emit('close')">
    <template v-if="kb">
      <el-descriptions :column="1" border>
        <el-descriptions-item label="名称">{{ kb.name }}</el-descriptions-item>
        <el-descriptions-item label="描述">{{ kb.description || '-' }}</el-descriptions-item>
        <el-descriptions-item label="嵌入模型">{{ kb.embedding_model }}</el-descriptions-item>
        <el-descriptions-item label="API Key">
          {{ kb.embedding_api_key_masked || '未配置' }}
        </el-descriptions-item>
        <el-descriptions-item label="Base URL">
          {{ kb.embedding_base_url || '默认' }}
        </el-descriptions-item>
        <el-descriptions-item label="分块数">{{ kb.chunk_count }}</el-descriptions-item>
        <el-descriptions-item label="文档数">{{ kb.document_count }}</el-descriptions-item>
        <el-descriptions-item label="创建时间">{{ formatDateTime(kb.created_at) }}</el-descriptions-item>
      </el-descriptions>

      <el-button style="margin-top: 16px" @click="$emit('editConfig')" :icon="Edit">
        编辑 Embedding 配置
      </el-button>

      <h4 style="margin: 24px 0 12px">上传文档</h4>
      <el-upload
        :auto-upload="false"
        :on-change="(f: any) => $emit('upload', f)"
        :show-file-list="false"
        accept=".txt,.md"
        drag
        v-loading="uploading"
      >
        <el-icon class="el-icon--upload"><UploadFilled /></el-icon>
        <div class="el-upload__text">拖拽文件到此处，或 <em>点击选择</em></div>
        <template #tip>
          <div class="el-upload__tip">仅支持 .txt 和 .md 文件</div>
        </template>
      </el-upload>

      <h4 style="margin: 24px 0 12px">文档列表</h4>
      <el-table :data="kb.documents || []" size="small" style="margin-top: 12px">
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
            <el-button text type="danger" size="small" @click="$emit('deleteDoc', row.id)">
              删除
            </el-button>
          </template>
        </el-table-column>
      </el-table>
      <el-empty v-if="(kb.documents || []).length === 0" description="暂无文档" />
    </template>
  </el-drawer>
</template>

<script setup lang="ts">
import { Edit, UploadFilled } from "@element-plus/icons-vue";
import { formatDateTime } from "@/utils/format";
import type { KnowledgeBase } from "@/types";

defineProps<{
  visible: boolean;
  kb: KnowledgeBase | null;
  uploading: boolean;
}>();

defineEmits<{
  "update:visible": [value: boolean];
  close: [];
  editConfig: [];
  upload: [file: any];
  deleteDoc: [docId: string];
}>();

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
