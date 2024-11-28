import { createApp } from 'vue'; // 从 'vue' 引入 createApp，而不是 Vue
import router from './router';
import App from '@/components/App.vue';

const app = createApp(App);  // 使用 createApp 创建 Vue 实例
app.use(router);
app.mount('#app');  // 挂载到 DOM 元素上

console.log(router.getRoutes());  // 打印路由信息

const ws = new WebSocket('ws://localhost:8001/ws');

ws.onopen = () => { console.log('WebSocket connection opened'); };
ws.onmessage = (event) => { console.log('Message from server:', event.data); };
ws.onerror = (error) => { console.error('WebSocket Error:', error); };
ws.onclose = (event) => {
  if (event.wasClean) {
    console.log(`Connection closed cleanly, code=${event.code}, reason=${event.reason}`);
  } else {
    console.error('Connection died');
  }
};
