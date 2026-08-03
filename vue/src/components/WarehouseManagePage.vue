<template>
  <div class="page" :class="{ embedded }">
    <div v-if="!embedded" class="header">
      <h2>录入/管理</h2>
      <div class="header-actions">
        <router-link class="btn" to="/warehouse/items">物品管理</router-link>
        <router-link class="btn-ghost" to="/warehouse">主页</router-link>
      </div>
    </div>

    <div v-if="!embedded" class="card">
      <div v-if="loadingMessage">加载中...</div>
      <div v-else class="muted">{{ message }}</div>
    </div>

    <div class="grid" :class="{ single: embedded }">
      <div class="panel">
        <div class="panel-title">快速录入</div>

        <div v-if="embedded" class="action-card" ref="actionCard">
          <div class="action-card-status">
            <span class="action-card-label">状态</span>
            <span class="action-card-value">{{ hint || '录入新物品' }}</span>
          </div>
          <div class="action-card-btns">
            <button type="button" class="btn-ghost" @click="$emit('close')">返回</button>
            <button type="button" class="btn-ghost" @click="reset">清空</button>
            <button type="button" class="btn" @click="quickCreate">保存</button>
            <label class="check-inline" title="连续录入：保存后保留位置信息">
              <input v-model="continuousMode" type="checkbox" /> 连续录入
            </label>
            <label class="check-inline" v-if="continuousMode" title="锁定分类：保存后保留分类信息">
              <input v-model="keepCategory" type="checkbox" /> 锁定分类
            </label>
          </div>
        </div>

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
            <button type="button" class="btn-ghost" :disabled="ocrLoading" @click="clearOcr">
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
          <div class="form-sticky-bar" v-if="!embedded">
            <div v-if="hint" class="hint">{{ hint }}</div>
            <div class="row">
              <router-link class="btn-ghost" to="/warehouse/items">返回</router-link>
              <button type="button" class="btn-ghost" @click="reset">清空</button>
              <button type="submit" class="btn">保存</button>
              <button type="button" class="btn-ghost btn-fold-batch" @click="expandAll">全部展开</button>
              <button type="button" class="btn-ghost btn-fold-batch" @click="collapseAll">全部折叠</button>
              <label class="check-inline" title="连续录入：保存后保留位置信息">
                <input v-model="continuousMode" type="checkbox" /> 连续录入
              </label>
              <label class="check-inline" v-if="continuousMode" title="锁定分类：保存后保留分类信息">
                <input v-model="keepCategory" type="checkbox" /> 锁定分类
              </label>
            </div>
          </div>
          <div class="section fold color-core">
            <button class="section-toggle" type="button" @click="toggle('core')">
              <span class="section-title">核心信息</span>
              <span class="toggle-text">{{ uiExpanded.core ? '收起' : '展开' }}</span>
            </button>
          <transition name="collapse">
            <div v-if="uiExpanded.core" class="section-body">
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
                <button type="button" class="btn-ghost" @click="clearItemImage">清除图片</button>
              </div>
            </div>
          </transition>
          </div>

          <div class="section fold color-time">
            <button class="section-toggle" type="button" @click="toggle('time')">
              <span class="section-title">时间空间信息</span>
              <span class="toggle-text">{{ uiExpanded.time ? '收起' : '展开' }}</span>
            </button>
          <transition name="collapse">
            <div v-if="uiExpanded.time" class="section-body">
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
                  区域
                  <select v-model="form.room" :disabled="locationFieldsDisabled" @change="onRoomChange">
                    <option value="">未设置</option>
                    <option v-for="r in areaRoomOptions" :key="r" :value="r">{{ r }}</option>
                  </select>
                </label>
                <template v-if="areaMapEnabled">
                  <label>
                    墙面
                    <select v-model="form.wall_side" :disabled="locationFieldsDisabled" @change="onWallChange">
                      <option value="">未设置</option>
                      <option v-for="w in wallSideOptions" :key="w.value" :value="w.value">{{ w.label }}</option>
                    </select>
                  </label>
                  <label class="grow">
                    收纳位
                    <select v-model="form.wall_slot" :disabled="locationFieldsDisabled">
                      <option value="">未设置</option>
                      <option v-for="s in wallSlotOptions" :key="s" :value="s">{{ s }}</option>
                    </select>
                  </label>
                </template>
                <label v-else class="grow">
                  收纳位
                  <select v-model="form.spot" :disabled="locationFieldsDisabled">
                    <option value="">未设置</option>
                    <option v-for="s in spotOptions" :key="s" :value="s">{{ s }}</option>
                  </select>
                </label>
                <label v-if="showSubSpot" class="grow">
                  细分位置
                  <input v-model.trim="form.location_free" :disabled="locationFieldsDisabled" placeholder="例如：第2层 / 左侧 / 上层" />
                </label>
              </div>
            </div>
          </transition>
          </div>

          <div class="section fold color-status">
            <button class="section-toggle" type="button" @click="toggle('status')">
              <span class="section-title">状态属性信息</span>
              <span class="toggle-text">{{ uiExpanded.status ? '收起' : '展开' }}</span>
            </button>
          <transition name="collapse">
            <div v-if="uiExpanded.status" class="section-body">
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
          </transition>
          </div>

          <div class="section fold color-finance">
            <button class="section-toggle" type="button" @click="toggle('finance')">
              <span class="section-title">财务价值（非必填）</span>
              <span class="toggle-text">{{ uiExpanded.finance ? '收起' : '展开' }}</span>
            </button>
          <transition name="collapse">
            <div v-if="uiExpanded.finance" class="section-body">
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
          </transition>
          </div>

          <div class="section fold color-dynamic">
            <button class="section-toggle" type="button" @click="toggle('dynamic')">
              <span class="section-title">动态维度</span>
              <span class="toggle-text">{{ uiExpanded.dynamic ? '收起' : '展开' }}</span>
            </button>
          <transition name="collapse">
            <div v-if="uiExpanded.dynamic" class="section-body">
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
                  <input v-model.trim="form.responsible_person" placeholder="可选" list="responsible-people" />
                  <datalist id="responsible-people">
                    <option v-for="p in responsiblePeopleOptions" :key="p" :value="p"></option>
                  </datalist>
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
          </transition>
          </div>

          <div class="section fold color-custom">
            <button class="section-toggle" type="button" @click="toggle('custom')">
              <span class="section-title">其他属性（允许自定义）</span>
              <span class="toggle-text">{{ uiExpanded.custom ? '收起' : '展开' }}</span>
            </button>
          <transition name="collapse">
            <div v-if="uiExpanded.custom" class="section-body">
              <div class="kv-head">
                <div>键</div>
                <div>值</div>
                <div></div>
              </div>
              <div v-for="(p, idx) in customPairs" :key="idx" class="kv-row">
                <input v-model.trim="p.k" placeholder="例如：保修期" />
                <input v-model.trim="p.v" placeholder="例如：2年" />
                <button type="button" class="btn-ghost" @click="removePair(idx)">移除</button>
              </div>
              <button type="button" class="btn-ghost" @click="addPair">新增一行</button>
            </div>
          </transition>
          </div>

          <div class="section fold">
            <button class="section-toggle" type="button" @click="toggle('other')">
              <span class="section-title">其他</span>
              <span class="toggle-text">{{ uiExpanded.other ? '收起' : '展开' }}</span>
            </button>
          <transition name="collapse">
            <div v-if="uiExpanded.other" class="section-body">
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
            </div>
          </transition>
          </div>

<!--           <div class="form-sticky-bar" v-if="!embedded">
            <div v-if="hint" class="hint">{{ hint }}</div>
            <div class="row">
              <button type="button" class="btn-ghost" @click="reset">清空</button>
              <button type="submit" class="btn">保存</button>
            </div>
          </div> -->
        </form>
      </div>

    </div>

    <button v-if="embedded && showBackTop" class="back-top-btn" @click="scrollToActionCard" title="回到顶部">
      ↑
    </button>
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
  玩具与游戏: ['手办/模型/盲盒', '积木/拼图', '桌游卡牌', '遥控/电动玩具', '户外玩具', '益智玩具'],
  运动器材: ['球类', '健身器材', '户外运动', '水上运动', '骑行'],
  乐器: ['键盘类', '弦乐', '打击乐', '管乐', '配件'],
  '园艺/户外': ['花盆/种植箱', '土壤/肥料/种子', '浇水工具', '修剪工具', '防护用品'],
  宠物用品: ['食品', '餐具', '寝具', '清洁', '出行', '玩具'],
  其他: ['其他'],
};
 
const DEFAULT_TYPE_TREE = TYPE_TREE;

const DEFAULT_ROOMS = ['玄关', '厨房', '客厅', '过道', '厕所', '房间1', '房间2', '房间3', '阳台', '其他'];
const DEFAULT_SPOTS = ['整面墙', '柜子', '抽屉', '台面', '床底', '冰箱', '收纳箱', '置物架', '其他'];
const WALL_TYPES = [
  { value: 'north', label: '北墙' },
  { value: 'south', label: '南墙' },
  { value: 'east', label: '东墙' },
  { value: 'west', label: '西墙' },
  { value: 'floor', label: '底面' },
];

export default {
  name: 'WarehouseManagePage',
  props: {
    embedded: { type: Boolean, default: false },
  },
  data() {
    return {
      loadingMessage: false,
      loadingItems: false,
      message: '',
      items: [],
      hint: '',
      locationPrefilled: false,
      locationPrefilledId: '',
      showBackTop: false,
      householdId: '',
      continuousMode: false,
      keepCategory: JSON.parse(localStorage.getItem('wh_keep_category') || 'false'),
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
      typeTree: { ...DEFAULT_TYPE_TREE },
      rooms: [...DEFAULT_ROOMS],
      spots: [...DEFAULT_SPOTS],
      responsiblePeople: ['我'],
      areaMap: [],
      uiExpanded: {
        core: true,
        time: true,
        status: false,
        finance: false,
        dynamic: false,
        custom: false,
        other: false,
      },
      uploadingImage: false,
      customPairs: [{ k: '', v: '' }],
      form: {
        id: null,
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
        wall_side: '',
        wall_slot: '',
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
    if (!this.embedded) this.fetchMessage();
    this.fetchItems();
    this.prefillFromRoute();
    this.fetchHouseholdId();
  },
  activated() {
    this.handleScroll();
  },
  mounted() {
    if (!this.embedded && window.innerWidth < 768) {
      const q = this.$route.query;
      const params = new URLSearchParams();
      for (const [k, v] of Object.entries(q)) { if (v != null) params.set(k, String(v)); }
      const qs = params.toString();
      this.$router.replace('/warehouse/wizard' + (qs ? '?' + qs : ''));
      return;
    }
    if (this.embedded) {
      window.addEventListener('scroll', this.handleScroll, true);
      this.$nextTick(() => this.handleScroll());
    }
  },
  beforeUnmount() {
    window.removeEventListener('scroll', this.handleScroll, true);
  },
  watch: {
    '$route.query.location_id'() {
      this.prefillFromRoute();
    },
    keepCategory(val) {
      localStorage.setItem('wh_keep_category', JSON.stringify(val));
    },
  },
  computed: {
    foldPrefsKey() {
      return `wh_fold_prefs_${this.householdId || 'default'}`;
    },
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
    areaMapEnabled() {
      return Array.isArray(this.areaMap) && this.areaMap.length > 0;
    },
    areaRoomOptions() {
      if (!this.areaMapEnabled) return this.roomOptions;
      return this.areaMap
        .map(r => (r && r.name ? String(r.name).trim() : ''))
        .filter(Boolean);
    },
    wallSideOptions() {
      return WALL_TYPES;
    },
    currentAreaRoom() {
      if (!this.areaMapEnabled || !this.form.room) return null;
      return this.areaMap.find(r => r && String(r.name).trim() === String(this.form.room).trim()) || null;
    },
    wallSlotOptions() {
      if (!this.areaMapEnabled) return this.spotOptions;
      if (!this.currentAreaRoom || !this.form.wall_side) return ['整面墙'];
      const walls = this.currentAreaRoom.walls && typeof this.currentAreaRoom.walls === 'object'
        ? this.currentAreaRoom.walls
        : {};
      const w = walls[this.form.wall_side];
      const spots = (w && Array.isArray(w.spots)) ? w.spots : [];
      const names = spots.map(s => (s && s.name ? String(s.name).trim() : '')).filter(Boolean);
      return names.length > 0 ? names : ['整面墙'];
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
      return this.items || [];
    },
    recordedAtText() {
      return this.form.recorded_at || new Date().toISOString();
    },
    locationFieldsDisabled() {
      return this.locationPrefilled;
    },
    showSubSpot() {
      const spot = this.areaMapEnabled
        ? (this.form.wall_slot || '').trim()
        : (this.form.spot || '').trim();
      const subDivisible = ['柜子', '抽屉', '收纳箱', '置物架', '冰箱'];
      return subDivisible.includes(spot);
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
    scrollToActionCard() {
      if (this.$refs.actionCard) {
        this.$refs.actionCard.scrollIntoView({ behavior: 'smooth', block: 'start' });
      }
    },
    handleScroll() {
      if (!this.embedded) return;
      if (this.$refs.actionCard) {
        const rect = this.$refs.actionCard.getBoundingClientRect();
        this.showBackTop = rect.bottom < -20;
      }
    },
    wallLabel(value) {
      const found = WALL_TYPES.find(w => w.value === value);
      return found ? found.label : '';
    },
    wallSlotOptionsFor(roomName, wallSide) {
      if (!this.areaMapEnabled || !roomName || !wallSide) return ['整面墙'];
      const room = this.areaMap.find(r => r && String(r.name).trim() === String(roomName).trim()) || null;
      if (!room) return ['整面墙'];
      const walls = room.walls && typeof room.walls === 'object' ? room.walls : {};
      const w = walls[wallSide];
      const spots = (w && Array.isArray(w.spots)) ? w.spots : [];
      const names = spots.map(s => (s && s.name ? String(s.name).trim() : '')).filter(Boolean);
      return names.length > 0 ? names : ['整面墙'];
    },
    parseWallFromSpot(spot) {
      const raw = (spot || '').trim();
      if (!raw) return { wall_side: '', wall_slot: '' };
      for (const w of WALL_TYPES) {
        const prefix = `${w.label}-`;
        if (raw.startsWith(prefix)) {
          return { wall_side: w.value, wall_slot: raw.slice(prefix.length).trim() || '整面墙' };
        }
      }
      return { wall_side: '', wall_slot: '' };
    },
    ensureWallDefaults() {
      if (!this.areaMapEnabled) return;
      if (!this.form.wall_side) this.form.wall_side = 'north';
      const opts = this.wallSlotOptions;
      const first = (opts && opts[0]) ? opts[0] : '整面墙';
      if (!this.form.wall_slot) this.form.wall_slot = first;
      if (Array.isArray(opts) && opts.length > 0 && !opts.includes(this.form.wall_slot)) {
        this.form.wall_slot = first;
      }
    },
    onRoomChange() {
      if (!this.areaMapEnabled) return;
      this.ensureWallDefaults();
    },
    onWallChange() {
      if (!this.areaMapEnabled) return;
      const opts = this.wallSlotOptions;
      this.form.wall_slot = (opts && opts[0]) ? opts[0] : '整面墙';
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
        this.areaMap = Array.isArray(res.data.area_map) ? res.data.area_map : [];
        if (!this.form.unit) this.form.unit = this.units[0] || '';
        this.ensureWallDefaults();
      } catch (e) {
        this.categories = [...DEFAULT_CATEGORIES];
        this.locations = [...DEFAULT_LOCATIONS];
        this.units = [...DEFAULT_UNITS];
        this.typeTree = { ...DEFAULT_TYPE_TREE };
        this.rooms = [...DEFAULT_ROOMS];
        this.spots = [...DEFAULT_SPOTS];
        this.responsiblePeople = ['我'];
        this.areaMap = [];
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
        if (Array.isArray(res.data)) {
          this.items = res.data;
        } else {
          this.items = [];
          console.warn('WarehouseManagePage expected /api/items to return an array, got:', res.data);
        }
      } catch (e) {
        console.error('Failed to fetch items:', e);
        this.items = [];
      } finally {
        this.loadingItems = false;
      }
    },
    async prefillFromRoute() {
      const locId = this.$route.query.location_id;
      if (!locId || this.embedded) return;
      try {
        const res = await api.get(`/api/public/locations/${locId}`);
        const loc = res.data;
        if (!loc || !loc.path) return;
        const ancestors = loc.path.split('/').filter(Boolean);
        // Fetch all locations to build name→id map (includes zone nodes)
        const ancRes = await api.get('/api/locations');
        // Walk tree to find path segments
        const nameMap = {};
        const walk = (nodes) => {
          if (!nodes) return;
          nodes.forEach(n => {
            nameMap[n.id] = n.name;
            if (n.children) walk(n.children);
          });
        };
        if (ancRes.data) {
          const rootNodes = Array.isArray(ancRes.data) ? ancRes.data : [ancRes.data];
          walk(rootNodes);
        }
        // ancestors[0]=zone, [1]=wall, [2]=unit, [3]=sub
        const zoneName = nameMap[ancestors[0]] || ancestors[0];
        const wallName = ancestors[1] ? (nameMap[ancestors[1]] || ancestors[1]) : '';
        const unitName = ancestors[2] ? (nameMap[ancestors[2]] || ancestors[2]) : '';
        const subName = ancestors[3] ? (nameMap[ancestors[3]] || ancestors[3]) : '';

        const formPatch = { room: zoneName };
        if (this.areaMapEnabled) {
          const wallSide = WALL_TYPES.find(w => w.value === wallName || w.label === wallName);
          formPatch.wall_side = wallSide ? wallSide.value : 'north';
          formPatch.wall_slot = unitName;
        } else {
          formPatch.spot = unitName;
        }
        if (subName) formPatch.location_free = subName;
        this.form = { ...this.form, ...formPatch };
        this.locationPrefilled = true;
        this.locationPrefilledId = String(locId);
        this.continuousMode = true;
      } catch (e) {
        console.error('Failed to prefill from location_id:', e);
      }
    },
    reset() {
      this.hint = '';
      this.form = {
        id: null,
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
        wall_side: '',
        wall_slot: '',
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
      this.uiExpanded.core = true;
      this.uiExpanded.time = true;
      this.uiExpanded.status = false;
      this.uiExpanded.finance = false;
      this.uiExpanded.dynamic = false;
      this.uiExpanded.custom = false;
      this.uiExpanded.other = false;
      this.ensureWallDefaults();
    },
    resetFormForContinuous() {
      // 保存位置字段和预填状态，保留连续模式
      const keep = {
        room: this.form.room,
        spot: this.form.spot,
        wall_side: this.form.wall_side,
        wall_slot: this.form.wall_slot,
        location_free: this.form.location_free,
      };
      if (this.keepCategory) {
        keep.type_l1 = this.form.type_l1;
        keep.type_l2 = this.form.type_l2;
        keep.category = this.form.category;
      }
      const prefilled = this.locationPrefilled;
      const prefilledId = this.locationPrefilledId;
      this.reset();
      this.form = { ...this.form, ...keep };
      this.locationPrefilled = prefilled;
      this.locationPrefilledId = prefilledId;
      this.continuousMode = true;
    },
    _resetAfterSave() {
      if (this.continuousMode) {
        this.resetFormForContinuous();
      } else {
        this.reset();
      }
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
        'location_free',
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
      if (this.areaMapEnabled) {
        const parsed = this.parseWallFromSpot(next.spot);
        if (parsed.wall_side) {
          next.wall_side = parsed.wall_side;
          next.wall_slot = parsed.wall_slot || '整面墙';
        } else {
          const fallbackWall = next.wall_side || 'north';
          const opts = this.wallSlotOptionsFor(next.room, fallbackWall);
          next.wall_side = fallbackWall;
          next.wall_slot = (next.spot && opts.includes(String(next.spot).trim()))
            ? String(next.spot).trim()
            : (opts[0] || '整面墙');
        }
      }
      if (typeof next.quantity === 'string') next.quantity = Number(next.quantity) || 0;
      if (typeof next.min_quantity === 'string') next.min_quantity = Number(next.min_quantity) || 0;
      if (typeof next.price === 'string') next.price = Number(next.price) || null;
      if (typeof next.value_score === 'string') next.value_score = Number(next.value_score) || null;
      if (typeof next.replacement_cycle_days === 'string') next.replacement_cycle_days = Number(next.replacement_cycle_days) || null;
      this.customPairs = this.parseCustomPairs(next.custom_json);
      this.uiExpanded.status = !!(next.usage_status || next.ownership);
      this.uiExpanded.finance = !!(next.price != null || next.value_score != null || next.replacement_cycle_days != null);
      this.uiExpanded.dynamic = !!(next.usage_frequency || (next.related_item_ids_arr && next.related_item_ids_arr.length > 0) || next.responsible_person);
      this.uiExpanded.custom = !!(next.custom_json && String(next.custom_json).trim());
      this.form = next;
      return applied;
    },
    editItem(it) {
      if (!it) return;
      const next = { ...this.form, id: it.id != null ? Number(it.id) : null };
      this.form = next;
      this.applyExtracted(it);
      this.hint = next.id ? `正在编辑 #${next.id}` : '';
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
      this.uiExpanded[key] = !this.uiExpanded[key];
      this.saveFoldPrefs();
    },
    saveFoldPrefs() {
      const key = this.foldPrefsKey;
      localStorage.setItem(key, JSON.stringify(this.uiExpanded));
    },
    loadFoldPrefs() {
      try {
        const raw = localStorage.getItem(this.foldPrefsKey);
        if (raw) {
          const obj = JSON.parse(raw);
          for (const k of Object.keys(this.uiExpanded)) {
            if (typeof obj[k] === 'boolean') this.uiExpanded[k] = obj[k];
          }
        }
      } catch (e) { /* ignore */ }
    },
    async fetchHouseholdId() {
      try {
        const res = await api.get('/api/me');
        if (res.data && res.data.household_id) {
          this.householdId = res.data.household_id;
          this.loadFoldPrefs();
        }
      } catch (e) { /* ignore */ }
    },
    expandAll() {
      for (const k of Object.keys(this.uiExpanded)) this.uiExpanded[k] = true;
      this.saveFoldPrefs();
    },
    collapseAll() {
      for (const k of Object.keys(this.uiExpanded)) this.uiExpanded[k] = false;
      this.saveFoldPrefs();
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
        const spot = this.areaMapEnabled
          ? `${this.wallLabel(this.form.wall_side) || '北墙'}-${(this.form.wall_slot || '').trim() || '整面墙'}`
          : (this.form.spot || '').trim();
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
          location_free: free || null,
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
        if (this.form.id != null) {
          await api.put(`/api/items/${this.form.id}`, payload);
          this.hint = '已更新';
        } else {
          if (this.locationPrefilledId) payload.location_id = this.locationPrefilledId;
          await api.post('/api/items', payload);
          this.hint = '已保存';
        }
        this.$emit('saved');
        await this.fetchItems();
        if (this.embedded) {
          setTimeout(() => this._resetAfterSave(), 2000);
        } else {
          this._resetAfterSave();
        }
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

.page.embedded {
  padding: 0;
  padding-bottom: 0;
  background: transparent;
  border: none;
  border-radius: 0;
  box-shadow: none;
  min-height: auto;
  box-sizing: border-box;
}

/* ─── 卡片式操作栏（桌面端base） ─── */
.action-card {
  position: sticky;
  top: 0;
  z-index: 10;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  margin: 0 0 20px 0;
  padding: 16px 20px;
  background: #fff;
  border-radius: 12px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.08), 0 1px 3px rgba(0, 0, 0, 0.05);
  border: 1px solid rgba(0, 0, 0, 0.06);
}
.action-card-status {
  display: flex;
  flex-direction: column;
  gap: 2px;
  min-width: 0;
}
.action-card-label {
  font-size: 11px;
  color: rgba(0, 0, 0, 0.45);
  text-transform: uppercase;
  letter-spacing: 0.5px;
}
.action-card-value {
  font-size: 15px;
  font-weight: 700;
  color: #1e293b;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
.action-card-btns {
  display: flex;
  gap: 12px;
  flex-shrink: 0;
}
/* ─── 回到顶部浮动按钮 ─── */
.back-top-btn {
  position: fixed;
  right: 24px;
  bottom: 40px;
  z-index: 50;
  width: 44px;
  height: 44px;
  border-radius: 50%;
  border: 1px solid rgba(0, 0, 0, 0.08);
  background: #fff;
  color: #1e293b;
  font-size: 20px;
  font-weight: 700;
  cursor: pointer;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.12);
  display: flex;
  align-items: center;
  justify-content: center;
  animation: fadeInUp 0.2s ease;
}
@keyframes fadeInUp {
  from { opacity: 0; transform: translateY(8px); }
  to { opacity: 1; transform: translateY(0); }
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

.grid {
  display: grid;
  grid-template-columns: 1fr;
  gap: 12px;
  align-items: stretch;
}

.grid.single {
  grid-template-columns: 1fr;
}

.panel {
  background: rgba(255, 255, 255, 0.7);
  border-radius: 10px;
  padding: 14px;
  border: 1px solid rgba(0, 0, 0, 0.10);
  margin-bottom: 20px;
  height: 100%;
  min-width: 0;
  box-sizing: border-box;
}

.panel-title {
  font-weight: 800;
  margin-bottom: 10px;
}

.form-sticky-bar {
  position: sticky;
  top: 0;
  z-index: 10;
  margin-bottom: 14px;
  padding: 12px 0;
  background: rgba(255, 255, 255, 0.92);
  backdrop-filter: blur(6px);
  border-bottom: 1px solid rgba(0, 0, 0, 0.06);
}
.form-sticky-bar .hint {
  text-align: center;
  font-size: 13px;
  margin-bottom: 6px;
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

.check-inline {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  margin-left: 12px;
  font-size: 13px;
  color: rgba(0, 0, 0, 0.55);
  cursor: pointer;
  white-space: nowrap;
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
  .page {
    padding: 12px;
    padding-bottom: calc(80px + env(safe-area-inset-bottom, 0px));
  }
  .page.embedded {
    padding: 0;
    padding-bottom: 0;
  }

  .action-card {
    position: sticky;
    top: 0;
    z-index: 10;
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 12px;
    margin: 0 0 16px 0;
    padding: 14px 16px;
    background: #fff;
    border-radius: 12px;
    box-shadow: 0 2px 12px rgba(0, 0, 0, 0.08), 0 1px 3px rgba(0, 0, 0, 0.05);
    border: 1px solid rgba(0, 0, 0, 0.06);
  }
  .action-card-status {
    display: flex;
    flex-direction: column;
    gap: 2px;
    min-width: 0;
  }
  .action-card-label {
    font-size: 10px;
    color: rgba(0, 0, 0, 0.45);
    text-transform: uppercase;
    letter-spacing: 0.5px;
  }
  .action-card-value {
    font-size: 14px;
    font-weight: 700;
    color: #1e293b;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
  }
  .action-card-btns {
    display: flex;
    gap: 10px;
    flex-shrink: 0;
  }

  .back-top-btn {
    right: 16px;
    bottom: 28px;
    width: 42px;
    height: 42px;
  }

  .grid {
    grid-template-columns: 1fr;
  }
}


/* P2-5 collapse transition */
.collapse-enter-active,
.collapse-leave-active {
  transition: max-height 0.35s ease, opacity 0.3s ease;
  overflow: hidden;
}
.collapse-enter-from,
.collapse-leave-to {
  max-height: 0;
  opacity: 0;
}
.collapse-enter-to,
.collapse-leave-from {
  max-height: 3000px;
  opacity: 1;
}

/* P2-6 batch fold buttons */
.btn-fold-batch {
  font-size: 12px;
  margin-left: 4px;
}
</style>
