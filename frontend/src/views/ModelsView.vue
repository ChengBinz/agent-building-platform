<template>
  <div class="models-view">
    <div class="page-header">
      <div>
        <h3>模型配置</h3>
        <p class="hint">添加 LLM / Embedding / Rerank / 视觉 / 语音 等模型，并设置全局默认。</p>
      </div>
      <div class="page-actions">
        <el-input
          v-model="search"
          placeholder="搜索 provider"
          clearable
          size="small"
          style="width: 220px"
          :prefix-icon="Search"
        />
        <el-select v-model="filterTag" placeholder="按能力筛选" clearable size="small" style="width: 160px">
          <el-option label="全部" value="" />
          <el-option label="Chat (LLM)" value="LLM" />
          <el-option label="Embedding" value="TEXT EMBEDDING" />
          <el-option label="Rerank" value="TEXT RE-RANK" />
          <el-option label="Vision" value="IMAGE2TEXT" />
          <el-option label="Speech2Text" value="SPEECH2TEXT" />
          <el-option label="TTS" value="TTS" />
        </el-select>
        <el-button size="small" type="primary" @click="loadAll" :loading="loading">刷新</el-button>
      </div>
    </div>

    <!-- ═══════════ Added models ═══════════ -->
    <el-divider content-position="left">
      <span class="section-title">已添加模型 ({{ addedModels.length }})</span>
    </el-divider>

    <div v-if="addedModels.length === 0" class="empty">
      还没有添加任何模型，下方"待添加"区域点击「添加」开始配置。
    </div>

    <el-row :gutter="16" v-else>
      <el-col :span="12" v-for="factory in addedFactories" :key="factory" style="margin-bottom: 16px">
        <el-card shadow="hover">
          <template #header>
            <div class="factory-header">
              <span class="factory-name">{{ factory }}</span>
              <el-tag size="small" type="success">已配置</el-tag>
            </div>
          </template>

          <div class="model-list">
            <div v-for="m in modelsByFactory[factory]" :key="m.id" class="model-row">
              <div class="model-info">
                <div class="model-name-line">
                  <span class="model-name">{{ m.model_name }}</span>
                  <el-tag size="small" :type="modelTypeColor(m.model_type)" style="margin-left: 8px">
                    {{ m.model_type }}
                  </el-tag>
                  <el-tag v-if="m.is_default" size="small" type="warning" style="margin-left: 4px">默认</el-tag>
                  <el-tag v-if="m.is_tools" size="small" effect="plain" style="margin-left: 4px">tools</el-tag>
                </div>
                <div class="model-meta">
                  <span>{{ m.api_key_masked || "—" }}</span>
                  <span v-if="m.base_url" class="base-url">· {{ m.base_url }}</span>
                  <span v-if="m.max_tokens">· {{ formatTokens(m.max_tokens) }}</span>
                </div>
              </div>
              <div class="model-actions">
                <el-button
                  v-if="!m.is_default"
                  link
                  size="small"
                  type="warning"
                  @click="handleSetDefault(m)"
                >
                  设为默认
                </el-button>
                <el-button link size="small" @click="handleEdit(m)">编辑</el-button>
                <el-popconfirm title="确认删除该模型？" @confirm="handleDelete(m)">
                  <template #reference>
                    <el-button link size="small" type="danger">删除</el-button>
                  </template>
                </el-popconfirm>
              </div>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <!-- ═══════════ System defaults (inline) ═══════════ -->
    <el-divider content-position="left">
      <span class="section-title">系统默认模型</span>
    </el-divider>

    <el-card shadow="never" class="defaults-card">
      <p class="hint" style="margin-bottom: 12px">新建对话 / 知识库时，如果没有显式选择模型，将使用这里设置的默认值。</p>
      <el-row :gutter="24">
        <el-col :span="12" v-for="t in defaultTypes" :key="t.value">
          <div class="default-item">
            <span class="default-label">{{ t.label }}</span>
            <el-select
              :model-value="currentDefault(t.value)"
              placeholder="未设置"
              clearable
              style="width: 100%"
              @change="(val: string | null) => handleDefaultChange(t.value, val)"
            >
              <el-option
                v-for="m in modelsOfType(t.value)"
                :key="m.id"
                :label="`${m.factory} / ${m.model_name}`"
                :value="m.id"
              />
            </el-select>
          </div>
        </el-col>
      </el-row>
    </el-card>

    <!-- ═══════════ Available factories ═══════════ -->
    <el-divider content-position="left">
      <span class="section-title">待添加模型 ({{ filteredFactories.length }})</span>
    </el-divider>

    <el-row :gutter="16">
      <el-col :span="8" v-for="f in filteredFactories" :key="f.name" style="margin-bottom: 16px">
        <el-card shadow="hover" class="factory-card">
          <div class="factory-card-header">
            <div>
              <div class="factory-name">{{ f.name }}</div>
              <div class="factory-tags">
                <el-tag v-for="t in parseTags(f.tags)" :key="t" size="small" effect="plain" style="margin-right: 4px">
                  {{ t }}
                </el-tag>
              </div>
            </div>
            <el-tag v-if="factoryAdded(f.name)" size="small" type="success">已配置</el-tag>
          </div>
          <div class="factory-meta">
            内置模型 {{ f.llm.length }} 个{{ f.url ? " · " + f.url : "" }}
          </div>
          <div class="factory-actions">
            <el-button size="small" type="primary" @click="openAddDialog(f)">添加</el-button>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <!-- ═══════════ Add / edit model dialog ═══════════ -->
    <el-dialog
      v-model="dialogVisible"
      :title="editingId ? '编辑模型' : '添加模型：' + form.factory"
      width="560px"
      :close-on-click-modal="false"
    >
      <el-form :model="form" label-width="110px" label-position="right">
        <el-form-item label="模型类型">
          <el-select v-model="form.model_type" :disabled="!!editingId" style="width: 100%">
            <el-option
              v-for="t in availableTypes"
              :key="t.value"
              :label="t.label"
              :value="t.value"
            />
          </el-select>
        </el-form-item>

        <el-form-item label="模型名称">
          <div style="display: flex; gap: 8px; width: 100%">
            <el-select
              v-if="fetchedModels.length > 0"
              v-model="form.model_name"
              filterable
              allow-create
              default-first-option
              placeholder="从远程模型选择或自定义输入"
              style="flex: 1"
              @change="handleModelNameChange"
            >
              <el-option
                v-for="name in fetchedModels"
                :key="name"
                :label="name"
                :value="name"
              />
            </el-select>
            <el-input
              v-else
              v-model="form.model_name"
              placeholder="请输入模型名称（如 qwen-max）"
              style="flex: 1"
            />
            <el-button
              :loading="fetchingModels"
              @click="handleFetchModels"
              :disabled="!form.api_key || !form.base_url"
              title="从 API 获取可用模型列表（部分 provider 的 embedding/rerank 模型可能不在列表中，可手动输入）"
            >
              获取模型
            </el-button>
          </div>
        </el-form-item>

        <el-form-item label="API Key">
          <el-input
            v-model="form.api_key"
            type="password"
            show-password
            :placeholder="editingId ? '留空表示不修改' : '请输入 API Key'"
          />
        </el-form-item>

        <el-form-item label="Base URL">
          <el-input v-model="form.base_url" :placeholder="currentFactoryUrl || '可选，使用 provider 默认'" />
        </el-form-item>

        <el-form-item label="最大 tokens">
          <el-input-number v-model="form.max_tokens" :min="0" :step="1024" style="width: 200px" />
        </el-form-item>

        <el-form-item label="支持工具调用">
          <el-switch v-model="form.is_tools" />
        </el-form-item>
      </el-form>

      <template #footer>
        <div style="display: flex; justify-content: space-between; width: 100%">
          <el-button
            :loading="testing"
            :disabled="!form.model_name || !form.api_key || !form.base_url"
            @click="handleTestConnection"
          >
            测试连接
          </el-button>
          <div>
            <el-button @click="dialogVisible = false">取消</el-button>
            <el-button type="primary" :loading="submitting" @click="submit">确定</el-button>
          </div>
        </div>
      </template>
    </el-dialog>

  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted } from "vue";
import { ElMessage } from "element-plus";
import { Search } from "@element-plus/icons-vue";
import {
  listFactories,
  listLLMModels,
  addLLMModel,
  updateLLMModel,
  deleteLLMModel,
  getDefaultModels,
  setDefaultModel,
  fetchAvailableModels,
  testModelConnection,
} from "@/api/models";
import type {
  FactoryInfo,
  LLMModel,
  LLMModelCreate,
  DefaultModel,
} from "@/types";

const loading = ref(false);
const submitting = ref(false);
const fetchingModels = ref(false);
const testing = ref(false);
const factories = ref<FactoryInfo[]>([]);
const addedModels = ref<LLMModel[]>([]);
const defaults = ref<DefaultModel[]>([]);
const search = ref("");
const filterTag = ref("");
const fetchedModels = ref<string[]>([]);

const dialogVisible = ref(false);
const editingId = ref<string | null>(null);
const currentFactoryUrl = ref<string>("");

const allTypes = [
  { value: "chat", label: "Chat" },
  { value: "embedding", label: "Embedding" },
  { value: "rerank", label: "Rerank" },
  { value: "image2text", label: "Vision" },
  { value: "speech2text", label: "Speech2Text" },
  { value: "tts", label: "TTS" },
];

const defaultTypes = allTypes;

const form = reactive<LLMModelCreate & { max_tokens: number | undefined }>({
  factory: "",
  model_name: "",
  model_type: "chat",
  api_key: "",
  base_url: "",
  max_tokens: undefined,
  is_tools: false,
});

// ── derived state ──

const filteredFactories = computed(() => {
  return factories.value.filter((f) => {
    if (search.value && !f.name.toLowerCase().includes(search.value.toLowerCase())) return false;
    if (filterTag.value && !f.tags.includes(filterTag.value)) return false;
    return true;
  });
});

const addedFactories = computed(() => {
  const set = new Set(addedModels.value.map((m) => m.factory));
  return [...set];
});

const modelsByFactory = computed(() => {
  const map: Record<string, LLMModel[]> = {};
  for (const m of addedModels.value) {
    (map[m.factory] ||= []).push(m);
  }
  return map;
});

const currentFactoryDef = computed<FactoryInfo | undefined>(() => {
  return factories.value.find((f) => f.name === form.factory);
});

const availableTypes = computed(() => {
  const f = currentFactoryDef.value;
  if (!f) return allTypes;
  const types = new Set<string>();
  for (const m of f.llm) types.add(m.model_type);
  // If the factory has no preset models (e.g. Ollama), let user pick any type
  if (types.size === 0) return allTypes;
  // Expose all factory-supported types + always allow chat / embedding / rerank generic ones
  return allTypes.filter((t) => types.has(t.value));
});

// ── helpers ──

function parseTags(tags: string): string[] {
  return tags.split(",").map((s) => s.trim()).filter(Boolean);
}

function factoryAdded(name: string): boolean {
  return addedModels.value.some((m) => m.factory === name);
}

function modelTypeColor(t: string): "" | "success" | "info" | "warning" | "danger" {
  const map: Record<string, "" | "success" | "info" | "warning" | "danger"> = {
    chat: "",
    embedding: "success",
    rerank: "info",
    image2text: "warning",
    speech2text: "danger",
    tts: "info",
  };
  return map[t] || "";
}

function formatTokens(n: number): string {
  if (n >= 1_000_000) return `${(n / 1_000_000).toFixed(1)}M`;
  if (n >= 1_000) return `${(n / 1_000).toFixed(0)}k`;
  return String(n);
}

function resetForm() {
  form.factory = "";
  form.model_name = "";
  form.model_type = "chat";
  form.api_key = "";
  form.base_url = "";
  form.max_tokens = undefined;
  form.is_tools = false;
  editingId.value = null;
  currentFactoryUrl.value = "";
  fetchedModels.value = [];
}

function handleModelNameChange(_val: string) {
  // no-op: preset auto-fill removed
}

async function handleFetchModels() {
  if (!form.api_key || !form.base_url) {
    ElMessage.warning("请先填写 API Key 和 Base URL");
    return;
  }
  fetchingModels.value = true;
  try {
    const { data } = await fetchAvailableModels(form.api_key, form.base_url);
    fetchedModels.value = data.models;
    ElMessage.success(`获取到 ${data.models.length} 个可用模型`);
  } catch (e: any) {
    ElMessage.error(e.response?.data?.detail || "获取模型列表失败");
  } finally {
    fetchingModels.value = false;
  }
}

async function handleTestConnection() {
  if (!form.model_name || !form.api_key || !form.base_url) {
    ElMessage.warning("请填写 API Key、Base URL 和模型名称");
    return;
  }
  testing.value = true;
  try {
    const { data } = await testModelConnection(form.api_key, form.base_url, form.model_name, form.model_type);
    if (data.success) {
      ElMessage.success(`连接成功${data.reply ? "，回复: " + data.reply : ""}`);
    } else {
      ElMessage.error(data.message);
    }
  } catch (e: any) {
    ElMessage.error(e.response?.data?.detail || "测试失败");
  } finally {
    testing.value = false;
  }
}

function openAddDialog(f: FactoryInfo) {
  resetForm();
  form.factory = f.name;
  currentFactoryUrl.value = f.url || "";
  // pick first supported type
  form.model_type = availableTypes.value[0]?.value || "chat";
  // prefill base_url from factory default
  form.base_url = f.url || "";
  dialogVisible.value = true;
}

function handleEdit(m: LLMModel) {
  resetForm();
  editingId.value = m.id;
  form.factory = m.factory;
  form.model_name = m.model_name;
  form.model_type = m.model_type;
  form.api_key = "";
  form.base_url = m.base_url || "";
  form.max_tokens = m.max_tokens;
  form.is_tools = m.is_tools;
  dialogVisible.value = true;
}

async function submit() {
  if (!form.model_name.trim()) {
    ElMessage.warning("请填写模型名称");
    return;
  }
  submitting.value = true;
  try {
    if (editingId.value) {
      await updateLLMModel(editingId.value, {
        model_name: form.model_name,
        api_key: form.api_key || undefined,
        base_url: form.base_url || undefined,
        max_tokens: form.max_tokens,
        is_tools: form.is_tools,
      });
      ElMessage.success("已更新");
    } else {
      if (!form.api_key?.trim()) {
        ElMessage.warning("请填写 API Key");
        submitting.value = false;
        return;
      }
      await addLLMModel({
        factory: form.factory,
        model_name: form.model_name,
        model_type: form.model_type,
        api_key: form.api_key,
        base_url: form.base_url || undefined,
        max_tokens: form.max_tokens,
        is_tools: form.is_tools,
      });
      ElMessage.success("已添加");
    }
    dialogVisible.value = false;
    await loadAll();
  } catch (e: any) {
    ElMessage.error(e.response?.data?.detail || "操作失败");
  } finally {
    submitting.value = false;
  }
}

async function handleDelete(m: LLMModel) {
  try {
    await deleteLLMModel(m.id);
    ElMessage.success("已删除");
    await loadAll();
  } catch (e: any) {
    ElMessage.error(e.response?.data?.detail || "删除失败");
  }
}

async function handleSetDefault(m: LLMModel) {
  try {
    await setDefaultModel(m.model_type, m.id);
    ElMessage.success("已设为默认");
    await loadAll();
  } catch (e: any) {
    ElMessage.error(e.response?.data?.detail || "设置失败");
  }
}

function currentDefault(model_type: string): string | undefined {
  return defaults.value.find((d) => d.model_type === model_type)?.llm_model_id;
}

function modelsOfType(model_type: string): LLMModel[] {
  return addedModels.value.filter((m) => m.model_type === model_type);
}

async function handleDefaultChange(model_type: string, model_id: string | null) {
  if (!model_id) return; // clearing not supported server-side; ignore
  try {
    await setDefaultModel(model_type, model_id);
    await loadAll();
  } catch (e: any) {
    ElMessage.error(e.response?.data?.detail || "设置失败");
  }
}

async function loadAll() {
  loading.value = true;
  try {
    const [fRes, mRes, dRes] = await Promise.all([
      listFactories(),
      listLLMModels(),
      getDefaultModels(),
    ]);
    factories.value = fRes.data;
    addedModels.value = mRes.data;
    defaults.value = dRes.data;
  } catch (e: any) {
    ElMessage.error("加载模型列表失败");
  } finally {
    loading.value = false;
  }
}

onMounted(loadAll);
</script>

<style scoped>
.models-view {
  padding: 4px;
}
.page-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 12px;
}
.page-header h3 {
  margin: 0 0 4px;
}
.hint {
  margin: 0;
  color: #909399;
  font-size: 13px;
}
.page-actions {
  display: flex;
  gap: 8px;
  align-items: center;
}
.section-title {
  font-weight: 600;
  color: #303133;
}
.empty {
  text-align: center;
  color: #909399;
  padding: 24px;
  background: #fafafa;
  border-radius: 4px;
  margin-bottom: 12px;
}
.factory-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
.factory-name {
  font-weight: 600;
  font-size: 15px;
}
.model-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}
.model-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 8px;
  background: #fafbfc;
  border: 1px solid #eef0f3;
  border-radius: 4px;
}
.model-info {
  flex: 1;
  min-width: 0;
}
.model-name-line {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 2px;
}
.model-name {
  font-family: monospace;
  font-size: 13px;
  color: #303133;
}
.model-meta {
  margin-top: 4px;
  font-size: 12px;
  color: #909399;
}
.base-url {
  word-break: break-all;
}
.model-actions {
  display: flex;
  gap: 4px;
  flex-shrink: 0;
}
.factory-card {
  height: 100%;
}
.factory-card-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
}
.factory-tags {
  margin-top: 4px;
  font-size: 12px;
}
.factory-meta {
  margin: 8px 0;
  font-size: 12px;
  color: #909399;
}
.factory-actions {
  display: flex;
  justify-content: flex-end;
}
.defaults-card {
  margin-bottom: 8px;
}
.defaults-card :deep(.el-card__body) {
  padding: 16px 20px;
}
.default-item {
  margin-bottom: 16px;
}
.default-label {
  display: block;
  font-weight: 600;
  font-size: 15px;
  margin-bottom: 8px;
}
</style>
