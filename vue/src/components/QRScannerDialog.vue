<template>
  <div class="scanner-overlay" @click.self="$emit('close')">
    <div class="scanner-dialog">
      <div class="dialog-header">
        <h3>扫码录入物品</h3>
        <button class="btn-ghost btn-sm" @click="$emit('close')">关闭</button>
      </div>

      <!-- Tab switch -->
      <div class="tabs">
        <button
          :class="['tab', { active: mode === 'camera' }]"
          @click="switchMode('camera')"
        >拍照扫码</button>
        <button
          :class="['tab', { active: mode === 'image' }]"
          @click="switchMode('image')"
        >导入图片</button>
      </div>

      <!-- Camera mode -->
      <div v-if="mode === 'camera'" class="camera-section">
        <div class="video-wrapper">
          <video ref="video" autoplay playsinline muted class="video"></video>
          <canvas ref="canvas" class="canvas-hidden"></canvas>
          <div v-if="cameraError" class="camera-error">{{ cameraError }}</div>
          <div v-else-if="!cameraReady" class="camera-loading">启动摄像头...</div>
        </div>
        <div class="scan-status">{{ scanning ? '识别中...' : '将二维码对准框内' }}</div>
      </div>

      <!-- Image import mode -->
      <div v-if="mode === 'image'" class="image-section">
        <label class="upload-btn">
          选择二维码图片
          <input
            type="file"
            accept="image/*"
            @change="onFilePick"
            hidden
          />
        </label>
        <div v-if="imageError" class="image-error">{{ imageError }}</div>
        <div v-if="imageResult" class="image-result">
          <img :src="imageResult" alt="preview" class="preview" />
        </div>
      </div>

      <div v-if="resultHint" class="result-hint" :class="{ error: resultError }">
        {{ resultHint }}
      </div>
    </div>
  </div>
</template>

<script>
import jsQR from 'jsqr';

const LOCATION_URL_RE = /\/location\/([0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12})/i;

export default {
  name: 'QRScannerDialog',

  emits: ['close'],

  data() {
    return {
      mode: 'camera',
      cameraReady: false,
      cameraError: '',
      scanning: false,
      stream: null,
      scanTimer: null,

      imageError: '',
      imageResult: '',

      resultHint: '',
      resultError: false,
    };
  },

  mounted() {
    this.startCamera();
  },

  beforeUnmount() {
    this.stopCamera();
  },

  methods: {
    switchMode(m) {
      if (m === this.mode) return;
      this.mode = m;
      this.resultHint = '';
      this.resultError = false;
      if (m === 'camera') {
        this.imageError = '';
        this.imageResult = '';
        this.startCamera();
      } else {
        this.stopCamera();
      }
    },

    // ── Camera ──

    async startCamera() {
      this.cameraError = '';
      this.cameraReady = false;
      this.scanning = false;
      try {
        const isMobile = /Mobi|Android|iPhone/i.test(navigator.userAgent);
        const constraints = isMobile
          ? { video: { facingMode: 'environment', width: { ideal: 640 }, height: { ideal: 480 } } }
          : { video: { width: { ideal: 640 }, height: { ideal: 480 } } };
        this.stream = await navigator.mediaDevices.getUserMedia(constraints);
        this.$refs.video.srcObject = this.stream;
        await this.$refs.video.play();
        this.cameraReady = true;
        this.startScanLoop();
      } catch (e) {
        if (e.name === 'NotAllowedError') {
          this.cameraError = '摄像头权限被拒绝，请允许访问摄像头或使用「导入图片」';
        } else if (e.name === 'NotFoundError' || e.name === 'NotReadableError') {
          this.cameraError = '未找到摄像头或摄像头被占用，请使用「导入图片」';
        } else {
          this.cameraError = `摄像头启动失败: ${e.message}`;
        }
      }
    },

    startScanLoop() {
      const video = this.$refs.video;
      const canvas = this.$refs.canvas;
      if (!video || !canvas) return;

      const ctx = canvas.getContext('2d');

      const tick = () => {
        if (!this.cameraReady || this.mode !== 'camera') {
          this.scanTimer = requestAnimationFrame(tick);
          return;
        }
        if (video.readyState !== video.HAVE_ENOUGH_DATA) {
          this.scanTimer = requestAnimationFrame(tick);
          return;
        }

        canvas.width = video.videoWidth;
        canvas.height = video.videoHeight;
        ctx.drawImage(video, 0, 0, canvas.width, canvas.height);

        const imageData = ctx.getImageData(0, 0, canvas.width, canvas.height);
        const code = jsQR(imageData.data, canvas.width, canvas.height);

        if (code && code.data) {
          this.handleDecode(code.data);
          return;
        }

        this.scanning = true;
        this.scanTimer = requestAnimationFrame(tick);
      };

      this.scanTimer = requestAnimationFrame(tick);
    },

    stopCamera() {
      if (this.scanTimer) {
        cancelAnimationFrame(this.scanTimer);
        this.scanTimer = null;
      }
      if (this.stream) {
        this.stream.getTracks().forEach(t => t.stop());
        this.stream = null;
      }
      this.cameraReady = false;
    },

    // ── Image import ──

    onFilePick(e) {
      this.imageError = '';
      this.resultHint = '';
      this.resultError = false;
      const file = e.target.files && e.target.files[0];
      if (!file) return;

      if (!file.type.startsWith('image/')) {
        this.imageError = '请选择图片文件';
        return;
      }

      const reader = new FileReader();
      reader.onload = () => {
        const dataUrl = reader.result;
        this.imageResult = dataUrl;
        this.decodeImage(dataUrl);
      };
      reader.onerror = () => {
        this.imageError = '图片读取失败';
      };
      reader.readAsDataURL(file);
    },

    decodeImage(dataUrl) {
      const img = new Image();
      img.onload = () => {
        const canvas = document.createElement('canvas');
        canvas.width = img.width;
        canvas.height = img.height;
        const ctx = canvas.getContext('2d');
        ctx.drawImage(img, 0, 0);
        const imageData = ctx.getImageData(0, 0, canvas.width, canvas.height);
        const code = jsQR(imageData.data, canvas.width, canvas.height);
        if (code && code.data) {
          this.handleDecode(code.data);
        } else {
          this.resultHint = '未能识别二维码，请确认图片包含清晰完整的二维码';
          this.resultError = true;
        }
      };
      img.onerror = () => {
        this.imageError = '图片加载失败';
      };
      img.src = dataUrl;
    },

    // ── Decode handler ──

    handleDecode(raw) {
      this.stopCamera();
      const match = raw.match(LOCATION_URL_RE);
      if (!match) {
        this.resultHint = `二维码内容不是有效的位置链接: ${raw.substring(0, 60)}...`;
        this.resultError = true;
        return;
      }
      const locId = match[1];
      this.resultHint = `已识别位置，正在跳转...`;
      this.$router.push(`/warehouse/manage?location_id=${locId}`);
    },
  },
};
</script>

<style scoped>
.scanner-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.45);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}

.scanner-dialog {
  background: #fff;
  border-radius: 14px;
  width: 90%;
  max-width: 440px;
  max-height: 90vh;
  overflow-y: auto;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.22);
}

.dialog-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 18px 20px 12px;
}

.dialog-header h3 {
  margin: 0;
  font-size: 17px;
}

/* Tabs */
.tabs {
  display: flex;
  border-bottom: 1px solid rgba(0, 0, 0, 0.1);
  padding: 0 20px;
}

.tab {
  flex: 1;
  padding: 10px 0;
  text-align: center;
  border: none;
  background: none;
  font-size: 14px;
  color: rgba(0, 0, 0, 0.5);
  cursor: pointer;
  border-bottom: 2px solid transparent;
  transition: all 0.15s;
}

.tab.active {
  color: #000;
  border-bottom-color: #3b82f6;
  font-weight: 600;
}

/* Camera */
.camera-section {
  padding: 16px 20px 20px;
}

.video-wrapper {
  position: relative;
  width: 100%;
  aspect-ratio: 4/3;
  background: #1a1a1a;
  border-radius: 10px;
  overflow: hidden;
  display: flex;
  align-items: center;
  justify-content: center;
}

.video {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.canvas-hidden {
  display: none;
}

.camera-loading,
.camera-error {
  position: absolute;
  inset: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  color: rgba(255, 255, 255, 0.8);
  font-size: 15px;
  padding: 20px;
  text-align: center;
}

.camera-error {
  color: #ff6b6b;
}

.scan-status {
  text-align: center;
  margin-top: 10px;
  font-size: 13px;
  color: rgba(0, 0, 0, 0.5);
}

/* Image */
.image-section {
  padding: 20px;
  text-align: center;
}

.upload-btn {
  display: inline-block;
  padding: 14px 32px;
  background: #3b82f6;
  color: #fff;
  border-radius: 10px;
  font-size: 15px;
  cursor: pointer;
  transition: background 0.15s;
}

.upload-btn:hover {
  background: #2563eb;
}

.image-error {
  margin-top: 12px;
  color: #dc2626;
  font-size: 13px;
}

.image-result {
  margin-top: 16px;
}

.preview {
  max-width: 100%;
  max-height: 240px;
  border-radius: 8px;
  border: 1px solid rgba(0, 0, 0, 0.1);
}

/* Result hint */
.result-hint {
  margin: 0 20px 16px;
  padding: 10px 14px;
  border-radius: 8px;
  background: rgba(59, 130, 246, 0.08);
  color: #2563eb;
  font-size: 14px;
  text-align: center;
}

.result-hint.error {
  background: rgba(220, 38, 38, 0.08);
  color: #dc2626;
}

@media (max-width: 480px) {
  .scanner-dialog {
    width: 100%;
    max-width: 100%;
    border-radius: 14px 14px 0 0;
    position: fixed;
    bottom: 0;
    max-height: 85vh;
  }
}
</style>
