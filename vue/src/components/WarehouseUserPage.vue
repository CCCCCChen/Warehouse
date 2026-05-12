<template>
  <div class="page">
    <h2>用户管理</h2>
    <div class="card">
      <div v-if="loading">加载中...</div>
      <div v-else>{{ message }}</div>
    </div>
  </div>
</template>

<script>
import { api } from '@/api/http';

export default {
  name: 'WarehouseUserPage',
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
        const res = await api.get('/api/warehouse/user');
        this.message = res.data.message || '';
      } catch (e) {
        console.error('Failed to fetch user page message:', e);
        this.message = '无法加载用户管理信息';
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
}
</style>

