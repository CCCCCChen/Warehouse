<template>
  <div class="items-page">
    <div class="header">
      <h2>物品管理</h2>
      <div class="header-actions">
        <button class="btn-ghost" @click="refresh">刷新</button>
        <button class="btn-ghost" @click="exportExcel" :disabled="loading || exporting">{{ exporting ? '导出中...' : '导出Excel' }}</button>
        <button class="btn-ghost" @click="downloadImportTemplate" :disabled="exporting || importing">下载导入模板</button>
        <button class="btn-ghost" @click="triggerExcelPick" :disabled="loading || exporting || importing">{{ importing ? '导入中...' : '导入Excel' }}</button>
        <router-link class="btn" to="/warehouse">返回主页</router-link>
        <input ref="excelInput" class="excel-input" type="file" accept=".xlsx,.xls" @change="onExcelPicked" />
      </div>
    </div>

    <div v-if="importSummary" class="import-summary" :class="{ danger: importHasErrors }">
      {{ importSummary }}
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
      <select v-model="filters.type_l1" class="filter-select">
        <option value="">全部大类</option>
        <option v-for="t in typeL1Options" :key="t" :value="t">{{ t }}</option>
      </select>
      <select v-model="filters.room" class="filter-select">
        <option value="">全部房间</option>
        <option v-for="r in roomOptions" :key="r" :value="r">{{ r }}</option>
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

    <div class="entry-wrap">
      <button class="entry-toggle" type="button" @click="entryOpen = !entryOpen">
        {{ entryOpen ? '收起录入' : '展开录入' }}
      </button>
      <div v-if="entryOpen" class="entry-body">
        <WarehouseManagePage ref="entry" :embedded="true" @saved="refresh" @close="closeEntry" />
      </div>
    </div>

    <div v-if="loading" class="hint">加载中...</div>
    <div v-else-if="filteredItems.length === 0" class="hint">没有匹配的物品</div>

    <div v-else class="items-list-wrap">
      <div class="mobile-list">
        <div v-for="it in filteredItems" :key="it.id" class="mobile-item" :class="rowClass(it)">
          <div class="mobile-line">
            <div class="mobile-title">
              <span v-if="it.code" class="mobile-code">{{ it.code }}</span>
              <span class="mobile-name">{{ it.name || '-' }}</span>
            </div>
            <div class="mobile-qty">{{ it.quantity }}{{ it.unit || '' }}</div>
          </div>
          <div class="mobile-line">
            <div class="mobile-meta">
              {{ displayType(it) }} · {{ displayLocation(it) }} · {{ it.expiry_date ? `到期 ${it.expiry_date}` : '无到期' }}
            </div>
            <div class="mobile-actions">
              <button class="btn-ghost btn-sm" @click="editInEntry(it)">编辑</button>
              <button class="btn-danger btn-sm" @click="remove(it.id)">删除</button>
            </div>
          </div>
        </div>
      </div>

      <table class="table table-desktop">
        <thead>
          <tr>
            <th>编码/名称</th>
            <th>类型/位置</th>
            <th>数量</th>
            <th>状态</th>
            <th>到期</th>
            <th>责任人</th>
            <th>操作</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="it in filteredItems" :key="it.id" :class="rowClass(it)">
            <td class="name" data-label="编码/名称">
              <div class="primary">{{ it.code || '-' }}</div>
              <div class="secondary">{{ it.name }}</div>
            </td>
            <td data-label="类型/位置">
              <div class="primary">{{ displayType(it) }}</div>
              <div class="secondary">{{ displayLocation(it) }}</div>
            </td>
            <td data-label="数量">
              <span class="primary">{{ it.quantity }}</span>
              <span class="secondary">{{ it.unit || '' }}</span>
            </td>
            <td data-label="状态">
              <div class="primary">{{ it.usage_status || '-' }}</div>
              <div class="secondary">{{ it.ownership || '-' }}</div>
            </td>
            <td data-label="到期"><div class="cell-value">{{ it.expiry_date || '-' }}</div></td>
            <td data-label="责任人"><div class="cell-value">{{ it.responsible_person || '-' }}</div></td>
            <td class="ops">
              <button class="btn-ghost btn-sm" @click="editInEntry(it)">编辑</button>
              <button class="btn-danger btn-sm" @click="remove(it.id)">删除</button>
            </td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>

<script>
import { api } from '@/api/http';
import { DEFAULT_CATEGORIES, DEFAULT_LOCATIONS, DEFAULT_UNITS } from '@/config/defaults';
import WarehouseManagePage from '@/components/WarehouseManagePage.vue';
import * as XLSX from 'xlsx';

const EXCEL_COLUMNS = [
  { key: 'id', title: 'ID', exportable: true, importable: true },
  { key: 'code', title: '编码', exportable: true, importable: true },
  { key: 'type_l1', title: '大类', exportable: true, importable: true },
  { key: 'type_l2', title: '小类', exportable: true, importable: true },
  { key: 'name', title: '名称', exportable: true, importable: true, required: true },
  { key: 'brand', title: '品牌', exportable: true, importable: true },
  { key: 'quantity', title: '数量', exportable: true, importable: true, required: true, type: 'int' },
  { key: 'unit', title: '单位', exportable: true, importable: true },
  { key: 'min_quantity', title: '最小库存', exportable: true, importable: true, type: 'int' },
  { key: 'room', title: '房间', exportable: true, importable: true },
  { key: 'spot', title: '位置', exportable: true, importable: true },
  { key: 'location', title: '位置(完整)', exportable: true, importable: true },
  { key: 'category', title: '分类(旧)', exportable: true, importable: true },
  { key: 'description', title: '描述', exportable: true, importable: true },
  { key: 'usage', title: '用途', exportable: true, importable: true },
  { key: 'barcode', title: '条码', exportable: true, importable: true },
  { key: 'tags', title: '标签', exportable: true, importable: true },
  { key: 'notes', title: '备注', exportable: true, importable: true },
  { key: 'purchase_date', title: '购买日期', exportable: true, importable: true, type: 'date' },
  { key: 'production_date', title: '生产日期', exportable: true, importable: true, type: 'date' },
  { key: 'expiry_date', title: '到期日期', exportable: true, importable: true, type: 'date' },
  { key: 'usage_status', title: '使用状态', exportable: true, importable: true },
  { key: 'ownership', title: '归属', exportable: true, importable: true },
  { key: 'price', title: '价格', exportable: true, importable: true, type: 'float' },
  { key: 'value_score', title: '价值评分', exportable: true, importable: true, type: 'float' },
  { key: 'replacement_cycle_days', title: '更换周期(天)', exportable: true, importable: true, type: 'int' },
  { key: 'usage_frequency', title: '使用频率', exportable: true, importable: true },
  { key: 'related_item_ids', title: '关联物品ID/编码', exportable: true, importable: true },
  { key: 'responsible_person', title: '责任人', exportable: true, importable: true },
  { key: 'custom_json', title: '自定义JSON', exportable: true, importable: true },
  { key: 'image_path', title: '图片URL', exportable: true, importable: true },
  { key: 'recorded_at', title: '录入时间(只读)', exportable: true, importable: false },
];

const DEFAULT_TYPE_TREE = {
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
  玩具与游戏: ['手办/模型/盲盒', '积木/拼图', '桌游卡牌', '遥控/电动玩具', '户外玩具', '益智玩具'],
  运动器材: ['球类', '健身器材', '户外运动', '水上运动', '骑行'],
  乐器: ['键盘类', '弦乐', '打击乐', '管乐', '配件'],
  '园艺/户外': ['花盆/种植箱', '土壤/肥料/种子', '浇水工具', '修剪工具', '防护用品'],
  宠物用品: ['食品', '餐具', '寝具', '清洁', '出行', '玩具'],
  其他: ['其他'],
};

const DEFAULT_ROOMS = ['玄关', '厨房', '客厅', '过道', '厕所', '房间1', '房间2', '房间3', '阳台', '其他'];
const DEFAULT_SPOTS = ['整面墙', '柜子', '抽屉', '台面', '床底', '冰箱', '收纳箱', '置物架', '其他'];

export default {
  name: 'ItemsPage',
  components: { WarehouseManagePage },
  data() {
    return {
      loading: false,
      exporting: false,
      importing: false,
      importSummary: '',
      importErrors: [],
      items: [],
      entryOpen: false,
      filters: {
        q: '',
        type_l1: '',
        room: '',
        onlyLowStock: false,
        onlyExpiring: false,
        sort: 'updated',
      },
      categories: [...DEFAULT_CATEGORIES],
      locations: [...DEFAULT_LOCATIONS],
      units: [...DEFAULT_UNITS],
      typeTree: { ...DEFAULT_TYPE_TREE },
      rooms: [...DEFAULT_ROOMS],
      spots: [...DEFAULT_SPOTS],
      responsiblePeople: ['我'],
      uiFold: {
        status: true,
        finance: true,
        dynamic: true,
        custom: true,
      },
      uploadingImage: false,
      customPairs: [{ k: '', v: '' }],
      form: {
        id: null,
        code: '',
        type_l1: '',
        type_l2: '',
        name: '',
        description: '',
        usage: '',
        image_path: '',
        quantity: 0,
        category: '',
        location: '',
        room: '',
        spot: '',
        location_free: '',
        unit: '',
        brand: '',
        min_quantity: 0,
        purchase_date: '',
        production_date: '',
        expiry_date: '',
        recorded_at: '',
        barcode: '',
        tags: '',
        notes: '',
        usage_status: '',
        ownership: '',
        price: null,
        value_score: null,
        replacement_cycle_days: null,
        usage_frequency: '',
        related_item_ids_arr: [],
        responsible_person: '',
        custom_json: '',
      },
    };
  },
  created() {
    this.loadConfig();
    this.refresh();
  },
  computed: {
    typeL1Options() {
      return Object.keys(this.typeTree || {});
    },
    typeL2Options() {
      const l1 = this.form.type_l1 || '';
      return (this.typeTree && this.typeTree[l1]) ? this.typeTree[l1] : [];
    },
    roomOptions() {
      return this.rooms && this.rooms.length > 0 ? this.rooms : DEFAULT_ROOMS;
    },
    spotOptions() {
      return this.spots && this.spots.length > 0 ? this.spots : DEFAULT_SPOTS;
    },
    responsiblePeopleOptions() {
      return this.responsiblePeople && this.responsiblePeople.length > 0 ? this.responsiblePeople : [];
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
      const currId = this.form.id ? Number(this.form.id) : null;
      return this.items.filter(it => it && it.id != null && Number(it.id) !== currId);
    },
    recordedAtText() {
      return this.form.recorded_at || new Date().toISOString();
    },
    lowStockCount() {
      return this.items.filter(it => this.isLowStock(it)).length;
    },
    expiringSoonCount() {
      return this.items.filter(it => this.isExpiringSoon(it)).length;
    },
    filteredItems() {
      const q = (this.filters.q || '').toLowerCase();
      const typeL1 = this.filters.type_l1;
      const room = this.filters.room;
      const onlyLow = this.filters.onlyLowStock;
      const onlyExp = this.filters.onlyExpiring;

      let list = this.items.filter(it => {
        if (typeL1 && (this.getTypeL1(it) || '') !== typeL1) return false;
        if (room && (it.room || '') !== room) return false;
        if (onlyLow && !this.isLowStock(it)) return false;
        if (onlyExp && !this.isExpiringSoon(it)) return false;
        if (!q) return true;
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

      if (this.filters.sort === 'expiry') {
        list = list.slice().sort((a, b) => (a.expiry_date || '9999-12-31').localeCompare(b.expiry_date || '9999-12-31'));
      } else if (this.filters.sort === 'quantity') {
        list = list.slice().sort((a, b) => (a.quantity ?? 0) - (b.quantity ?? 0));
      } else if (this.filters.sort === 'name') {
        list = list.slice().sort((a, b) => (a.name || '').localeCompare(b.name || ''));
      }

      return list;
    },
    importHasErrors() {
      return Array.isArray(this.importErrors) && this.importErrors.length > 0;
    },
  },
  methods: {
    closeEntry() {
      this.entryOpen = false;
    },
    downloadBlob(blob, filename) {
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = filename;
      document.body.appendChild(a);
      a.click();
      a.remove();
      setTimeout(() => URL.revokeObjectURL(url), 1500);
    },
    toIsoDateString(v) {
      if (!v) return '';
      if (v instanceof Date && !Number.isNaN(v.getTime())) {
        const y = v.getFullYear();
        const m = String(v.getMonth() + 1).padStart(2, '0');
        const d = String(v.getDate()).padStart(2, '0');
        return `${y}-${m}-${d}`;
      }
      if (typeof v === 'number' && Number.isFinite(v)) {
        const days = Math.floor(v - 25569);
        const ms = days * 86400 * 1000;
        const dt = new Date(ms);
        if (!Number.isNaN(dt.getTime())) {
          const y = dt.getUTCFullYear();
          const m = String(dt.getUTCMonth() + 1).padStart(2, '0');
          const d = String(dt.getUTCDate()).padStart(2, '0');
          return `${y}-${m}-${d}`;
        }
      }
      const s = String(v).trim();
      if (!s) return '';
      const dt = new Date(s);
      if (!Number.isNaN(dt.getTime())) {
        const y = dt.getFullYear();
        const m = String(dt.getMonth() + 1).padStart(2, '0');
        const d = String(dt.getDate()).padStart(2, '0');
        return `${y}-${m}-${d}`;
      }
      return s;
    },
    normalizeNumber(v, kind) {
      if (v == null) return null;
      if (typeof v === 'number' && Number.isFinite(v)) {
        if (kind === 'int') return Math.trunc(v);
        return v;
      }
      const s = String(v).trim();
      if (!s) return null;
      const n = Number(s);
      if (!Number.isFinite(n)) return null;
      if (kind === 'int') return Math.trunc(n);
      return n;
    },
    normalizeString(v) {
      if (v == null) return null;
      const s = String(v).trim();
      return s ? s : null;
    },
    buildCodeToIdMap() {
      const map = {};
      for (const it of this.items || []) {
        const code = (it && it.code) ? String(it.code).trim() : '';
        if (!code) continue;
        map[code] = it.id;
      }
      return map;
    },
    normalizeRelatedItemIds(v, codeToId) {
      const raw = this.normalizeString(v);
      if (!raw) return null;
      const parts = raw.split(',').map(s => s.trim()).filter(Boolean);
      const mapped = parts.map(p => {
        if (/^\d+$/.test(p)) return p;
        const id = codeToId && codeToId[p];
        return id != null ? String(id) : p;
      });
      return mapped.join(',');
    },
    exportExcel() {
      try {
        this.exporting = true;
        const cols = EXCEL_COLUMNS.filter(c => c.exportable);
        const header = cols.map(c => c.title);
        const rows = (this.filteredItems || []).map(it => {
          const row = {};
          for (const c of cols) {
            let v = it ? it[c.key] : '';
            if (c.type === 'date') v = this.toIsoDateString(v);
            if (c.key === 'recorded_at' && v) {
              const dt = new Date(v);
              if (!Number.isNaN(dt.getTime())) v = dt.toISOString();
            }
            row[c.title] = v == null ? '' : v;
          }
          return row;
        });

        const ws = XLSX.utils.json_to_sheet(rows, { header, skipHeader: false });
        const wb = XLSX.utils.book_new();
        XLSX.utils.book_append_sheet(wb, ws, 'items');
        const out = XLSX.write(wb, { bookType: 'xlsx', type: 'array' });
        const blob = new Blob([out], { type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' });
        const name = `items_${new Date().toISOString().slice(0, 10)}.xlsx`;
        this.downloadBlob(blob, name);
      } finally {
        this.exporting = false;
      }
    },
    downloadImportTemplate() {
      const cols = EXCEL_COLUMNS.filter(c => c.importable);
      const header = cols.map(c => c.title);
      const example = {};
      for (const c of cols) example[c.title] = '';
      const ws = XLSX.utils.json_to_sheet([example], { header, skipHeader: false });
      const wb = XLSX.utils.book_new();
      XLSX.utils.book_append_sheet(wb, ws, 'template');
      const out = XLSX.write(wb, { bookType: 'xlsx', type: 'array' });
      const blob = new Blob([out], { type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' });
      const name = `items_import_template.xlsx`;
      this.downloadBlob(blob, name);
    },
    triggerExcelPick() {
      this.importSummary = '';
      this.importErrors = [];
      const el = this.$refs.excelInput;
      if (el) {
        el.value = '';
        el.click();
      }
    },
    async onExcelPicked(e) {
      const file = e && e.target && e.target.files ? e.target.files[0] : null;
      if (!file) return;
      await this.importExcelFile(file);
      e.target.value = '';
    },
    async importExcelFile(file) {
      this.importing = true;
      this.importSummary = '';
      this.importErrors = [];
      const errors = [];
      let created = 0;
      let updated = 0;
      let skipped = 0;

      try {
        const buf = await file.arrayBuffer();
        const wb = XLSX.read(buf, { type: 'array', cellDates: true });
        const sheetName = wb.SheetNames && wb.SheetNames.length > 0 ? wb.SheetNames[0] : '';
        if (!sheetName) {
          this.importSummary = '导入失败：未找到工作表';
          return;
        }
        const ws = wb.Sheets[sheetName];
        const rawRows = XLSX.utils.sheet_to_json(ws, { defval: '' });
        const cols = EXCEL_COLUMNS.filter(c => c.importable);
        const titleToCol = {};
        for (const c of cols) titleToCol[c.title] = c;

        const hasAnyKnownHeader = rawRows.length > 0 && Object.keys(rawRows[0] || {}).some(k => titleToCol[k]);
        if (!hasAnyKnownHeader) {
          this.importSummary = '导入失败：表头不匹配，请使用“下载导入模板”生成的表格';
          return;
        }

        const codeToId = this.buildCodeToIdMap();

        for (let i = 0; i < rawRows.length; i++) {
          const src = rawRows[i] || {};
          const lineNo = i + 2;
          const dst = {};

          let hasValue = false;
          for (const c of cols) {
            if (!(c.title in src)) continue;
            const v = src[c.title];
            if (v !== '' && v != null) hasValue = true;
            if (c.type === 'int') dst[c.key] = this.normalizeNumber(v, 'int');
            else if (c.type === 'float') dst[c.key] = this.normalizeNumber(v, 'float');
            else if (c.type === 'date') dst[c.key] = this.toIsoDateString(v) || null;
            else if (c.key === 'related_item_ids') dst[c.key] = this.normalizeRelatedItemIds(v, codeToId);
            else if (c.key === 'custom_json') dst[c.key] = this.normalizeString(v);
            else dst[c.key] = this.normalizeString(v);
          }

          if (!hasValue) {
            skipped++;
            continue;
          }

          const name = dst.name;
          if (!name) {
            errors.push(`第${lineNo}行：名称不能为空`);
            continue;
          }

          const quantity = dst.quantity == null ? 0 : dst.quantity;
          if (!Number.isFinite(Number(quantity))) {
            errors.push(`第${lineNo}行：数量格式不正确`);
            continue;
          }
          dst.quantity = Math.trunc(Number(quantity));

          if (dst.custom_json) {
            try {
              const obj = JSON.parse(dst.custom_json);
              if (!obj || typeof obj !== 'object' || Array.isArray(obj)) {
                errors.push(`第${lineNo}行：自定义JSON必须是对象`);
                continue;
              }
            } catch (e) {
              errors.push(`第${lineNo}行：自定义JSON不是合法JSON`);
              continue;
            }
          }

          const id = dst.id != null ? Number(dst.id) : null;
          delete dst.id;

          if (id != null && Number.isFinite(id) && id > 0) {
            const payload = {};
            for (const [k, v] of Object.entries(dst)) {
              if (v === null) continue;
              if (typeof v === 'string' && !v.trim()) continue;
              payload[k] = v;
            }
            payload.quantity = dst.quantity;
            try {
              await api.put(`/api/items/${id}`, payload);
              updated++;
            } catch (e) {
              errors.push(`第${lineNo}行：更新失败（ID=${id}）`);
            }
          } else {
            const payload = {
              code: dst.code || null,
              type_l1: dst.type_l1 || null,
              type_l2: dst.type_l2 || null,
              name: dst.name,
              description: dst.description || null,
              usage: dst.usage || null,
              image_path: dst.image_path || null,
              quantity: dst.quantity,
              category: dst.category || null,
              location: dst.location || null,
              room: dst.room || null,
              spot: dst.spot || null,
              unit: dst.unit || null,
              brand: dst.brand || null,
              min_quantity: dst.min_quantity == null ? 0 : dst.min_quantity,
              purchase_date: dst.purchase_date || null,
              production_date: dst.production_date || null,
              expiry_date: dst.expiry_date || null,
              barcode: dst.barcode || null,
              tags: dst.tags || null,
              notes: dst.notes || null,
              usage_status: dst.usage_status || null,
              ownership: dst.ownership || null,
              price: dst.price == null ? null : dst.price,
              value_score: dst.value_score == null ? null : dst.value_score,
              replacement_cycle_days: dst.replacement_cycle_days == null ? null : dst.replacement_cycle_days,
              usage_frequency: dst.usage_frequency || null,
              related_item_ids: dst.related_item_ids || null,
              responsible_person: dst.responsible_person || null,
              custom_json: dst.custom_json || null,
            };

            try {
              await api.post('/api/items', payload);
              created++;
            } catch (e) {
              errors.push(`第${lineNo}行：创建失败（名称=${dst.name}）`);
            }
          }
        }

        await this.refresh();
      } finally {
        this.importErrors = errors.slice(0, 50);
        const errText = errors.length > 0 ? `，失败${errors.length}条` : '';
        const tip = errors.length > 0 ? `。示例错误：${errors[0]}` : '';
        this.importSummary = `导入完成：新增${created}条，更新${updated}条，跳过${skipped}条${errText}${tip}`;
        this.importing = false;
      }
    },
    async loadConfig() {
      try {
        const res = await api.get('/api/config');
        this.categories = Array.isArray(res.data.categories) ? res.data.categories : [...DEFAULT_CATEGORIES];
        this.locations = Array.isArray(res.data.locations) ? res.data.locations : [...DEFAULT_LOCATIONS];
        this.units = Array.isArray(res.data.units) ? res.data.units : [...DEFAULT_UNITS];
        this.typeTree = (res.data.type_tree && typeof res.data.type_tree === 'object') ? res.data.type_tree : { ...DEFAULT_TYPE_TREE };
        this.rooms = Array.isArray(res.data.rooms) ? res.data.rooms : [...DEFAULT_ROOMS];
        this.spots = Array.isArray(res.data.spots) ? res.data.spots : [...DEFAULT_SPOTS];
        this.responsiblePeople = Array.isArray(res.data.responsible_people) ? res.data.responsible_people : ['我'];
      } catch (e) {
        this.categories = [...DEFAULT_CATEGORIES];
        this.locations = [...DEFAULT_LOCATIONS];
        this.units = [...DEFAULT_UNITS];
        this.typeTree = { ...DEFAULT_TYPE_TREE };
        this.rooms = [...DEFAULT_ROOMS];
        this.spots = [...DEFAULT_SPOTS];
        this.responsiblePeople = ['我'];
      }
    },
    editInEntry(it) {
      this.entryOpen = true;
      this.$nextTick(() => {
        if (this.$refs.entry && typeof this.$refs.entry.editItem === 'function') {
          this.$refs.entry.editItem(it);
        }
        const entryEl = this.$el.querySelector('.entry-wrap');
        if (entryEl) {
          entryEl.classList.add('entry-pulse');
          entryEl.scrollIntoView({ behavior: 'smooth', block: 'start' });
          setTimeout(() => entryEl.classList.remove('entry-pulse'), 600);
        }
      });
    },
    toggle(key) {
      this.uiFold[key] = !this.uiFold[key];
    },
    getTypeL1(it) {
      return it.type_l1 || (it.category || '');
    },
    displayType(it) {
      const l1 = it.type_l1 || '';
      const l2 = it.type_l2 || '';
      if (l1 && l2) return `${l1}-${l2}`;
      if (l1) return l1;
      if (it.category) return it.category;
      return '-';
    },
    displayLocation(it) {
      const room = it.room || '';
      const spot = it.spot || '';
      const loc = it.location || '';
      if (room && spot) return `${room}-${spot}`;
      if (room && loc) return `${room}-${loc}`;
      if (loc) return loc;
      return '-';
    },
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
        if (Array.isArray(res.data)) {
          this.items = res.data;
        } else {
          this.items = [];
          console.warn('ItemsPage expected /api/items to return an array, got:', res.data);
        }
      } catch (e) {
        console.error('Failed to load items:', e);
        this.items = [];
      } finally {
        this.loading = false;
      }
    },
    resetFoldsForNew() {
      this.uiFold.status = true;
      this.uiFold.finance = true;
      this.uiFold.dynamic = true;
      this.uiFold.custom = true;
    },
    resetForm() {
      this.form = {
        id: null,
        code: '',
        type_l1: '',
        type_l2: '',
        name: '',
        description: '',
        usage: '',
        image_path: '',
        quantity: 0,
        category: '',
        location: '',
        room: '',
        spot: '',
        location_free: '',
        unit: '',
        brand: '',
        min_quantity: 0,
        purchase_date: '',
        production_date: '',
        expiry_date: '',
        recorded_at: '',
        barcode: '',
        tags: '',
        notes: '',
        usage_status: '',
        ownership: '',
        price: null,
        value_score: null,
        replacement_cycle_days: null,
        usage_frequency: '',
        related_item_ids_arr: [],
        responsible_person: '',
        custom_json: '',
      };
      this.customPairs = [{ k: '', v: '' }];
      this.resetFoldsForNew();
    },
    startEdit(it) {
      this.form = {
        id: it.id,
        code: it.code || '',
        type_l1: it.type_l1 || '',
        type_l2: it.type_l2 || '',
        name: it.name,
        description: it.description || '',
        usage: it.usage || '',
        image_path: it.image_path || '',
        quantity: it.quantity,
        category: it.category || '',
        location: it.location || '',
        room: it.room || '',
        spot: it.spot || '',
        location_free: '',
        unit: it.unit || '',
        brand: it.brand || '',
        min_quantity: it.min_quantity ?? 0,
        purchase_date: it.purchase_date || '',
        production_date: it.production_date || '',
        expiry_date: it.expiry_date || '',
        recorded_at: it.recorded_at ? String(it.recorded_at) : '',
        barcode: it.barcode || '',
        tags: it.tags || '',
        notes: it.notes || '',
        usage_status: it.usage_status || '',
        ownership: it.ownership || '',
        price: it.price ?? null,
        value_score: it.value_score ?? null,
        replacement_cycle_days: it.replacement_cycle_days ?? null,
        usage_frequency: it.usage_frequency || '',
        related_item_ids_arr: this.parseRelatedIds(it.related_item_ids),
        responsible_person: it.responsible_person || '',
        custom_json: it.custom_json || '',
      };
      this.customPairs = this.parseCustomPairs(it.custom_json);
      this.uiFold.status = !(it.usage_status || it.ownership);
      this.uiFold.finance = !(it.price != null || it.value_score != null || it.replacement_cycle_days != null);
      this.uiFold.dynamic = !(it.usage_frequency || it.related_item_ids || it.responsible_person);
      this.uiFold.custom = !(it.custom_json && String(it.custom_json).trim());
    },
    onTypeL1Change() {
      const l1 = this.form.type_l1 || '';
      const list = (this.typeTree && this.typeTree[l1]) ? this.typeTree[l1] : [];
      if (list.length > 0 && this.form.type_l2 && !list.includes(this.form.type_l2)) {
        this.form.type_l2 = '';
      }
    },
    parseRelatedIds(text) {
      const raw = (text || '').trim();
      if (!raw) return [];
      return raw.split(',').map(s => s.trim()).filter(Boolean);
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
      if (this.customPairs.length === 0) {
        this.customPairs.push({ k: '', v: '' });
      }
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
    clearImage() {
      this.form.image_path = '';
    },
    async onPickImage(e) {
      const file = e && e.target && e.target.files ? e.target.files[0] : null;
      if (!file) return;
      await this.uploadImage(file);
      e.target.value = '';
    },
    async uploadImage(file) {
      this.uploadingImage = true;
      try {
        const fd = new FormData();
        fd.append('file', file);
        const res = await api.post('/api/items/upload_image', fd);
        const url = res.data && res.data.image_url ? res.data.image_url : '';
        if (url) {
          this.form.image_path = url;
        }
      } catch (e) {
        console.error('Failed to upload image:', e);
      } finally {
        this.uploadingImage = false;
      }
    },
    async onSubmit() {
      try {
        const customJson = this.pairsToJson();
        const room = (this.form.room || '').trim();
        const spot = (this.form.spot || '').trim();
        const free = (this.form.location_free || '').trim();
        const location = room && spot ? `${room}-${spot}${free ? `-${free}` : ''}` : (this.form.location || '');
        const payload = {
          code: this.form.code || null,
          type_l1: this.form.type_l1 || null,
          type_l2: this.form.type_l2 || null,
          name: this.form.name,
          description: this.form.description || null,
          usage: this.form.usage || null,
          image_path: this.form.image_path || null,
          quantity: this.form.quantity,
          category: this.form.category || null,
          location: location || null,
          room: room || null,
          spot: spot || null,
          unit: this.form.unit || null,
          brand: this.form.brand || null,
          min_quantity: Number.isFinite(Number(this.form.min_quantity)) ? Number(this.form.min_quantity) : 0,
          purchase_date: this.form.purchase_date || null,
          production_date: this.form.production_date || null,
          expiry_date: this.form.expiry_date || null,
          barcode: this.form.barcode || null,
          tags: this.form.tags || null,
          notes: this.form.notes || null,
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
        if (!window.confirm('确认删除该物品？此操作不可撤销。')) return;
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
.excel-input {
  display: none;
}

.import-summary {
  margin: 10px 0 12px;
  padding: 10px 12px;
  border-radius: 10px;
  background: rgba(17, 24, 39, 0.06);
  border: 1px solid rgba(0, 0, 0, 0.10);
  color: #111827;
  font-size: 13px;
}

.import-summary.danger {
  background: rgba(176, 0, 32, 0.10);
  border-color: rgba(176, 0, 32, 0.20);
  color: #7f0018;
}

.items-page {
  padding: 20px;
  padding-bottom: calc(60px + env(safe-area-inset-bottom, 0px));
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

/* 让上面所有头部模块 不被压缩 */
.header,
.stats,
.filters,
.entry-wrap,
.hint {
  flex-shrink: 0;
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

.entry-wrap {
  background: rgba(255, 255, 255, 0.7);
  padding: 12px;
  border-radius: 8px;
  margin-bottom: 20px;
  border: 1px solid rgba(0, 0, 0, 0.10);
  transition: border-color 0.3s;
}

.entry-wrap.entry-pulse {
  border-color: #007aff;
  animation: entryPulse 0.6s ease;
}

@keyframes entryPulse {
  0% { box-shadow: 0 0 0 0 rgba(0, 122, 255, 0.4); }
  50% { box-shadow: 0 0 0 8px rgba(0, 122, 255, 0.1); }
  100% { box-shadow: 0 0 0 0 rgba(0, 122, 255, 0); }
}

.entry-toggle {
  width: 100%;
  display: flex;
  justify-content: center;
  padding: 10px 12px;
  border-radius: 10px;
  border: 1px solid rgba(0, 0, 0, 0.12);
  background: rgba(17, 24, 39, 0.06);
  cursor: pointer;
}

.entry-body {
  margin-top: 12px;
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
  margin-bottom: 12px;
  flex-wrap: wrap;
}

.row > label {
  flex: 1 1 200px;
}

.row .grow {
  flex: 2 1 300px;
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

input {
  padding: 8px 10px;
  border-radius: 6px;
  border: 1px solid rgba(0, 0, 0, 0.15);
}

textarea {
  padding: 8px 10px;
  border-radius: 6px;
  border: 1px solid rgba(0, 0, 0, 0.15);
  resize: vertical;
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

.section {
  border: 1px solid rgba(0, 0, 0, 0.10);
  border-radius: 10px;
  padding: 12px;
  margin-bottom: 12px;
  background: rgba(255, 255, 255, 0.65);
}

.section.color-core { background: #eff6ff; border-color: #bfdbfe; }
.section.color-time { background: #ecfdf5; border-color: #a7f3d0; }
.section.color-status { background: #fef3c7; border-color: #fde68a; }
.section.color-finance { background: #fef2f2; border-color: #fecaca; }
.section.color-dynamic { background: #f5f3ff; border-color: #ddd6fe; }
.section.color-custom { background: #f3f4f6; border-color: #e5e7eb; }

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
  flex-wrap: wrap;
}

.items-list-wrap {
  flex: 1;
  overflow-y: auto;
  width: 100%;
  padding-right: 4px;
  padding-bottom: 20px;
}

.mobile-list {
  display: none;
  flex-direction: column;
  gap: 10px;
  /*height: 100%;*/
}

.mobile-item {
  border: 1px solid rgba(0, 0, 0, 0.10);
  border-radius: 12px;
  padding: 10px 12px;
  margin-bottom: 20px;
  background: rgba(255, 255, 255, 0.7);
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.mobile-item.row-warn {
  background: rgba(255, 193, 7, 0.12);
}

.mobile-item.row-danger {
  background: rgba(176, 0, 32, 0.12);
}

.mobile-line {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
}

.mobile-title {
  min-width: 0;
  flex: 1;
  display: flex;
  gap: 8px;
  align-items: baseline;
  overflow: hidden;
}

.mobile-code {
  flex: 0 0 auto;
  font-weight: 700;
  color: rgba(0, 0, 0, 0.7);
  white-space: nowrap;
}

.mobile-name {
  min-width: 0;
  flex: 1;
  font-weight: 700;
  overflow: hidden;
  white-space: nowrap;
  text-overflow: ellipsis;
}

.mobile-qty {
  flex: 0 0 auto;
  font-weight: 800;
  white-space: nowrap;
}

.mobile-meta {
  min-width: 0;
  flex: 1;
  color: rgba(0, 0, 0, 0.62);
  font-size: 12px;
  overflow: hidden;
  white-space: nowrap;
  text-overflow: ellipsis;
}

.mobile-actions {
  flex: 0 0 auto;
  display: flex;
  gap: 8px;
}

.mobile-actions button {
  padding: 6px 8px;
  border-radius: 8px;
}

.cell-value {
  min-width: 0;
  overflow-wrap: anywhere;
  word-break: break-word;
}

@media (max-width: 900px) {
  .items-page {
    padding: 12px;
    padding-bottom: calc(80px + env(safe-area-inset-bottom, 0px));
  }
  .stats {
    grid-template-columns: 1fr;
  }
  .filters {
    flex-direction: column;
    align-items: stretch;
  }
  .filter-input,
  .filter-select {
    width: 100%;
    min-width: 0;
  }
  .check {
    width: 100%;
    justify-content: flex-start;
  }
  .ops {
    justify-content: flex-end;
  }

  .table.table-desktop {
    display: none;
  }

  .mobile-list {
    display: flex;
    flex-direction: column;
    gap: 10px;
  }
}
</style>
