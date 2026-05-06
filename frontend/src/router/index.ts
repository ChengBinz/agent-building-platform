import { createRouter, createWebHistory } from "vue-router";
import { useAuthStore } from "@/stores/auth";

const router = createRouter({
  history: createWebHistory(),
  routes: [
    {
      path: "/",
      redirect: "/chat",
    },
    {
      path: "/login",
      name: "Login",
      component: () => import("@/views/Login.vue"),
      meta: { guest: true },
    },
    {
      path: "/",
      component: () => import("@/components/layout/AppLayout.vue"),
      children: [
        {
          path: "/chat",
          name: "Chat",
          component: () => import("@/views/ChatView.vue"),
        },
        {
          path: "/knowledge",
          name: "Knowledge",
          component: () => import("@/views/KnowledgeView.vue"),
        },
        {
          path: "/models",
          name: "Models",
          component: () => import("@/views/ModelsView.vue"),
        },
        {
          path: "/monitoring",
          name: "Monitoring",
          component: () => import("@/views/MonitorView.vue"),
        },
        {
          path: "/admin/users",
          name: "AdminUsers",
          component: () => import("@/views/admin/AdminUsers.vue"),
        },
        {
          path: "/admin/settings",
          name: "AdminSettings",
          component: () => import("@/views/admin/AdminSettings.vue"),
        },
      ],
    },
  ],
});

router.beforeEach(async (to) => {
  const auth = useAuthStore();

  // On first visit, try to restore session if token exists
  if (!auth.isAuthenticated) {
    const ok = await auth.refreshAccessToken();
    if (ok) {
      await auth.fetchUser();
    }
  }

  if (to.meta.guest) {
    // Already logged in, redirect to chat
    if (auth.isAuthenticated) return "/chat";
    return true;
  }

  if (!auth.isAuthenticated) return "/login";
  return true;
});

export default router;
