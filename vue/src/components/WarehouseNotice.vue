<template>
  <div class="page">
    <div class="header">
      <h2>公告</h2>
      <div class="header-actions">
        <router-link class="link ghost" to="/warehouse">主页</router-link>
      </div>
    </div>

    <div class="grid">
      <div class="panel">
        <div class="panel-title">发布公告</div>
        <form class="form" @submit.prevent="addNotice">
          <div class="row">
            <label>
              标题
              <input v-model.trim="draft.title" required />
            </label>
            <label>
              类型
              <select v-model="draft.level">
                <option value="info">通知</option>
                <option value="warn">提醒</option>
                <option value="danger">重要</option>
              </select>
            </label>
          </div>
          <label class="full">
            内容
            <input v-model.trim="draft.content" placeholder="例如：纸巾快用完了，周末一起补货" />
          </label>
          <div class="row">
            <label class="check">
              <input v-model="draft.pinned" type="checkbox" />
              置顶
            </label>
            <button type="submit">发布</button>
            <button type="button" class="ghost-btn" @click="resetDraft">清空</button>
          </div>
        </form>
      </div>

      <div class="panel">
        <div class="panel-title">公告列表</div>
        <div v-if="notices.length === 0" class="muted">暂无公告</div>
        <ul v-else class="list">
          <li v-for="n in notices" :key="n.id" class="item" :class="n.level">
            <div class="item-head">
              <div class="strong">
                {{ n.title }}
                <span v-if="n.pinned" class="badge">置顶</span>
              </div>
              <div class="meta">{{ formatTime(n.createdAt) }}</div>
            </div>
            <div class="muted">{{ n.content || '-' }}</div>
            <div class="ops">
              <button class="small" @click="togglePin(n.id)">{{ n.pinned ? '取消置顶' : '置顶' }}</button>
              <button class="small danger" @click="remove(n.id)">删除</button>
            </div>
          </li>
        </ul>
      </div>
    </div>
  </div>
</template>

<script>
export default {
  name: 'WarehouseNotice',
  data() {
    return {
      notices: [],
      draft: {
        title: '',
        content: '',
        level: 'info',
        pinned: false,
      },
    };
  },
  created() {
    this.load();
  },
  methods: {
    load() {
      try {
        const raw = localStorage.getItem('warehouse_notices');
        const list = raw ? JSON.parse(raw) : [];
        this.notices = Array.isArray(list) ? list : [];
      } catch (e) {
        this.notices = [];
      }
      if (this.notices.length === 0) {
        const id = String(Date.now());
        this.notices = [
          {
            id,
            title: '欢迎使用家庭仓库',
            content: '可以在这里记录补货提醒、临期提醒、家庭分工等。',
            level: 'info',
            pinned: true,
            createdAt: Date.now(),
          },
        ];
        this.persist();
      }
    },
    persist() {
      const sorted = this.notices
        .slice()
        .sort((a, b) => {
          if (!!a.pinned !== !!b.pinned) return a.pinned ? -1 : 1;
          return (b.createdAt || 0) - (a.createdAt || 0);
        });
      this.notices = sorted;
      localStorage.setItem('warehouse_notices', JSON.stringify(this.notices));
    },
    resetDraft() {
      this.draft = { title: '', content: '', level: 'info', pinned: false };
    },
    addNotice() {
      const id = String(Date.now());
      this.notices = [
        {
          id,
          title: this.draft.title,
          content: this.draft.content || '',
          level: this.draft.level,
          pinned: !!this.draft.pinned,
          createdAt: Date.now(),
        },
        ...this.notices,
      ];
      this.persist();
      this.resetDraft();
    },
    togglePin(id) {
      this.notices = this.notices.map(n => (n.id === id ? { ...n, pinned: !n.pinned } : n));
      this.persist();
    },
    remove(id) {
      this.notices = this.notices.filter(n => n.id !== id);
      this.persist();
    },
    formatTime(ts) {
      const d = new Date(ts);
      if (Number.isNaN(d.getTime())) return '';
      const y = d.getFullYear();
      const m = String(d.getMonth() + 1).padStart(2, '0');
      const day = String(d.getDate()).padStart(2, '0');
      const hh = String(d.getHours()).padStart(2, '0');
      const mm = String(d.getMinutes()).padStart(2, '0');
      return `${y}-${m}-${day} ${hh}:${mm}`;
    },
  },
}
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

.check {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  min-width: auto;
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

.item {
  border-radius: 12px;
  padding: 12px;
  background: rgba(255, 255, 255, 0.8);
}

.item.info {
  background: rgba(31, 111, 235, 0.10);
}

.item.warn {
  background: rgba(255, 193, 7, 0.22);
}

.item.danger {
  background: rgba(176, 0, 32, 0.14);
}

.item-head {
  display: flex;
  justify-content: space-between;
  gap: 10px;
  flex-wrap: wrap;
  margin-bottom: 6px;
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
  background: rgba(0, 0, 0, 0.10);
  font-weight: 700;
}

.meta {
  color: rgba(0, 0, 0, 0.55);
  font-size: 12px;
}

.muted {
  color: rgba(0, 0, 0, 0.70);
}

.ops {
  margin-top: 10px;
  display: flex;
  gap: 8px;
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

@media (max-width: 900px) {
  .grid {
    grid-template-columns: 1fr;
  }
}
</style>
