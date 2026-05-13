<template>
  <div class="warehouse-page">
    <h2 class="page-title">{{ msg }}</h2>
    <div class="quick-nav">
      <router-link class="nav-btn ghost" to="/households">切换家庭</router-link>
      <router-link class="nav-btn" to="/warehouse/items">物品管理</router-link>
      <router-link class="nav-btn" to="/warehouse/manage">录入/管理</router-link>
      <router-link class="nav-btn" to="/warehouse/user">用户管理</router-link>
      <router-link class="nav-btn" to="/warehouse/notice">公告</router-link>
      <router-link class="nav-btn ghost" to="/warehouse/map-test">区域设置(测试)</router-link>
      <router-link class="nav-btn ghost" to="/warehouse/llm-test">LLM 测试</router-link>
      <router-link class="nav-btn ghost" to="/warehouse/settings">设置中心</router-link>
    </div>
    <div class="grid-container">
      <div class="grid-item">
        <WarehouseNotice />
      </div>
      <div class="grid-item">
        <RandomNumbers />
      </div>
      <div class="grid-item">
        <DashboardSummary />
      </div>
      <div class="grid-item">
        <DataComponent />
      </div>
    </div>
  </div>
</template>

<script>
import { api } from '@/api/http';
import WarehouseNotice from './WarehouseNotice.vue';
import RandomNumbers from './RandomNumbers.vue';
import DashboardSummary from './DashboardSummary.vue';
import DataComponent from './Data.vue';

export default {
  name: 'WarehousePage',
  components: {
    WarehouseNotice,
    RandomNumbers,
    DashboardSummary,
    DataComponent
  },
  data() {
    return {
      msg: 'Hello, Warehouse Page!',
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
  display: flex;
  gap: 10px;
  justify-content: center;
  flex-wrap: wrap;
  margin-bottom: 16px;
}

.nav-btn {
  padding: 10px 12px;
  border-radius: 10px;
  background: #111827;
  color: white;
  text-decoration: none;
}

.nav-btn.ghost {
  background: #1f6feb;
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

/* 媒体查询，针对移动端设备 */
@media (max-width: 768px) {
  .grid-container {
    grid-template-columns: 1fr;
  }
}
</style>
