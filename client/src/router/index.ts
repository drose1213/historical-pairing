import { createRouter, createWebHistory } from "vue-router";

const router = createRouter({
  history: createWebHistory(),
  routes: [
    {
      path: "/",
      name: "home",
      component: () => import("../pages/GameStartPage.vue"),
    },
    {
      path: "/play/:gameId",
      name: "play",
      component: () => import("../pages/GamePlayPage.vue"),
      meta: { requiresAuth: true },
    },
    {
      path: "/results/:gameId",
      name: "results",
      component: () => import("../pages/GameResultsPage.vue"),
      meta: { requiresAuth: true },
    },
    {
      path: "/profile",
      name: "profile",
      component: () => import("../pages/PersonalCenterPage.vue"),
      meta: { requiresAuth: true },
    },
    {
      path: "/admin",
      name: "admin",
      component: () => import("../pages/AdminDashboardPage.vue"),
      meta: { requiresAuth: true, requiresAdmin: true },
    },
  ],
});

export default router;
