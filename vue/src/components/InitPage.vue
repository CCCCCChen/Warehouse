<template>
  <div class="page">
    <div class="header">
      <h2>初始化 / 加入家庭</h2>
    </div>

    <div class="grid">
      <div class="panel">
        <div v-if="status && status.can_adopt_default" class="token">
          <div class="token-title">检测到历史数据</div>
          <div class="muted">默认家庭里已有 {{ status.default_items_count }} 条物品记录，可以直接“接管默认家庭”继续使用。</div>
          <div class="row">
            <button type="button" :disabled="adopting" @click="adoptDefault">
              {{ adopting ? '处理中...' : '接管默认家庭' }}
            </button>
          </div>
        </div>

        <div class="panel-title">创建家庭</div>
        <form class="form" @submit.prevent="createHousehold">
          <label class="full">
            家庭名称
            <input v-model.trim="createForm.name" required />
          </label>
          <div class="row">
            <button type="submit" :disabled="creating">{{ creating ? '创建中...' : '创建' }}</button>
          </div>
        </form>

        <div v-if="createdToken" class="token">
          <div class="token-title">管理员 Token（请妥善保存）</div>
          <pre class="pre">{{ createdToken }}</pre>
          <div class="row">
            <button type="button" @click="goWarehouse">进入仓库</button>
            <button type="button" class="ghost-btn" @click="copy(createdToken)">复制</button>
          </div>
        </div>
      </div>

      <div class="panel">
        <div class="panel-title">加入家庭（邀请码）</div>
        <form class="form" @submit.prevent="joinHousehold">
          <label class="full">
            Household ID
            <input v-model.trim="joinForm.household_id" required />
          </label>
          <label class="full">
            邀请码
            <input v-model.trim="joinForm.invite_code" required />
          </label>
          <div class="row">
            <button type="submit" :disabled="joining">{{ joining ? '加入中...' : '加入' }}</button>
          </div>
        </form>
      </div>
    </div>

    <div v-if="hint" class="hint">{{ hint }}</div>
  </div>
</template>

<script>
import { api } from '@/api/http';
import { setAuthToken, setHouseholdId } from '@/auth/storage';

export default {
  name: 'InitPage',
  data() {
    return {
      creating: false,
      joining: false,
      adopting: false,
      hint: '',
      createdToken: '',
      status: null,
      createForm: {
        name: '',
      },
      joinForm: {
        household_id: '',
        invite_code: '',
      },
    };
  },
  created() {
    this.fetchStatus();
  },
  methods: {
    async fetchStatus() {
      try {
        const res = await api.get('/api/init/status');
        this.status = res.data;
      } catch (e) {
        this.status = null;
      }
    },
    async adoptDefault() {
      this.hint = '';
      this.adopting = true;
      try {
        const res = await api.post('/api/init/adopt_default');
        const householdId = res.data.household_id;
        const token = res.data.owner_token;
        setHouseholdId(householdId);
        setAuthToken(token);
        this.createdToken = token;
        this.hint = '已接管默认家庭';
      } catch (e) {
        const detail = (e && e.response && e.response.data) ? e.response.data : null;
        this.hint = detail ? JSON.stringify(detail) : '接管失败';
      } finally {
        this.adopting = false;
      }
    },
    async createHousehold() {
      this.hint = '';
      this.creating = true;
      try {
        const res = await api.post('/api/init/household', this.createForm);
        const householdId = res.data.household_id;
        const token = res.data.owner_token;
        setHouseholdId(householdId);
        setAuthToken(token);
        this.createdToken = token;
        this.hint = '创建成功';
        this.fetchStatus();
      } catch (e) {
        const detail = (e && e.response && e.response.data) ? e.response.data : null;
        this.hint = detail ? JSON.stringify(detail) : '创建失败';
      } finally {
        this.creating = false;
      }
    },
    async joinHousehold() {
      this.hint = '';
      this.joining = true;
      try {
        const res = await api.post('/api/init/join', this.joinForm);
        setHouseholdId(res.data.household_id);
        setAuthToken(res.data.token);
        this.hint = '加入成功';
        this.$router.push('/warehouse');
      } catch (e) {
        const detail = (e && e.response && e.response.data) ? e.response.data : null;
        this.hint = detail ? JSON.stringify(detail) : '加入失败';
      } finally {
        this.joining = false;
      }
    },
    goWarehouse() {
      this.$router.push('/warehouse');
    },
    async copy(text) {
      try {
        await navigator.clipboard.writeText(text);
        this.hint = '已复制';
      } catch (e) {
        this.hint = '复制失败';
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
  margin-bottom: 12px;
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
  font-weight: 900;
  margin-bottom: 10px;
}

.form {
  display: block;
}

.row {
  display: flex;
  gap: 12px;
  flex-wrap: wrap;
  margin-top: 10px;
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
  margin-top: 12px;
  color: rgba(0, 0, 0, 0.75);
}

.muted {
  color: rgba(0, 0, 0, 0.65);
}

.token {
  margin-top: 12px;
  background: rgba(17, 24, 39, 0.06);
  border: 1px dashed rgba(0, 0, 0, 0.18);
  border-radius: 12px;
  padding: 12px;
}

.token-title {
  font-weight: 800;
  margin-bottom: 6px;
}

.pre {
  margin: 0;
  padding: 10px;
  border-radius: 10px;
  background: rgba(255, 255, 255, 0.7);
  border: 1px solid rgba(0, 0, 0, 0.12);
  white-space: pre-wrap;
  word-break: break-word;
}

@media (max-width: 900px) {
  .grid {
    grid-template-columns: 1fr;
  }
}
</style>
