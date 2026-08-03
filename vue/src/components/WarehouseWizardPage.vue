<template>
  <div class="wizard-page">
    <div class="wizard-header">
      <button class="btn-back" @click="$router.push('/warehouse')">← 返回</button>
      <h2>录入物品</h2>
    </div>

    <!-- 图片上传区 -->
    <div
      class="image-drop"
      :class="{ 'has-image': !!imagePreview }"
      @click="$refs.imageInput.click()"
    >
      <input
        type="file"
        accept="image/*"
        capture="environment"
        @change="onImagePick"
        ref="imageInput"
        hidden
      />
      <template v-if="!imagePreview">
        <div class="drop-icon">📷</div>
        <div class="drop-text">拍照或选择图片</div>
        <div class="drop-sub">AI 将自动识别物品信息</div>
      </template>
      <img v-else :src="imagePreview" class="preview" />
      <div v-if="imagePreview" class="preview-overlay">点击重新选择</div>
    </div>

    <!-- AI 填充状态 -->
    <div v-if="aiFilling" class="ai-banner">
      <span class="ai-spinner"></span>
      AI 正在识别图片…
    </div>
    <div v-else-if="aiDone" class="ai-banner success">
      已识别 {{ Object.keys(aiFilledFields).length }} 个字段，蓝色边框项为 AI 填充
    </div>

    <!-- 表单区域：分组可折叠 -->
    <div class="form-body">

      <!-- 基本信息 -->
      <section class="form-group">
        <div class="group-header" @click="toggleGroup('basic')">
          <span>基本信息</span>
          <span class="toggle-arrow" :class="{ open: groups.basic }">▾</span>
        </div>
        <div v-show="groups.basic" class="group-body">
          <div class="field">
            <label>物品名称 <span class="required">*</span></label>
            <input
              v-model.trim="form.name"
              ref="nameInput"
              placeholder="输入物品名称…"
              :class="{ 'ai-filled': aiFilledFields.name }"
              @input="clearAiMark('name')"
            />
          </div>
          <div class="field">
            <label>大类</label>
            <select
              v-model="form.type_l1"
              :class="{ 'ai-filled': aiFilledFields.type_l1 }"
              @change="clearAiMark('type_l1')"
            >
              <option value="">选择大类…</option>
              <option v-for="t in typeL1Options" :key="t" :value="t">{{ t }}</option>
            </select>
          </div>
          <div class="field">
            <label>小类</label>
            <select
              v-model="form.type_l2"
              :class="{ 'ai-filled': aiFilledFields.type_l2 }"
              @change="clearAiMark('type_l2')"
            >
              <option value="">选择小类…</option>
              <option v-for="t in typeL2Options" :key="t" :value="t">{{ t }}</option>
            </select>
          </div>
          <div class="field-row">
            <div class="field" style="flex:2">
              <label>数量</label>
              <input
                v-model.number="form.quantity"
                type="number"
                min="0"
                :class="{ 'ai-filled': aiFilledFields.quantity }"
                @input="clearAiMark('quantity')"
              />
            </div>
            <div class="field" style="flex:1">
              <label>单位</label>
              <input
                v-model.trim="form.unit"
                placeholder="个"
                :class="{ 'ai-filled': aiFilledFields.unit }"
                @input="clearAiMark('unit')"
              />
            </div>
          </div>
          <div class="field">
            <label>品牌</label>
            <input
              v-model.trim="form.brand"
              placeholder="品牌名称…"
              :class="{ 'ai-filled': aiFilledFields.brand }"
              @input="clearAiMark('brand')"
            />
          </div>
        </div>
      </section>

      <!-- 位置信息 -->
      <section class="form-group">
        <div class="group-header" @click="toggleGroup('location')">
          <span>位置信息</span>
          <span class="toggle-arrow" :class="{ open: groups.location }">▾</span>
        </div>
        <div v-show="groups.location" class="group-body">
          <div class="field">
            <label>区域</label>
            <select
              v-model="form.room"
              :disabled="locationFieldsDisabled"
              :class="{ 'ai-filled': aiFilledFields.room }"
              @change="clearAiMark('room')"
            >
              <option value="">选择区域…</option>
              <option v-for="r in roomOptions" :key="r" :value="r">{{ r }}</option>
              <option v-if="form.room && !roomOptions.includes(form.room)" :value="form.room">{{ form.room }}（不在列表中）</option>
            </select>
          </div>
          <div class="field">
            <label>收纳位</label>
            <select
              v-model="form.spot"
              :disabled="locationFieldsDisabled"
              :class="{ 'ai-filled': aiFilledFields.spot }"
              @change="clearAiMark('spot')"
            >
              <option value="">选择收纳位…</option>
              <option v-for="s in spotOptions" :key="s" :value="s">{{ s }}</option>
            </select>
          </div>
          <div class="field" v-if="showSubSpot">
            <label>细分位置</label>
            <input
              v-model.trim="form.location_free"
              placeholder="如：第2层"
              :disabled="locationFieldsDisabled"
              :class="{ 'ai-filled': aiFilledFields.location_free }"
              @input="clearAiMark('location_free')"
            />
          </div>
          <div class="field" v-if="areaMapEnabled">
            <label>墙面</label>
            <select
              v-model="form.wall_side"
              :disabled="locationFieldsDisabled"
              :class="{ 'ai-filled': aiFilledFields.wall_side }"
              @change="clearAiMark('wall_side')"
            >
              <option value="">选择墙面…</option>
              <option v-for="w in wallSideOptions" :key="w" :value="w">{{ w }}</option>
            </select>
          </div>
          <div class="field" v-if="areaMapEnabled">
            <label>墙面槽位</label>
            <input
              v-model.trim="form.wall_slot"
              placeholder="如：上格"
              :disabled="locationFieldsDisabled"
              :class="{ 'ai-filled': aiFilledFields.wall_slot }"
              @input="clearAiMark('wall_slot')"
            />
          </div>
        </div>
      </section>

      <!-- 时间状态 -->
      <section class="form-group">
        <div class="group-header" @click="toggleGroup('time')">
          <span>时间状态</span>
          <span class="toggle-arrow" :class="{ open: groups.time }">▾</span>
        </div>
        <div v-show="groups.time" class="group-body">
          <div class="field-row">
            <div class="field" style="flex:1">
              <label>购买日期</label>
              <input
                v-model="form.purchase_date"
                type="date"
                :class="{ 'ai-filled': aiFilledFields.purchase_date }"
                @input="clearAiMark('purchase_date')"
              />
            </div>
            <div class="field" style="flex:1">
              <label>保质期</label>
              <input
                v-model="form.expiry_date"
                type="date"
                :class="{ 'ai-filled': aiFilledFields.expiry_date }"
                @input="clearAiMark('expiry_date')"
              />
            </div>
          </div>
          <div class="field-row">
            <div class="field" style="flex:1">
              <label>使用状态</label>
              <select
                v-model="form.usage_status"
                :class="{ 'ai-filled': aiFilledFields.usage_status }"
                @change="clearAiMark('usage_status')"
              >
                <option value="">选择状态…</option>
                <option value="在用">在用</option>
                <option value="闲置">闲置</option>
                <option value="已用完">已用完</option>
              </select>
            </div>
            <div class="field" style="flex:1">
              <label>归属</label>
              <select
                v-model="form.ownership"
                :class="{ 'ai-filled': aiFilledFields.ownership }"
                @change="clearAiMark('ownership')"
              >
                <option value="">选择归属…</option>
                <option value="个人">个人</option>
                <option value="家庭">家庭</option>
                <option value="公司">公司</option>
              </select>
            </div>
          </div>
        </div>
      </section>

      <!-- 财务信息 -->
      <section class="form-group">
        <div class="group-header" @click="toggleGroup('finance')">
          <span>财务信息</span>
          <span class="toggle-arrow" :class="{ open: groups.finance }">▾</span>
        </div>
        <div v-show="groups.finance" class="group-body">
          <div class="field-row">
            <div class="field" style="flex:1">
              <label>价格 (元)</label>
              <input
                v-model.number="form.price"
                type="number"
                step="0.01"
                min="0"
                placeholder="0.00"
                :class="{ 'ai-filled': aiFilledFields.price }"
                @input="clearAiMark('price')"
              />
            </div>
            <div class="field" style="flex:1">
              <label>价值评分 (0-5)</label>
              <input
                v-model.number="form.value_score"
                type="number"
                step="0.1"
                min="0"
                max="5"
                placeholder="3.0"
                :class="{ 'ai-filled': aiFilledFields.value_score }"
                @input="clearAiMark('value_score')"
              />
            </div>
          </div>
        </div>
      </section>

      <!-- 补充信息 -->
      <section class="form-group">
        <div class="group-header" @click="toggleGroup('extra')">
          <span>补充信息</span>
          <span class="toggle-arrow" :class="{ open: groups.extra }">▾</span>
        </div>
        <div v-show="groups.extra" class="group-body">
          <div class="field">
            <label>负责人</label>
            <select
              v-model="form.responsible_person"
              :class="{ 'ai-filled': aiFilledFields.responsible_person }"
              @change="clearAiMark('responsible_person')"
            >
              <option value="">选择负责人…</option>
              <option v-for="p in personOptions" :key="p" :value="p">{{ p }}</option>
            </select>
          </div>
          <div class="field">
            <label>备注</label>
            <textarea
              v-model.trim="form.notes"
              rows="3"
              placeholder="备注信息…"
              :class="{ 'ai-filled': aiFilledFields.notes }"
              @input="clearAiMark('notes')"
            ></textarea>
          </div>
          <div class="field">
            <label>标签</label>
            <input
              v-model.trim="form.tags"
              placeholder="逗号分隔多个标签"
              :class="{ 'ai-filled': aiFilledFields.tags }"
              @input="clearAiMark('tags')"
            />
          </div>
        </div>
      </section>
    </div>

    <!-- 底部保存 -->
    <div class="wizard-footer">
      <button class="btn-primary" :disabled="saving" @click="submitWizard" style="width:100%">
        {{ saving ? '保存中…' : '保存物品' }}
      </button>
    </div>

    <div v-if="hint" class="hint" :class="{ 'hint-error': hintType === 'error' }">{{ hint }}</div>
  </div>
</template>

<script>
import { api } from '@/api/http';

export default {
  name: 'WarehouseWizardPage',
  data() {
    return {
      groups: {
        basic: true,
        location: false,
        time: false,
        finance: false,
        extra: false,
      },
      saving: false,
      hint: '',
      hintType: 'success',
      aiFilling: false,
      aiDone: false,
      aiFilledFields: {},
      form: {
        name: '',
        type_l1: '',
        type_l2: '',
        quantity: 1,
        unit: '',
        brand: '',
        image_path: '',
        room: '',
        spot: '',
        location_free: '',
        wall_side: '',
        wall_slot: '',
        expiry_date: '',
        purchase_date: '',
        usage_status: '',
        ownership: '',
        price: null,
        value_score: null,
        responsible_person: '',
        notes: '',
        tags: '',
      },
      typeL1Options: [],
      typeL2Options: [],
      roomOptions: [],
      spotOptions: [],
      personOptions: [],
      wallSideOptions: [],
      locationPrefilled: false,
      locationPrefilledId: '',
      imageFile: null,
      imagePreview: '',
      areaMapEnabled: false,
    };
  },
  computed: {
    showSubSpot() {
      const spot = (this.form.spot || '').trim();
      const subSpotItems = ['柜子', '抽屉', '收纳箱', '置物架', '冰箱'];
      return subSpotItems.includes(spot);
    },
    locationFieldsDisabled() {
      return this.locationPrefilled;
    },
  },
  watch: {
    'form.type_l1'(val) {
      const tree = this._configTypeTree || {};
      this.typeL2Options = tree[val] || [];
      if (this.form.type_l2 && !this.typeL2Options.includes(this.form.type_l2)) {
        this.form.type_l2 = '';
      }
    },
  },
  async mounted() {
    await this.loadConfig();
    await this.prefillFromRoute();
    this.$nextTick(() => { this.$refs.nameInput && this.$refs.nameInput.focus(); });
  },
  methods: {
    toggleGroup(key) {
      this.groups[key] = !this.groups[key];
    },
    clearAiMark(key) {
      if (this.aiFilledFields[key]) {
        this.$delete(this.aiFilledFields, key);
      }
    },

    async loadConfig() {
      try {
        const res = await api.get('/api/config');
        const d = res.data || {};
        const tree = d.type_tree || {};
        this.typeL1Options = Object.keys(tree);
        this.roomOptions = Array.isArray(d.rooms) ? d.rooms : [];
        this.spotOptions = Array.isArray(d.spots) ? d.spots : [];
        this.personOptions = Array.isArray(d.responsible_people) ? d.responsible_people : [];
        this._configTypeTree = tree;
        this._configLocations = Array.isArray(d.locations) ? d.locations : [];
        this._configUnits = Array.isArray(d.units) ? d.units : [];

        // area_map
        const areaMap = d.area_map;
        if (Array.isArray(areaMap) && areaMap.length > 0) {
          this.areaMapEnabled = true;
          this.wallSideOptions = ['north', 'south', 'east', 'west', 'floor'];
        }
      } catch (e) { /* ignore */ }
    },

    async prefillFromRoute() {
      const locId = this.$route.query.location_id;
      if (!locId) return;
      try {
        const locRes = await api.get(`/api/public/locations/${locId}`);
        const loc = locRes.data;
        if (!loc || !loc.path) return;
        const ancestors = loc.path.split('/').filter(Boolean);

        const ancRes = await api.get('/api/locations');
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

        const zoneName = nameMap[ancestors[0]] || ancestors[0];
        const unitName = ancestors[2] ? (nameMap[ancestors[2]] || ancestors[2]) : '';
        const subName = ancestors[3] ? (nameMap[ancestors[3]] || ancestors[3]) : '';

        this.form.room = zoneName;
        this.form.spot = unitName;
        if (subName) this.form.location_free = subName;
        this.locationPrefilled = true;
        this.locationPrefilledId = String(locId);
        this.groups.location = true;
      } catch (e) {
        console.error('Failed to prefill from location_id:', e);
      }
    },

    onImagePick(e) {
      const f = e && e.target && e.target.files ? e.target.files[0] : null;
      if (!f) return;
      this.imageFile = f;
      const reader = new FileReader();
      reader.onload = (ev) => {
        this.imagePreview = ev.target.result;
      };
      reader.readAsDataURL(f);
      this.runAiExtract(f);
    },

    async runAiExtract(file) {
      this.aiFilling = true;
      this.aiDone = false;
      this.hint = '';
      try {
        const fd = new FormData();
        fd.append('file', file);
        const res = await api.post('/api/ocr/item_extract', fd);
        const extracted = res.data && res.data.extracted ? res.data.extracted : {};
        this.aiFillForm(extracted);
        this.aiDone = true;
      } catch (e) {
        const msg = this.errorText(e, 'AI 识别');
        this.hint = msg;
        this.hintType = 'error';
      } finally {
        this.aiFilling = false;
      }
    },

    aiFillForm(extracted) {
      const filled = {};
      const mapper = {
        name: 'name',
        type_l1: 'type_l1',
        type_l2: 'type_l2',
        quantity: 'quantity',
        unit: 'unit',
        brand: 'brand',
        room: 'room',
        spot: 'spot',
        location_free: 'location_free',
        wall_side: 'wall_side',
        wall_slot: 'wall_slot',
        expiry_date: 'expiry_date',
        purchase_date: 'purchase_date',
        usage_status: 'usage_status',
        ownership: 'ownership',
        price: 'price',
        value_score: 'value_score',
        responsible_person: 'responsible_person',
        notes: 'notes',
        tags: 'tags',
      };

      for (const [apiKey, formKey] of Object.entries(mapper)) {
        const val = extracted[apiKey];
        if (val === null || val === undefined || val === '') continue;
        if (apiKey === 'quantity') {
          const n = Number(val);
          if (n > 0) {
            this.form[formKey] = n;
            filled[formKey] = true;
          }
          continue;
        }
        if (apiKey === 'price' || apiKey === 'value_score') {
          const n = Number(val);
          if (!isNaN(n)) {
            this.form[formKey] = n;
            filled[formKey] = true;
          }
          continue;
        }
        this.form[formKey] = val;
        filled[formKey] = true;
      }

      this.aiFilledFields = filled;

      // Auto-expand groups that received AI-filled data
      if (filled.name || filled.type_l1 || filled.type_l2 || filled.quantity || filled.unit || filled.brand) {
        this.groups.basic = true;
      }
      if (filled.room || filled.spot || filled.location_free || filled.wall_side || filled.wall_slot) {
        this.groups.location = true;
      }
      if (filled.expiry_date || filled.purchase_date || filled.usage_status || filled.ownership) {
        this.groups.time = true;
      }
      if (filled.price || filled.value_score) {
        this.groups.finance = true;
      }
      if (filled.responsible_person || filled.notes || filled.tags) {
        this.groups.extra = true;
      }
    },

    async uploadImage() {
      if (!this.imageFile) return '';
      const fd = new FormData(); fd.append('file', this.imageFile);
      const res = await api.post('/api/items/upload_image', fd);
      return res.data && res.data.image_url ? res.data.image_url : '';
    },

    async submitWizard() {
      if (!this.form.name.trim()) {
        this.hint = '请输入物品名称';
        this.hintType = 'error';
        return;
      }
      this.saving = true;
      this.hint = '';
      try {
        let imageUrl = '';
        if (this.imageFile) {
          imageUrl = await this.uploadImage();
        }
        const free = (this.form.location_free || '').trim();
        const locationParts = [this.form.room, this.form.spot];
        if (free) locationParts.push(free);
        const locationStr = locationParts.filter(Boolean).join('-');

        const payload = {
          name: this.form.name.trim(),
          type_l1: this.form.type_l1 || null,
          type_l2: this.form.type_l2 || null,
          quantity: this.form.quantity || 1,
          unit: this.form.unit || null,
          image_path: imageUrl || null,
          room: this.form.room || null,
          spot: this.form.spot || null,
          location_free: free || null,
          wall_side: this.form.wall_side || null,
          wall_slot: this.form.wall_slot || null,
          location: locationStr || null,
          expiry_date: this.form.expiry_date || null,
          purchase_date: this.form.purchase_date || null,
          usage_status: this.form.usage_status || null,
          ownership: this.form.ownership || null,
          price: this.form.price || null,
          value_score: this.form.value_score || null,
          brand: this.form.brand || null,
          responsible_person: this.form.responsible_person || null,
          notes: this.form.notes || null,
          tags: this.form.tags || null,
        };
        if (this.locationPrefilledId) payload.location_id = this.locationPrefilledId;

        await api.post('/api/items', payload);
        this.hint = '保存成功！';
        this.hintType = 'success';

        this.resetForm();
        this.$nextTick(() => { this.$refs.nameInput && this.$refs.nameInput.focus(); });
      } catch (e) {
        this.hint = this.errorText(e, '保存');
        this.hintType = 'error';
      } finally {
        this.saving = false;
      }
    },

    resetForm() {
      const keepLocation = this.$route.query.location_id;
      const saved = {
        room: keepLocation ? this.form.room : '',
        spot: keepLocation ? this.form.spot : '',
        location_free: keepLocation ? this.form.location_free : '',
      };
      this.form = {
        name: '',
        type_l1: '',
        type_l2: '',
        quantity: 1,
        unit: '',
        image_path: '',
        room: saved.room,
        spot: saved.spot,
        location_free: saved.location_free,
        wall_side: '',
        wall_slot: '',
        expiry_date: '',
        purchase_date: '',
        usage_status: '',
        ownership: '',
        price: null,
        value_score: null,
        brand: '',
        responsible_person: '',
        notes: '',
        tags: '',
      };
      this.imageFile = null;
      this.imagePreview = '';
      this.aiFilledFields = {};
      this.aiDone = false;
    },

    errorText(e, action) {
      const status = e && e.response ? e.response.status : null;
      const detail = e && e.response && e.response.data && e.response.data.detail ? String(e.response.data.detail) : '';
      if (status === 401) return `${action}失败：未登录`;
      if (status) return `${action}失败：HTTP ${status}${detail ? ' (' + detail + ')' : ''}`;
      return `${action}失败：无法连接服务器`;
    },
  },
};
</script>

<style scoped>
.wizard-page {
  max-width: 520px;
  margin: 0 auto;
  padding: 16px;
  min-height: 100vh;
  min-height: 100dvh;
  display: flex;
  flex-direction: column;
  box-sizing: border-box;
  padding-bottom: calc(80px + env(safe-area-inset-bottom, 0px));
}

.wizard-header {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 12px;
  flex-shrink: 0;
}
.wizard-header h2 { margin: 0; font-size: 18px; }
.btn-back {
  padding: 6px 10px;
  border: 1px solid #d1d5db;
  background: white;
  border-radius: 6px;
  cursor: pointer;
  font-size: 14px;
}

/* Image drop zone */
.image-drop {
  border: 2px dashed #d1d5db;
  border-radius: 12px;
  padding: 32px 16px;
  text-align: center;
  cursor: pointer;
  margin-bottom: 12px;
  transition: border-color 0.2s, background 0.2s;
  position: relative;
  overflow: hidden;
  flex-shrink: 0;
}
.image-drop:hover { border-color: #3b82f6; }
.image-drop.has-image { padding: 0; border-style: solid; }
.drop-icon { font-size: 36px; margin-bottom: 8px; }
.drop-text { font-size: 15px; font-weight: 600; color: #374151; }
.drop-sub { font-size: 12px; color: #9ca3af; margin-top: 4px; }
.preview {
  width: 100%;
  max-height: 200px;
  object-fit: cover;
  display: block;
}
.preview-overlay {
  position: absolute;
  inset: 0;
  background: rgba(0,0,0,0.35);
  color: white;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 14px;
  opacity: 0;
  transition: opacity 0.2s;
}
.image-drop.has-image:hover .preview-overlay { opacity: 1; }

/* AI banner */
.ai-banner {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 12px;
  border-radius: 8px;
  background: #eff6ff;
  border: 1px solid #bfdbfe;
  color: #1d4ed8;
  font-size: 13px;
  margin-bottom: 12px;
  flex-shrink: 0;
}
.ai-banner.success {
  background: #f0fdf4;
  border-color: #bbf7d0;
  color: #166534;
}
.ai-spinner {
  width: 14px;
  height: 14px;
  border: 2px solid #bfdbfe;
  border-top-color: #3b82f6;
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
  flex-shrink: 0;
}
@keyframes spin { to { transform: rotate(360deg); } }

/* Form body */
.form-body {
  flex: 1;
  min-height: 0;
  overflow-y: auto;
}

/* Form groups */
.form-group {
  border: 1px solid #e5e7eb;
  border-radius: 10px;
  margin-bottom: 10px;
  overflow: hidden;
}
.group-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 14px;
  background: #f9fafb;
  font-size: 14px;
  font-weight: 700;
  color: #374151;
  cursor: pointer;
  user-select: none;
}
.toggle-arrow {
  font-size: 12px;
  color: #9ca3af;
  transition: transform 0.2s;
}
.toggle-arrow.open { transform: rotate(180deg); }
.group-body {
  padding: 14px;
  display: flex;
  flex-direction: column;
  gap: 14px;
}

/* Fields */
.field {
  display: flex;
  flex-direction: column;
  gap: 4px;
}
.field-row {
  display: flex;
  gap: 12px;
}
.field label {
  font-size: 13px;
  font-weight: 600;
  color: #374151;
}
.required { color: #ef4444; }
.field input,
.field select,
.field textarea {
  padding: 10px 12px;
  border: 1px solid #d1d5db;
  border-radius: 8px;
  font-size: 15px;
  background: white;
  width: 100%;
  box-sizing: border-box;
  -webkit-appearance: none;
  transition: border-color 0.2s, box-shadow 0.2s;
}
.field input:disabled,
.field select:disabled {
  background: #f3f4f6;
  color: #6b7280;
}
.field textarea {
  resize: vertical;
  font-family: inherit;
}

/* AI-filled marker */
.ai-filled {
  border-color: #3b82f6 !important;
  box-shadow: 0 0 0 1px #3b82f6;
  background: #f8faff;
}

/* Footer */
.wizard-footer {
  flex-shrink: 0;
  padding-top: 12px;
  border-top: 1px solid #f3f4f6;
}
.btn-primary {
  padding: 12px 0;
  border: none;
  background: #3b82f6;
  color: white;
  border-radius: 8px;
  cursor: pointer;
  font-size: 16px;
  font-weight: 600;
}
.btn-primary:disabled { opacity: 0.5; cursor: not-allowed; }

.hint {
  margin-top: 10px;
  padding: 8px 12px;
  background: #f0fdf4;
  border: 1px solid #bbf7d0;
  border-radius: 8px;
  font-size: 13px;
  color: #166534;
  flex-shrink: 0;
}
.hint-error {
  background: #fef2f2;
  border-color: #fecaca;
  color: #dc2626;
}
</style>
