<template>
  <div class="user-skill-tab">
    <div class="tab-header">
      <el-input
        v-model="searchText"
        placeholder="搜索自定义技能"
        prefix-icon="Search"
        style="width: 300px"
        clearable
      />
      <el-button type="primary" @click="openDialog()">
        <el-icon><Plus /></el-icon>
        新增技能
      </el-button>
    </div>

    <el-table :data="filteredSkills" v-loading="loading" stripe style="width: 100%">
      <el-table-column prop="name" label="技能名称" min-width="150" />
      <el-table-column prop="description" label="描述" min-width="200" show-overflow-tooltip />
      <el-table-column prop="skill_type" label="类型" width="100">
        <template #default="{ row }">
          <el-tag size="small">{{ row.skill_type }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="version" label="版本" width="80" align="center" />
      <el-table-column prop="is_active" label="状态" width="80" align="center">
        <template #default="{ row }">
          <el-switch
            v-model="row.is_active"
            @change="handleToggleActive(row)"
            size="small"
          />
        </template>
      </el-table-column>
      <el-table-column label="操作" width="200" align="center">
        <template #default="{ row }">
          <el-button type="primary" link size="small" @click="showDetail(row)">
            详情
          </el-button>
          <el-button type="primary" link size="small" @click="openDialog(row)">
            编辑
          </el-button>
          <el-popconfirm title="确定删除该技能？" @confirm="handleDelete(row)">
            <template #reference>
              <el-button type="danger" link size="small">删除</el-button>
            </template>
          </el-popconfirm>
        </template>
      </el-table-column>
    </el-table>

    <!-- 新增/编辑对话框 -->
    <el-dialog
      v-model="dialogVisible"
      :title="editingSkill ? '编辑技能' : '新增技能'"
      width="700px"
      destroy-on-close
    >
      <el-form :model="form" label-width="100px">
        <el-form-item label="技能名称" required>
          <el-input v-model="form.name" placeholder="输入技能名称" />
        </el-form-item>
        <el-form-item label="描述">
          <el-input v-model="form.description" type="textarea" :rows="2" placeholder="输入技能描述" />
        </el-form-item>
        <el-form-item label="技能类型">
          <el-select v-model="form.skill_type" style="width: 100%">
            <el-option label="Prompt 模板" value="prompt" />
            <el-option label="任务工作流" value="workflow" />
            <el-option label="技能编排" value="chain" />
          </el-select>
        </el-form-item>
        <el-form-item label="版本">
          <el-input v-model="form.version" placeholder="1.0.0" />
        </el-form-item>
        <el-form-item label="技能内容">
          <el-input
            v-model="form.content"
            type="textarea"
            :rows="8"
            placeholder="输入 Prompt 模板或工作流定义"
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handleSave" :loading="saving">保存</el-button>
      </template>
    </el-dialog>

    <!-- 详情对话框 -->
    <el-dialog
      v-model="detailVisible"
      :title="selectedSkill?.name || '技能详情'"
      width="700px"
      destroy-on-close
    >
      <div v-if="selectedSkill" class="skill-detail">
        <el-descriptions :column="2" border>
          <el-descriptions-item label="技能名称">{{ selectedSkill.name }}</el-descriptions-item>
          <el-descriptions-item label="类型">
            <el-tag size="small">{{ selectedSkill.skill_type }}</el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="版本">{{ selectedSkill.version }}</el-descriptions-item>
          <el-descriptions-item label="状态">
            <el-tag :type="selectedSkill.is_active ? 'success' : 'danger'" size="small">
              {{ selectedSkill.is_active ? '启用' : '禁用' }}
            </el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="描述" :span="2">
            {{ selectedSkill.description || '-' }}
          </el-descriptions-item>
        </el-descriptions>
        <div v-if="selectedSkill.content" class="content-section">
          <h4>技能内容</h4>
          <pre class="content-code">{{ selectedSkill.content }}</pre>
        </div>
      </div>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from "vue";
import { Plus } from "@element-plus/icons-vue";
import { useSkillStore } from "@/stores/skill";
import type { Skill } from "@/types";

const skillStore = useSkillStore();
const loading = computed(() => skillStore.loading);
const skills = computed(() => skillStore.userSkills);

const searchText = ref("");
const dialogVisible = ref(false);
const detailVisible = ref(false);
const editingSkill = ref<Skill | null>(null);
const selectedSkill = ref<Skill | null>(null);
const saving = ref(false);

const form = ref({
  name: "",
  description: "",
  skill_type: "prompt",
  content: "",
  version: "1.0.0",
});

const filteredSkills = computed(() => {
  if (!searchText.value) return skills.value;
  const keyword = searchText.value.toLowerCase();
  return skills.value.filter(
    (s) =>
      s.name.toLowerCase().includes(keyword) ||
      (s.description && s.description.toLowerCase().includes(keyword))
  );
});

onMounted(() => {
  skillStore.fetchUserSkills();
});

function openDialog(skill?: Skill) {
  editingSkill.value = skill || null;
  if (skill) {
    form.value = {
      name: skill.name,
      description: skill.description || "",
      skill_type: skill.skill_type,
      content: skill.content || "",
      version: skill.version,
    };
  } else {
    form.value = {
      name: "",
      description: "",
      skill_type: "prompt",
      content: "",
      version: "1.0.0",
    };
  }
  dialogVisible.value = true;
}

async function handleSave() {
  if (!form.value.name) {
    return;
  }
  saving.value = true;
  try {
    if (editingSkill.value) {
      await skillStore.updateSkill(editingSkill.value.id, form.value);
    } else {
      await skillStore.createSkill(form.value);
    }
    dialogVisible.value = false;
  } finally {
    saving.value = false;
  }
}

async function handleDelete(skill: Skill) {
  await skillStore.deleteSkill(skill.id);
}

async function handleToggleActive(skill: Skill) {
  await skillStore.toggleSkill(skill.id, skill.is_active, false);
}

function showDetail(skill: Skill) {
  selectedSkill.value = skill;
  detailVisible.value = true;
}
</script>

<style scoped>
.user-skill-tab {
  padding: 16px 0;
}

.tab-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}

.skill-detail {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.content-section h4 {
  margin: 0 0 8px 0;
  font-size: 14px;
  color: #303133;
}

.content-code {
  background: #f5f7fa;
  padding: 12px;
  border-radius: 6px;
  font-size: 13px;
  overflow-x: auto;
  white-space: pre-wrap;
  word-break: break-word;
  margin: 0;
  max-height: 400px;
  overflow-y: auto;
}
</style>
