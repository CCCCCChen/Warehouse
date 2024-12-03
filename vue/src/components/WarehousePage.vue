<template>
  <div>
    <!-- PC端显示为2x2布局 -->
    <!-- 移动端显示为1x4布局 -->
    <div class="iframe-container">
      <iframe v-bind:src='`/warehouse/notice`' title="Component A" class="iframe"></iframe>
      <iframe v-bind:src="iframe02Url" title="Component B" class="iframe"></iframe>
      <iframe v-bind:src="iframe03Url" title="Component C" class="iframe"></iframe>
      <iframe v-bind:src="iframe04Url" title="Component D" class="iframe"></iframe>
    </div>
  </div>
</template>

<script>
import axios from 'axios';
export default {
  name: 'WarehousePage',  // 使用多词名称
  computed: {
    isPc() {
      return window.innerWidth >= 768; // 根据窗口宽度判断是否为PC端
    },
    iframe01Url() {
      // URL for loading A.vue asynchronously
      return `/warehouse/notice`;
    },
    iframe02Url() {
      // URL for loading B.vue asynchronously
      return `${window.location.origin}/random_numbers`;
    },
    iframe03Url() {
      // URL for loading B.vue asynchronously
      return `${window.location.origin}/`;
    },
    iframe04Url() {
      // URL for loading B.vue asynchronously
      return "http://10.12.3.6";
      
      //return `${window.location.origin}/component-b`;
    }
  },
  data() {
    return {
      msg: 'Hello, Warehouse Page!',
    };
  },
  created() {
    axios.get('http://localhost:8000/api/warehouse')
      .then(response => {
        console.log(response.data);
        this.msg = 'Hello, '+ response.data.message +'!';
        //msg = response.data;
      })
      .catch(error => {
        console.error(error);
      });
  },
};
</script>


<style>
.iframe-container {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 10px; /* 根据需要调整间距 */
}

.iframe {
  width: 100%;
  height: 50vh; /* 高度为页面高度除以2，可以根据需要调整 */
  border: none; /* 移除边框 */
  border-radius: 5px; /* 设置圆角 */
  overflow: hidden; /* 确保内容不会超出圆角边界 */
    /* 设置背景色为粉色渐变*/
  background: linear-gradient(to right, #ff7e5f, #feb47b);

}

/* 媒体查询，针对移动端设备 */
@media (max-width: 768px) {
  .iframe-container {
    grid-template-columns: repeat(1, 1fr);
  }
}
</style>