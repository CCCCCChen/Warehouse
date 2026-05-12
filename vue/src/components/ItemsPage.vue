<template>
  <div class="items-page">
    <div class="header">
      <h2>物品管理</h2>
      <div class="header-actions">
        <button @click="refresh">刷新</button>
        <router-link class="link" to="/warehouse">返回主页</router-link>
      </div>
    </div>

    <div class="stats">
      <div class="stat">
        <div class="stat-label">总物品</div>
        <div class="stat-value">{{ items.length }}</div>
      </div>
      <div class="stat warn">
        <div class="stat-label">低库存</div>
        <div class="stat-value">{{ lowStockCount }}</div>
      </div>
      <div class="stat danger">
        <div class="stat-label">临期(30天)</div>
        <div class="stat-value">{{ expiringSoonCount }}</div>
      </div>
    </div>

    <div class="filters">
      <input v-model.trim="filters.q" class="filter-input" placeholder="搜索：名称/品牌/条码/标签/备注" />
      <select v-model="filters.category" class="filter-select">
        <option value="">全部分类</option>
        <option v-for="c in categories" :key="c" :value="c">{{ c }}</option>
      </select>
      <select v-model="filters.location" class="filter-select">
        <option value="">全部位置</option>
        <option v-for="l in locations" :key="l" :value="l">{{ l }}</option>
      </select>
      <label class="check">
        <input v-model="filters.onlyLowStock" type="checkbox" />
        仅低库存
      </label>
      <label class="check">
        <input v-model="filters.onlyExpiring" type="checkbox" />
        仅临期
      </label>
      <select v-model="filters.sort" class="filter-select">
        <option value="updated">默认</option>
        <option value="expiry">按保质期</option>
        <option value="quantity">按数量</option>
        <option value="name">按名称</option>
      </select>
    </div>

    <form class="form" @submit.prevent="onSubmit">
      <div class="form-title">{{ form.id ? `编辑 #${form.id}` : '快速录入' }}</div>

      <div class="row">
        <label>
          名称
          <input v-model.trim="form.name" required />
        </label>
        <label>
          分类
          <select v-model="form.category">
            <option value="">未设置</option>
            <option v-for="c in categories" :key="c" :value="c">{{ c }}</option>
          </select>
        </label>
        <label>
          位置
          <select v-model="form.location">
            <option value="">未设置</option>
            <option v-for="l in locations" :key="l" :value="l">{{ l }}</option>
          </select>
        </label>
      </div>

      <div class="row">
        <label>
          数量
          <input v-model.number="form.quantity" type="number" min="0" required />
        </label>
        <label>
          单位
          <select v-model="form.unit">
            <option value="">未设置</option>
            <option v-for="u in units" :key="u" :value="u">{{ u }}</option>
          </select>
        </label>
        <label>
          最低库存
          <input v-model.number="form.min_quantity" type="number" min="0" />
        </label>
      </div>

      <div class="row">
        <label>
          品牌
          <input v-model.trim="form.brand" placeholder="可选" />
        </label>
        <label>
          条码
          <input v-model.trim="form.barcode" placeholder="可选" />
        </label>
      </div>

      <div class="row">
        <label>
          采购日期
          <input v-model="form.purchase_date" type="date" />
        </label>
        <label>
          保质期/到期日
          <input v-model="form.expiry_date" type="date" />
        </label>
      </div>

      <label class="full">
        标签（用逗号分隔）
        <input v-model.trim="form.tags" placeholder="例如：厨房,常用,易耗" />
      </label>
      <label class="full">
        备注
        <input v-model.trim="form.notes" placeholder="例如：适合做早餐；替换品牌可选XX" />
      </label>
      <label class="full">
        描述
        <input v-model.trim="form.description" placeholder="可选" />
      </label>

      <div class="row">
        <button type="submit">{{ form.id ? '保存更新' : '新增物品' }}</button>
        <button v-if="form.id" type="button" class="ghost" @click="resetForm">取消编辑</button>
      </div>
    </form>

    <div v-if="loading" class="hint">加载中...</div>
    <div v-else-if="filteredItems.length === 0" class="hint">没有匹配的物品</div>

    <table v-else class="table">
      <thead>
        <tr>
          <th>名称</th>
          <th>分类/位置</th>
          <th>数量</th>
          <th>最低</th>
          <th>到期</th>
          <th>品牌/条码</th>
          <th>标签</th>
          <th>操作</th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="it in filteredItems" :key="it.id" :class="rowClass(it)">
          <td class="name">
            <div class="primary">{{ it.name }}</div>
            <div class="secondary">{{ it.notes || it.description || '-' }}</div>
          </td>
          <td>
            <div class="primary">{{ it.category || '-' }}</div>
            <div class="secondary">{{ it.location || '-' }}</div>
          </td>
          <td>
            <span class="primary">{{ it.quantity }}</span>
            <span class="secondary">{{ it.unit || '' }}</span>
          </td>
          <td>{{ it.min_quantity ?? 0 }}</td>
          <td>{{ it.expiry_date || '-' }}</td>
          <td>
            <div class="primary">{{ it.brand || '-' }}</div>
            <div class="secondary">{{ it.barcode || '-' }}</div>
          </td>
          <td>{{ it.tags || '-' }}</td>
          <td class="ops">
            <button @click="startEdit(it)">编辑</button>
            <button class="danger" @click="remove(it.id)">删除</button>
          </td>
        </tr>
      </tbody>
    </table>
  </div>
</template>

<script>
import { api } from '@/api/http';

export default {
  name: 'ItemsPage',
  data() {
    return {
      loading: false,
      items: [],
      filters: {
        q: '',
        category: '',
        location: '',
        onlyLowStock: false,
        onlyExpiring: false,
        sort: 'updated',
      },
      categories: [
        '厨房-食材',
        '厨房-调味',
        '厨房-饮品',
        '清洁-洗护',
        '清洁-家务',
        '卫浴-洗漱',
        '卫浴-纸品',
        '日用-收纳',
        '日用-文具',
        '家电-耗材',
        '药品-常备',
        '母婴-用品',
        '宠物-用品',
        '其他',
      ],
      locations: [
        '厨房-冰箱',
        '厨房-橱柜',
        '厨房-台面',
        '客厅-柜子',
        '卧室-衣柜',
        '卫生间-柜子',
        '阳台-储物',
        '杂物间',
        '车里',
        '其他',
      ],
      units: ['个', '件', '袋', '瓶', '盒', '包', '卷', '罐', '支', '片', 'kg', 'g', 'L', 'ml'],
      form: {
        id: null,
        name: '',
        description: '',
        quantity: 0,
        category: '',
        location: '',
        unit: '',
        brand: '',
        min_quantity: 0,
        purchase_date: '',
        expiry_date: '',
        barcode: '',
        tags: '',
        notes: '',
      },
    };
  },
  created() {
    this.refresh();
  },
  computed: {
    lowStockCount() {
      return this.items.filter(it => this.isLowStock(it)).length;
    },
    expiringSoonCount() {
      return this.items.filter(it => this.isExpiringSoon(it)).length;
    },
    filteredItems() {
      const q = (this.filters.q || '').toLowerCase();
      const category = this.filters.category;
      const location = this.filters.location;
      const onlyLow = this.filters.onlyLowStock;
      const onlyExp = this.filters.onlyExpiring;

      let list = this.items.filter(it => {
        if (category && (it.category || '') !== category) return false;
        if (location && (it.location || '') !== location) return false;
        if (onlyLow && !this.isLowStock(it)) return false;
        if (onlyExp && !this.isExpiringSoon(it)) return false;
        if (!q) return true;
        const hay = [
          it.name,
          it.brand,
          it.barcode,
          it.tags,
          it.notes,
          it.description,
          it.category,
          it.location,
        ]
          .filter(Boolean)
          .join(' ')
          .toLowerCase();
        return hay.includes(q);
      });

      if (this.filters.sort === 'expiry') {
        list = list.slice().sort((a, b) => (a.expiry_date || '9999-12-31').localeCompare(b.expiry_date || '9999-12-31'));
      } else if (this.filters.sort === 'quantity') {
        list = list.slice().sort((a, b) => (a.quantity ?? 0) - (b.quantity ?? 0));
      } else if (this.filters.sort === 'name') {
        list = list.slice().sort((a, b) => (a.name || '').localeCompare(b.name || ''));
      }

      return list;
    },
  },
  methods: {
    isLowStock(it) {
      const minq = Number(it.min_quantity ?? 0);
      const q = Number(it.quantity ?? 0);
      return minq > 0 && q <= minq;
    },
    isExpiringSoon(it) {
      if (!it.expiry_date) return false;
      const d = new Date(it.expiry_date);
      if (Number.isNaN(d.getTime())) return false;
      const now = new Date();
      const diff = d.getTime() - now.getTime();
      const days = diff / (1000 * 60 * 60 * 24);
      return days >= 0 && days <= 30;
    },
    rowClass(it) {
      if (this.isLowStock(it) && this.isExpiringSoon(it)) return 'row-danger';
      if (this.isExpiringSoon(it)) return 'row-danger';
      if (this.isLowStock(it)) return 'row-warn';
      return '';
    },
    async refresh() {
      this.loading = true;
      try {
        const res = await api.get('/api/items');
        this.items = res.data;
      } catch (e) {
        console.error('Failed to load items:', e);
      } finally {
        this.loading = false;
      }
    },
    resetForm() {
      this.form = {
        id: null,
        name: '',
        description: '',
        quantity: 0,
        category: '',
        location: '',
        unit: '',
        brand: '',
        min_quantity: 0,
        purchase_date: '',
        expiry_date: '',
        barcode: '',
        tags: '',
        notes: '',
      };
    },
    startEdit(it) {
      this.form = {
        id: it.id,
        name: it.name,
        description: it.description || '',
        quantity: it.quantity,
        category: it.category || '',
        location: it.location || '',
        unit: it.unit || '',
        brand: it.brand || '',
        min_quantity: it.min_quantity ?? 0,
        purchase_date: it.purchase_date || '',
        expiry_date: it.expiry_date || '',
        barcode: it.barcode || '',
        tags: it.tags || '',
        notes: it.notes || '',
      };
    },
    async onSubmit() {
      try {
        const payload = {
          name: this.form.name,
          description: this.form.description || null,
          quantity: this.form.quantity,
          category: this.form.category || null,
          location: this.form.location || null,
          unit: this.form.unit || null,
          brand: this.form.brand || null,
          min_quantity: this.form.min_quantity ?? 0,
          purchase_date: this.form.purchase_date || null,
          expiry_date: this.form.expiry_date || null,
          barcode: this.form.barcode || null,
          tags: this.form.tags || null,
          notes: this.form.notes || null,
        };
        if (this.form.id) {
          const id = this.form.id;
          await api.put(`/api/items/${id}`, payload);
        } else {
          await api.post('/api/items', payload);
        }
        this.resetForm();
        await this.refresh();
      } catch (e) {
        console.error('Failed to submit item:', e);
      }
    },
    async remove(id) {
      try {
        await api.delete(`/api/items/${id}`);
        await this.refresh();
      } catch (e) {
        console.error('Failed to delete item:', e);
      }
    },
  },
};
</script>

<style scoped>
.items-page {
  padding: 20px;
  max-width: 1200px;
  margin: 0 auto;
  background: rgba(255, 255, 255, 0.55);
  border: 1px solid rgba(0, 0, 0, 0.12);
  border-radius: 14px;
  box-shadow: 0 10px 30px rgba(0, 0, 0, 0.08);
}

.header {
  display: flex;
  align-items: center;
  justify-content: space-between;
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
  padding: 8px 10px;
  border-radius: 8px;
  background: #111827;
  color: white;
  text-decoration: none;
}

.stats {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 10px;
  margin-bottom: 12px;
}

.stat {
  background: rgba(255, 255, 255, 0.7);
  border-radius: 10px;
  padding: 10px;
}

.stat.warn {
  background: rgba(255, 193, 7, 0.2);
}

.stat.danger {
  background: rgba(176, 0, 32, 0.15);
}

.stat-label {
  color: #444;
  font-size: 12px;
}

.stat-value {
  font-size: 22px;
  font-weight: 700;
  margin-top: 2px;
}

.filters {
  display: flex;
  gap: 10px;
  flex-wrap: wrap;
  align-items: center;
  margin-bottom: 12px;
}

.filter-input {
  flex: 1;
  min-width: 220px;
}

.filter-select {
  min-width: 140px;
}

.check {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  background: rgba(255, 255, 255, 0.7);
  padding: 8px 10px;
  border-radius: 10px;
}

.form {
  background: rgba(255, 255, 255, 0.7);
  padding: 12px;
  border-radius: 8px;
  margin-bottom: 20px;
  border: 1px solid rgba(0, 0, 0, 0.10);
}

.form-title {
  font-weight: 700;
  margin-bottom: 10px;
}

.row {
  display: flex;
  gap: 12px;
  margin-bottom: 10px;
  flex-wrap: wrap;
}

.full {
  display: block;
  margin-bottom: 10px;
}

label {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

input {
  padding: 8px 10px;
  border-radius: 6px;
  border: 1px solid rgba(0, 0, 0, 0.15);
}

select {
  padding: 8px 10px;
  border-radius: 6px;
  border: 1px solid rgba(0, 0, 0, 0.15);
}

.ghost {
  background: transparent;
  border: 1px solid rgba(0, 0, 0, 0.25);
  padding: 6px 10px;
  border-radius: 6px;
}

.hint {
  color: #444;
  padding: 10px 0;
}

.table {
  width: 100%;
  border-collapse: collapse;
  background: rgba(255, 255, 255, 0.7);
  border-radius: 8px;
  overflow: hidden;
  border: 1px solid rgba(0, 0, 0, 0.10);
}

.table th,
.table td {
  padding: 10px;
  border-bottom: 1px solid rgba(0, 0, 0, 0.08);
  text-align: left;
  vertical-align: top;
}

.name {
  max-width: 340px;
}

.primary {
  font-weight: 600;
}

.secondary {
  color: rgba(0, 0, 0, 0.6);
  font-size: 12px;
  margin-top: 2px;
  word-break: break-word;
}

.row-warn {
  background: rgba(255, 193, 7, 0.12);
}

.row-danger {
  background: rgba(176, 0, 32, 0.12);
}

.ops {
  display: flex;
  gap: 8px;
}

.danger {
  background: #b00020;
  color: white;
  border: none;
  padding: 6px 10px;
  border-radius: 6px;
}

@media (max-width: 900px) {
  .stats {
    grid-template-columns: 1fr;
  }
  .table {
    display: block;
    overflow-x: auto;
  }
}
</style>
