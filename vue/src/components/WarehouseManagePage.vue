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
          <label class="check">
            <input v-model="ocrUseAsItemImage" type="checkbox" />
            同时保存为物品图片
          </label>
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
          <details v-if="ocrLast" class="details">
            <summary>查看识别结果</summary>
            <div class="details-body">
              <div class="details-title">extracted</div>
              <pre class="pre">{{ ocrLastText }}</pre>
              <div v-if="ocrRaw" class="details-title">raw</div>
              <pre v-if="ocrRaw" class="pre">{{ ocrRaw }}</pre>
            </div>
          </details>
        </div>

        <form class="form" @submit.prevent="quickCreate">
          <div class="section">
            <div class="section-title">核心信息</div>
            <div class="row">
              <label>
                编码
                <input v-model="form.code" placeholder="创建后自动生成" readonly />
              </label>
              <label>
                大类
                <select v-model="form.type_l1" @change="onTypeL1Change">
                  <option value="">未设置</option>
                  <option v-for="t in typeL1Options" :key="t" :value="t">{{ t }}</option>
                </select>
              </label>
              <label>
                子类
                <select v-model="form.type_l2">
                  <option value="">未设置</option>
                  <option v-for="t in typeL2Options" :key="t" :value="t">{{ t }}</option>
                </select>
              </label>
            </div>

            <div class="row">
              <label class="grow">
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
              <label>
                最低库存
                <input v-model.number="form.min_quantity" type="number" min="0" />
              </label>
            </div>

            <label class="full">
              用途
              <textarea v-model.trim="form.usage" rows="3" placeholder="可写用途、使用场景、注意事项等"></textarea>
            </label>

            <div class="row">
              <label class="grow">
                物品图片
                <input type="file" accept="image/*" @change="onPickItemImage" />
              </label>
              <label class="grow">
                图片地址
                <input v-model.trim="form.image_path" placeholder="上传后自动填充" />
              </label>
            </div>
            <div v-if="form.image_path" class="image-preview">
              <img :src="form.image_path" alt="item" />
              <button type="button" class="ghost-btn" @click="clearItemImage">清除图片</button>
            </div>
          </div>

          <div class="section">
            <div class="section-title">时间空间信息</div>
            <div class="row">
              <label>
                生产日期
                <input v-model="form.production_date" type="date" />
              </label>
              <label>
                记录日期
                <input :value="recordedAtText" readonly />
              </label>
              <label>
                Expire Date
                <input v-model="form.expiry_date" type="date" />
              </label>
              <label>
                购买日期
                <input v-model="form.purchase_date" type="date" />
              </label>
            </div>
            <div class="row">
              <label>
                房间
                <select v-model="form.room">
                  <option value="">未设置</option>
                  <option v-for="r in roomOptions" :key="r" :value="r">{{ r }}</option>
                </select>
              </label>
              <label class="grow">
                位置
                <select v-model="form.spot">
                  <option value="">未设置</option>
                  <option v-for="s in spotOptions" :key="s" :value="s">{{ s }}</option>
                </select>
              </label>
              <label class="grow">
                位置补充
                <input v-model.trim="form.location_free" placeholder="例如：东侧墙-第三层 / 床底-左侧" />
              </label>
            </div>
          </div>

          <div class="section fold">
            <button class="section-toggle" type="button" @click="toggle('status')">
              <span class="section-title">状态属性信息</span>
              <span class="toggle-text">{{ uiFold.status ? '展开' : '收起' }}</span>
            </button>
            <div v-if="!uiFold.status" class="section-body">
              <div class="row">
                <label>
                  使用状态
                  <select v-model="form.usage_status">
                    <option value="">未设置</option>
                    <option v-for="s in usageStatusOptions" :key="s" :value="s">{{ s }}</option>
                  </select>
                </label>
                <label>
                  所有权
                  <select v-model="form.ownership">
                    <option value="">未设置</option>
                    <option v-for="o in ownershipOptions" :key="o" :value="o">{{ o }}</option>
                  </select>
                </label>
              </div>
            </div>
          </div>

          <div class="section fold">
            <button class="section-toggle" type="button" @click="toggle('finance')">
              <span class="section-title">财务价值（非必填）</span>
              <span class="toggle-text">{{ uiFold.finance ? '展开' : '收起' }}</span>
            </button>
            <div v-if="!uiFold.finance" class="section-body">
              <div class="row">
                <label>
                  价格
                  <input v-model.number="form.price" type="number" min="0" step="0.01" />
                </label>
                <label>
                  使用价值
                  <input v-model.number="form.value_score" type="number" min="0" step="0.1" />
                </label>
                <label>
                  建议更换周期（天）
                  <input v-model.number="form.replacement_cycle_days" type="number" min="0" />
                </label>
              </div>
            </div>
          </div>

          <div class="section fold">
            <button class="section-toggle" type="button" @click="toggle('dynamic')">
              <span class="section-title">动态维度</span>
              <span class="toggle-text">{{ uiFold.dynamic ? '展开' : '收起' }}</span>
            </button>
            <div v-if="!uiFold.dynamic" class="section-body">
              <div class="row">
                <label>
                  使用频率
                  <select v-model="form.usage_frequency">
                    <option value="">未设置</option>
                    <option v-for="f in usageFrequencyOptions" :key="f" :value="f">{{ f }}</option>
                  </select>
                </label>
                <label class="grow">
                  责任人
                  <input v-model.trim="form.responsible_person" placeholder="可选" />
                </label>
              </div>
              <label class="full">
                关联物品
                <select v-model="form.related_item_ids_arr" multiple>
                  <option v-for="it in relatedCandidates" :key="it.id" :value="String(it.id)">
                    {{ it.code ? `${it.code} ` : '' }}{{ it.name }}
                  </option>
                </select>
              </label>
            </div>
          </div>

          <div class="section fold">
            <button class="section-toggle" type="button" @click="toggle('custom')">
              <span class="section-title">其他属性（允许自定义）</span>
              <span class="toggle-text">{{ uiFold.custom ? '展开' : '收起' }}</span>
            </button>
            <div v-if="!uiFold.custom" class="section-body">
              <div class="kv-head">
                <div>键</div>
                <div>值</div>
                <div></div>
              </div>
              <div v-for="(p, idx) in customPairs" :key="idx" class="kv-row">
                <input v-model.trim="p.k" placeholder="例如：保修期" />
                <input v-model.trim="p.v" placeholder="例如：2年" />
                <button type="button" class="ghost-btn" @click="removePair(idx)">移除</button>
              </div>
              <button type="button" class="ghost-btn" @click="addPair">新增一行</button>
            </div>
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
            <label>
              标签
              <input v-model.trim="form.tags" placeholder="厨房,常用" />
            </label>
          </div>

          <label class="full">
            备注
            <textarea v-model.trim="form.notes" rows="2" placeholder="可选"></textarea>
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
import { DEFAULT_CATEGORIES, DEFAULT_LOCATIONS, DEFAULT_UNITS } from '@/config/defaults';

const TYPE_TREE = {
  家电: ['大家电', '小家电', '厨卫电器', '环境电器'],
  家具: ['客厅家具', '餐厅家具', '卧室家具', '书房家具', '储物家具'],
  家纺: ['床品', '毯子', '毛巾浴巾', '地毯地垫', '其他'],
  厨具餐具: ['炊具', '刀具砧板', '餐具', '水具', '烘焙工具'],
  食品: ['主食', '调味料', '零食', '饮料', '冷冻食品', '干货'],
  日化清洁: ['个人洗护', '家庭清洁', '卫浴用品', '其他'],
  工具五金: ['手动工具', '电动工具', '五金耗材', '维修配件'],
  电子产品: ['数码设备', '影音设备', '网络设备', '存储设备', '充电设备'],
  书籍: ['文学小说', '社科历史', '专业书籍', '生活艺术', '儿童绘本', '期刊杂志'],
  药品: ['内服药', '外用药', '医疗器械', '保健品', '家庭急救包'],
  文件证件: ['身份证明', '学历证明', '资产证明', '合同票据', '医疗档案'],
  纪念品: ['旅行纪念', '礼物收藏', '手工DIY', '奖杯证书'],
  宠物用品: ['食品', '餐具', '寝具', '清洁', '出行', '玩具'],
  其他: ['其他'],
};

const DEFAULT_ROOMS = ['玄关', '厨房', '客厅', '过道', '厕所', '房间1', '房间2', '房间3', '阳台', '其他'];
const DEFAULT_SPOTS = ['整面墙', '柜子', '抽屉', '台面', '床底', '冰箱', '收纳箱', '置物架', '其他'];

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
      ocrLast: null,
      ocrRaw: '',
      ocrUseAsItemImage: true,
      categories: [...DEFAULT_CATEGORIES],
      locations: [...DEFAULT_LOCATIONS],
      units: [...DEFAULT_UNITS],
      uiFold: {
        status: true,
        finance: true,
        dynamic: true,
        custom: true,
      },
      uploadingImage: false,
      customPairs: [{ k: '', v: '' }],
      form: {
        code: '',
        type_l1: '',
        type_l2: '',
        name: '',
        quantity: 1,
        unit: '件',
        category: '',
        location: '',
        room: '',
        spot: '',
        location_free: '',
        min_quantity: 0,
        production_date: '',
        purchase_date: '',
        expiry_date: '',
        brand: '',
        barcode: '',
        tags: '',
        notes: '',
        description: '',
        usage: '',
        image_path: '',
        usage_status: '',
        ownership: '',
        price: null,
        value_score: null,
        replacement_cycle_days: null,
        usage_frequency: '',
        related_item_ids_arr: [],
        responsible_person: '',
        custom_json: '',
        recorded_at: '',
      },
    };
  },
  created() {
    this.loadConfig();
    this.fetchMessage();
    this.fetchItems();
  },
  computed: {
    typeL1Options() {
      return Object.keys(TYPE_TREE);
    },
    typeL2Options() {
      const l1 = this.form.type_l1 || '';
      return TYPE_TREE[l1] || [];
    },
    roomOptions() {
      return DEFAULT_ROOMS;
    },
    spotOptions() {
      return DEFAULT_SPOTS;
    },
    usageStatusOptions() {
      return ['在用', '备用（囤货）', '待维修', '待处理'];
    },
    ownershipOptions() {
      return ['自有', '借用'];
    },
    usageFrequencyOptions() {
      return ['高', '中', '低', '很少'];
    },
    relatedCandidates() {
      return this.items || [];
    },
    recordedAtText() {
      return this.form.recorded_at || new Date().toISOString();
    },
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
    ocrLastText() {
      return this.ocrLast ? JSON.stringify(this.ocrLast, null, 2) : '';
    },
  },
  methods: {
    async loadConfig() {
      try {
        const res = await api.get('/api/config');
        this.categories = Array.isArray(res.data.categories) ? res.data.categories : [...DEFAULT_CATEGORIES];
        this.locations = Array.isArray(res.data.locations) ? res.data.locations : [...DEFAULT_LOCATIONS];
        this.units = Array.isArray(res.data.units) ? res.data.units : [...DEFAULT_UNITS];
        if (!this.form.unit) this.form.unit = this.units[0] || '';
      } catch (e) {
        this.categories = [...DEFAULT_CATEGORIES];
        this.locations = [...DEFAULT_LOCATIONS];
        this.units = [...DEFAULT_UNITS];
      }
    },
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
        code: '',
        type_l1: '',
        type_l2: '',
        name: '',
        quantity: 1,
        unit: '件',
        category: '',
        location: '',
        room: '',
        spot: '',
        location_free: '',
        min_quantity: 0,
        production_date: '',
        purchase_date: '',
        expiry_date: '',
        brand: '',
        barcode: '',
        tags: '',
        notes: '',
        description: '',
        usage: '',
        image_path: '',
        usage_status: '',
        ownership: '',
        price: null,
        value_score: null,
        replacement_cycle_days: null,
        usage_frequency: '',
        related_item_ids_arr: [],
        responsible_person: '',
        custom_json: '',
        recorded_at: '',
      };
      this.customPairs = [{ k: '', v: '' }];
      this.uiFold.status = true;
      this.uiFold.finance = true;
      this.uiFold.dynamic = true;
      this.uiFold.custom = true;
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
      this.ocrLast = null;
      this.ocrRaw = '';
    },
    applyExtracted(extracted) {
      let obj = extracted;
      if (!obj) return 0;
      if (typeof obj === 'string') {
        try {
          obj = JSON.parse(obj);
        } catch (e) {
          return 0;
        }
      }
      if (Array.isArray(obj)) {
        obj = obj[0];
      }
      if (obj && typeof obj === 'object' && obj.extracted && typeof obj.extracted === 'object') {
        obj = obj.extracted;
      }
      if (!obj || typeof obj !== 'object') return 0;
      const next = { ...this.form };
      const keys = [
        'code',
        'type_l1',
        'type_l2',
        'name',
        'description',
        'usage',
        'image_path',
        'quantity',
        'location',
        'room',
        'spot',
        'unit',
        'brand',
        'min_quantity',
        'production_date',
        'purchase_date',
        'expiry_date',
        'barcode',
        'tags',
        'notes',
        'usage_status',
        'ownership',
        'price',
        'value_score',
        'replacement_cycle_days',
        'usage_frequency',
        'responsible_person',
        'related_item_ids',
        'custom_json',
      ];
      let applied = 0;
      keys.forEach(k => {
        const v = obj[k];
        if (v !== undefined && v !== null && String(v).trim() !== '') {
          if (k === 'related_item_ids') {
            next.related_item_ids_arr = String(v).split(',').map(s => s.trim()).filter(Boolean);
            applied += 1;
            return;
          }
          next[k] = v;
          applied += 1;
        }
      });
      if (!next.type_l1 && next.category) next.type_l1 = next.category;
      if (!next.type_l2) next.type_l2 = '';
      if (!next.room && typeof next.location === 'string' && next.location.includes('-')) {
        const parts = next.location.split('-').map(s => s.trim()).filter(Boolean);
        if (parts.length >= 2) {
          next.room = parts[0];
          next.spot = parts.slice(1).join('-');
        }
      }
      if (typeof next.quantity === 'string') next.quantity = Number(next.quantity) || 0;
      if (typeof next.min_quantity === 'string') next.min_quantity = Number(next.min_quantity) || 0;
      if (typeof next.price === 'string') next.price = Number(next.price) || null;
      if (typeof next.value_score === 'string') next.value_score = Number(next.value_score) || null;
      if (typeof next.replacement_cycle_days === 'string') next.replacement_cycle_days = Number(next.replacement_cycle_days) || null;
      this.customPairs = this.parseCustomPairs(next.custom_json);
      this.uiFold.status = !(next.usage_status || next.ownership);
      this.uiFold.finance = !(next.price != null || next.value_score != null || next.replacement_cycle_days != null);
      this.uiFold.dynamic = !(next.usage_frequency || (next.related_item_ids_arr && next.related_item_ids_arr.length > 0) || next.responsible_person);
      this.uiFold.custom = !(next.custom_json && String(next.custom_json).trim());
      this.form = next;
      return applied;
    },
    async runOcr() {
      if (!this.ocrFile || this.ocrLoading) return;
      this.ocrLoading = true;
      this.ocrHint = '';
      this.ocrLast = null;
      this.ocrRaw = '';
      try {
        const fd = new FormData();
        fd.append('file', this.ocrFile);
        fd.append('prompt', this.ocrPrompt || '');
        const res = await api.post('/api/ocr/item_extract', fd);
        const extracted = (res.data || {}).extracted || null;
        const raw = (res.data || {}).raw || '';
        this.ocrLast = extracted;
        this.ocrRaw = raw;
        const applied = this.applyExtracted(extracted);
        if (this.ocrUseAsItemImage) {
          await this.uploadImage(this.ocrFile);
        }
        this.ocrHint = applied > 0
          ? '已自动填充表单，请核对后点击“保存”。'
          : '识别成功但未匹配到字段，请查看识别结果并调整提示词。';
      } catch (e) {
        console.error('OCR failed:', e);
        const detail = (e && e.response && e.response.data) ? e.response.data : null;
        this.ocrHint = detail ? `识别失败：${JSON.stringify(detail)}` : '识别失败，请检查后端配置与网络';
      } finally {
        this.ocrLoading = false;
      }
    },
    toggle(key) {
      this.uiFold[key] = !this.uiFold[key];
    },
    onTypeL1Change() {
      const l1 = this.form.type_l1 || '';
      const list = TYPE_TREE[l1] || [];
      if (list.length > 0 && this.form.type_l2 && !list.includes(this.form.type_l2)) {
        this.form.type_l2 = '';
      }
    },
    async onPickItemImage(e) {
      const file = (e.target && e.target.files && e.target.files[0]) || null;
      if (!file) return;
      await this.uploadImage(file);
      e.target.value = '';
    },
    clearItemImage() {
      this.form.image_path = '';
    },
    async uploadImage(file) {
      this.uploadingImage = true;
      try {
        const fd = new FormData();
        fd.append('file', file);
        const res = await api.post('/api/items/upload_image', fd);
        const url = res.data && res.data.image_url ? res.data.image_url : '';
        if (url) this.form.image_path = url;
      } catch (e) {
        console.error('Failed to upload item image:', e);
      } finally {
        this.uploadingImage = false;
      }
    },
    parseCustomPairs(text) {
      const raw = (text || '').trim();
      if (!raw) return [{ k: '', v: '' }];
      try {
        const obj = JSON.parse(raw);
        if (!obj || typeof obj !== 'object' || Array.isArray(obj)) return [{ k: '', v: '' }];
        const pairs = Object.entries(obj).map(([k, v]) => ({ k: String(k), v: v == null ? '' : String(v) }));
        return pairs.length > 0 ? pairs : [{ k: '', v: '' }];
      } catch (e) {
        return [{ k: '', v: '' }];
      }
    },
    addPair() {
      this.customPairs.push({ k: '', v: '' });
    },
    removePair(idx) {
      this.customPairs.splice(idx, 1);
      if (this.customPairs.length === 0) this.customPairs.push({ k: '', v: '' });
    },
    pairsToJson() {
      const obj = {};
      for (const p of this.customPairs) {
        const k = (p.k || '').trim();
        if (!k) continue;
        obj[k] = (p.v || '').trim();
      }
      const keys = Object.keys(obj);
      return keys.length > 0 ? JSON.stringify(obj) : '';
    },
    async quickCreate() {
      this.hint = '';
      try {
        const customJson = this.pairsToJson();
        const room = (this.form.room || '').trim();
        const spot = (this.form.spot || '').trim();
        const free = (this.form.location_free || '').trim();
        const location = room && spot ? `${room}-${spot}${free ? `-${free}` : ''}` : (this.form.location || '');
        const category = this.form.type_l1
          ? `${this.form.type_l1}${this.form.type_l2 ? `-${this.form.type_l2}` : ''}`
          : (this.form.category || null);
        const payload = {
          code: this.form.code || null,
          type_l1: this.form.type_l1 || null,
          type_l2: this.form.type_l2 || null,
          name: this.form.name,
          quantity: this.form.quantity,
          unit: this.form.unit || null,
          category,
          location: location || null,
          room: room || null,
          spot: spot || null,
          min_quantity: Number.isFinite(Number(this.form.min_quantity)) ? Number(this.form.min_quantity) : 0,
          production_date: this.form.production_date || null,
          purchase_date: this.form.purchase_date || null,
          expiry_date: this.form.expiry_date || null,
          brand: this.form.brand || null,
          barcode: this.form.barcode || null,
          tags: this.form.tags || null,
          notes: this.form.notes || null,
          description: this.form.description || null,
          usage: this.form.usage || null,
          image_path: this.form.image_path || null,
          usage_status: this.form.usage_status || null,
          ownership: this.form.ownership || null,
          price: this.form.price == null || this.form.price === '' ? null : Number(this.form.price),
          value_score: this.form.value_score == null || this.form.value_score === '' ? null : Number(this.form.value_score),
          replacement_cycle_days: this.form.replacement_cycle_days == null || this.form.replacement_cycle_days === '' ? null : Number(this.form.replacement_cycle_days),
          usage_frequency: this.form.usage_frequency || null,
          related_item_ids: (this.form.related_item_ids_arr || []).join(',') || null,
          responsible_person: this.form.responsible_person || null,
          custom_json: customJson || null,
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

.details {
  margin-top: 10px;
}

.details-body {
  margin-top: 8px;
}

.details-title {
  font-weight: 800;
  margin: 10px 0 6px;
}

.pre {
  margin: 0;
  padding: 12px;
  border-radius: 10px;
  background: rgba(17, 24, 39, 0.06);
  border: 1px solid rgba(0, 0, 0, 0.12);
  white-space: pre-wrap;
  word-break: break-word;
  max-height: 320px;
  overflow: auto;
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
  margin-bottom: 12px;
}

.row > label {
  flex: 1 1 200px;
}

.full {
  display: block;
  width: 100%;
  margin-bottom: 12px;
}

label {
  display: flex;
  flex-direction: column;
  gap: 6px;
  font-weight: 500;
  font-size: 14px;
}

input, select, textarea {
  box-sizing: border-box;
  width: 100%;
}

input,
select {
  padding: 8px 10px;
  border-radius: 8px;
  border: 1px solid rgba(0, 0, 0, 0.15);
}

textarea {
  padding: 8px 10px;
  border-radius: 8px;
  border: 1px solid rgba(0, 0, 0, 0.15);
  resize: vertical;
}

.check {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  margin: 8px 0 0;
}

.ghost-btn {
  background: transparent;
  border: 1px solid rgba(0, 0, 0, 0.25);
  padding: 6px 10px;
  border-radius: 8px;
}

.section {
  border: 1px solid rgba(0, 0, 0, 0.10);
  border-radius: 10px;
  padding: 12px;
  margin-bottom: 12px;
  background: rgba(255, 255, 255, 0.65);
}

.section-title {
  font-weight: 800;
  margin-bottom: 10px;
}

.section.fold {
  padding: 0;
  overflow: hidden;
}

.section-toggle {
  width: 100%;
  border: none;
  background: rgba(255, 255, 255, 0.65);
  padding: 12px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  cursor: pointer;
}

.toggle-text {
  color: rgba(0, 0, 0, 0.55);
  font-size: 12px;
}

.section-body {
  padding: 12px;
}

.row .grow {
  flex: 1;
  min-width: 220px;
}

.image-preview {
  display: flex;
  gap: 12px;
  align-items: center;
  flex-wrap: wrap;
  margin-top: 8px;
}

.image-preview img {
  width: 120px;
  height: 120px;
  object-fit: cover;
  border-radius: 10px;
  border: 1px solid rgba(0, 0, 0, 0.12);
}

.kv-head,
.kv-row {
  display: grid;
  grid-template-columns: 1fr 1fr auto;
  gap: 10px;
  align-items: center;
  margin-bottom: 8px;
}

.kv-head {
  font-weight: 700;
  color: rgba(0, 0, 0, 0.6);
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
