<template>
  <div class="panel-page">
    <header class="panel-header">
      <span class="breadcrumb" v-if="breadcrumb.length">
        <template v-for="(seg, i) in breadcrumb" :key="i">
          <span v-if="i > 0" class="sep">›</span>
          <span class="crumb">{{ seg }}</span>
        </template>
      </span>
      <span class="breadcrumb muted" v-else>加载中…</span>
    </header>

    <section class="actions" v-if="loc">
      <button class="action-btn primary" @click="go('/warehouse/manage')">
        <span class="icon">📦</span>
        <span class="label">录入物品</span>
      </button>
      <button class="action-btn" @click="go('/warehouse/items')">
        <span class="icon">📋</span>
        <span class="label">查看物品</span>
      </button>
      <button class="action-btn" @click="go('/warehouse/settings')">
        <span class="icon">⚙️</span>
        <span class="label">位置设置</span>
      </button>
    </section>

    <footer class="panel-footer" v-if="loc">
      最后更新: {{ loc.updated_at || '—' }}
    </footer>
    <p class="err" v-if="error">{{ error }}</p>
  </div>
</template>

<script>
import axios from 'axios';

const BASE = process.env.VUE_APP_API_BASE_URL || 'http://127.0.0.1:18808';

export default {
  name: 'LocationPanelPage',
  data() {
    return {
      loc: null,
      error: '',
    };
  },
  computed: {
    breadcrumb() {
      if (!this.loc || !this.loc.path) return [];
      return this.loc.path
        .split('/')
        .filter(Boolean)
        .map((id, i, arr) => {
          // Use cached names if available, fallback to truncated ID
          return this._names[id] || (i === arr.length - 1 ? this.loc.name : id.slice(0, 8));
        });
    },
  },
  created() {
    this._names = {};
    this.load();
  },
  methods: {
    async load() {
      const id = this.$route.params.id;
      try {
        const res = await axios.get(`${BASE}/api/public/locations/${id}`);
        this.loc = res.data;
        // Cache ancestor names from path segments
        if (res.data.path) {
          const ids = res.data.path.split('/').filter(Boolean);
          if (ids.length > 1) {
            // Fetch ancestors to get real names
            const ancRes = await axios.get(`${BASE}/api/public/locations/${id}/ancestors`);
            ancRes.data.forEach(a => { this._names[a.id] = a.name; });
          }
        }
        this._names[this.loc.id] = this.loc.name;
      } catch (e) {
        this.error = '无法加载位置信息';
      }
    },
    go(path) {
      const q = `location_id=${encodeURIComponent(this.$route.params.id)}`;
      this.$router.push(`${path}?${q}`);
    },
  },
};
</script>

<style scoped>
.panel-page {
  max-width: 420px;
  margin: 0 auto;
  padding: 24px 20px;
  min-height: 100vh;
  display: flex;
  flex-direction: column;
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
  background: #f5f5f7;
}

.panel-header {
  padding: 12px 0 24px;
  text-align: center;
}

.breadcrumb {
  font-size: 15px;
  color: #1d1d1f;
}

.sep {
  margin: 0 6px;
  color: #86868b;
}

.muted {
  color: #86868b;
}

.actions {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 16px;
  padding: 20px 0;
}

.action-btn {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 20px 24px;
  border: none;
  border-radius: 16px;
  background: #fff;
  box-shadow: 0 2px 8px rgba(0,0,0,0.06);
  cursor: pointer;
  font-size: 18px;
  color: #1d1d1f;
  transition: all 0.15s;
  min-height: 56px;
}

.action-btn:hover {
  background: #f0f0f5;
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(0,0,0,0.1);
}

.action-btn.primary {
  background: #007aff;
  color: #fff;
  box-shadow: 0 4px 14px rgba(0,122,255,0.3);
}

.action-btn.primary:hover {
  background: #0066d6;
}

.icon {
  font-size: 28px;
  width: 40px;
  text-align: center;
}

.label {
  font-weight: 500;
}

.panel-footer {
  padding: 16px 0 0;
  text-align: center;
  font-size: 13px;
  color: #86868b;
}

.err {
  color: #ff3b30;
  text-align: center;
  padding: 20px;
}
</style>
