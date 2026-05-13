<template>
  <div class="page">
    <div class="header">
      <h2>LLM 接入测试</h2>
      <div class="header-actions">
        <router-link class="link ghost" to="/warehouse">主页</router-link>
      </div>
    </div>

    <div class="frame">
      <div class="panel">
        <div class="panel-title">状态</div>
        <div class="row">
          <button @click="fetchStatus">刷新状态</button>
        </div>
        <pre class="pre">{{ statusText }}</pre>
      </div>

      <div class="panel">
        <div class="panel-title">测试调用（文本 / 图片）</div>
        <div class="row">
          <label class="file">
            上传图片（可选）
            <input type="file" accept="image/*" @change="onPickImage" />
          </label>
        </div>
        <div v-if="previewUrl" class="preview">
          <img :src="previewUrl" alt="preview" />
        </div>
        <label class="full">
          提示词
          <textarea v-model.trim="prompt" rows="6" placeholder="输入你要测试的提示词"></textarea>
        </label>
        <div class="row">
          <button :disabled="running || !prompt" @click="runTest">
            {{ running ? '调用中...' : '调用 /api/llm/test' }}
          </button>
          <button class="ghost-btn" :disabled="running" @click="clearAll">清空</button>
        </div>
        <div v-if="hint" class="muted">{{ hint }}</div>
        <div class="panel-subtitle">返回值</div>
        <pre class="pre">{{ resultText }}</pre>
      </div>
    </div>
  </div>
</template>

<script>
import { api } from '@/api/http';

export default {
  name: 'LlmTestPage',
  data() {
    return {
      status: null,
      running: false,
      hint: '',
      file: null,
      previewUrl: '',
      prompt: '',
      result: null,
      error: null,
    };
  },
  computed: {
    statusText() {
      return this.status ? JSON.stringify(this.status, null, 2) : '未加载';
    },
    resultText() {
      if (this.error) return JSON.stringify(this.error, null, 2);
      return this.result ? JSON.stringify(this.result, null, 2) : '未调用';
    },
  },
  created() {
    this.fetchStatus();
  },
  methods: {
    async fetchStatus() {
      this.hint = '';
      try {
        const res = await api.get('/api/llm/status');
        this.status = res.data;
      } catch (e) {
        console.error('Failed to fetch status:', e);
        this.status = { error: '无法获取状态' };
      }
    },
    onPickImage(e) {
      const f = (e.target && e.target.files && e.target.files[0]) || null;
      this.file = f;
      if (this.previewUrl) URL.revokeObjectURL(this.previewUrl);
      this.previewUrl = f ? URL.createObjectURL(f) : '';
    },
    clearAll() {
      this.hint = '';
      this.prompt = '';
      this.result = null;
      this.error = null;
      this.file = null;
      if (this.previewUrl) URL.revokeObjectURL(this.previewUrl);
      this.previewUrl = '';
    },
    async runTest() {
      if (!this.prompt || this.running) return;
      this.running = true;
      this.hint = '';
      this.result = null;
      this.error = null;
      try {
        const fd = new FormData();
        fd.append('prompt', this.prompt);
        if (this.file) fd.append('file', this.file);
        const res = await api.post('/api/llm/test', fd);
        this.result = res.data;
        this.hint = '调用成功';
      } catch (e) {
        const detail = (e && e.response && e.response.data) ? e.response.data : null;
        this.error = detail || { error: '调用失败' };
        this.hint = '调用失败（查看返回值详情）';
      } finally {
        this.running = false;
      }
    },
  },
};
</script>

<style scoped>
.page {
  padding: 20px;
  max-width: 1200px;
  margin: 0 auto;
  background: rgba(255, 255, 255, 0.55);
  border: 1px solid rgba(0, 0, 0, 0.12);
  border-radius: 14px;
  box-shadow: 0 10px 30px rgba(0, 0, 0, 0.08);
}

.header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 12px;
  flex-wrap: wrap;
  margin-bottom: 12px;
}

.header-actions {
  display: flex;
  gap: 10px;
  align-items: center;
}

.link {
  display: inline-block;
  padding: 10px 12px;
  border-radius: 8px;
  background: #1f6feb;
  color: white;
  text-decoration: none;
}

.link.ghost {
  background: #111827;
}

.frame {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 12px;
  align-items: stretch;
}

.panel {
  background: rgba(255, 255, 255, 0.7);
  border-radius: 10px;
  padding: 14px;
  border: 1px solid rgba(0, 0, 0, 0.10);
  height: 100%;
}

.panel-title {
  font-weight: 900;
  margin-bottom: 10px;
}

.panel-subtitle {
  font-weight: 800;
  margin-top: 14px;
  margin-bottom: 8px;
}

.row {
  display: flex;
  gap: 12px;
  flex-wrap: wrap;
  margin-bottom: 10px;
}

.full {
  display: block;
  margin-bottom: 10px;
}

label {
  display: flex;
  flex-direction: column;
  gap: 6px;
  min-width: 160px;
  flex: 1;
}

textarea,
input {
  padding: 8px 10px;
  border-radius: 8px;
  border: 1px solid rgba(0, 0, 0, 0.15);
}

.ghost-btn {
  background: transparent;
  border: 1px solid rgba(0, 0, 0, 0.25);
  padding: 6px 10px;
  border-radius: 8px;
}

.muted {
  color: rgba(0, 0, 0, 0.65);
}

.pre {
  margin: 0;
  padding: 12px;
  border-radius: 10px;
  background: rgba(17, 24, 39, 0.06);
  border: 1px solid rgba(0, 0, 0, 0.12);
  white-space: pre-wrap;
  word-break: break-word;
  max-height: 420px;
  overflow: auto;
}

.preview {
  margin: 10px 0;
  border-radius: 12px;
  overflow: hidden;
  border: 1px solid rgba(0, 0, 0, 0.12);
}

.preview img {
  display: block;
  width: 100%;
  max-height: 260px;
  object-fit: contain;
  background: rgba(255, 255, 255, 0.6);
}

@media (max-width: 900px) {
  .frame {
    grid-template-columns: 1fr;
  }
}
</style>

