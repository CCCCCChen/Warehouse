<template>
  <div class="warehouse-page">
    <h2 class="page-title">{{ msg }}</h2>
    <div class="quick-nav">
      <div class="nav-main">
        <router-link class="nav-btn ghost" to="/households">切换家庭</router-link>
        <router-link class="nav-btn ghost" to="/warehouse/settings">设置中心</router-link>
        <button class="nav-btn toggle" type="button" @click="navOpen = !navOpen">
          {{ navOpen ? '收起' : '展开' }}
        </button>
      </div>

      <div v-if="navOpen" class="nav-more">
        <div class="nav-group">
          <div class="nav-group-title">页面</div>
          <div class="nav-group-actions">
            <router-link class="nav-btn" to="/warehouse/outbound">出库</router-link>
            <router-link class="nav-btn" to="/warehouse/items">物品管理</router-link>
            <router-link class="nav-btn" to="/warehouse/manage">快速录入</router-link>
            <router-link class="nav-btn" to="/warehouse/notice">公告</router-link>
            <router-link class="nav-btn" to="/warehouse/user">用户管理</router-link>
          </div>
        </div>

        <div class="nav-group">
          <div class="nav-group-title">测试</div>
          <div class="nav-group-actions">
            <router-link class="nav-btn ghost" to="/warehouse/map-test">区域设置</router-link>
            <router-link class="nav-btn ghost" to="/warehouse/llm-test">LLM</router-link>
          </div>
        </div>
      </div>
    </div>
    <div class="grid-container">
      <div class="grid-item">
        <div class="panel">
          <DashboardNoticeTile />
        </div>
      </div>
      <div class="grid-item">
        <div class="panel">
          <WarehouseOutboundPage :embedded="true" />
        </div>
      </div>
      <div class="grid-item">
        <div class="panel">
          <ItemsEmbeddedTile :limit="20" />
        </div>
      </div>
      <div class="grid-item">
        <DataComponent />
      </div>
    </div>
  </div>
</template>

<script>
import { api } from '@/api/http';
import DashboardNoticeTile from './DashboardNoticeTile.vue';
import ItemsEmbeddedTile from './ItemsEmbeddedTile.vue';
import WarehouseOutboundPage from './WarehouseOutboundPage.vue';
import DataComponent from './Data.vue';

export default {
  name: 'WarehousePage',
  components: {
    DashboardNoticeTile,
    ItemsEmbeddedTile,
    WarehouseOutboundPage,
    DataComponent
  },
  data() {
    return {
      msg: 'Hello, Warehouse Page!',
      navOpen: false,
    };
  },
  created() {
    api.get('/api/me')
      .then(response => {
        const name = response.data.household_name || response.data.household_id;
        this.msg = `家庭：${name}`;
      })
      .catch(() => {
        this.msg = 'Warehouse';
      });
  },
};
</script>

<style scoped>
.warehouse-page {
  padding: 20px;
}

.page-title {
  text-align: center;
  margin-bottom: 20px;
  color: #333;
}

.quick-nav {
  display: grid;
  gap: 10px;
  justify-content: center;
  margin-bottom: 16px;
}

.nav-main {
  display: flex;
  gap: 10px;
  justify-content: center;
  flex-wrap: wrap;
}

.nav-more {
  max-width: 1200px;
  margin: 0 auto;
  display: grid;
  gap: 10px;
}

.nav-group {
  padding: 10px 12px;
  border-radius: 12px;
  background: rgba(255, 255, 255, 0.65);
  border: 1px solid rgba(0, 0, 0, 0.12);
}

.nav-group-title {
  font-weight: 900;
  color: rgba(0, 0, 0, 0.70);
  font-size: 12px;
  margin-bottom: 8px;
}

.nav-group-actions {
  display: flex;
  gap: 10px;
  flex-wrap: wrap;
  justify-content: center;
}

.nav-btn {
  padding: 10px 12px;
  border-radius: 10px;
  background: #111827;
  color: white;
  text-decoration: none;
  border: none;
  cursor: pointer;
}

.nav-btn.ghost {
  background: #1f6feb;
}

.nav-btn.toggle {
  background: rgba(0, 0, 0, 0.75);
  font-weight: 800;
}

.grid-container {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 15px;
}

.grid-item {
  width: 100%;
  height: 50vh;
  border-radius: 8px;
  overflow: auto;
  background: linear-gradient(to right, #ff7e5f, #feb47b);
  box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
  padding: 15px;
  box-sizing: border-box;
}

.panel {
  background: rgba(255, 255, 255, 0.72);
  border: 1px solid rgba(0, 0, 0, 0.10);
  border-radius: 12px;
  padding: 14px;
  box-sizing: border-box;
}

.panel-title {
  font-weight: 900;
  font-size: 18px;
  color: #111827;
  margin-bottom: 8px;
}

.panel-desc {
  color: rgba(0, 0, 0, 0.65);
  margin-bottom: 12px;
  font-size: 13px;
  line-height: 1.5;
}

.panel-actions {
  display: flex;
  gap: 10px;
  flex-wrap: wrap;
}

.panel-btn {
  display: inline-block;
  padding: 10px 12px;
  border-radius: 10px;
  background: #111827;
  color: white;
  text-decoration: none;
  font-weight: 700;
}

.panel-btn.ghost {
  background: #1f6feb;
}

/* 媒体查询，针对移动端设备 */
@media (max-width: 768px) {
  .grid-container {
    grid-template-columns: 1fr;
  }
}
</style>
