<template>
  <div class="models-view">
    <div class="page-header">
      <h3>模型配置</h3>
    </div>

    <el-row :gutter="16">
      <el-col :span="12" v-for="provider in providers" :key="provider.name" style="margin-bottom: 16px">
        <el-card>
          <template #header>
            <div class="provider-header">
              <span class="provider-name">{{ provider.name }}</span>
              <el-tag :type="provider.configured ? 'success' : 'info'" size="small">
                {{ provider.configured ? '已配置' : '未配置' }}
              </el-tag>
            </div>
          </template>
          <div class="model-list">
            <div v-for="model in provider.models" :key="model.name" class="model-item">
              <div class="model-name">{{ model.name }}</div>
              <el-tag size="small" :type="model.available ? '' : 'danger'">
                {{ model.available ? '可用' : '不可用' }}
              </el-tag>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <div class="env-notice" v-if="unconfiguredProviders.length > 0">
      <el-alert
        title="提示"
        type="warning"
        :closable="false"
        show-icon
      >
        <template #default>
          以下服务商未配置 API Key，请在 <code>.env</code> 文件中设置对应的环境变量：
          <span v-for="p in unconfiguredProviders" :key="p.name" style="margin-left: 8px">
            <el-tag size="small">{{ p.name === 'OpenAI' ? 'OPENAI_API_KEY' : 'ANTHROPIC_API_KEY' }}</el-tag>
          </span>
        </template>
      </el-alert>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from "vue";
import { getModels } from "@/api/admin";
import type { ProviderInfo } from "@/types";

const providers = ref<ProviderInfo[]>([]);

const unconfiguredProviders = computed(() =>
  providers.value.filter((p) => !p.configured)
);

onMounted(async () => {
  try {
    const { data } = await getModels();
    providers.value = data;
  } catch {
    // fallback placeholder
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

.provider-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.provider-name {
  font-weight: 600;
  font-size: 16px;
}

.model-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.model-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 8px 0;
  border-bottom: 1px solid #f0f2f5;
}

.model-item:last-child {
  border-bottom: none;
}

.model-name {
  font-family: monospace;
  font-size: 13px;
}

.env-notice {
  margin-top: 16px;
}
</style>
