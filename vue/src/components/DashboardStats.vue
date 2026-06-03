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
        <div class="label">临期({{ expiringDays }}天)</div>
        <div class="value">{{ expiringSoonCount }}</div>
      </div>
    </div>
  </div>
</template>

<script>
import { api } from '@/api/http';

export default {
  name: 'DashboardStats',
  data() {
    return {
      loading: false,
      items: [],
      expiringDays: 30,
    };
  },
  computed: {
    lowStockCount() {
      return this.items.filter(it => (it.min_quantity ?? 0) > 0 && (it.quantity ?? 0) <= (it.min_quantity ?? 0)).length;
    },
    expiringSoonCount() {
      const now = new Date();
      const daysLimit = Number(this.expiringDays || 30) || 30;
      return this.items.filter(it => {
        if (!it.expiry_date) return false;
        const d = new Date(it.expiry_date);
        if (Number.isNaN(d.getTime())) return false;
        const diff = d.getTime() - now.getTime();
        const days = diff / (1000 * 60 * 60 * 24);
        return days >= 0 && days <= daysLimit;
      }).length;
    },
  },
  created() {
    this.loadPrefs();
    this.fetchItems();
  },
  methods: {
    loadPrefs() {
      try {
        const raw = localStorage.getItem('warehouse_prefs');
        const v = raw ? JSON.parse(raw) : null;
        if (v && typeof v === 'object') {
          const d = Number(v.expiringDays || 30);
          this.expiringDays = Number.isFinite(d) && d > 0 ? d : 30;
        }
      } catch (e) {
        this.expiringDays = 30;
      }
    },
    async fetchItems() {
      this.loading = true;
      try {
        const res = await api.get('/api/items');
        this.items = Array.isArray(res.data) ? res.data : [];
      } catch (e) {
        this.items = [];
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
  margin-top: 12px;
}

.title {
  font-weight: 900;
  font-size: 14px;
  margin-bottom: 8px;
}

.cards {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 8px;
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
  font-size: 20px;
  font-weight: 900;
  margin-top: 2px;
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

