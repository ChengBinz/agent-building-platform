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

          <!-- 模型列表 -->
          <div class="model-list">
            <div v-for="model in provider.models" :key="model.name" class="model-item">
              <span class="model-name">{{ model.name }}</span>
              <el-tag size="small" :type="model.available ? '' : 'danger'">
                {{ model.available ? '可用' : '不可用' }}
              </el-tag>
            </div>
          </div>

          <!-- API Key 配置区 -->
          <div class="apikey-section" v-if="providerKey(provider.name) !== 'ollama'">
            <el-divider />
            <div class="apikey-form">
              <el-input
                v-model="keyForms[providerKey(provider.name)].api_key"
                :placeholder="savedKeys[providerKey(provider.name)] ? '已保存 (点击清除可删除)' : '输入 API Key'"
                type="password"
                show-password
                size="small"
                :disabled="!!savedKeys[providerKey(provider.name)]"
              />
              <el-input
                v-model="keyForms[providerKey(provider.name)].base_url"
                placeholder="Base URL (可选)"
                size="small"
                style="margin-top: 6px"
              />
              <div class="apikey-actions">
                <el-button
                  v-if="!savedKeys[providerKey(provider.name)]"
                  type="primary"
                  size="small"
                  :loading="saving[providerKey(provider.name)]"
                  @click="handleSaveKey(provider.name)"
                >
                  保存
                </el-button>
                <el-button
                  v-else
                  type="danger"
                  size="small"
                  :loading="saving[providerKey(provider.name)]"
                  @click="handleClearKey(provider.name)"
                >
                  清除
                </el-button>
              </div>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted } from "vue";
import { ElMessage } from "element-plus";
import { getModels, listApiKeys, saveApiKey, deleteApiKey } from "@/api/admin";
import type { ProviderInfo, ApiKeyInfo } from "@/types";

const providers = ref<ProviderInfo[]>([]);
const userKeys = ref<ApiKeyInfo[]>([]);
const saving = reactive<Record<string, boolean>>({});

// provider display name → key mapping
const KEY_MAP: Record<string, string> = {
  OpenAI: "openai",
  Anthropic: "anthropic",
  DeepSeek: "deepseek",
  "阿里百炼": "dashscope",
  Ollama: "ollama",
  Embedding: "embedding",
};

function providerKey(name: string): string {
  return KEY_MAP[name] || name.toLowerCase();
}

// saved key per provider key
const savedKeys = computed(() => {
  const map: Record<string, ApiKeyInfo> = {};
  for (const k of userKeys.value) {
    map[k.provider] = k;
  }
  return map;
});

// form state per provider
const keyForms = reactive<Record<string, { api_key: string; base_url: string }>>({});
// initialize form entries
for (const key of Object.values(KEY_MAP)) {
  keyForms[key] = { api_key: "", base_url: "" };
}

onMounted(async () => {
  try {
    const [modelRes, keyRes] = await Promise.all([getModels(), listApiKeys()]);
    providers.value = modelRes.data;
    userKeys.value = keyRes.data;
    // pre-fill base_url from saved keys
    for (const k of keyRes.data) {
      if (keyForms[k.provider]) {
        keyForms[k.provider].base_url = k.base_url || "";
      }
    }
  } catch {
    // ignore
  }
});

async function handleSaveKey(displayName: string) {
  const key = providerKey(displayName);
  const form = keyForms[key];
  if (!form.api_key.trim()) {
    ElMessage.warning("请输入 API Key");
    return;
  }
  saving[key] = true;
  try {
    const { data } = await saveApiKey({
      provider: key,
      api_key: form.api_key,
      base_url: form.base_url || undefined,
    });
    // refresh
    const keys = await listApiKeys();
    userKeys.value = keys.data;
    const models = await getModels();
    providers.value = models.data;
    form.api_key = "";
    ElMessage.success("API Key 已保存");
  } catch (e: any) {
    ElMessage.error(e.response?.data?.detail || "保存失败");
  } finally {
    saving[key] = false;
  }
}

async function handleClearKey(displayName: string) {
  const key = providerKey(displayName);
  const saved = savedKeys.value[key];
  if (!saved) return;
  saving[key] = true;
  try {
    await deleteApiKey(saved.id);
    const keys = await listApiKeys();
    userKeys.value = keys.data;
    const models = await getModels();
    providers.value = models.data;
    keyForms[key].api_key = "";
    keyForms[key].base_url = "";
    ElMessage.success("API Key 已清除");
  } catch (e: any) {
    ElMessage.error(e.response?.data?.detail || "清除失败");
  } finally {
    saving[key] = false;
  }
}
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
.apikey-section {
  margin-top: 4px;
}
.apikey-form {
  display: flex;
  flex-direction: column;
}
.apikey-actions {
  margin-top: 6px;
  display: flex;
  justify-content: flex-end;
}
</style>
