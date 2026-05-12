import { createRouter, createWebHistory } from "vue-router";
import { useAuthStore } from "@/stores/auth";
import { ElMessage } from "element-plus";

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
          path: "/mcp",
          name: "MCP",
          component: () => import("@/views/McpView.vue"),
        },
        {
          path: "/skill",
          name: "Skill",
          component: () => import("@/views/SkillView.vue"),
        },
        {
          path: "/admin/users",
          name: "AdminUsers",
          component: () => import("@/views/admin/AdminUsers.vue"),
          meta: { requiresAdmin: true },
        },
        {
          path: "/admin/settings",
          name: "AdminSettings",
          component: () => import("@/views/admin/AdminSettings.vue"),
          meta: { requiresAdmin: true },
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
    if (auth.isAuthenticated) {
      return auth.isAdmin ? "/admin/users" : "/chat";
    }
    return true;
  }

  if (!auth.isAuthenticated) return "/login";

  // Admin routes require superuser
  if (to.meta.requiresAdmin && !auth.isAdmin) {
    ElMessage.warning("无权访问管理页面");
    return "/chat";
  }

  // Admin users can only access admin pages
  if (auth.isAdmin && !to.meta.requiresAdmin) {
    return "/admin/users";
  }

  return true;
});

export default router;
