<template>
  <div class="tile">
    <div class="head">
      <div class="title">物品管理</div>
      <div class="actions">
        <router-link class="btn ghost" to="/warehouse/manage">快速录入</router-link>
        <router-link class="btn" to="/warehouse/items">全量管理</router-link>
      </div>
    </div>

    <div class="row">
      <input v-model.trim="q" class="input" placeholder="搜索：名称/品牌/条码/标签/备注" />
      <button class="btn solid" type="button" :disabled="loading" @click="refresh">刷新</button>
    </div>

    <div class="muted" v-if="loading">加载中...</div>
    <div class="hint" v-else-if="filtered.length === 0">没有匹配的物品</div>
    <div v-else class="list">
      <div v-for="it in limited" :key="it.id" class="item" :class="rowClass(it)">
        <div class="name">{{ it.name || '-' }}</div>
        <div class="meta">
          <span>库存：{{ it.quantity ?? 0 }}</span>
          <span v-if="(it.min_quantity ?? 0) > 0">阈值：{{ it.min_quantity }}</span>
          <span v-if="it.room || it.spot">位置：{{ (it.room || '') }}{{ it.spot ? `-${it.spot}` : '' }}</span>
        </div>
      </div>
      <div v-if="filtered.length > limit" class="more muted">
        仅显示前 {{ limit }} 条，剩余 {{ filtered.length - limit }} 条请进入全量管理查看。
      </div>
    </div>

    <div class="stats muted" v-if="!loading">
      共 {{ items.length }} 种；当前匹配 {{ filtered.length }} 种；低库存 {{ lowStockCount }} 种
    </div>
  </div>
</template>

<script>
import { api } from '@/api/http';

export default {
  name: 'ItemsEmbeddedTile',
  props: {
    limit: {
      type: Number,
      default: 20,
    },
  },
  data() {
    return {
      loading: false,
      items: [],
      q: '',
    };
  },
  computed: {
    lowStockCount() {
      return (this.items || []).filter(it => (it.min_quantity ?? 0) > 0 && (it.quantity ?? 0) <= (it.min_quantity ?? 0)).length;
    },
    filtered() {
      const q = (this.q || '').toLowerCase();
      if (!q) return this.items || [];
      return (this.items || []).filter(it => {
        if (!it) return false;
        const hay = [
          it.code,
          it.name,
          it.usage,
          it.brand,
          it.barcode,
          it.tags,
          it.notes,
          it.description,
          it.type_l1,
          it.type_l2,
          it.room,
          it.spot,
          it.location,
          it.usage_status,
          it.ownership,
          it.responsible_person,
        ]
          .filter(Boolean)
          .join(' ')
          .toLowerCase();
        return hay.includes(q);
      });
    },
    limited() {
      const n = Number(this.limit || 20) || 20;
      return this.filtered.slice(0, Math.max(1, n));
    },
  },
  created() {
    this.refresh();
  },
  methods: {
    rowClass(it) {
      const min = Number(it && it.min_quantity != null ? it.min_quantity : 0) || 0;
      const q = Number(it && it.quantity != null ? it.quantity : 0) || 0;
      return min > 0 && q <= min ? 'low' : '';
    },
    async refresh() {
      if (this.loading) return;
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
.tile {
  color: #111827;
}

.head {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 10px;
  flex-wrap: wrap;
  margin-bottom: 10px;
}

.title {
  font-weight: 900;
  font-size: 18px;
}

.actions {
  display: flex;
  gap: 10px;
  flex-wrap: wrap;
}

.btn {
  display: inline-block;
  padding: 8px 10px;
  border-radius: 10px;
  background: rgba(0, 0, 0, 0.75);
  color: white;
  text-decoration: none;
  font-weight: 800;
  border: none;
}

.btn.ghost {
  background: #1f6feb;
}

.btn.solid {
  background: #111827;
}

.row {
  display: flex;
  gap: 10px;
  flex-wrap: wrap;
  align-items: center;
}

.input {
  flex: 1;
  min-width: 200px;
  padding: 10px 12px;
  border-radius: 10px;
  border: 1px solid rgba(0, 0, 0, 0.15);
  outline: none;
}

.muted {
  color: rgba(0, 0, 0, 0.65);
}

.hint {
  margin-top: 10px;
  color: rgba(0, 0, 0, 0.65);
}

.list {
  margin-top: 12px;
  display: grid;
  gap: 8px;
}

.item {
  padding: 10px 12px;
  border-radius: 10px;
  background: rgba(255, 255, 255, 0.70);
  border: 1px solid rgba(0, 0, 0, 0.10);
}

.item.low {
  border-color: rgba(176, 0, 32, 0.35);
  background: rgba(176, 0, 32, 0.06);
}

.name {
  font-weight: 900;
}

.meta {
  margin-top: 4px;
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
  font-size: 12px;
  color: rgba(0, 0, 0, 0.65);
}

.more {
  margin-top: 4px;
  font-size: 12px;
}

.stats {
  margin-top: 12px;
  font-size: 12px;
}
</style>

