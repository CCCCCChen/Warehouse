<template>
  <div class="dash">
    <div class="title">家庭仓库概览</div>

    <div v-if="loading" class="muted">加载中...</div>
    <div v-else class="cards">
      <div class="card">
        <div class="label">总物品</div>
        <div class="value">{{ items.length }}</div>
      </div>
      <div class="card warn">
        <div class="label">低库存</div>
        <div class="value">{{ lowStockCount }}</div>
      </div>
      <div class="card danger">
        <div class="label">临期(30天)</div>
        <div class="value">{{ expiringSoonCount }}</div>
      </div>
    </div>

    <div v-if="!loading" class="quick">
      <router-link class="btn" to="/warehouse/items">管理物品</router-link>
      <router-link class="btn ghost" to="/warehouse/manage">快速录入</router-link>
      <router-link class="btn ghost" to="/warehouse/notice">公告</router-link>
    </div>
  </div>
</template>

<script>
import { api } from '@/api/http';

export default {
  name: 'DashboardSummary',
  data() {
    return {
      loading: false,
      items: [],
    };
  },
  computed: {
    lowStockCount() {
      return this.items.filter(it => (it.min_quantity ?? 0) > 0 && (it.quantity ?? 0) <= (it.min_quantity ?? 0)).length;
    },
    expiringSoonCount() {
      const now = new Date();
      return this.items.filter(it => {
        if (!it.expiry_date) return false;
        const d = new Date(it.expiry_date);
        if (Number.isNaN(d.getTime())) return false;
        const diff = d.getTime() - now.getTime();
        const days = diff / (1000 * 60 * 60 * 24);
        return days >= 0 && days <= 30;
      }).length;
    },
  },
  created() {
    this.fetchItems();
  },
  methods: {
    async fetchItems() {
      this.loading = true;
      try {
        const res = await api.get('/api/items');
        this.items = res.data;
      } catch (e) {
        console.error('Failed to fetch items for dashboard:', e);
      } finally {
        this.loading = false;
      }
    },
  },
};
</script>

<style scoped>
.dash {
  color: #111827;
}

.title {
  font-weight: 900;
  font-size: 18px;
  margin-bottom: 10px;
}

.cards {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 10px;
}

.card {
  background: rgba(255, 255, 255, 0.7);
  border-radius: 10px;
  padding: 10px;
}

.card.warn {
  background: rgba(255, 193, 7, 0.20);
}

.card.danger {
  background: rgba(176, 0, 32, 0.14);
}

.label {
  font-size: 12px;
  color: rgba(0, 0, 0, 0.65);
}

.value {
  font-size: 22px;
  font-weight: 900;
  margin-top: 2px;
}

.quick {
  margin-top: 12px;
  display: flex;
  gap: 10px;
  flex-wrap: wrap;
}

.btn {
  display: inline-block;
  padding: 10px 12px;
  border-radius: 10px;
  background: #1f6feb;
  color: white;
  text-decoration: none;
  font-weight: 700;
}

.btn.ghost {
  background: #111827;
}

.muted {
  color: rgba(0, 0, 0, 0.65);
}

@media (max-width: 900px) {
  .cards {
    grid-template-columns: 1fr;
  }
}
</style>

