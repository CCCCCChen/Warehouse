<template>
  <div :class="embedded ? 'embedded' : 'page'">
    <div v-if="!embedded" class="header">
      <h2>出库</h2>
      <div class="header-actions">
        <router-link class="link ghost" to="/warehouse">主页</router-link>
      </div>
    </div>

    <div :class="embedded ? 'content' : 'card'">
      <div v-if="embedded" class="embed-head">
        <div class="embed-title">出库</div>
        <div class="embed-actions">
          <router-link class="embed-link" to="/warehouse/outbound">全屏打开</router-link>
          <button class="btn danger" type="button" :disabled="!canSave" @click="save">
            {{ saving ? '保存中...' : '保存出库' }}
          </button>
        </div>
      </div>
      <div class="row">
        <input v-model.trim="q" class="input" placeholder="搜索：名称/品牌/条码/标签/备注" />
        <button class="btn" type="button" :disabled="loading" @click="refresh">刷新</button>
      </div>
      <div class="muted" v-if="loading">加载中...</div>
      <div class="hint" v-else-if="filteredItems.length === 0">没有匹配的物品</div>
      <div v-else class="list">
        <div v-for="it in filteredItems" :key="it.id" class="item" :class="rowClass(it)">
          <div class="left">
            <div class="name">{{ it.name || '-' }}</div>
            <div class="meta">
              <span v-if="it.brand">品牌：{{ it.brand }}</span>
              <span v-if="it.barcode">条码：{{ it.barcode }}</span>
              <span v-if="it.room || it.spot">位置：{{ (it.room || '') }}{{ it.spot ? `-${it.spot}` : '' }}</span>
              <span v-if="it.unit">单位：{{ it.unit }}</span>
              <span>库存：{{ it.quantity ?? 0 }}</span>
              <span v-if="(it.min_quantity ?? 0) > 0">阈值：{{ it.min_quantity }}</span>
            </div>
          </div>

          <div class="right">
            <div class="controls">
              <button class="small" type="button" :disabled="(getOutboundQty(it) <= 0) || saving" @click="dec(it)">-</button>
              <div class="qty">{{ getOutboundQty(it) }}</div>
              <button class="small" type="button" :disabled="(getOutboundQty(it) >= (it.quantity ?? 0)) || saving" @click="inc(it)">+</button>
              <button class="small ghost" type="button" :disabled="(it.quantity ?? 0) <= 0 || saving" @click="setToZero(it)">扣到 0</button>
            </div>
            <div class="after muted">剩余：{{ remainingQty(it) }}</div>
          </div>
        </div>
      </div>

      <div class="footer">
        <div class="muted">{{ saveSummary }}</div>
        <button v-if="!embedded" class="btn danger" type="button" :disabled="!canSave" @click="save">
          {{ saving ? '保存中...' : '保存出库' }}
        </button>
      </div>

      <div v-if="hint" class="hint">{{ hint }}</div>
      <div v-if="lowStockHint" class="warn">{{ lowStockHint }}</div>
    </div>
  </div>
</template>

<script>
import { api } from '@/api/http';

export default {
  name: 'WarehouseOutboundPage',
  props: {
    embedded: {
      type: Boolean,
      default: false,
    },
  },
  data() {
    return {
      loading: false,
      saving: false,
      items: [],
      q: '',
      outboundQty: {},
      hint: '',
      lowStockHint: '',
    };
  },
  computed: {
    filteredItems() {
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
    saveLines() {
      const lines = [];
      const map = this.outboundQty || {};
      Object.keys(map).forEach(k => {
        const id = Number(k);
        const qty = Number(map[k] || 0);
        if (!Number.isFinite(id) || !Number.isFinite(qty) || qty <= 0) return;
        lines.push({ item_id: id, qty });
      });
      return lines;
    },
    canSave() {
      return !this.saving && this.saveLines.length > 0;
    },
    saveSummary() {
      const cnt = this.saveLines.reduce((acc, ln) => acc + (ln.qty || 0), 0);
      const kinds = this.saveLines.length;
      if (kinds <= 0) return '未选择出库物品';
      return `本次出库：${kinds} 种，共 ${cnt} 件`;
    },
  },
  created() {
    this.refresh();
  },
  methods: {
    loadPrefs() {
      try {
        const raw = localStorage.getItem('warehouse_prefs');
        const v = raw ? JSON.parse(raw) : null;
        if (v && typeof v === 'object') {
          return {
            notifyLowStock: v.notifyLowStock !== false,
          };
        }
      } catch (e) {
        return { notifyLowStock: true };
      }
      return { notifyLowStock: true };
    },
    isLowStock(it) {
      const min = Number(it && it.min_quantity != null ? it.min_quantity : 0) || 0;
      const q = Number(it && it.quantity != null ? it.quantity : 0) || 0;
      return min > 0 && q <= min;
    },
    rowClass(it) {
      return this.isLowStock(it) ? 'low' : '';
    },
    async refresh() {
      if (this.loading) return;
      this.loading = true;
      this.hint = '';
      try {
        const res = await api.get('/api/items');
        this.items = Array.isArray(res.data) ? res.data : [];
      } catch (e) {
        this.items = [];
        this.hint = '加载失败，请检查网络或后端服务';
      } finally {
        this.loading = false;
      }
    },
    getOutboundQty(it) {
      const id = it && it.id != null ? Number(it.id) : null;
      if (id == null) return 0;
      const v = Number((this.outboundQty || {})[id] || 0);
      return Number.isFinite(v) && v > 0 ? v : 0;
    },
    setOutboundQty(it, nextQty) {
      const id = it && it.id != null ? Number(it.id) : null;
      if (id == null) return;
      const max = Number(it && it.quantity != null ? it.quantity : 0) || 0;
      const v = Number(nextQty || 0);
      const clamped = Math.max(0, Math.min(max, Number.isFinite(v) ? v : 0));
      this.outboundQty = { ...(this.outboundQty || {}), [id]: clamped };
    },
    inc(it) {
      this.setOutboundQty(it, this.getOutboundQty(it) + 1);
    },
    dec(it) {
      this.setOutboundQty(it, this.getOutboundQty(it) - 1);
    },
    setToZero(it) {
      const max = Number(it && it.quantity != null ? it.quantity : 0) || 0;
      this.setOutboundQty(it, max);
    },
    remainingQty(it) {
      const max = Number(it && it.quantity != null ? it.quantity : 0) || 0;
      const used = this.getOutboundQty(it);
      const left = max - used;
      return left >= 0 ? left : 0;
    },
    async save() {
      if (!this.canSave) return;
      this.saving = true;
      this.hint = '';
      this.lowStockHint = '';
      try {
        const res = await api.post('/api/stock/outbound', { lines: this.saveLines });
        const data = res && res.data ? res.data : {};
        const lowIds = Array.isArray(data.low_stock_item_ids) ? data.low_stock_item_ids.map(Number) : [];
        const updated = Array.isArray(data.updated_items) ? data.updated_items : [];
        this.outboundQty = {};
        await this.refresh();
        this.hint = '已保存';

        const prefs = this.loadPrefs();
        if (prefs.notifyLowStock && lowIds.length > 0) {
          const map = {};
          updated.forEach(it => {
            if (it && it.id != null) map[Number(it.id)] = it;
          });
          const names = lowIds
            .map(id => (map[id] && map[id].name) ? String(map[id].name) : `#${id}`)
            .slice(0, 8);
          this.lowStockHint = `低库存提醒：${names.join('、')}${lowIds.length > names.length ? '…' : ''}`;
        }
      } catch (e) {
        const detail = (e && e.response && e.response.data) ? e.response.data : null;
        this.hint = detail ? `保存失败：${JSON.stringify(detail)}` : '保存失败，请检查网络或后端服务';
      } finally {
        this.saving = false;
      }
    },
  },
};
</script>

<style scoped>
.embedded {
  width: 100%;
  box-sizing: border-box;
}

.page {
  padding: 20px;
  padding-bottom: 60px;
  max-width: 1200px;
  margin: 0 auto;
  background: rgba(255, 255, 255, 0.55);
  border: 1px solid rgba(0, 0, 0, 0.12);
  border-radius: 14px;
  box-shadow: 0 10px 30px rgba(0, 0, 0, 0.08);
  min-height: 100vh;
  min-height: 100dvh;
  box-sizing: border-box;
}

.content {
  padding: 0;
  box-sizing: border-box;
}

.embed-head {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 10px;
  flex-wrap: wrap;
  margin-bottom: 10px;
}

.embed-actions {
  display: flex;
  gap: 10px;
  align-items: center;
  flex-wrap: wrap;
}

.embed-title {
  font-weight: 900;
  color: #111827;
}

.embed-link {
  display: inline-block;
  padding: 8px 10px;
  border-radius: 10px;
  background: rgba(0, 0, 0, 0.75);
  color: white;
  text-decoration: none;
  font-weight: 800;
}

.header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 12px;
  flex-wrap: wrap;
  margin-bottom: 12px;
}

.header-actions {
  display: flex;
  gap: 10px;
  align-items: center;
}

.link {
  display: inline-block;
  padding: 10px 12px;
  border-radius: 8px;
  background: #1f6feb;
  color: white;
  text-decoration: none;
}

.link.ghost {
  background: #111827;
}

.card {
  padding: 16px;
  border-radius: 10px;
  background: rgba(255, 255, 255, 0.7);
  border: 1px solid rgba(0, 0, 0, 0.08);
}

.row {
  display: flex;
  gap: 10px;
  flex-wrap: wrap;
  align-items: center;
}

.input {
  flex: 1;
  min-width: 220px;
  padding: 10px 12px;
  border-radius: 10px;
  border: 1px solid rgba(0, 0, 0, 0.15);
  outline: none;
}

.btn {
  padding: 10px 12px;
  border-radius: 10px;
  border: none;
  background: #111827;
  color: white;
  font-weight: 700;
}

.btn:disabled {
  opacity: 0.5;
}

.btn.danger {
  background: #b00020;
}

.list {
  margin-top: 12px;
  display: grid;
  gap: 10px;
}

.item {
  display: flex;
  justify-content: space-between;
  gap: 12px;
  padding: 12px;
  border-radius: 12px;
  border: 1px solid rgba(0, 0, 0, 0.10);
  background: rgba(255, 255, 255, 0.75);
}

.item.low {
  border-color: rgba(176, 0, 32, 0.35);
  background: rgba(176, 0, 32, 0.06);
}

.left {
  min-width: 0;
}

.name {
  font-weight: 900;
  color: #111827;
}

.meta {
  margin-top: 4px;
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  font-size: 12px;
  color: rgba(0, 0, 0, 0.65);
}

.right {
  flex-shrink: 0;
  text-align: right;
}

.controls {
  display: flex;
  align-items: center;
  justify-content: flex-end;
  gap: 8px;
  flex-wrap: wrap;
}

.small {
  padding: 6px 10px;
  border-radius: 10px;
  border: none;
  background: #1f6feb;
  color: white;
  font-weight: 900;
}

.small:disabled {
  opacity: 0.5;
}

.small.ghost {
  background: rgba(0, 0, 0, 0.70);
}

.qty {
  min-width: 32px;
  text-align: center;
  font-weight: 900;
  color: #111827;
}

.after {
  margin-top: 6px;
}

.footer {
  margin-top: 14px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 12px;
  flex-wrap: wrap;
}

.muted {
  color: rgba(0, 0, 0, 0.65);
}

.hint {
  margin-top: 12px;
  color: rgba(0, 0, 0, 0.65);
}

.warn {
  margin-top: 10px;
  padding: 10px 12px;
  border-radius: 10px;
  background: rgba(255, 193, 7, 0.20);
  border: 1px solid rgba(255, 193, 7, 0.35);
  color: rgba(0, 0, 0, 0.8);
  font-weight: 700;
}

@media (max-width: 720px) {
  .item {
    flex-direction: column;
    align-items: stretch;
  }
  .right {
    text-align: left;
  }
  .controls {
    justify-content: flex-start;
  }
}
</style>
