<template>
  <el-dialog
    :model-value="visible"
    @update:model-value="$emit('update:visible', $event)"
    :title="agent ? '编辑智能体' : '新建智能体'"
    width="560px"
    destroy-on-close
  >
    <el-form label-width="90px" :model="form" class="agent-form">
      <el-form-item label="名称">
        <el-input v-model="form.name" placeholder="智能体名称" />
      </el-form-item>
      <el-form-item label="描述">
        <el-input v-model="form.description" type="textarea" :rows="2" placeholder="描述智能体的功能" />
      </el-form-item>
      <el-form-item label="头像URL">
        <el-input v-model="form.avatar" placeholder="可选，头像图片链接" />
      </el-form-item>
      <el-form-item label="系统提示词">
        <el-input v-model="form.system_prompt" type="textarea" :rows="4" placeholder="定义智能体的行为、角色和能力" />
      </el-form-item>
      <el-form-item label="默认模型">
        <el-select v-model="form.modelSelect" placeholder="选择模型" style="width: 100%">
          <el-option-group v-for="p in providers" :key="p.key" :label="p.name">
            <el-option
              v-for="m in p.models"
              :key="`${p.key}:${m.name}`"
              :label="`${p.name} - ${m.name}`"
              :value="`${p.key}:${m.name}`"
            />
          </el-option-group>
        </el-select>
      </el-form-item>
      <el-form-item label="知识库">
        <el-select
          v-model="form.kb_ids"
          multiple
          collapse-tags
          collapse-tags-tooltip
          placeholder="选择关联知识库（可选）"
          style="width: 100%"
        >
          <el-option v-for="kb in knowledgeBases" :key="kb.id" :label="kb.name" :value="kb.id" />
        </el-select>
      </el-form-item>
    </el-form>
    <template #footer>
      <el-button @click="$emit('update:visible', false)">取消</el-button>
      <el-button type="primary" @click="handleSave">保存</el-button>
    </template>
  </el-dialog>
</template>

<script setup lang="ts">
import { ref, watch } from "vue";
import { listKnowledgeBases } from "@/api/knowledge";
import type { Agent, KnowledgeBase, ProviderWithKey } from "@/types";

const props = defineProps<{
  visible: boolean;
  agent: Agent | null;
  providers: ProviderWithKey[];
}>();

const emit = defineEmits<{
  "update:visible": [value: boolean];
  save: [data: any];
}>();

const knowledgeBases = ref<KnowledgeBase[]>([]);
const form = ref({
  name: "",
  description: "",
  avatar: "",
  system_prompt: "",
  modelSelect: "",
  kb_ids: [] as string[],
});

watch(
  () => props.visible,
  async (val) => {
    if (!val) return;
    // Load knowledge bases
    try {
      const { data } = await listKnowledgeBases();
      knowledgeBases.value = data;
    } catch { /* ignore */ }
    // Populate form from agent
    const a = props.agent;
    if (a) {
      form.value = {
        name: a.name,
        description: a.description || "",
        avatar: a.avatar || "",
        system_prompt: a.system_prompt || "",
        modelSelect: a.provider ? `${a.provider}:${a.model_name}` : "",
        kb_ids: a.kb_ids ? [...a.kb_ids] : [],
      };
    } else {
      form.value = { name: "", description: "", avatar: "", system_prompt: "", modelSelect: "", kb_ids: [] };
    }
  },
);

function handleSave() {
  const { name, description, avatar, system_prompt, modelSelect, kb_ids } = form.value;
  const agentName = name.trim() || "新的智能体";
  let provider = "";
  let modelName = "";
  if (modelSelect) {
    const [p, m] = modelSelect.split(":");
    provider = p;
    modelName = m;
  }
  emit("save", {
    name: agentName,
    description: description || undefined,
    avatar: avatar || undefined,
    system_prompt: system_prompt || undefined,
    model_name: modelName,
    provider,
    kb_ids: kb_ids.length > 0 ? kb_ids : undefined,
  });
}
</script>

<style scoped>
.agent-form :deep(.el-form-item__label) {
  white-space: nowrap;
}
</style>
