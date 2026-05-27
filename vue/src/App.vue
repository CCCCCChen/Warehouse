<template>
  <div class="app-shell">
    <router-view />
    <footer class="beian-footer">
      <span class="beian-item">
        ICP备案号：
        <a class="beian-link" :href="icpHref" target="_blank" rel="noopener noreferrer">{{ icpText }}</a>
      </span>
      <span v-if="psapText" class="beian-item">
        公安备案号：
        <a class="beian-link" :href="psapHref" target="_blank" rel="noopener noreferrer">{{ psapText }}</a>
      </span>
    </footer>
  </div>
</template>

<script>
export default {
  name: "App-app",
  computed: {
    icpText() {
      const v = (process.env.VUE_APP_ICP_NUMBER || '').trim();
      return v || '未配置';
    },
    psapText() {
      return (process.env.VUE_APP_PSAP_NUMBER || '').trim();
    },
    icpHref() {
      return 'https://beian.miit.gov.cn/';
    },
    psapHref() {
      const code = encodeURIComponent(this.psapText);
      return `https://www.beian.gov.cn/portal/registerSystemInfo?recordcode=${code}`;
    },
  },
};
</script>

<style>
.app-shell {
  min-height: 100vh;
  min-height: 100dvh;
  box-sizing: border-box;
  padding-bottom: calc(48px + env(safe-area-inset-bottom, 0px));
}

.beian-footer {
  position: fixed;
  left: 0;
  right: 0;
  bottom: 0;
  height: 48px;
  padding: 8px 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 14px;
  flex-wrap: wrap;
  box-sizing: border-box;
  font-size: 12px;
  color: rgba(0, 0, 0, 0.60);
  background: rgba(255, 255, 255, 0.92);
  border-top: 1px solid rgba(0, 0, 0, 0.08);
  backdrop-filter: blur(8px);
  padding-bottom: calc(8px + env(safe-area-inset-bottom, 0px));
}

.beian-item {
  display: inline-flex;
  gap: 6px;
  align-items: center;
  white-space: nowrap;
}

.beian-link {
  color: inherit;
  text-decoration: none;
}

.beian-link:hover {
  text-decoration: underline;
}
</style>
