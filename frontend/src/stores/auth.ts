// Auth store: login, register, logout, token management
// TODO: implement

import { defineStore } from "pinia";
import { ref } from "vue";

export const useAuthStore = defineStore("auth", () => {
  const token = ref("");
  const isAuthenticated = ref(false);

  return { token, isAuthenticated };
});
