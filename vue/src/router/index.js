import { createRouter, createWebHistory } from 'vue-router';
import App from '@/components/App.vue';

const routes = [
  { path: '/', component: App },
  { path: '/random_numbers', component: () => import('@/components/RandomNumbers.vue')},
  { path: '/warehouse', component: () => import('@/components/WarehousePage.vue') },
];

const router = createRouter({
  history: createWebHistory(),
  routes,
});

export default router;