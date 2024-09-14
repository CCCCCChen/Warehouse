<template>
  <div>
    <h1>{{msg}}</h1>
    <h2>仓库主页内容</h2>
  </div>
</template>

<script>
import axios from 'axios';
export default {
  name: 'WarehousePage',  // 使用多词名称
  data() {
    return {
      msg: 'Hello, Warehouse Page!',
    };
  },
  created() {
    axios.get('http://localhost:8000/warehouse')
      .then(response => {
        console.log(response.data);
        this.msg = response.data;
        //msg = response.data;
      })
      .catch(error => {
        console.error(error);
      });
  },
};
</script>
