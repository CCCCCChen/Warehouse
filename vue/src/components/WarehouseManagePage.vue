<template>
  <div class="page">
    <h2>录入/管理</h2>
    <div class="card">
      <div v-if="loading">加载中...</div>
      <div v-else>{{ message }}</div>
    </div>

    <div class="nav">
      <router-link class="link" to="/warehouse/items">进入物品管理</router-link>
    </div>
  </div>
</template>

<script>
import { api } from '@/api/http';

export default {
  name: 'WarehouseManagePage',
  data() {
    return {
      loading: false,
      message: '',
    };
  },
  created() {
    this.fetchMessage();
  },
  methods: {
    async fetchMessage() {
      this.loading = true;
      try {
        const res = await api.get('/api/warehouse/manage');
        this.message = res.data.message || '';
      } catch (e) {
        console.error('Failed to fetch manage page message:', e);
        this.message = '无法加载录入/管理信息';
      } finally {
        this.loading = false;
      }
    },
  },
};
</script>

<style scoped>
.page {
  padding: 20px;
}

.card {
  padding: 16px;
  border-radius: 8px;
  background: rgba(255, 255, 255, 0.7);
  margin-bottom: 12px;
}

.link {
  display: inline-block;
  padding: 10px 12px;
  border-radius: 8px;
  background: #1f6feb;
  color: white;
  text-decoration: none;
}
</style>

