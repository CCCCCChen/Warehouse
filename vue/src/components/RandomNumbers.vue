<template>
  <div>
    <h1>Random Numbers Component</h1>
    <button @click="fetchData">Fetch Random Numbers</button>
    <!-- 显示随机数 -->
    <ul v-if="randomNumbers && randomNumbers.length">
      <li v-for="(number, index) in randomNumbers" :key="index">{{ number }}</li>
    </ul>
  </div>
</template>

<script>
import { api } from '@/api/http';

export default {
  name: 'RandomNumbers',  
  data() {
    return {
      randomNumbers: [], // 初始化一个空数组来存储随机数
    };
  },
  methods: {
    fetchData() {
      api.get('/api/random_numbers')
        .then(response => {
          // 后端返回的是 {"numbers": [...]}
          this.randomNumbers = response.data.numbers;
        })
        .catch(error => {
          console.error("Error fetching data: ", error);
        });
    }
  }
}
</script>
