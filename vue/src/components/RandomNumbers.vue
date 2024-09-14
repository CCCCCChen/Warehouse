<template>
    <div>
      <h1>My Component 0222</h1>
      <button @click="fetchData">Fetch Random Numbers</button>
      <!-- 显示随机数 -->
      <ul>
        <li v-for="number in randomNumbers" :key="number">{{ number }}</li>
      </ul>
    </div>
  </template>
  <script>
  
  import axios from 'axios';
  
  export default {
    name: 'RandomNumbers',  
    data() {
      return {
        randomNumbers: [], // 初始化一个空数组来存储随机数
      };
    },
    methods: {
      fetchData() {
        axios.get('http://localhost:8000/api/random_numbers')
          .then(response => {
            // 假设后端返回的数据是一个数字数组
            this.randomNumbers = response.data; // 直接赋值给 randomNumbers
          })
          .catch(error => {
            console.error("Error fetching data: ", error);
          });
      }
    }
  }
  </script>
  