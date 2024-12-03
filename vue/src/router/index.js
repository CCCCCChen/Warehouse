import { createRouter, createWebHistory } from 'vue-router';
import { defineAsyncComponent } from 'vue';
// import App from '../App.vue';
import HelloWorld from '@/components/HelloWorld.vue';

const routes = [
  { path: '/', component: HelloWorld },
  { path: '/random_numbers', component: () => import('@/components/RandomNumbers.vue')},
  { path: '/warehouse', component: () => import('@/components/WarehousePage.vue')},
  { path: '/warehouse/notice', component: defineAsyncComponent(() => import('@/components/WarehouseNotice.vue'))},
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

export default router;