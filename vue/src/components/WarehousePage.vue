<template>
  <div class="warehouse-page">
    <h2 class="page-title">{{ msg }}</h2>
    <div class="grid-container">
      <div class="grid-item">
        <WarehouseNotice />
      </div>
      <div class="grid-item">
        <RandomNumbers />
      </div>
      <div class="grid-item">
        <HelloWorld msg="Welcome to Warehouse Component" />
      </div>
      <div class="grid-item">
        <DataComponent />
      </div>
    </div>
  </div>
</template>

<script>
import axios from 'axios';
import WarehouseNotice from './WarehouseNotice.vue';
import RandomNumbers from './RandomNumbers.vue';
import HelloWorld from './HelloWorld.vue';
import DataComponent from './Data.vue';

export default {
  name: 'WarehousePage',
  components: {
    WarehouseNotice,
    RandomNumbers,
    HelloWorld,
    DataComponent
  },
  data() {
    return {
      msg: 'Hello, Warehouse Page!',
    };
  },
  created() {
    // 修复硬编码，使用环境变量或默认的本地后端地址
    const apiBaseUrl = process.env.VUE_APP_API_BASE_URL || 'http://127.0.0.1:18808';
    axios.get(`${apiBaseUrl}/api/warehouse`)
      .then(response => {
        this.msg = response.data.message;
      })
      .catch(error => {
        console.error('Failed to fetch warehouse info:', error);
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
