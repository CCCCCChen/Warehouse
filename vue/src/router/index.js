import { createRouter, createWebHistory } from 'vue-router';
import { defineAsyncComponent } from 'vue';
import { getAuthToken } from '@/auth/storage';
// import App from '../App.vue';

const routes = [
  { path: '/', redirect: '/warehouse' },
  { path: '/init', component: () => import('@/components/InitPage.vue')},
  { path: '/random_numbers', component: () => import('@/components/RandomNumbers.vue')},
  { path: '/warehouse', component: () => import('@/components/WarehousePage.vue')},
  { path: '/warehouse/items', component: () => import('@/components/ItemsPage.vue')},
  { path: '/warehouse/user', component: () => import('@/components/WarehouseUserPage.vue')},
  { path: '/warehouse/manage', component: () => import('@/components/WarehouseManagePage.vue')},
  { path: '/warehouse/notice', component: defineAsyncComponent(() => import('@/components/WarehouseNotice.vue'))},
  { path: '/warehouse/llm-test', component: () => import('@/components/LlmTestPage.vue')},
  { path: '/warehouse/settings', component: () => import('@/components/SettingsPage.vue')},
  /* 
  { path: '/warehouse/search', component: defineAsyncComponent(() =>  import('@/components/Search.vue'))},
  { path: '/warehouse/data', component: defineAsyncComponent(() => import('@/components/Data.vue'))},
  { path: '/warehouse/map', component: defineAsyncComponent(() => import('@/components/Map.vue'))},
  { path: '/warehouse/setting', component: defineAsyncComponent(() => import('@/components/Setting.vue'))},
   */
];

const router = createRouter({
  history: createWebHistory(),
  routes,
});

router.beforeEach((to) => {
  if (to.path.startsWith('/warehouse')) {
    const token = getAuthToken();
    if (!token) {
      return { path: '/init' };
    }
  }
  return true;
});

export default router;
