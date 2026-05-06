<template>
  <div class="monitor-view">
    <div class="page-header">
      <h3>监控面板</h3>
    </div>

    <!-- Summary Cards -->
    <el-row :gutter="16" style="margin-bottom: 16px">
      <el-col :span="6" v-for="card in summaryCards" :key="card.label">
        <el-card class="stat-card">
          <div class="stat-label">{{ card.label }}</div>
          <div class="stat-value">{{ card.value }}</div>
        </el-card>
      </el-col>
    </el-row>

    <!-- Usage by Model -->
    <el-card>
      <template #header>
        <span>各模型用量</span>
      </template>
      <el-table :data="usageByModel" v-loading="loading" stripe>
        <el-table-column prop="model_name" label="模型" min-width="200" />
        <el-table-column prop="request_count" label="请求次数" width="120" align="right" />
        <el-table-column prop="total_tokens" label="总 Token 数" width="150" align="right">
          <template #default="{ row }">
            {{ formatNumber(row.total_tokens) }}
          </template>
        </el-table-column>
      </el-table>
      <el-empty v-if="!loading && usageByModel.length === 0" description="暂无用量数据" />
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from "vue";
import { getUsageSummary, getUsageByModel } from "@/api/admin";
import { formatNumber } from "@/utils/format";
import type { UsageSummary, UsageByModel } from "@/types";

const loading = ref(false);
const summary = ref<UsageSummary | null>(null);
const usageByModel = ref<UsageByModel[]>([]);

const summaryCards = ref([
  { label: "总对话数", value: 0 },
  { label: "总消息数", value: 0 },
  { label: "总 Token", value: 0 },
  { label: "活跃用户", value: 0 },
]);

onMounted(async () => {
  loading.value = true;
  try {
    const [s, m] = await Promise.all([getUsageSummary(), getUsageByModel()]);
    summary.value = s.data;
    usageByModel.value = m.data;

    summaryCards.value = [
      { label: "总对话数", value: s.data.total_conversations },
      { label: "总消息数", value: s.data.total_messages },
      { label: "总 Token", value: formatNumber(s.data.total_tokens) },
      { label: "活跃用户", value: s.data.active_users },
    ];
  } catch {
    // fallback
  } finally {
    loading.value = false;
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
</style>
