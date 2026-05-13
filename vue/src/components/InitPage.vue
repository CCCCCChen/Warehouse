<template>
  <div class="page">
    <div class="header">
      <h2>家庭选择 / 切换</h2>
      <div class="header-actions">
        <button class="ghost-btn" type="button" @click="refresh">刷新</button>
        <button class="ghost-btn" type="button" @click="clearAll">清空本机记录</button>
      </div>
    </div>

    <div class="cards">
      <button class="card add" type="button" @click="openCreate">
        <div class="add-plus">+</div>
        <div class="add-text">创建家庭</div>
      </button>

      <button class="card join" type="button" @click="openJoin">
        <div class="add-plus">+</div>
        <div class="add-text">邀请码加入</div>
      </button>

      <button
        v-if="status && status.can_adopt_default"
        class="card adopt"
        type="button"
        :disabled="adopting"
        @click="adoptDefault"
      >
        <div class="card-title">接管默认家庭</div>
        <div class="card-sub">历史数据：{{ status.default_items_count }} 条物品</div>
        <div class="badge danger">{{ adopting ? '处理中...' : '可接管' }}</div>
      </button>

      <div v-if="sessions.length === 0" class="empty">
        本机还没有保存过 token。你仍然可以创建/加入家庭，或从“服务器已有家庭”中选择一个并输入 token。
      </div>

      <div v-if="sessions.length > 0" class="session-grid">
        <div v-for="s in sessions" :key="s.household_id" class="session-wrap">
          <button class="card session" type="button" :disabled="loggingIn" @click="selectSession(s)">
            <div class="card-title">
              {{ s.household_name || '未命名家庭' }}
              <span v-if="isCurrent(s)" class="badge">当前</span>
            </div>
            <div class="card-sub">household_id: {{ s.household_id }}</div>
            <div class="row">
              <span v-if="s.role" class="pill">role={{ s.role }}</span>
              <span v-if="s.token" class="pill ok">已保存 token</span>
              <span v-else class="pill warn">未保存 token</span>
            </div>
          </button>
          <button class="icon-btn danger" type="button" :disabled="loggingIn" @click="remove(s.household_id)">
            ×
          </button>
        </div>
      </div>

      <div v-if="serverHouseholds.length > 0" class="section-title">服务器已有家庭</div>
      <div v-if="serverHouseholds.length > 0" class="session-grid">
        <div v-for="h in serverHouseholds" :key="h.household_id" class="session-wrap">
          <button class="card session" type="button" :disabled="loggingIn" @click="selectSession(h)">
            <div class="card-title">
              {{ h.household_name || '未命名家庭' }}
              <span v-if="isCurrent(h)" class="badge">当前</span>
            </div>
            <div class="card-sub">household_id: {{ h.household_id }}</div>
            <div class="row">
              <span class="pill warn">需要输入 token</span>
            </div>
          </button>
        </div>
      </div>
    </div>

    <div v-if="showCreate" class="modal-mask" @click.self="closeCreate">
      <div class="modal">
        <div class="modal-title">创建家庭</div>
        <label class="full">
          家庭名称
          <input v-model.trim="createForm.name" placeholder="例如：家里" />
        </label>
        <div class="row">
          <button type="button" :disabled="creating || !createForm.name" @click="createHousehold">
            {{ creating ? '创建中...' : '创建' }}
          </button>
          <button type="button" class="ghost-btn" @click="closeCreate">取消</button>
        </div>
      </div>
    </div>

    <div v-if="showJoin" class="modal-mask" @click.self="closeJoin">
      <div class="modal">
        <div class="modal-title">邀请码加入</div>
        <label class="full">
          Household ID
          <input v-model.trim="joinForm.household_id" placeholder="例如：default 或 8f..." />
        </label>
        <label class="full">
          邀请码
          <input v-model.trim="joinForm.invite_code" placeholder="例如：ABCDEF" />
        </label>
        <div class="row">
          <button type="button" :disabled="joining || !joinForm.household_id || !joinForm.invite_code" @click="joinHousehold">
            {{ joining ? '加入中...' : '加入' }}
          </button>
          <button type="button" class="ghost-btn" @click="closeJoin">取消</button>
        </div>
      </div>
    </div>

    <div v-if="showToken" class="modal-mask" @click.self="closeToken">
      <div class="modal">
        <div class="modal-title">输入 Token</div>
        <div class="muted">家庭：{{ tokenTarget.household_name || tokenTarget.household_id }}</div>
        <label class="full">
          Token
          <input v-model.trim="tokenForm.token" placeholder="Bearer Token" />
        </label>
        <div class="row">
          <button type="button" :disabled="loggingIn || !tokenForm.token" @click="confirmToken">
            {{ loggingIn ? '验证中...' : '进入' }}
          </button>
          <button type="button" class="ghost-btn" @click="closeToken">取消</button>
          <button type="button" class="ghost-btn" :disabled="!tokenForm.token" @click="copy(tokenForm.token)">复制</button>
        </div>
      </div>
    </div>

    <div v-if="showIssuedToken" class="modal-mask" @click.self="closeIssuedToken">
      <div class="modal">
        <div class="modal-title">请保存 Token</div>
        <div class="muted">家庭：{{ issuedTarget.household_name || issuedTarget.household_id }}</div>
        <div class="token-box">{{ issuedToken }}</div>
        <div class="muted">Token 只在创建/加入时展示一次，请妥善保存。</div>
        <div class="row">
          <button type="button" @click="copy(issuedToken)">复制</button>
          <button type="button" class="ghost-btn" @click="enterAfterIssued">我已保存，进入</button>
        </div>
      </div>
    </div>

    <div v-if="hint" class="hint">{{ hint }}</div>
  </div>
</template>

<script>
import { api } from '@/api/http';
import {
  clearAllSessions,
  clearAuth,
  getHouseholdId,
  getSessions,
  removeSession,
  setCurrentSession,
  upsertSession,
} from '@/auth/storage';

export default {
  name: 'InitPage',
  data() {
    return {
      hint: '',
      status: null,
      sessions: [],
      serverHouseholds: [],
      loadingHouseholds: false,
      creating: false,
      joining: false,
      adopting: false,
      loggingIn: false,
      showCreate: false,
      showJoin: false,
      showToken: false,
      showIssuedToken: false,
      tokenTarget: { household_id: '', household_name: '' },
      issuedTarget: { household_id: '', household_name: '' },
      issuedToken: '',
      createForm: {
        name: '',
      },
      joinForm: {
        household_id: '',
        invite_code: '',
      },
      tokenForm: {
        token: '',
      },
    };
  },
  created() {
    this.refresh();
  },
  methods: {
    refresh() {
      this.loadSessions();
      this.fetchStatus();
      this.fetchHouseholds();
    },
    loadSessions() {
      const list = getSessions()
        .map((s) => ({
          household_id: s && s.household_id ? String(s.household_id) : '',
          household_name: s && s.household_name ? String(s.household_name) : '',
          token: s && s.token ? String(s.token) : '',
          role: s && s.role ? String(s.role) : '',
          updated_at: s && s.updated_at ? Number(s.updated_at) : 0,
        }))
        .filter((s) => s.household_id);
      list.sort((a, b) => (b.updated_at || 0) - (a.updated_at || 0));
      this.sessions = list;
    },
    async fetchStatus() {
      try {
        const res = await api.get('/api/init/status');
        this.status = res.data;
      } catch (e) {
        this.status = null;
      }
    },
    async fetchHouseholds() {
      this.loadingHouseholds = true;
      try {
        const res = await api.get('/api/init/households');
        const rows = Array.isArray(res.data) ? res.data : [];
        const sessionIds = new Set(this.sessions.map(s => s.household_id));
        this.serverHouseholds = rows
          .map((r) => ({
            household_id: r && r.household_id ? String(r.household_id) : '',
            household_name: r && r.household_name ? String(r.household_name) : '',
            token: '',
            role: '',
            updated_at: 0,
          }))
          .filter((h) => h.household_id && !sessionIds.has(h.household_id));
      } catch (e) {
        this.serverHouseholds = [];
      } finally {
        this.loadingHouseholds = false;
      }
    },
    parseError(e, fallback) {
      const detail = (e && e.response && e.response.data) ? e.response.data : null;
      return detail ? JSON.stringify(detail) : (fallback || '操作失败');
    },
    isCurrent(session) {
      const current = getHouseholdId();
      return Boolean(current && session && session.household_id === current);
    },
    openCreate() {
      this.hint = '';
      this.showCreate = true;
    },
    closeCreate() {
      this.showCreate = false;
      this.createForm.name = '';
    },
    openJoin() {
      this.hint = '';
      this.showJoin = true;
    },
    closeJoin() {
      this.showJoin = false;
      this.joinForm.household_id = '';
      this.joinForm.invite_code = '';
    },
    openToken(target) {
      this.hint = '';
      this.tokenTarget = {
        household_id: target.household_id,
        household_name: target.household_name,
      };
      this.tokenForm.token = '';
      this.showToken = true;
    },
    closeToken() {
      this.showToken = false;
      this.tokenTarget = { household_id: '', household_name: '' };
      this.tokenForm.token = '';
    },
    openIssuedToken(target, token) {
      this.issuedTarget = {
        household_id: target.household_id,
        household_name: target.household_name,
      };
      this.issuedToken = token || '';
      this.showIssuedToken = true;
    },
    closeIssuedToken() {
      this.showIssuedToken = false;
      this.issuedTarget = { household_id: '', household_name: '' };
      this.issuedToken = '';
    },
    enterAfterIssued() {
      this.showIssuedToken = false;
      this.$router.push('/warehouse');
    },
    async adoptDefault() {
      this.hint = '';
      this.adopting = true;
      try {
        const res = await api.post('/api/init/adopt_default');
        const householdId = res.data.household_id;
        const token = res.data.owner_token;
        await this.verifyAndPersist({ household_id: householdId, household_name: '默认家庭' }, token, true);
        this.openIssuedToken({ household_id: householdId, household_name: '默认家庭' }, token);
      } catch (e) {
        this.hint = this.parseError(e, '接管失败');
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
        const target = { household_id: householdId, household_name: this.createForm.name, role: 'owner' };
        await this.verifyAndPersist(target, token, true);
        this.closeCreate();
        this.openIssuedToken(target, token);
      } catch (e) {
        this.hint = this.parseError(e, '创建失败');
      } finally {
        this.creating = false;
      }
    },
    async joinHousehold() {
      this.hint = '';
      this.joining = true;
      try {
        const res = await api.post('/api/init/join', this.joinForm);
        const target = { household_id: res.data.household_id, household_name: '' };
        await this.verifyAndPersist(target, res.data.token, true);
        this.closeJoin();
        this.openIssuedToken(target, res.data.token);
      } catch (e) {
        this.hint = this.parseError(e, '加入失败');
      } finally {
        this.joining = false;
      }
    },
    async verifyAndPersist(target, token, persist) {
      this.hint = '';
      this.loggingIn = true;
      setCurrentSession(target.household_id, token);
      try {
        const meRes = await api.get('/api/me');
        const me = meRes.data || {};
        if (me.household_id && String(me.household_id) !== String(target.household_id)) {
          throw new Error('TOKEN_HOUSEHOLD_MISMATCH');
        }
        if (persist) {
          upsertSession({
            household_id: target.household_id,
            household_name: target.household_name || me.household_name || '',
            token,
            role: me.role || target.role || '',
          });
        }
        this.loadSessions();
        this.showToken = false;
        await this.fetchHouseholds();
      } catch (e) {
        clearAuth();
        this.hint = this.parseError(e, 'Token 无效或服务不可用');
        throw e;
      } finally {
        this.loggingIn = false;
      }
    },
    selectSession(session) {
      if (session.token) {
        this.verifyAndPersist(session, session.token, true)
          .then(() => this.$router.push('/warehouse'))
          .catch(() => {});
      } else {
        this.openToken(session);
      }
    },
    confirmToken() {
      const token = this.tokenForm.token;
      if (!token) return;
      this.verifyAndPersist(this.tokenTarget, token, true)
        .then(() => this.$router.push('/warehouse'))
        .catch(() => {});
    },
    remove(householdId) {
      removeSession(householdId);
      this.loadSessions();
      this.hint = '已移除';
    },
    clearAll() {
      clearAllSessions();
      this.loadSessions();
      this.hint = '已清空';
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

.header-actions {
  display: flex;
  gap: 10px;
  flex-wrap: wrap;
}

.cards {
  display: block;
}

  .section-title {
    font-weight: 900;
    margin: 14px 2px 10px;
  }

.session-grid {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 12px;
}

.session-wrap {
  position: relative;
}

.row {
  display: flex;
  gap: 10px;
  flex-wrap: wrap;
  margin-top: 8px;
}

.full {
  display: block;
  margin-bottom: 10px;
}

.card {
  display: flex;
  flex-direction: column;
  justify-content: space-between;
  text-align: left;
  width: 100%;
  min-height: 110px;
  padding: 14px;
  border-radius: 12px;
  border: 1px solid rgba(0, 0, 0, 0.14);
  background: rgba(255, 255, 255, 0.72);
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.06);
  cursor: pointer;
}

.card:hover {
  border-color: rgba(0, 0, 0, 0.24);
}

.ghost-btn {
  background: transparent;
  border: 1px solid rgba(0, 0, 0, 0.25);
  padding: 6px 10px;
  border-radius: 8px;
}

.card.add,
.card.join {
  align-items: center;
  justify-content: center;
  text-align: center;
  min-height: 120px;
  margin-bottom: 12px;
}

.add-plus {
  font-size: 32px;
  font-weight: 900;
  line-height: 1;
}

.add-text {
  margin-top: 6px;
  font-weight: 800;
}

.card.adopt {
  margin-bottom: 12px;
}

.card-title {
  font-weight: 900;
  font-size: 16px;
  display: flex;
  align-items: center;
  gap: 8px;
}

.card-sub {
  margin-top: 8px;
  color: rgba(0, 0, 0, 0.65);
  font-size: 12px;
  word-break: break-word;
}

.pill {
  display: inline-flex;
  align-items: center;
  padding: 2px 8px;
  border-radius: 999px;
  font-size: 12px;
  border: 1px solid rgba(0, 0, 0, 0.12);
  background: rgba(255, 255, 255, 0.7);
}

.pill.ok {
  border-color: rgba(16, 185, 129, 0.35);
  background: rgba(16, 185, 129, 0.10);
}

.pill.warn {
  border-color: rgba(245, 158, 11, 0.35);
  background: rgba(245, 158, 11, 0.10);
}

.badge {
  display: inline-flex;
  align-items: center;
  padding: 2px 8px;
  border-radius: 999px;
  font-size: 12px;
  background: rgba(17, 24, 39, 0.08);
  border: 1px solid rgba(0, 0, 0, 0.12);
}

.badge.danger {
  border-color: rgba(239, 68, 68, 0.3);
  background: rgba(239, 68, 68, 0.10);
}

.icon-btn {
  position: absolute;
  top: 8px;
  right: 8px;
  width: 28px;
  height: 28px;
  border-radius: 999px;
  border: 1px solid rgba(0, 0, 0, 0.15);
  background: rgba(255, 255, 255, 0.85);
  cursor: pointer;
}

.icon-btn.danger {
  border-color: rgba(239, 68, 68, 0.35);
  background: rgba(239, 68, 68, 0.10);
}

.empty {
  color: rgba(0, 0, 0, 0.65);
  padding: 12px 2px;
}

.modal-mask {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.30);
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 20px;
  z-index: 30;
}

.modal {
  width: 100%;
  max-width: 520px;
  background: rgba(255, 255, 255, 0.95);
  border: 1px solid rgba(0, 0, 0, 0.18);
  border-radius: 14px;
  padding: 14px;
  box-shadow: 0 18px 60px rgba(0, 0, 0, 0.20);
}

.modal-title {
  font-weight: 900;
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

.token-box {
  margin: 10px 0;
  padding: 10px;
  border-radius: 10px;
  background: rgba(255, 255, 255, 0.75);
  border: 1px dashed rgba(0, 0, 0, 0.22);
  white-space: pre-wrap;
  word-break: break-word;
  font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, "Liberation Mono", "Courier New", monospace;
}

.hint {
  margin-top: 12px;
  color: rgba(0, 0, 0, 0.75);
}

.muted {
  color: rgba(0, 0, 0, 0.65);
}

@media (max-width: 900px) {
  .session-grid {
    grid-template-columns: 1fr;
  }
}
</style>
