import { defineStore } from "pinia";
import { ref } from "vue";
import { ElMessage } from "element-plus";
import * as skillApi from "@/api/skill";
import type { Skill } from "@/types";

export const useSkillStore = defineStore("skill", () => {
  const systemSkills = ref<Skill[]>([]);
  const userSkills = ref<Skill[]>([]);
  const loading = ref(false);

  async function fetchSystemSkills() {
    loading.value = true;
    try {
      const { data } = await skillApi.listSystemSkills();
      systemSkills.value = data;
    } catch (e: any) {
      ElMessage.error(e.response?.data?.detail || "获取系统技能列表失败");
    } finally {
      loading.value = false;
    }
  }

  async function fetchUserSkills() {
    loading.value = true;
    try {
      const { data } = await skillApi.listUserSkills();
      userSkills.value = data;
    } catch (e: any) {
      ElMessage.error(e.response?.data?.detail || "获取用户技能列表失败");
    } finally {
      loading.value = false;
    }
  }

  async function createSkill(params: {
    name: string;
    description?: string;
    skill_type?: string;
    content?: string;
    version?: string;
  }) {
    try {
      const { data } = await skillApi.createSkill(params);
      userSkills.value.unshift(data);
      return data as Skill;
    } catch (e: any) {
      ElMessage.error(e.response?.data?.detail || "创建技能失败");
      return null;
    }
  }

  async function updateSkill(id: string, params: {
    name?: string;
    description?: string;
    skill_type?: string;
    content?: string;
    version?: string;
    is_active?: boolean;
  }) {
    try {
      const { data } = await skillApi.updateSkill(id, params);
      const idx = userSkills.value.findIndex((s) => s.id === id);
      if (idx !== -1) {
        userSkills.value[idx] = { ...userSkills.value[idx], ...data };
      }
      return data as Skill;
    } catch (e: any) {
      ElMessage.error(e.response?.data?.detail || "更新技能失败");
      return null;
    }
  }

  async function deleteSkill(id: string) {
    try {
      await skillApi.deleteSkill(id);
      userSkills.value = userSkills.value.filter((s) => s.id !== id);
      ElMessage.success("技能已删除");
    } catch (e: any) {
      ElMessage.error(e.response?.data?.detail || "删除技能失败");
    }
  }

  async function toggleSkill(id: string, isActive: boolean, isSystem: boolean) {
    try {
      const { data } = await skillApi.toggleSkill(id, isActive);
      if (isSystem) {
        const idx = systemSkills.value.findIndex((s) => s.id === id);
        if (idx !== -1) {
          systemSkills.value[idx] = { ...systemSkills.value[idx], ...data };
        }
      } else {
        const idx = userSkills.value.findIndex((s) => s.id === id);
        if (idx !== -1) {
          userSkills.value[idx] = { ...userSkills.value[idx], ...data };
        }
      }
      ElMessage.success(isActive ? "技能已启用" : "技能已禁用");
      return data as Skill;
    } catch (e: any) {
      ElMessage.error(e.response?.data?.detail || "更新技能状态失败");
      return null;
    }
  }

  return {
    systemSkills,
    userSkills,
    loading,
    fetchSystemSkills,
    fetchUserSkills,
    createSkill,
    updateSkill,
    deleteSkill,
    toggleSkill,
  };
});
