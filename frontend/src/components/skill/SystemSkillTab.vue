<template>
  <div class="system-skill-tab">
    <div class="tab-header">
      <el-input
        v-model="searchText"
        placeholder="搜索系统技能"
        prefix-icon="Search"
        style="width: 300px"
        clearable
      />
    </div>

    <el-table :data="filteredSkills" v-loading="loading" stripe style="width: 100%">
      <el-table-column prop="name" label="技能名称" min-width="150" />
      <el-table-column prop="description" label="描述" min-width="250" show-overflow-tooltip />
      <el-table-column prop="skill_type" label="类型" width="100">
        <template #default="{ row }">
          <el-tag size="small">{{ row.skill_type }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="version" label="版本" width="80" align="center" />
      <el-table-column prop="is_active" label="状态" width="100" align="center">
        <template #default="{ row }">
          <el-switch
            v-model="row.is_active"
            @change="handleToggleActive(row)"
            size="small"
          />
        </template>
      </el-table-column>
      <el-table-column label="操作" width="80" align="center">
        <template #default="{ row }">
          <el-button type="primary" link size="small" @click="showDetail(row)">
            详情
          </el-button>
        </template>
      </el-table-column>
    </el-table>

    <!-- 技能详情对话框 -->
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
import { useSkillStore } from "@/stores/skill";
import type { Skill } from "@/types";

const skillStore = useSkillStore();
const loading = computed(() => skillStore.loading);
const skills = computed(() => skillStore.systemSkills);

const searchText = ref("");
const detailVisible = ref(false);
const selectedSkill = ref<Skill | null>(null);

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
  skillStore.fetchSystemSkills();
});

async function handleToggleActive(skill: Skill) {
  await skillStore.toggleSkill(skill.id, skill.is_active, true);
}

function showDetail(skill: Skill) {
  selectedSkill.value = skill;
  detailVisible.value = true;
}
</script>

<style scoped>
.system-skill-tab {
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
