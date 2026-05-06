import { defineStore } from "pinia";
import { ref, computed } from "vue";
import { useRouter } from "vue-router";
import apiClient from "@/api/client";
import { setToken, setRefreshToken, getRefreshToken, clearTokens } from "@/utils/storage";
import type { User } from "@/types";
import { ElMessage } from "element-plus";

export const useAuthStore = defineStore("auth", () => {
  const user = ref<User | null>(null);
  const loading = ref(false);

  const isAuthenticated = computed(() => !!user.value);

  async function login(username: string, password: string) {
    loading.value = true;
    try {
      const { data } = await apiClient.post("/auth/login", { username, password });
      setToken(data.access_token);
      setRefreshToken(data.refresh_token);
      await fetchUser();
      ElMessage.success("登录成功");
      return true;
    } catch (e: any) {
      ElMessage.error(e.response?.data?.detail || "登录失败");
      return false;
    } finally {
      loading.value = false;
    }
  }

  async function register(params: {
    username: string;
    email: string;
    password: string;
    display_name?: string;
  }) {
    loading.value = true;
    try {
      await apiClient.post("/auth/register", params);
      return await login(params.username, params.password);
    } catch (e: any) {
      ElMessage.error(e.response?.data?.detail || "注册失败");
      return false;
    } finally {
      loading.value = false;
    }
  }

  async function fetchUser() {
    try {
      const { data } = await apiClient.get("/auth/me");
      user.value = data;
    } catch {
      user.value = null;
    }
  }

  async function refreshAccessToken(): Promise<boolean> {
    const refreshToken = getRefreshToken();
    if (!refreshToken) return false;
    try {
      const { data } = await apiClient.post("/auth/refresh", { refresh_token: refreshToken });
      setToken(data.access_token);
      setRefreshToken(data.refresh_token);
      return true;
    } catch {
      return false;
    }
  }

  function logout() {
    clearTokens();
    user.value = null;
    ElMessage.success("已退出登录");
  }

  return { user, loading, isAuthenticated, login, register, fetchUser, refreshAccessToken, logout };
});
