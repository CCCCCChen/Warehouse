<template>
  <div class="wizard-page">
    <div class="wizard-header">
      <button class="btn-back" @click="$router.push('/warehouse')">← 返回</button>
      <h2>录入物品</h2>
    </div>

    <!-- 进度条 -->
    <div class="progress-bar">
      <div class="progress-fill" :style="{ width: ((currentStep + 1) / 5 * 100) + '%' }"></div>
    </div>
    <div class="step-labels">
      <span
        v-for="(s, idx) in steps"
        :key="idx"
        class="step-label"
        :class="{ active: idx === currentStep, done: idx < currentStep }"
        :style="{ cursor: idx <= currentStep ? 'pointer' : 'default' }"
        @click="goToStep(idx)"
      >
        <span class="step-num">{{ idx + 1 }}</span>
        {{ s }}
      </span>
    </div>

    <!-- 步骤内容 -->
    <div class="step-content">
      <!-- 步骤1: 核心信息 -->
      <div v-show="currentStep === 0" class="step-panel">
        <div class="field">
          <label>物品名称 <span class="required">*</span></label>
          <input v-model.trim="form.name" ref="nameInput" placeholder="输入物品名称…" />
        </div>
        <div class="field">
          <label>大类</label>
          <select v-model="form.type_l1">
            <option value="">选择大类…</option>
            <option v-for="t in typeL1Options" :key="t" :value="t">{{ t }}</option>
          </select>
        </div>
        <div class="field">
          <label>小类</label>
          <select v-model="form.type_l2">
            <option value="">选择小类…</option>
            <option v-for="t in typeL2Options" :key="t" :value="t">{{ t }}</option>
          </select>
        </div>
        <div class="field">
          <label>数量</label>
          <input v-model.number="form.quantity" type="number" min="0" />
        </div>
        <div class="field">
          <label>物品图片</label>
          <div class="image-upload">
            <input type="file" accept="image/*" @change="onImagePick" ref="imageInput" />
            <button class="btn-ghost" @click="$refs.imageInput.click()">选择图片</button>
            <img v-if="form.image_path" :src="form.image_path" class="preview" />
          </div>
        </div>
      </div>

      <!-- 步骤2: 位置信息 -->
      <div v-show="currentStep === 1" class="step-panel">
        <div class="field">
          <label>区域</label>
          <select v-model="form.room" :disabled="locationFieldsDisabled">
            <option value="">选择区域…</option>
            <option v-for="r in roomOptions" :key="r" :value="r">{{ r }}</option>
          </select>
        </div>
        <div class="field">
          <label>收纳位</label>
          <select v-model="form.spot" :disabled="locationFieldsDisabled">
            <option value="">选择收纳位…</option>
            <option v-for="s in spotOptions" :key="s" :value="s">{{ s }}</option>
          </select>
        </div>
        <div class="field" v-if="showSubSpot">
          <label>细分位置</label>
          <input v-model.trim="form.location_free" placeholder="如：第2层" :disabled="locationFieldsDisabled" />
        </div>
      </div>

      <!-- 步骤3: 时间状态 -->
      <div v-show="currentStep === 2" class="step-panel">
        <div class="field">
          <label>保质期</label>
          <input v-model="form.expiry_date" type="date" />
        </div>
        <div class="field">
          <label>购买日期</label>
          <input v-model="form.purchase_date" type="date" />
        </div>
        <div class="field">
          <label>使用状态</label>
          <select v-model="form.usage_status">
            <option value="">选择状态…</option>
            <option value="在用">在用</option>
            <option value="闲置">闲置</option>
            <option value="待处理">待处理</option>
            <option value="已用完">已用完</option>
          </select>
        </div>
        <div class="field">
          <label>归属</label>
          <select v-model="form.ownership">
            <option value="">选择归属…</option>
            <option value="个人">个人</option>
            <option value="家庭">家庭</option>
            <option value="公司">公司</option>
          </select>
        </div>
      </div>

      <!-- 步骤4: 财务信息 -->
      <div v-show="currentStep === 3" class="step-panel">
        <div class="field">
          <label>价格 (元)</label>
          <input v-model.number="form.price" type="number" step="0.01" min="0" placeholder="0.00" />
        </div>
        <div class="field">
          <label>价值评分 (0-5)</label>
          <input v-model.number="form.value_score" type="number" step="0.1" min="0" max="5" placeholder="3.0" />
        </div>
      </div>

      <!-- 步骤5: 补充信息 -->
      <div v-show="currentStep === 4" class="step-panel">
        <div class="field">
          <label>品牌</label>
          <input v-model.trim="form.brand" placeholder="品牌名称…" />
        </div>
        <div class="field">
          <label>负责人</label>
          <select v-model="form.responsible_person">
            <option value="">选择负责人…</option>
            <option v-for="p in personOptions" :key="p" :value="p">{{ p }}</option>
          </select>
        </div>
        <div class="field">
          <label>备注</label>
          <textarea v-model.trim="form.notes" rows="3" placeholder="备注信息…"></textarea>
        </div>
        <div class="field">
          <label>标签</label>
          <input v-model.trim="form.tags" placeholder="逗号分隔多个标签" />
        </div>
      </div>
    </div>

    <!-- 底部导航 -->
    <div class="wizard-footer">
      <button v-if="currentStep > 0" class="btn-ghost" @click="currentStep--">上一步</button>
      <div class="spacer"></div>
      <button v-if="currentStep < 4" class="btn-primary" @click="currentStep++">下一步</button>
      <button v-else class="btn-primary" :disabled="saving" @click="submitWizard">
        {{ saving ? '保存中…' : '保存物品' }}
      </button>
    </div>

    <div v-if="hint" class="hint">{{ hint }}</div>
  </div>
</template>

<script>
import { api } from '@/api/http';

export default {
  name: 'WarehouseWizardPage',
  data() {
    return {
      steps: ['核心信息', '位置信息', '时间状态', '财务信息', '补充信息'],
      currentStep: 0,
      saving: false,
      hint: '',
      form: {
        name: '',
        type_l1: '',
        type_l2: '',
        quantity: 1,
        image_path: '',
        room: '',
        spot: '',
        location_free: '',
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
      },
      typeL1Options: [],
      typeL2Options: [],
      roomOptions: [],
      spotOptions: [],
      personOptions: [],
      locationPrefilled: false,
      locationPrefilledId: '',
      imageFile: null,
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
  async mounted() {
    await this.loadConfig();
    await this.prefillFromRoute();
    this.$nextTick(() => { this.$refs.nameInput && this.$refs.nameInput.focus(); });
  },
  methods: {
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
      } catch (e) { /* ignore */ }
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
    goToStep(idx) {
      if (idx <= this.currentStep) this.currentStep = idx;
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
      } catch (e) {
        console.error('Failed to prefill from location_id:', e);
      }
    },
    onImagePick(e) {
      const f = e && e.target && e.target.files ? e.target.files[0] : null;
      if (!f) return;
      this.imageFile = f;
      const reader = new FileReader();
      reader.onload = (ev) => { this.form.image_path = ev.target.result; };
      reader.readAsDataURL(f);
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
          image_path: imageUrl || null,
          room: this.form.room || null,
          spot: this.form.spot || null,
          location_free: free || null,
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

        this.resetForm();
        this.currentStep = 0;
        this.$nextTick(() => { this.$refs.nameInput && this.$refs.nameInput.focus(); });
      } catch (e) {
        this.hint = this.errorText(e, '保存');
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
        image_path: '',
        room: saved.room,
        spot: saved.spot,
        location_free: saved.location_free,
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
  margin-bottom: 16px;
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

/* Progress */
.progress-bar {
  height: 4px;
  background: #e5e7eb;
  border-radius: 2px;
  margin-bottom: 10px;
  flex-shrink: 0;
}
.progress-fill {
  height: 100%;
  background: #3b82f6;
  border-radius: 2px;
  transition: width 0.3s;
}
.step-labels {
  display: flex;
  justify-content: space-between;
  margin-bottom: 20px;
  flex-shrink: 0;
  font-size: 11px;
  color: #9ca3af;
  user-select: none;
}
.step-label {
  display: flex;
  align-items: center;
  gap: 4px;
  text-align: center;
  transition: color 0.2s;
}
.step-label.active { color: #3b82f6; font-weight: 700; }
.step-label.done { color: #10b981; }
.step-num {
  width: 18px;
  height: 18px;
  border-radius: 50%;
  background: #e5e7eb;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 10px;
  font-weight: 700;
  color: #6b7280;
}
.step-label.active .step-num { background: #3b82f6; color: white; }
.step-label.done .step-num { background: #10b981; color: white; }

/* Step Content */
.step-content {
  flex: 1;
  min-height: 0;
  overflow-y: auto;
}
.step-panel {
  display: flex;
  flex-direction: column;
  gap: 14px;
}
.field {
  display: flex;
  flex-direction: column;
  gap: 4px;
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

/* Image upload */
.image-upload {
  display: flex;
  align-items: center;
  gap: 8px;
}
.image-upload input[type="file"] { display: none; }
.image-upload .btn-ghost {
  padding: 8px 14px;
  border: 1px dashed #3b82f6;
  background: white;
  color: #3b82f6;
  border-radius: 8px;
  cursor: pointer;
  font-size: 13px;
  flex-shrink: 0;
}
.preview {
  width: 56px;
  height: 56px;
  object-fit: cover;
  border-radius: 8px;
  border: 1px solid #e5e7eb;
}

/* Footer */
.wizard-footer {
  display: flex;
  align-items: center;
  margin-top: 16px;
  flex-shrink: 0;
  padding-top: 12px;
  border-top: 1px solid #f3f4f6;
}
.spacer { flex: 1; }
.btn-ghost {
  padding: 10px 20px;
  border: 1px solid #d1d5db;
  background: white;
  border-radius: 8px;
  cursor: pointer;
  font-size: 14px;
}
.btn-primary {
  padding: 10px 24px;
  border: none;
  background: #3b82f6;
  color: white;
  border-radius: 8px;
  cursor: pointer;
  font-size: 14px;
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
</style>
