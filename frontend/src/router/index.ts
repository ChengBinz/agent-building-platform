import { createRouter, createWebHistory } from "vue-router";

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
    },
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
});

export default router;
