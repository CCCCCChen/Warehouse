<template>
  <div class="page">
    <div class="header">
      <h2>录入/管理</h2>
      <div class="header-actions">
        <router-link class="link" to="/warehouse/items">物品管理</router-link>
        <router-link class="link ghost" to="/warehouse">主页</router-link>
      </div>
    </div>

    <div class="card">
      <div v-if="loadingMessage">加载中...</div>
      <div v-else class="muted">{{ message }}</div>
    </div>

    <div class="grid">
      <div class="panel">
        <div class="panel-title">快速录入</div>

        <div class="ocr">
          <div class="ocr-title">图片识别录入</div>
          <div class="row">
            <label class="file">
              选择图片
              <input type="file" accept="image/*" @change="onPickImage" />
            </label>
            <label class="full">
              提示词（可选，留空使用后端默认）
              <input v-model.trim="ocrPrompt" placeholder="可选" />
            </label>
          </div>
          <div v-if="ocrPreviewUrl" class="preview">
            <img :src="ocrPreviewUrl" alt="preview" />
          </div>
          <div class="row">
            <button type="button" :disabled="!ocrFile || ocrLoading" @click="runOcr">
              {{ ocrLoading ? '识别中...' : '识别并填充' }}
            </button>
            <button type="button" class="ghost-btn" :disabled="ocrLoading" @click="clearOcr">
              清除图片
            </button>
          </div>
          <div v-if="ocrHint" class="muted">{{ ocrHint }}</div>
        </div>

        <form class="form" @submit.prevent="quickCreate">
          <div class="row">
            <label>
              名称
              <input v-model.trim="form.name" required />
            </label>
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
          </div>

          <div class="row">
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
              到期日
              <input v-model="form.expiry_date" type="date" />
            </label>
            <label>
              标签
              <input v-model.trim="form.tags" placeholder="厨房,常用" />
            </label>
          </div>

          <label class="full">
            备注
            <input v-model.trim="form.notes" placeholder="可选" />
          </label>
          <label class="full">
            描述
            <input v-model.trim="form.description" placeholder="可选" />
          </label>

          <div class="row">
            <button type="submit">保存</button>
            <button type="button" class="ghost-btn" @click="reset">清空</button>
          </div>
          <div v-if="hint" class="hint">{{ hint }}</div>
        </form>
      </div>

      <div class="panel">
        <div class="panel-title">提醒</div>
        <div class="sub-title">低库存</div>
        <div v-if="loadingItems" class="muted">加载中...</div>
        <div v-else-if="lowStockItems.length === 0" class="muted">暂无</div>
        <ul v-else class="list">
          <li v-for="it in lowStockItems" :key="it.id" class="list-item warn">
            <span class="strong">{{ it.name }}</span>
            <span class="muted">{{ it.quantity }}{{ it.unit || '' }} / 最低 {{ it.min_quantity }}</span>
          </li>
        </ul>

        <div class="sub-title">临期(30天)</div>
        <div v-if="loadingItems" class="muted">加载中...</div>
        <div v-else-if="expiringItems.length === 0" class="muted">暂无</div>
        <ul v-else class="list">
          <li v-for="it in expiringItems" :key="it.id" class="list-item danger">
            <span class="strong">{{ it.name }}</span>
            <span class="muted">到期 {{ it.expiry_date }}</span>
          </li>
        </ul>
      </div>
    </div>
  </div>
</template>

<script>
import { api } from '@/api/http';

export default {
  name: 'WarehouseManagePage',
  data() {
    return {
      loadingMessage: false,
      loadingItems: false,
      message: '',
      items: [],
      hint: '',
      ocrFile: null,
      ocrPreviewUrl: '',
      ocrLoading: false,
      ocrHint: '',
      ocrPrompt: '',
      categories: [
        '厨房-食材',
        '厨房-调味',
        '厨房-饮品',
        '清洁-洗护',
        '清洁-家务',
        '卫浴-洗漱',
        '卫浴-纸品',
        '日用-收纳',
        '药品-常备',
        '其他',
      ],
      locations: [
        '厨房-冰箱',
        '厨房-橱柜',
        '卫生间-柜子',
        '客厅-柜子',
        '阳台-储物',
        '杂物间',
        '其他',
      ],
      units: ['个', '件', '袋', '瓶', '盒', '包', '卷', '罐', '支', '片', 'kg', 'g', 'L', 'ml'],
      form: {
        name: '',
        quantity: 1,
        unit: '件',
        category: '',
        location: '',
        min_quantity: 0,
        purchase_date: '',
        expiry_date: '',
        brand: '',
        barcode: '',
        tags: '',
        notes: '',
        description: '',
      },
    };
  },
  created() {
    this.fetchMessage();
    this.fetchItems();
  },
  computed: {
    lowStockItems() {
      return this.items
        .filter(it => (it.min_quantity ?? 0) > 0 && (it.quantity ?? 0) <= (it.min_quantity ?? 0))
        .slice()
        .sort((a, b) => (a.quantity ?? 0) - (b.quantity ?? 0))
        .slice(0, 8);
    },
    expiringItems() {
      const now = new Date();
      return this.items
        .filter(it => {
          if (!it.expiry_date) return false;
          const d = new Date(it.expiry_date);
          if (Number.isNaN(d.getTime())) return false;
          const diff = d.getTime() - now.getTime();
          const days = diff / (1000 * 60 * 60 * 24);
          return days >= 0 && days <= 30;
        })
        .slice()
        .sort((a, b) => (a.expiry_date || '').localeCompare(b.expiry_date || ''))
        .slice(0, 8);
    },
  },
  methods: {
    async fetchMessage() {
      this.loadingMessage = true;
      try {
        const res = await api.get('/api/warehouse/manage');
        this.message = res.data.message || '';
      } catch (e) {
        console.error('Failed to fetch manage page message:', e);
        this.message = '无法加载录入/管理信息';
      } finally {
        this.loadingMessage = false;
      }
    },
    async fetchItems() {
      this.loadingItems = true;
      try {
        const res = await api.get('/api/items');
        this.items = res.data;
      } catch (e) {
        console.error('Failed to fetch items:', e);
      } finally {
        this.loadingItems = false;
      }
    },
    reset() {
      this.hint = '';
      this.form = {
        name: '',
        quantity: 1,
        unit: '件',
        category: '',
        location: '',
        min_quantity: 0,
        purchase_date: '',
        expiry_date: '',
        brand: '',
        barcode: '',
        tags: '',
        notes: '',
        description: '',
      };
    },
    onPickImage(e) {
      const f = (e.target && e.target.files && e.target.files[0]) || null;
      this.ocrHint = '';
      this.ocrFile = f;
      if (this.ocrPreviewUrl) {
        URL.revokeObjectURL(this.ocrPreviewUrl);
      }
      this.ocrPreviewUrl = f ? URL.createObjectURL(f) : '';
    },
    clearOcr() {
      this.ocrHint = '';
      this.ocrFile = null;
      if (this.ocrPreviewUrl) {
        URL.revokeObjectURL(this.ocrPreviewUrl);
      }
      this.ocrPreviewUrl = '';
      this.ocrPrompt = '';
    },
    applyExtracted(extracted) {
      if (!extracted || typeof extracted !== 'object') return;
      const next = { ...this.form };
      const keys = [
        'name',
        'description',
        'quantity',
        'category',
        'location',
        'unit',
        'brand',
        'min_quantity',
        'purchase_date',
        'expiry_date',
        'barcode',
        'tags',
        'notes',
      ];
      keys.forEach(k => {
        if (extracted[k] !== undefined && extracted[k] !== null && String(extracted[k]).trim() !== '') {
          next[k] = extracted[k];
        }
      });
      if (typeof next.quantity === 'string') next.quantity = Number(next.quantity) || 0;
      if (typeof next.min_quantity === 'string') next.min_quantity = Number(next.min_quantity) || 0;
      this.form = next;
    },
    async runOcr() {
      if (!this.ocrFile || this.ocrLoading) return;
      this.ocrLoading = true;
      this.ocrHint = '';
      try {
        const fd = new FormData();
        fd.append('file', this.ocrFile);
        fd.append('prompt', this.ocrPrompt || '');
        const res = await api.post('/api/ocr/item_extract', fd);
        const extracted = (res.data || {}).extracted || null;
        this.applyExtracted(extracted);
        this.ocrHint = '已自动填充表单，请核对后点击“保存”。';
      } catch (e) {
        console.error('OCR failed:', e);
        this.ocrHint = '识别失败，请检查后端配置与网络';
      } finally {
        this.ocrLoading = false;
      }
    },
    async quickCreate() {
      this.hint = '';
      try {
        const payload = {
          name: this.form.name,
          quantity: this.form.quantity,
          unit: this.form.unit || null,
          category: this.form.category || null,
          location: this.form.location || null,
          min_quantity: this.form.min_quantity ?? 0,
          purchase_date: this.form.purchase_date || null,
          expiry_date: this.form.expiry_date || null,
          brand: this.form.brand || null,
          barcode: this.form.barcode || null,
          tags: this.form.tags || null,
          notes: this.form.notes || null,
          description: this.form.description || null,
        };
        await api.post('/api/items', payload);
        this.hint = '已保存';
        this.reset();
        await this.fetchItems();
      } catch (e) {
        console.error('Failed to create item:', e);
        this.hint = '保存失败';
      }
    },
  },
};
</script>

<style scoped>
.page {
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

.card {
  padding: 16px;
  border-radius: 8px;
  background: rgba(255, 255, 255, 0.7);
  margin-bottom: 12px;
  border: 1px solid rgba(0, 0, 0, 0.10);
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

.grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 12px;
  align-items: stretch;
}

.panel {
  background: rgba(255, 255, 255, 0.7);
  border-radius: 10px;
  padding: 14px;
  border: 1px solid rgba(0, 0, 0, 0.10);
  height: 100%;
}

.panel-title {
  font-weight: 800;
  margin-bottom: 10px;
}

.ocr {
  background: rgba(17, 24, 39, 0.04);
  border: 1px dashed rgba(0, 0, 0, 0.18);
  border-radius: 12px;
  padding: 12px;
  margin-bottom: 12px;
}

.ocr-title {
  font-weight: 800;
  margin-bottom: 10px;
}

.file input[type="file"] {
  padding: 6px 0;
  border: none;
}

.preview {
  margin: 10px 0;
  border-radius: 12px;
  overflow: hidden;
  border: 1px solid rgba(0, 0, 0, 0.12);
}

.preview img {
  display: block;
  width: 100%;
  max-height: 260px;
  object-fit: contain;
  background: rgba(255, 255, 255, 0.6);
}

.sub-title {
  margin-top: 10px;
  margin-bottom: 6px;
  font-weight: 700;
}

.form {
  display: block;
}

.row {
  display: flex;
  gap: 12px;
  flex-wrap: wrap;
  margin-bottom: 10px;
}

.full {
  display: block;
  margin-bottom: 10px;
}

label {
  display: flex;
  flex-direction: column;
  gap: 6px;
  min-width: 160px;
  flex: 1;
}

input,
select {
  padding: 8px 10px;
  border-radius: 8px;
  border: 1px solid rgba(0, 0, 0, 0.15);
}

.ghost-btn {
  background: transparent;
  border: 1px solid rgba(0, 0, 0, 0.25);
  padding: 6px 10px;
  border-radius: 8px;
}

.hint {
  margin-top: 8px;
  color: #111827;
}

.list {
  list-style: none;
  padding: 0;
  margin: 0;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.list-item {
  padding: 10px;
  border-radius: 10px;
  display: flex;
  justify-content: space-between;
  gap: 10px;
  flex-wrap: wrap;
}

.list-item.warn {
  background: rgba(255, 193, 7, 0.22);
}

.list-item.danger {
  background: rgba(176, 0, 32, 0.14);
}

.strong {
  font-weight: 700;
}

.muted {
  color: rgba(0, 0, 0, 0.65);
}

@media (max-width: 900px) {
  .grid {
    grid-template-columns: 1fr;
  }
}
</style>
