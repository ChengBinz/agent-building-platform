<template>
  <div class="admin-settings">
    <div class="page-header">
      <h3>系统设置</h3>
    </div>

    <!-- System Stats -->
    <el-row :gutter="16" style="margin-bottom: 24px">
      <el-col :span="6" v-for="card in statCards" :key="card.label">
        <el-card class="stat-card">
          <div class="stat-label">{{ card.label }}</div>
          <div class="stat-value">{{ card.value }}</div>
        </el-card>
      </el-col>
    </el-row>

    <!-- Environment Info -->
    <el-card>
      <template #header>
        <span>系统信息</span>
      </template>
      <el-descriptions :column="2" border>
        <el-descriptions-item label="应用名称">AI Agent Platform</el-descriptions-item>
        <el-descriptions-item label="版本号">0.1.0</el-descriptions-item>
        <el-descriptions-item label="数据库">PostgreSQL 16 + pgvector</el-descriptions-item>
        <el-descriptions-item label="向量数据库">Qdrant</el-descriptions-item>
        <el-descriptions-item label="缓存">Redis (可选)</el-descriptions-item>
        <el-descriptions-item label="默认 LLM">gpt-4o-mini</el-descriptions-item>
        <el-descriptions-item label="默认嵌入模型">text-embedding-3-small</el-descriptions-item>
        <el-descriptions-item label="分块大小">{{ CHUNK_SIZE }}</el-descriptions-item>
      </el-descriptions>
    </el-card>

    <!-- Connection Status -->
    <el-card style="margin-top: 16px">
      <template #header>
        <span>服务连接状态</span>
      </template>
      <el-row :gutter="16">
        <el-col :span="8" v-for="svc in services" :key="svc.name">
          <div class="service-item">
            <span class="service-name">{{ svc.name }}</span>
            <el-tag :type="svc.ok ? 'success' : 'danger'" size="small">
              {{ svc.ok ? '正常' : '不可用' }}
            </el-tag>
          </div>
        </el-col>
      </el-row>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from "vue";
import { getSystemStats } from "@/api/admin";
import type { SystemStats } from "@/types";

const CHUNK_SIZE = 512;

const stats = ref<SystemStats | null>(null);

const statCards = ref([
  { label: "用户数", value: 0 },
  { label: "对话数", value: 0 },
  { label: "知识库数", value: 0 },
  { label: "总 Token", value: 0 },
]);

const services = ref([
  { name: "PostgreSQL", ok: true },
  { name: "Qdrant", ok: true },
  { name: "Redis", ok: true },
]);

onMounted(async () => {
  try {
    const { data } = await getSystemStats();
    stats.value = data;
    statCards.value = [
      { label: "用户数", value: data.user_count },
      { label: "对话数", value: data.conversation_count },
      { label: "知识库数", value: data.knowledge_base_count },
      { label: "总 Token", value: data.total_tokens },
    ];
  } catch {
    // fallback
  }
});
</script>

<style scoped>
.page-header {
  margin-bottom: 16px;
}

.page-header h3 {
  margin: 0;
}

.stat-card {
  text-align: center;
}

.stat-label {
  font-size: 13px;
  color: #909399;
  margin-bottom: 8px;
}

.stat-value {
  font-size: 28px;
  font-weight: bold;
  color: #303133;
}

.service-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 0;
}

.service-name {
  font-weight: 500;
}
</style>
