<template>
  <div class="page">
    <div class="header">
      <h2>设置中心</h2>
      <div class="header-actions">
        <router-link class="link ghost" to="/warehouse">主页</router-link>
      </div>
    </div>

    <div class="grid">
      <div class="panel">
        <div class="panel-title">当前身份</div>
        <div v-if="loadingMe" class="muted">加载中...</div>
        <pre v-else class="pre">{{ meText }}</pre>

        <div class="panel-title">邀请码（7天有效）</div>
        <div class="row">
          <button :disabled="!isOwner || creatingInvite" @click="createInvite">
            {{ creatingInvite ? '生成中...' : '生成邀请码' }}
          </button>
          <label>
            max_uses
            <input v-model.number="inviteMaxUses" type="number" min="1" />
          </label>
        </div>
        <div v-if="latestInvite" class="token">
          <div class="token-title">邀请码</div>
          <pre class="pre">{{ latestInvite.invite_code }}</pre>
          <div class="row">
            <button class="ghost-btn" @click="copy(latestInvite.invite_code)">复制</button>
          </div>
        </div>

        <div class="panel-title">邀请码列表</div>
        <div v-if="loadingInvites" class="muted">加载中...</div>
        <div v-else-if="invites.length === 0" class="muted">暂无</div>
        <ul v-else class="list">
          <li v-for="i in invites" :key="i.id" class="list-item">
            <div class="left">
              <div class="strong">#{{ i.id }} {{ i.revoked ? '（已撤销）' : '' }}</div>
              <div class="muted">expires_at: {{ i.expires_at }}</div>
              <div class="muted">used: {{ i.used_count }}/{{ i.max_uses }}</div>
            </div>
            <div class="right">
              <button class="danger" :disabled="!isOwner || i.revoked" @click="revokeInvite(i.id)">撤销</button>
            </div>
          </li>
        </ul>
      </div>

      <div class="panel">
        <div class="panel-title">家庭配置（分类/位置/单位）</div>
        <div v-if="loadingConfig" class="muted">加载中...</div>
        <div v-else class="form">
          <label class="full">
            分类（每行一个）
            <textarea v-model="configText.categories" rows="8"></textarea>
          </label>
          <label class="full">
            位置（每行一个）
            <textarea v-model="configText.locations" rows="8"></textarea>
          </label>
          <label class="full">
            单位（每行一个）
            <textarea v-model="configText.units" rows="6"></textarea>
          </label>
          <details class="details">
            <summary>物品与录入字段配置</summary>
            <div class="details-body">
              <label class="full">
                类型树（JSON：大类 -> 子类数组）
                <textarea v-model="configText.typeTreeJson" rows="10"></textarea>
              </label>
              <label class="full">
                房间（每行一个）
                <textarea v-model="configText.rooms" rows="6"></textarea>
              </label>
              <label class="full">
                位置点（每行一个）
                <textarea v-model="configText.spots" rows="6"></textarea>
              </label>
              <label class="full">
                责任人候选（每行一个）
                <textarea v-model="configText.responsiblePeople" rows="6"></textarea>
              </label>
            </div>
          </details>
          <details class="details">
            <summary>区域管理配置</summary>
            <div class="details-body">
              <div class="row">
                <router-link class="link" to="/warehouse/map-test">打开区域设置测试页</router-link>
              </div>
              <label class="full">
                区域配置（JSON）
                <textarea v-model="configText.areaMapJson" rows="10"></textarea>
              </label>
            </div>
          </details>
          <div class="row">
            <button :disabled="!isOwner || savingConfig" @click="saveConfig">
              {{ savingConfig ? '保存中...' : '保存配置' }}
            </button>
            <button class="ghost-btn" @click="reloadAll">刷新</button>
          </div>
        </div>

        <div class="panel-title">成员（设备 token）</div>
        <div v-if="loadingMembers" class="muted">加载中...</div>
        <div v-else-if="members.length === 0" class="muted">暂无</div>
        <ul v-else class="list">
          <li v-for="m in members" :key="m.id" class="list-item">
            <div class="left">
              <div class="strong">#{{ m.id }} role={{ m.role }} {{ m.revoked ? '（已撤销）' : '' }}</div>
              <div class="muted">{{ m.created_at }}</div>
            </div>
            <div class="right">
              <button :disabled="!isOwner || m.role === 'owner' || m.revoked" @click="promote(m.id)">提升为 owner</button>
            </div>
          </li>
        </ul>
      </div>
    </div>

    <div v-if="hint" class="hint">{{ hint }}</div>
  </div>
</template>

<script>
import { api } from '@/api/http';

export default {
  name: 'SettingsPage',
  data() {
    return {
      hint: '',
      me: null,
      config: null,
      members: [],
      invites: [],
      latestInvite: null,
      inviteMaxUses: 10,
      loadingMe: false,
      loadingConfig: false,
      loadingMembers: false,
      loadingInvites: false,
      savingConfig: false,
      creatingInvite: false,
      configText: {
        categories: '',
        locations: '',
        units: '',
        rooms: '',
        spots: '',
        responsiblePeople: '',
        typeTreeJson: '',
        areaMapJson: '',
      },
    };
  },
  computed: {
    isOwner() {
      return this.me && this.me.role === 'owner';
    },
    meText() {
      return this.me ? JSON.stringify(this.me, null, 2) : '未加载';
    },
  },
  created() {
    this.reloadAll();
  },
  methods: {
    async reloadAll() {
      this.hint = '';
      await Promise.all([this.fetchMe(), this.fetchConfig(), this.fetchMembers(), this.fetchInvites()]);
    },
    async fetchMe() {
      this.loadingMe = true;
      try {
        const res = await api.get('/api/me');
        this.me = res.data;
      } catch (e) {
        this.me = null;
      } finally {
        this.loadingMe = false;
      }
    },
    async fetchConfig() {
      this.loadingConfig = true;
      try {
        const res = await api.get('/api/config');
        this.config = res.data;
        this.configText.categories = (res.data.categories || []).join('\n');
        this.configText.locations = (res.data.locations || []).join('\n');
        this.configText.units = (res.data.units || []).join('\n');
        this.configText.rooms = (res.data.rooms || []).join('\n');
        this.configText.spots = (res.data.spots || []).join('\n');
        this.configText.responsiblePeople = (res.data.responsible_people || []).join('\n');
        this.configText.typeTreeJson = JSON.stringify(res.data.type_tree || {}, null, 2);
        this.configText.areaMapJson = JSON.stringify(res.data.area_map || [], null, 2);
      } catch (e) {
        this.config = null;
      } finally {
        this.loadingConfig = false;
      }
    },
    parseLines(text) {
      return (text || '')
        .split('\n')
        .map(s => s.trim())
        .filter(Boolean);
    },
    parseJson(text, fallback) {
      const raw = (text || '').trim();
      if (!raw) return fallback;
      return JSON.parse(raw);
    },
    async saveConfig() {
      this.hint = '';
      this.savingConfig = true;
      try {
        const payload = {
          categories: this.parseLines(this.configText.categories),
          locations: this.parseLines(this.configText.locations),
          units: this.parseLines(this.configText.units),
          rooms: this.parseLines(this.configText.rooms),
          spots: this.parseLines(this.configText.spots),
          responsible_people: this.parseLines(this.configText.responsiblePeople),
          type_tree: this.parseJson(this.configText.typeTreeJson, {}),
          area_map: this.parseJson(this.configText.areaMapJson, []),
        };
        const res = await api.put('/api/config', payload);
        this.config = res.data;
        this.hint = '已保存';
      } catch (e) {
        const detail = (e && e.response && e.response.data) ? e.response.data : null;
        this.hint = detail ? JSON.stringify(detail) : '保存失败';
      } finally {
        this.savingConfig = false;
      }
    },
    async fetchMembers() {
      this.loadingMembers = true;
      try {
        const res = await api.get('/api/household/members');
        this.members = res.data;
      } catch (e) {
        this.members = [];
      } finally {
        this.loadingMembers = false;
      }
    },
    async promote(id) {
      this.hint = '';
      try {
        await api.post(`/api/household/members/${id}/promote`);
        await this.fetchMembers();
        this.hint = '已提升';
      } catch (e) {
        const detail = (e && e.response && e.response.data) ? e.response.data : null;
        this.hint = detail ? JSON.stringify(detail) : '提升失败';
      }
    },
    async fetchInvites() {
      this.loadingInvites = true;
      try {
        const res = await api.get('/api/household/invites');
        this.invites = res.data;
      } catch (e) {
        this.invites = [];
      } finally {
        this.loadingInvites = false;
      }
    },
    async createInvite() {
      this.hint = '';
      this.creatingInvite = true;
      try {
        const res = await api.post('/api/household/invites', { max_uses: this.inviteMaxUses });
        this.latestInvite = res.data;
        await this.fetchInvites();
        this.hint = '已生成邀请码';
      } catch (e) {
        const detail = (e && e.response && e.response.data) ? e.response.data : null;
        this.hint = detail ? JSON.stringify(detail) : '生成失败';
      } finally {
        this.creatingInvite = false;
      }
    },
    async revokeInvite(id) {
      this.hint = '';
      try {
        await api.delete(`/api/household/invites/${id}`);
        await this.fetchInvites();
        this.hint = '已撤销';
      } catch (e) {
        const detail = (e && e.response && e.response.data) ? e.response.data : null;
        this.hint = detail ? JSON.stringify(detail) : '撤销失败';
      }
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
  padding-bottom: 60px;
  max-width: 1200px;
  margin: 0 auto;
  background: rgba(255, 255, 255, 0.55);
  border: 1px solid rgba(0, 0, 0, 0.12);
  border-radius: 14px;
  box-shadow: 0 10px 30px rgba(0, 0, 0, 0.08);
  min-height: 100vh;
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
  margin: 12px 0 10px;
}

.panel-title:first-child {
  margin-top: 0;
}

.row {
  display: flex;
  gap: 12px;
  flex-wrap: wrap;
  margin-bottom: 10px;
  align-items: flex-end;
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

textarea,
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

.danger {
  background: #b00020;
  color: white;
  border: none;
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

.pre {
  margin: 0;
  padding: 12px;
  border-radius: 10px;
  background: rgba(17, 24, 39, 0.06);
  border: 1px solid rgba(0, 0, 0, 0.12);
  white-space: pre-wrap;
  word-break: break-word;
  max-height: 260px;
  overflow: auto;
}

.list {
  list-style: none;
  padding: 0;
  margin: 0;
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.list-item {
  background: rgba(255, 255, 255, 0.75);
  border-radius: 12px;
  padding: 12px;
  display: flex;
  justify-content: space-between;
  gap: 12px;
}

.left {
  min-width: 220px;
}

.right {
  display: flex;
  gap: 8px;
  align-items: flex-start;
  flex-wrap: wrap;
}

.strong {
  font-weight: 800;
}

.token {
  margin: 10px 0 12px;
  background: rgba(17, 24, 39, 0.06);
  border: 1px dashed rgba(0, 0, 0, 0.18);
  border-radius: 12px;
  padding: 12px;
}

.token-title {
  font-weight: 800;
  margin-bottom: 6px;
}

.details {
  margin: 10px 0;
  background: rgba(17, 24, 39, 0.04);
  border: 1px dashed rgba(0, 0, 0, 0.18);
  border-radius: 12px;
  padding: 10px 12px;
}

.details summary {
  cursor: pointer;
  font-weight: 800;
}

.details-body {
  margin-top: 10px;
  display: flex;
  flex-direction: column;
  gap: 10px;
}

@media (max-width: 900px) {
  .page {
    padding: 12px;
    padding-bottom: 80px;
  }
  .grid {
    grid-template-columns: 1fr;
  }
}
</style>
