<template>
  <div class="tile">
    <div class="head">
      <div class="title">公告</div>
      <router-link class="btn" to="/warehouse/notice">进入公告</router-link>
    </div>

    <div v-if="topNotices.length === 0" class="muted">暂无公告</div>
    <div v-else class="list">
      <div v-for="n in topNotices" :key="n.id" class="notice" :class="n.level">
        <div class="notice-title">
          <span class="strong">{{ n.title }}</span>
          <span v-if="n.pinned" class="badge">置顶</span>
        </div>
        <div class="notice-meta">{{ formatTime(n.createdAt) }}</div>
        <div class="notice-content">{{ n.content || '-' }}</div>
      </div>
    </div>

    <DashboardStats />
  </div>
</template>

<script>
import DashboardStats from './DashboardStats.vue';

export default {
  name: 'DashboardNoticeTile',
  components: { DashboardStats },
  data() {
    return {
      notices: [],
    };
  },
  computed: {
    topNotices() {
      return (this.notices || []).slice(0, 3);
    },
  },
  created() {
    this.load();
  },
  methods: {
    load() {
      try {
        const raw = localStorage.getItem('warehouse_notices');
        const list = raw ? JSON.parse(raw) : [];
        const arr = Array.isArray(list) ? list : [];
        this.notices = arr
          .slice()
          .sort((a, b) => {
            if (!!a.pinned !== !!b.pinned) return a.pinned ? -1 : 1;
            return (b.createdAt || 0) - (a.createdAt || 0);
          });
      } catch (e) {
        this.notices = [];
      }
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
.tile {
  color: #111827;
}

.head {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 10px;
  flex-wrap: wrap;
  margin-bottom: 10px;
}

.title {
  font-weight: 900;
  font-size: 18px;
}

.btn {
  display: inline-block;
  padding: 10px 12px;
  border-radius: 10px;
  background: #111827;
  color: white;
  text-decoration: none;
  font-weight: 700;
}

.list {
  display: grid;
  gap: 10px;
}

.notice {
  background: rgba(255, 255, 255, 0.70);
  border-radius: 10px;
  padding: 10px 12px;
}

.notice.warn {
  background: rgba(255, 193, 7, 0.20);
}

.notice.danger {
  background: rgba(176, 0, 32, 0.14);
}

.notice-title {
  display: flex;
  gap: 8px;
  align-items: center;
  flex-wrap: wrap;
}

.strong {
  font-weight: 900;
}

.badge {
  font-size: 12px;
  padding: 2px 6px;
  border-radius: 999px;
  background: rgba(31, 111, 235, 0.14);
  color: #1f6feb;
  font-weight: 900;
}

.notice-meta {
  margin-top: 4px;
  font-size: 12px;
  color: rgba(0, 0, 0, 0.65);
}

.notice-content {
  margin-top: 6px;
  color: rgba(0, 0, 0, 0.72);
  font-size: 13px;
}

.muted {
  color: rgba(0, 0, 0, 0.65);
}
</style>

