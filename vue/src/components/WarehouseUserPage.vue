<template>
  <div class="page">
    <div class="header">
      <h2>用户管理</h2>
      <div class="header-actions">
        <router-link class="link ghost" to="/warehouse">主页</router-link>
      </div>
    </div>

    <div class="card">
      <div v-if="loading" class="muted">加载中...</div>
      <div v-else class="muted">{{ message }}</div>
    </div>

    <div class="grid">
      <div class="panel">
        <div class="panel-title">家庭成员</div>
        <form class="form" @submit.prevent="addUser">
          <div class="row">
            <label>
              姓名
              <input v-model.trim="newUser.name" required />
            </label>
            <label>
              角色
              <select v-model="newUser.role">
                <option value="管理员">管理员</option>
                <option value="采购">采购</option>
                <option value="使用者">使用者</option>
              </select>
            </label>
          </div>
          <label class="full">
            备注
            <input v-model.trim="newUser.note" placeholder="可选，例如：负责日用品补货" />
          </label>
          <div class="row">
            <button type="submit">添加</button>
            <button type="button" class="ghost-btn" @click="resetNewUser">清空</button>
          </div>
        </form>

        <div v-if="users.length === 0" class="muted">暂无成员</div>
        <ul v-else class="list">
          <li v-for="u in users" :key="u.id" class="list-item">
            <div class="left">
              <div class="strong">
                {{ u.name }}
                <span class="badge">{{ u.role }}</span>
                <span v-if="u.isDefault" class="badge primary">默认</span>
              </div>
              <div class="muted">{{ u.note || '-' }}</div>
            </div>
            <div class="right">
              <button class="small" @click="setDefault(u.id)">设为默认</button>
              <button class="small danger" @click="removeUser(u.id)">移除</button>
            </div>
          </li>
        </ul>
      </div>

      <div class="panel">
        <div class="panel-title">偏好设置</div>
        <div class="prefs">
          <label class="check">
            <input v-model="prefs.notifyLowStock" type="checkbox" />
            低库存提醒
          </label>
          <label class="check">
            <input v-model="prefs.notifyExpiring" type="checkbox" />
            临期提醒
          </label>
          <label class="full">
            临期阈值（天）
            <input v-model.number="prefs.expiringDays" type="number" min="1" />
          </label>
          <button class="save" @click="savePrefs">保存偏好</button>
          <div v-if="hint" class="muted">{{ hint }}</div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { api } from '@/api/http';

export default {
  name: 'WarehouseUserPage',
  data() {
    return {
      loading: false,
      message: '',
      users: [],
      newUser: {
        name: '',
        role: '使用者',
        note: '',
      },
      prefs: {
        notifyLowStock: true,
        notifyExpiring: true,
        expiringDays: 30,
      },
      hint: '',
    };
  },
  created() {
    this.fetchMessage();
    this.loadUsers();
    this.loadPrefs();
  },
  methods: {
    async fetchMessage() {
      this.loading = true;
      try {
        const res = await api.get('/api/warehouse/user');
        this.message = res.data.message || '';
      } catch (e) {
        console.error('Failed to fetch user page message:', e);
        this.message = '无法加载用户管理信息';
      } finally {
        this.loading = false;
      }
    },
    loadUsers() {
      try {
        const raw = localStorage.getItem('warehouse_users');
        const list = raw ? JSON.parse(raw) : [];
        this.users = Array.isArray(list) ? list : [];
      } catch (e) {
        this.users = [];
      }
      if (this.users.length === 0) {
        const id = String(Date.now());
        this.users = [{ id, name: '我', role: '管理员', note: '', isDefault: true }];
        this.persistUsers();
      }
    },
    persistUsers() {
      localStorage.setItem('warehouse_users', JSON.stringify(this.users));
    },
    resetNewUser() {
      this.newUser = { name: '', role: '使用者', note: '' };
    },
    addUser() {
      const id = String(Date.now());
      const user = {
        id,
        name: this.newUser.name,
        role: this.newUser.role,
        note: this.newUser.note || '',
        isDefault: this.users.length === 0,
      };
      this.users = [user, ...this.users];
      if (this.users.filter(u => u.isDefault).length === 0) {
        this.users[0].isDefault = true;
      }
      this.persistUsers();
      this.resetNewUser();
    },
    setDefault(id) {
      this.users = this.users.map(u => ({ ...u, isDefault: u.id === id }));
      this.persistUsers();
    },
    removeUser(id) {
      const removedDefault = this.users.find(u => u.id === id)?.isDefault;
      this.users = this.users.filter(u => u.id !== id);
      if (removedDefault && this.users.length > 0) {
        this.users[0].isDefault = true;
      }
      this.persistUsers();
    },
    loadPrefs() {
      try {
        const raw = localStorage.getItem('warehouse_prefs');
        const v = raw ? JSON.parse(raw) : null;
        if (v && typeof v === 'object') {
          this.prefs = {
            notifyLowStock: !!v.notifyLowStock,
            notifyExpiring: !!v.notifyExpiring,
            expiringDays: Number(v.expiringDays || 30),
          };
        }
      } catch (e) {
        this.prefs = {
          notifyLowStock: true,
          notifyExpiring: true,
          expiringDays: 30,
        };
      }
    },
    savePrefs() {
      this.hint = '';
      localStorage.setItem('warehouse_prefs', JSON.stringify(this.prefs));
      this.hint = '已保存';
      setTimeout(() => {
        this.hint = '';
      }, 1500);
    },
  },
};
</script>

<style scoped>
.page {
  padding: 20px;
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
}

.panel {
  background: rgba(255, 255, 255, 0.7);
  border-radius: 10px;
  padding: 14px;
}

.panel-title {
  font-weight: 800;
  margin-bottom: 10px;
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
  min-width: 200px;
}

.right {
  display: flex;
  gap: 8px;
  align-items: flex-start;
  flex-wrap: wrap;
}

.strong {
  font-weight: 800;
  display: flex;
  gap: 8px;
  align-items: center;
  flex-wrap: wrap;
}

.badge {
  font-size: 12px;
  padding: 2px 8px;
  border-radius: 999px;
  background: rgba(0, 0, 0, 0.08);
  font-weight: 700;
}

.badge.primary {
  background: rgba(31, 111, 235, 0.18);
  color: #0b3a8a;
}

.muted {
  color: rgba(0, 0, 0, 0.65);
}

.small {
  padding: 6px 10px;
  border-radius: 10px;
}

.danger {
  background: #b00020;
  color: white;
  border: none;
}

.prefs {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.check {
  display: inline-flex;
  align-items: center;
  gap: 8px;
}

.save {
  background: #111827;
  color: white;
  border: none;
  padding: 10px 12px;
  border-radius: 10px;
}

@media (max-width: 900px) {
  .grid {
    grid-template-columns: 1fr;
  }
}
</style>
