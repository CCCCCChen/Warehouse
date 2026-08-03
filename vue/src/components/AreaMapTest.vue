<template>
  <div class="area-map-page">
    <div class="header">
      <h2>区域与墙面标注</h2>
      <div class="header-actions">
        <button class="btn-ghost" :disabled="loading" @click="loadFromServer">加载</button>
        <button class="btn-primary" :disabled="loading" @click="saveToServer">保存</button>
        <button class="btn-ghost" :disabled="loading" @click="exportAreaJson">导出JSON</button>
        <button class="btn-ghost" :disabled="loading" @click="triggerJsonPick">导入JSON</button>
        <router-link class="link" to="/warehouse">返回</router-link>
        <input ref="jsonInput" class="json-input" type="file" accept=".json,application/json" @change="onJsonPicked" />
      </div>
    </div>

    <!-- 房间选择器 -->
    <div class="room-selector">
      <button
        v-for="(room, idx) in rooms"
        :key="idx"
        class="room-chip"
        :class="{ active: selectedRoomIndex === idx }"
        @click="selectRoom(idx)"
      >
        {{ room.name }}
      </button>
      <button class="room-chip add-chip" @click="startRoomDraw">+ 新区域</button>
    </div>

    <!-- 主内容区 -->
    <div class="main-grid">
      <!-- 左侧：房间画布 -->
      <div class="panel room-panel" :class="{ collapsed: selectedRoomIndex !== null && isMobile }">
        <div class="panel-title">
          房间/区域布局
          <div class="zoom-controls">
            <button @click="adjustRoomZoom(-0.1)">-</button>
            <span>{{ Math.round(roomZoom * 100) }}%</span>
            <button @click="adjustRoomZoom(0.1)">+</button>
          </div>
        </div>
        <div class="muted">拖拽画矩形创建房间，选中后可拖动移动。</div>

        <div
          class="canvas-scroll-area"
          @wheel="onRoomWheel"
          @touchstart="onRoomTouchStart"
          @touchmove="onRoomTouchMove"
          @touchend="onRoomTouchEnd"
          @touchcancel="onRoomTouchEnd"
        >
          <div
            class="canvas-container"
            ref="roomCanvas"
            :style="{ transform: `scale(${roomZoom})`, transformOrigin: 'top left' }"
            @mousedown="onRoomMouseDown"
            @mousemove="onRoomMouseMove"
            @mouseup="onRoomMouseUp"
            @mouseleave="onRoomMouseUp"
          >
            <div
              v-for="(room, idx) in rooms"
              :key="idx"
              class="room-box"
              :class="{ active: selectedRoomIndex === idx }"
              :style="boxStyle(room)"
              @mousedown.stop="onRoomDragStart($event, idx)"
              @touchstart.stop.prevent="onRoomDragStartTouch($event, idx)"
            >
              <div class="room-name">{{ room.name }}</div>
            </div>
            <div
              v-if="drawingRoom"
              class="room-box drawing"
              :style="boxStyle(drawingRoom)"
            ></div>
          </div>
        </div>

        <div v-if="selectedRoomIndex !== null" class="edit-box">
          <div class="strong">编辑区域</div>
          <label>名称 <input v-model.trim="rooms[selectedRoomIndex].name" /></label>
          <button class="btn-danger" @click="deleteRoom(selectedRoomIndex)">删除此区域</button>
        </div>
      </div>

      <!-- 右侧：墙面标注 -->
      <div class="panel wall-panel" v-if="selectedRoomIndex !== null">
        <div class="panel-title">
          墙面标注 — {{ rooms[selectedRoomIndex].name }}
          <div class="zoom-controls">
            <button @click="adjustWallZoom(-0.1)">-</button>
            <span>{{ Math.round(wallZoom * 100) }}%</span>
            <button @click="adjustWallZoom(0.1)">+</button>
          </div>
        </div>

        <div class="wall-tabs">
          <button
            v-for="wall in wallTypes"
            :key="wall.value"
            class="tab-btn"
            :class="{ active: selectedWallType === wall.value }"
            @click="selectWall(wall.value)"
          >
            {{ wall.label }}
          </button>
        </div>

        <div class="wall-content" v-if="currentWall">
          <label class="wall-image-row">
            <span class="strong">背景图</span>
            <div class="row">
              <input v-model.trim="currentWall.image" placeholder="图片 URL…" />
              <input type="file" accept="image/*" @change="onWallImageUpload" class="img-pick" />
            </div>
          </label>

          <!-- 工具栏 -->
          <div class="toolbar">
            <button :class="{ active: mode === 'add' }" @click="mode = 'add'">添加标记</button>
            <button :class="{ active: mode === 'move' }" @click="mode = 'move'">移动标记</button>
            <button :class="{ active: mode === 'delete' }" @click="mode = 'delete'">删除标记</button>
            <span class="mode-hint">{{ modeHint }}</span>
          </div>

          <!-- 墙面图片画布 -->
          <div
            class="canvas-scroll-area wall-scroll"
            @wheel="onWallWheel"
            @touchstart="onWallTouchStart"
            @touchmove="onWallTouchMove"
            @touchend="onWallTouchEnd"
            @touchcancel="onWallTouchEnd"
          >
            <div
              class="wall-canvas"
              ref="wallCanvas"
              :style="wallCanvasStyle"
              @click="onWallClick"
            >
              <div v-if="!currentWall.image" class="empty-bg">未设置背景图</div>

              <div
                v-for="(dot, idx) in currentWallDots"
                :key="idx"
                class="marker-dot"
                :class="{
                  active: selectedDotIndex === idx,
                  movable: mode === 'move'
                }"
                :style="dotStyle(dot)"
                @click.stop="onDotClick(idx)"
                @mousedown.stop="onDotDragStart($event, idx)"
                @touchstart.stop.prevent="onDotDragStartTouch($event, idx)"
              >
                <span class="dot-num">{{ idx + 1 }}</span>
              </div>
            </div>
          </div>

          <!-- 编辑面板 -->
          <div v-if="selectedDotIndex !== null" class="edit-box mt-2">
            <div class="strong">编辑标记 #{{ selectedDotIndex + 1 }}</div>
            <label>名称 <input v-model.trim="currentWallDots[selectedDotIndex].name" /></label>
            <div class="edit-actions">
              <button class="btn-danger" @click="deleteDot(selectedDotIndex)">删除此标记</button>
              <button class="btn-ghost" @click="selectedDotIndex = null">完成</button>
            </div>
          </div>
        </div>
      </div>

      <!-- 未选房间时的提示 -->
      <div class="panel wall-panel empty-wall" v-else>
        <div class="panel-title">墙面标注</div>
        <div class="muted">请先选择一个房间，或画一个新房间。</div>
      </div>
    </div>

    <!-- 命名对话框 -->
    <div v-if="namingDialog.show" class="naming-overlay" @click.self="namingDialog.show = false">
      <div class="naming-dialog">
        <div class="naming-title">新标记命名</div>
        <input
          ref="namingInput"
          v-model.trim="namingDialog.name"
          placeholder="输入名称…"
          @keyup.enter="confirmNaming"
        />
        <div class="naming-actions">
          <button class="btn-ghost" @click="namingDialog.show = false">取消</button>
          <button class="btn-primary" @click="confirmNaming">确定</button>
        </div>
      </div>
    </div>

    <div v-if="hint" class="hint">{{ hint }}</div>
  </div>
</template>

<script>
import { api } from '@/api/http';

export default {
  name: 'AreaMapTest',
  data() {
    return {
      rooms: [],
      loading: false,
      hint: '',
      wallImageLoadId: 0,
      selectedRoomIndex: null,
      drawingRoom: null,
      startPos: null,
      isMobile: false,

      wallTypes: [
        { label: '北墙', value: 'north' },
        { label: '南墙', value: 'south' },
        { label: '东墙', value: 'east' },
        { label: '西墙', value: 'west' },
        { label: '底面', value: 'floor' },
      ],
      selectedWallType: 'north',

      mode: 'add',
      selectedDotIndex: null,

      namingDialog: { show: false, name: '', coords: null },

      roomZoom: 1.0,
      wallZoom: 1.0,

      dragInfo: null,
      roomPinch: null,
      wallPinch: null,
    };
  },
  created() {
    this.checkMobile();
    window.addEventListener('resize', this.checkMobile);
    this.loadFromServer();
  },
  beforeUnmount() {
    window.removeEventListener('resize', this.checkMobile);
  },
  computed: {
    currentWall() {
      const room = this.rooms[this.selectedRoomIndex];
      if (!room) return null;
      if (!room.walls[this.selectedWallType]) {
        room.walls[this.selectedWallType] = { image: '', dots: [] };
      }
      return room.walls[this.selectedWallType];
    },
    currentWallDots() {
      return this.currentWall ? (this.currentWall.dots || []) : [];
    },
    modeHint() {
      const map = { add: '点击墙面放置标记', move: '拖拽标记改变位置', delete: '点击标记将其删除' };
      return map[this.mode] || '';
    },
    wallCanvasStyle() {
      const w = this.currentWall;
      const width = w && Number.isFinite(Number(w._img_w)) && Number(w._img_w) > 0 ? Math.round(Number(w._img_w)) : 2000;
      const height = w && Number.isFinite(Number(w._img_h)) && Number(w._img_h) > 0 ? Math.round(Number(w._img_h)) : 2000;
      return {
        backgroundImage: w && w.image ? `url(${w.image})` : 'none',
        width: `${width}px`,
        height: `${height}px`,
        transform: `scale(${this.wallZoom})`,
        transformOrigin: 'top left',
      };
    }
  },
  watch: {
    'currentWall.image': { immediate: true, handler(v) { this.updateCurrentWallImageSize(v); } },
    selectedRoomIndex() { this.$nextTick(() => { const w = this.currentWall; this.updateCurrentWallImageSize(w ? w.image : ''); }); },
    selectedWallType() { this.selectedDotIndex = null; this.$nextTick(() => { const w = this.currentWall; this.updateCurrentWallImageSize(w ? w.image : ''); }); },
  },
  methods: {
    /* ====== 响应式 ====== */
    checkMobile() { this.isMobile = window.innerWidth <= 768; },

    /* ====== 房间选择 ====== */
    selectRoom(idx) { this.selectedRoomIndex = idx; this.selectedDotIndex = null; this.mode = 'add'; },
    startRoomDraw() { this.selectedRoomIndex = null; this.selectedDotIndex = null; this.hint = '在下方灰色画布上拖拽鼠标画出新房间'; },
    selectWall(type) { this.selectedWallType = type; this.selectedDotIndex = null; this.mode = 'add'; },

    /* ====== 墙面点击 ====== */
    onWallClick(e) {
      if (!this.currentWall) return;
      if (e.target.closest('.marker-dot')) return;
      if (this.mode === 'add') this.openNamingDialog(e);
    },

    /* ====== 命名对话框 ====== */
    openNamingDialog(e) {
      const w = this.currentWall;
      const imgW = w._img_w || 2000;
      const imgH = w._img_h || 2000;
      const rect = e.currentTarget.getBoundingClientRect();
      const ox = (e.clientX - rect.left) / this.wallZoom;
      const oy = (e.clientY - rect.top) / this.wallZoom;
      const x = Math.max(0, Math.min(1000, Math.round(ox / imgW * 1000)));
      const y = Math.max(0, Math.min(1000, Math.round(oy / imgH * 1000)));
      this.namingDialog = { show: true, name: '', coords: { x, y } };
      this.$nextTick(() => { this.$refs.namingInput && this.$refs.namingInput.focus(); });
    },
    confirmNaming() {
      const name = this.namingDialog.name || `储物单元`;
      const { x, y } = this.namingDialog.coords || {};
      if (this.currentWall && x != null && y != null) {
        if (!this.currentWall.dots) this.currentWall.dots = [];
        this.currentWall.dots.push({ name, x, y });
        this.selectedDotIndex = this.currentWall.dots.length - 1;
      }
      this.namingDialog = { show: false, name: '', coords: null };
    },

    /* ====== 标记点击 ====== */
    onDotClick(idx) {
      if (this.mode === 'delete') { this.deleteDot(idx); return; }
      if (this.mode === 'add') { this.selectedDotIndex = idx; }
    },

    /* ====== 标记拖拽 ====== */
    onDotDragStart(e, idx) {
      if (this.mode !== 'move') return;
      this.selectedDotIndex = idx;
      const el = this.$refs.wallCanvas; if (!el) return;
      const rect = el.getBoundingClientRect();
      const cx = (e.clientX - rect.left) / this.wallZoom;
      const cy = (e.clientY - rect.top) / this.wallZoom;
      this.dragInfo = { type: 'dot', index: idx, startX: cx, startY: cy, origX: this.currentWallDots[idx].x, origY: this.currentWallDots[idx].y, imgW: this.currentWall._img_w || 2000, imgH: this.currentWall._img_h || 2000 };
      window.addEventListener('mousemove', this.onDotDragMove);
      window.addEventListener('mouseup', this.onDotDragEnd);
    },
    onDotDragStartTouch(e, idx) {
      if (this.mode !== 'move') return;
      this.selectedDotIndex = idx;
      const t = this.firstTouch(e); if (!t) return;
      const el = this.$refs.wallCanvas; if (!el) return;
      const rect = el.getBoundingClientRect();
      const cx = (t.clientX - rect.left) / this.wallZoom;
      const cy = (t.clientY - rect.top) / this.wallZoom;
      this.dragInfo = { type: 'dot', index: idx, startX: cx, startY: cy, origX: this.currentWallDots[idx].x, origY: this.currentWallDots[idx].y, imgW: this.currentWall._img_w || 2000, imgH: this.currentWall._img_h || 2000 };
      window.addEventListener('touchmove', this.onDotDragMoveTouch, { passive: false });
      window.addEventListener('touchend', this.onDotDragEndTouch);
    },
    onDotDragMove(e) {
      if (!this.dragInfo || this.dragInfo.type !== 'dot') return;
      const el = this.$refs.wallCanvas; if (!el) return;
      const rect = el.getBoundingClientRect();
      const cx = (e.clientX - rect.left) / this.wallZoom;
      const cy = (e.clientY - rect.top) / this.wallZoom;
      const dx = (cx - this.dragInfo.startX) / this.dragInfo.imgW * 1000;
      const dy = (cy - this.dragInfo.startY) / this.dragInfo.imgH * 1000;
      const dot = this.currentWallDots[this.dragInfo.index];
      dot.x = Math.max(0, Math.min(1000, Math.round(this.dragInfo.origX + dx)));
      dot.y = Math.max(0, Math.min(1000, Math.round(this.dragInfo.origY + dy)));
    },
    onDotDragEnd() { this.dragInfo = null; window.removeEventListener('mousemove', this.onDotDragMove); window.removeEventListener('mouseup', this.onDotDragEnd); },
    onDotDragMoveTouch(e) {
      if (!this.dragInfo || this.dragInfo.type !== 'dot') return;
      e.preventDefault();
      const t = this.firstTouch(e); if (!t) return;
      const el = this.$refs.wallCanvas; if (!el) return;
      const rect = el.getBoundingClientRect();
      const cx = (t.clientX - rect.left) / this.wallZoom;
      const cy = (t.clientY - rect.top) / this.wallZoom;
      const dx = (cx - this.dragInfo.startX) / this.dragInfo.imgW * 1000;
      const dy = (cy - this.dragInfo.startY) / this.dragInfo.imgH * 1000;
      const dot = this.currentWallDots[this.dragInfo.index];
      dot.x = Math.max(0, Math.min(1000, Math.round(this.dragInfo.origX + dx)));
      dot.y = Math.max(0, Math.min(1000, Math.round(this.dragInfo.origY + dy)));
    },
    onDotDragEndTouch() { this.dragInfo = null; window.removeEventListener('touchmove', this.onDotDragMoveTouch); window.removeEventListener('touchend', this.onDotDragEndTouch); },

    /* ====== 标记删除 ====== */
    deleteDot(idx) {
      if (!this.currentWall || !this.currentWall.dots) return;
      this.currentWall.dots.splice(idx, 1);
      if (this.selectedDotIndex === idx) this.selectedDotIndex = null;
      else if (this.selectedDotIndex > idx) this.selectedDotIndex--;
    },

    /* ====== 标记样式 ====== */
    dotStyle(dot) {
      const w = this.currentWall;
      const imgW = w && w._img_w ? w._img_w : 2000;
      const imgH = w && w._img_h ? w._img_h : 2000;
      return { left: `${dot.x / 1000 * imgW}px`, top: `${dot.y / 1000 * imgH}px` };
    },

    /* ====== 图片尺寸 ====== */
    updateCurrentWallImageSize(url) {
      const wall = this.currentWall; if (!wall) return;
      const raw = (url || '').trim();
      if (!raw) { delete wall._img_w; delete wall._img_h; return; }
      const id = ++this.wallImageLoadId;
      const img = new Image();
      img.onload = () => {
        if (id !== this.wallImageLoadId || !this.currentWall || (this.currentWall.image || '').trim() !== raw) return;
        const iw = img.naturalWidth || img.width, ih = img.naturalHeight || img.height;
        if (!Number.isFinite(iw) || !Number.isFinite(ih) || iw <= 0 || ih <= 0) return;
        this.currentWall._img_w = iw; this.currentWall._img_h = ih;
      };
      img.onerror = () => { if (id === this.wallImageLoadId && this.currentWall && (this.currentWall.image || '').trim() === raw) { delete this.currentWall._img_w; delete this.currentWall._img_h; } };
      img.src = raw;
    },

    /* ====== 房间绘制 ====== */
    firstTouch(e) { return (e.touches && e.touches[0]) || (e.changedTouches && e.changedTouches[0]) || null; },
    boxStyle(box) { return { left: box.x + 'px', top: box.y + 'px', width: box.w + 'px', height: box.h + 'px' }; },
    onRoomMouseDown(e) {
      if (this.dragInfo) return;
      const rect = e.currentTarget.getBoundingClientRect();
      const cx = (e.clientX - rect.left) / this.roomZoom, cy = (e.clientY - rect.top) / this.roomZoom;
      this.startPos = { x: cx, y: cy }; this.drawingRoom = { x: cx, y: cy, w: 0, h: 0 }; this.selectedRoomIndex = null;
    },
    onRoomDragStart(e, idx) {
      this.selectedRoomIndex = idx; this.selectedDotIndex = null; this.mode = 'add';
      const rect = e.currentTarget.parentElement.getBoundingClientRect();
      const cx = (e.clientX - rect.left) / this.roomZoom, cy = (e.clientY - rect.top) / this.roomZoom;
      this.dragInfo = { type: 'room', index: idx, startX: cx, startY: cy, origX: this.rooms[idx].x, origY: this.rooms[idx].y };
    },
    onRoomDragStartTouch(e, idx) {
      this.selectedRoomIndex = idx; this.selectedDotIndex = null; this.mode = 'add';
      const t = this.firstTouch(e); if (!t) return;
      const rect = e.currentTarget.parentElement.getBoundingClientRect();
      const cx = (t.clientX - rect.left) / this.roomZoom, cy = (t.clientY - rect.top) / this.roomZoom;
      this.dragInfo = { type: 'room', index: idx, startX: cx, startY: cy, origX: this.rooms[idx].x, origY: this.rooms[idx].y };
    },
    onRoomMouseMove(e) {
      const rect = e.currentTarget.getBoundingClientRect();
      const cx = (e.clientX - rect.left) / this.roomZoom, cy = (e.clientY - rect.top) / this.roomZoom;
      if (this.dragInfo && this.dragInfo.type === 'room') {
        this.rooms[this.dragInfo.index].x = Math.max(0, this.dragInfo.origX + cx - this.dragInfo.startX);
        this.rooms[this.dragInfo.index].y = Math.max(0, this.dragInfo.origY + cy - this.dragInfo.startY);
        return;
      }
      if (!this.drawingRoom) return;
      this.drawingRoom.x = Math.min(this.startPos.x, cx); this.drawingRoom.y = Math.min(this.startPos.y, cy);
      this.drawingRoom.w = Math.abs(cx - this.startPos.x); this.drawingRoom.h = Math.abs(cy - this.startPos.y);
    },
    onRoomMouseUp() {
      if (this.dragInfo && this.dragInfo.type === 'room') { this.dragInfo = null; return; }
      if (!this.drawingRoom) return;
      if (this.drawingRoom.w > 20 && this.drawingRoom.h > 20) {
        this.rooms.push({ name: `房间 ${this.rooms.length + 1}`, x: this.drawingRoom.x, y: this.drawingRoom.y, w: this.drawingRoom.w, h: this.drawingRoom.h, walls: {} });
        this.selectedRoomIndex = this.rooms.length - 1;
      }
      this.drawingRoom = null; this.startPos = null;
    },
    deleteRoom(idx) { this.rooms.splice(idx, 1); if (this.selectedRoomIndex === idx) this.selectedRoomIndex = null; else if (this.selectedRoomIndex > idx) this.selectedRoomIndex--; },

    /* ====== 缩放 ====== */
    adjustRoomZoom(d) { this.roomZoom = this.clampZoom((this.roomZoom || 1) + d); },
    adjustWallZoom(d) { this.wallZoom = this.clampZoom((this.wallZoom || 1) + d); },
    clampZoom(z) { const v = Number(z); return Number.isFinite(v) ? Math.min(3, Math.max(0.2, v)) : 1; },
    onRoomWheel(e) { if (!(e.ctrlKey || e.metaKey || e.altKey)) return; e.preventDefault(); this.roomZoom = this.clampZoom(this.roomZoom + (e.deltaY < 0 ? 0.08 : -0.08)); },
    onWallWheel(e) { if (!(e.ctrlKey || e.metaKey || e.altKey)) return; e.preventDefault(); this.wallZoom = this.clampZoom(this.wallZoom + (e.deltaY < 0 ? 0.08 : -0.08)); },

    /* ====== 触屏 ====== */
    touchDistance(t1, t2) { const dx = t1.clientX - t2.clientX, dy = t1.clientY - t2.clientY; return Math.sqrt(dx * dx + dy * dy); },
    onRoomTouchStart(e) {
      if (!e.touches) return;
      if (e.touches.length === 2) { e.preventDefault(); this.roomPinch = { dist: this.touchDistance(e.touches[0], e.touches[1]), zoom: this.roomZoom }; return; }
      if (e.touches.length !== 1 || this.dragInfo) return;
      const t = this.firstTouch(e); if (!t) return;
      const rect = this.$refs.roomCanvas.getBoundingClientRect();
      const cx = (t.clientX - rect.left) / this.roomZoom, cy = (t.clientY - rect.top) / this.roomZoom;
      e.preventDefault(); this.startPos = { x: cx, y: cy }; this.drawingRoom = { x: cx, y: cy, w: 0, h: 0 }; this.selectedRoomIndex = null;
    },
    onRoomTouchMove(e) {
      if (!e.touches) return;
      if (this.roomPinch && e.touches.length === 2) { e.preventDefault(); const d = this.touchDistance(e.touches[0], e.touches[1]); this.roomZoom = this.clampZoom(this.roomPinch.zoom * d / (this.roomPinch.dist || d)); return; }
      if (e.touches.length !== 1) return;
      const t = this.firstTouch(e); if (!t) return;
      const rect = this.$refs.roomCanvas.getBoundingClientRect();
      const cx = (t.clientX - rect.left) / this.roomZoom, cy = (t.clientY - rect.top) / this.roomZoom;
      e.preventDefault();
      if (this.dragInfo && this.dragInfo.type === 'room') {
        this.rooms[this.dragInfo.index].x = Math.max(0, this.dragInfo.origX + cx - this.dragInfo.startX);
        this.rooms[this.dragInfo.index].y = Math.max(0, this.dragInfo.origY + cy - this.dragInfo.startY);
        return;
      }
      if (!this.drawingRoom || !this.startPos) return;
      this.drawingRoom.x = Math.min(this.startPos.x, cx); this.drawingRoom.y = Math.min(this.startPos.y, cy);
      this.drawingRoom.w = Math.abs(cx - this.startPos.x); this.drawingRoom.h = Math.abs(cy - this.startPos.y);
    },
    onRoomTouchEnd(e) {
      if (this.roomPinch) { if (!e || !e.touches || e.touches.length < 2) this.roomPinch = null; return; }
      if (this.dragInfo && this.dragInfo.type === 'room') { this.dragInfo = null; return; }
      if (!this.drawingRoom) return;
      if (this.drawingRoom.w > 20 && this.drawingRoom.h > 20) {
        this.rooms.push({ name: `房间 ${this.rooms.length + 1}`, x: this.drawingRoom.x, y: this.drawingRoom.y, w: this.drawingRoom.w, h: this.drawingRoom.h, walls: {} });
        this.selectedRoomIndex = this.rooms.length - 1;
      }
      this.drawingRoom = null; this.startPos = null;
    },
    onWallTouchStart(e) {
      if (!e.touches) return;
      if (e.touches.length === 2) { e.preventDefault(); this.wallPinch = { dist: this.touchDistance(e.touches[0], e.touches[1]), zoom: this.wallZoom }; }
    },
    onWallTouchMove(e) {
      if (!e.touches) return;
      if (this.wallPinch && e.touches.length === 2) { e.preventDefault(); const d = this.touchDistance(e.touches[0], e.touches[1]); this.wallZoom = this.clampZoom(this.wallPinch.zoom * d / (this.wallPinch.dist || d)); }
    },
    onWallTouchEnd(e) {
      if (this.wallPinch) { if (!e || !e.touches || e.touches.length < 2) this.wallPinch = null; }
    },

    /* ====== Location 树 → rooms 反向构建 ====== */
    buildRoomsFromLocations(tree) {
      const rooms = [];
      // tree is an array of zone nodes
      for (const zone of tree || []) {
        if (!zone || typeof zone !== 'object') continue;
        const name = (zone.name || '').trim() || `房间 ${rooms.length + 1}`;
        const room = { name, x: 50, y: 50 + rooms.length * 30, w: 150, h: 100, walls: {} };
        room._location_id = zone.id;

        for (const wall of zone.children || []) {
          if (!wall || wall.level !== 'wall') continue;
          const wName = (wall.name || '').trim();
          if (!wName) continue;
          const wData = { image: wall.map_image_url || '', dots: [] };
          wData._location_id = wall.id;

          for (const unit of wall.children || []) {
            if (!unit || unit.level !== 'unit') continue;
            const uName = (unit.name || '').trim() || '储物单元';
            let x = 500, y = 500;
            if (unit.coordinates) {
              try {
                const c = typeof unit.coordinates === 'string' ? JSON.parse(unit.coordinates) : unit.coordinates;
                if (c && Number.isFinite(c.x)) x = Math.max(0, Math.min(1000, Math.round(c.x)));
                if (c && Number.isFinite(c.y)) y = Math.max(0, Math.min(1000, Math.round(c.y)));
              } catch (e) { /* ignore */ }
            }
            const dot = { name: uName, x, y };
            dot._location_id = unit.id;
            wData.dots.push(dot);
          }
          room.walls[wName] = wData;
        }
        rooms.push(room);
      }
      return rooms;
    },

    /* ====== 数据加载 ====== */
    normalizeNumber(v, fallback) { const n = Number(v); return Number.isFinite(n) ? n : fallback; },
    normalizeRooms(list) {
      const out = [];
      for (const r of list || []) {
        if (!r || typeof r !== 'object') continue;
        const name = (r.name == null ? '' : String(r.name)).trim() || `房间 ${out.length + 1}`;
        const x = Math.max(0, this.normalizeNumber(r.x, 0));
        const y = Math.max(0, this.normalizeNumber(r.y, 0));
        const w = Math.max(10, this.normalizeNumber(r.w, 100));
        const h = Math.max(10, this.normalizeNumber(r.h, 80));
        const wallsIn = r.walls && typeof r.walls === 'object' && !Array.isArray(r.walls) ? r.walls : {};
        const wallsOut = {};
        for (const [k, wv] of Object.entries(wallsIn)) {
          if (!wv || typeof wv !== 'object') continue;
          const image = (wv.image == null ? '' : String(wv.image)).trim();
          const imgW = this.normalizeNumber(wv._img_w, null);
          const imgH = this.normalizeNumber(wv._img_h, null);
          const itemsIn = Array.isArray(wv.dots) ? wv.dots : (Array.isArray(wv.spots) ? wv.spots : []);
          const dotsOut = [];
          for (const s of itemsIn) {
            if (!s || typeof s !== 'object') continue;
            const sName = (s.name == null ? '' : String(s.name)).trim() || `储物单元 ${dotsOut.length + 1}`;
            if (s.w != null && s.h != null) {
              const cx = Math.round((s.x + s.w / 2) / (imgW || 2000) * 1000);
              const cy = Math.round((s.y + s.h / 2) / (imgH || 2000) * 1000);
              dotsOut.push({ name: sName, x: Math.max(0, Math.min(1000, cx)), y: Math.max(0, Math.min(1000, cy)) });
            } else {
              const dx = Math.max(0, Math.min(1000, this.normalizeNumber(s.x, 500)));
              const dy = Math.max(0, Math.min(1000, this.normalizeNumber(s.y, 500)));
              dotsOut.push({ name: sName, x: dx, y: dy });
            }
          }
          const wallOut = { image, dots: dotsOut };
          if (imgW != null && imgH != null && Number.isFinite(imgW) && Number.isFinite(imgH) && imgW > 0 && imgH > 0) { wallOut._img_w = imgW; wallOut._img_h = imgH; }
          wallsOut[k] = wallOut;
        }
        out.push({ name, x, y, w, h, walls: wallsOut });
      }
      return out.length > 0 ? out : [{ name: '客厅', x: 50, y: 50, w: 150, h: 100, walls: {} }];
    },

    async loadFromServer() {
      this.hint = '';
      this.loading = true;
      try {
        // Priority 1: load from Location table
        const locRes = await api.get('/api/locations');
        const tree = locRes.data;
        if (Array.isArray(tree) && tree.length > 0) {
          this.rooms = this.buildRoomsFromLocations(tree);
          this.selectedRoomIndex = null;
          this.selectedDotIndex = null;
          this.hint = '已从位置表加载';
          this.loading = false;
          return;
        }
      } catch (e) {
        // Fall through to config
      }

      // Priority 2: fall back to config area_map
      try {
        const res = await api.get('/api/config');
        const area = res.data && res.data.area_map;
        if (Array.isArray(area) && area.length > 0) {
          this.rooms = this.normalizeRooms(area);
          this.selectedRoomIndex = null;
          this.selectedDotIndex = null;
          this.hint = '已从配置加载';
        } else {
          this.rooms = [{ name: '客厅', x: 50, y: 50, w: 150, h: 100, walls: {} }];
          this.hint = '已创建默认房间';
        }
      } catch (e) {
        this.hint = this.requestErrorText(e, '加载');
        if (this.rooms.length === 0) {
          this.rooms = [{ name: '客厅', x: 50, y: 50, w: 150, h: 100, walls: {} }];
        }
      } finally {
        this.loading = false;
      }
    },

    /* ====== 保存 ====== */
    async saveToServer() {
      this.hint = '';
      this.loading = true;
      try {
        const current = await api.get('/api/config');
        const d = current.data || {};
        const roomNames = Array.isArray(this.rooms)
          ? Array.from(new Set(this.rooms.map(r => (r && r.name != null ? String(r.name).trim() : '')).filter(Boolean)))
          : [];
        const payload = {
          categories: Array.isArray(d.categories) ? d.categories : [],
          locations: Array.isArray(d.locations) ? d.locations : [],
          units: Array.isArray(d.units) ? d.units : [],
          type_tree: d.type_tree && typeof d.type_tree === 'object' ? d.type_tree : {},
          rooms: roomNames,
          spots: Array.isArray(d.spots) ? d.spots : [],
          responsible_people: Array.isArray(d.responsible_people) ? d.responsible_people : [],
          area_map: this.rooms,
        };
        await api.put('/api/config', payload);

        try {
          await api.post('/api/locations/sync-from-area-map', { area_map: this.rooms });
          this.hint = '已保存并同步到位置表';
        } catch (e) {
          this.hint = '配置已保存，位置同步失败：' + this.requestErrorText(e, '同步');
        }
      } catch (e) {
        this.hint = this.requestErrorText(e, '保存');
      } finally {
        this.loading = false;
      }
    },

    /* ====== JSON 导入导出 ====== */
    exportAreaJson() {
      const text = JSON.stringify(this.rooms || [], null, 2);
      const blob = new Blob([text], { type: 'application/json;charset=utf-8' });
      const name = `area_map_${new Date().toISOString().slice(0, 10)}.json`;
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a'); a.href = url; a.download = name;
      document.body.appendChild(a); a.click(); a.remove();
      setTimeout(() => URL.revokeObjectURL(url), 1500);
    },
    triggerJsonPick() { const el = this.$refs.jsonInput; if (el) { el.value = ''; el.click(); } },
    async onJsonPicked(e) {
      const file = e && e.target && e.target.files ? e.target.files[0] : null;
      if (!file) return;
      try {
        const text = await file.text();
        this.applyAreaMapFromText(text);
        this.hint = '已从文件导入';
      } catch (err) { this.hint = '导入失败：无法读取文件'; }
      finally { e.target.value = ''; }
    },
    applyAreaMapFromText(text) {
      const raw = (text || '').trim();
      if (!raw) throw new Error('内容为空');
      let parsed;
      try { parsed = JSON.parse(raw); } catch (e) { throw new Error('JSON 解析失败'); }
      const area = Array.isArray(parsed) ? parsed
        : (parsed && typeof parsed === 'object' && Array.isArray(parsed.area_map)) ? parsed.area_map
        : (parsed && typeof parsed === 'object' && Array.isArray(parsed.rooms)) ? parsed.rooms : null;
      if (!Array.isArray(area)) throw new Error('格式不支持');
      const normalized = this.normalizeRooms(area);
      if (normalized.length === 0) throw new Error('没有有效数据');
      this.rooms = normalized;
      this.selectedRoomIndex = null; this.selectedDotIndex = null;
    },

    /* ====== 图片上传 ====== */
    async onWallImageUpload(e) {
      const f = e && e.target && e.target.files ? e.target.files[0] : null;
      if (!f) return;
      try {
        const fd = new FormData(); fd.append('file', f);
        const res = await api.post('/api/items/upload_image', fd);
        const url = res.data && res.data.image_url ? String(res.data.image_url) : '';
        if (!url) { this.hint = '图片上传失败'; return; }
        this.currentWall.image = url;
        this.hint = '墙面图片已上传';
      } catch (err) { this.hint = this.requestErrorText(err, '图片上传'); }
      finally { e.target.value = ''; }
    },

    requestErrorText(e, action) {
      const status = e && e.response ? e.response.status : null;
      const detail = e && e.response && e.response.data && e.response.data.detail ? String(e.response.data.detail) : '';
      if (status === 401) return `${action}失败：未登录`;
      if (status === 403) return `${action}失败：权限不足`;
      if (status) return `${action}失败：HTTP ${status}${detail ? ` (${detail})` : ''}`;
      const msg = e && e.message ? String(e.message) : '';
      if (msg && /timeout/i.test(msg)) return `${action}失败：超时`;
      return `${action}失败：无法连接服务器`;
    },
  }
};
</script>

<style scoped>
.area-map-page {
  padding: 16px;
  width: 100%; max-width: 100%; margin: 0;
  min-height: 100vh; min-height: 100dvh;
  padding-bottom: calc(60px + env(safe-area-inset-bottom, 0px));
  box-sizing: border-box;
}

/* Header */
.header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px; flex-wrap: wrap; gap: 8px; }
.header h2 { margin: 0; font-size: 18px; white-space: nowrap; }
.header-actions { display: flex; gap: 6px; align-items: center; flex-wrap: wrap; }
.btn-ghost { padding: 6px 12px; border: 1px solid #d1d5db; background: white; border-radius: 6px; cursor: pointer; font-size: 13px; }
.btn-primary { padding: 6px 12px; border: none; background: #3b82f6; color: white; border-radius: 6px; cursor: pointer; font-size: 13px; font-weight: 600; }
.btn-primary:disabled, .btn-ghost:disabled { opacity: 0.5; cursor: not-allowed; }
.btn-danger { padding: 6px 12px; background: #ef4444; color: white; border: none; border-radius: 6px; cursor: pointer; font-size: 13px; }
.link { padding: 6px 12px; background: #111827; color: white; text-decoration: none; border-radius: 6px; font-size: 13px; }
.json-input { display: none; }

/* Room Selector */
.room-selector { display: flex; gap: 8px; margin-bottom: 12px; overflow-x: auto; padding-bottom: 4px; -webkit-overflow-scrolling: touch; flex-shrink: 0; }
.room-selector::-webkit-scrollbar { height: 3px; }
.room-selector::-webkit-scrollbar-thumb { background: #cbd5e1; border-radius: 3px; }
.room-chip { padding: 6px 14px; border: 1px solid #d1d5db; background: white; border-radius: 20px; cursor: pointer; font-size: 13px; white-space: nowrap; flex-shrink: 0; user-select: none; }
.room-chip.active { background: #3b82f6; color: white; border-color: #3b82f6; }
.add-chip { border-style: dashed; color: #3b82f6; border-color: #3b82f6; }

/* Main Grid */
.main-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 16px; flex: 1; min-height: 0; }

/* Panels */
.panel { background: rgba(255,255,255,0.85); border: 1px solid rgba(0,0,0,0.1); border-radius: 12px; padding: 14px; display: flex; flex-direction: column; min-width: 0; min-height: 0; }
.panel-title { font-weight: 800; font-size: 16px; margin-bottom: 8px; display: flex; align-items: center; flex-shrink: 0; }
.muted { color: rgba(0,0,0,0.55); font-size: 13px; flex-shrink: 0; margin-bottom: 8px; }
.strong { font-weight: 700; }
.mt-2 { margin-top: 10px; }

/* Zoom */
.zoom-controls { display: inline-flex; align-items: center; gap: 8px; margin-left: auto; font-weight: normal; font-size: 13px; }
.zoom-controls button { width: 22px; height: 22px; border-radius: 4px; border: 1px solid #ccc; background: white; cursor: pointer; display: flex; align-items: center; justify-content: center; }

/* Canvas */
.canvas-scroll-area { width: 100%; flex: none; height: min(50vh, 480px); min-height: 240px; max-width: 100%; background: #f0f0f0; border: 1px solid #ccc; overflow: auto; position: relative; margin-top: 8px; touch-action: pan-x pan-y; }
.canvas-container { width: 2000px; height: 2000px; background: #f0f0f0; position: relative; cursor: crosshair; }

/* Room Boxes */
.room-box { position: absolute; background: rgba(59,130,246,0.3); border: 2px solid #3b82f6; display: flex; align-items: center; justify-content: center; cursor: pointer; user-select: none; }
.room-box.active { background: rgba(16,185,129,0.4); border-color: #10b981; }
.room-box.drawing { border-style: dashed; background: rgba(59,130,246,0.1); }
.room-name { font-weight: bold; color: #fff; text-shadow: 0 1px 2px rgba(0,0,0,0.8); pointer-events: none; }

/* Edit Box */
.edit-box { margin-top: 12px; padding: 10px; background: rgba(0,0,0,0.04); border-radius: 8px; display: flex; flex-direction: column; gap: 8px; flex-shrink: 0; }
.edit-box label { display: flex; flex-direction: column; gap: 4px; font-size: 13px; }
.edit-box label input { padding: 6px 8px; border-radius: 6px; border: 1px solid #ccc; }
.edit-actions { display: flex; gap: 8px; }

/* Wall Tabs */
.wall-tabs { display: flex; gap: 6px; margin-bottom: 10px; flex-wrap: wrap; flex-shrink: 0; }
.tab-btn { padding: 5px 10px; background: #e5e7eb; border: none; border-radius: 6px; cursor: pointer; font-size: 13px; }
.tab-btn.active { background: #3b82f6; color: white; }

/* Wall Content */
.wall-content { background: #f9fafb; padding: 10px; border-radius: 8px; border: 1px solid #e5e7eb; flex: 1; display: flex; flex-direction: column; min-height: 0; }
.wall-image-row { display: flex; flex-direction: column; gap: 4px; margin-bottom: 8px; flex-shrink: 0; }
.row { display: flex; gap: 8px; align-items: center; }
.row input { flex: 1; padding: 5px 8px; border-radius: 6px; border: 1px solid #ccc; font-size: 13px; }
.img-pick { width: auto; flex: 0; }

/* Toolbar */
.toolbar { display: flex; gap: 6px; align-items: center; margin-bottom: 8px; flex-wrap: wrap; flex-shrink: 0; }
.toolbar button { padding: 5px 12px; border: 1px solid #d1d5db; background: white; border-radius: 6px; cursor: pointer; font-size: 13px; }
.toolbar button.active { background: #3b82f6; color: white; border-color: #3b82f6; }
.mode-hint { font-size: 12px; color: #9ca3af; margin-left: 4px; }

/* Wall Canvas */
.wall-canvas { background-color: transparent; background-size: 100% 100%; background-position: top left; background-repeat: no-repeat; position: relative; cursor: crosshair; }
.empty-bg { position: absolute; top: 50%; left: 50%; transform: translate(-50%,-50%); color: #9ca3af; font-weight: bold; pointer-events: none; font-size: 14px; }

/* Marker Dots */
.marker-dot { position: absolute; width: 28px; height: 28px; border-radius: 50%; background: rgba(239,68,68,0.85); border: 2px solid #dc2626; display: flex; align-items: center; justify-content: center; transform: translate(-50%, -50%); cursor: pointer; user-select: none; z-index: 2; transition: transform 0.15s, box-shadow 0.15s; }
.marker-dot:hover { transform: translate(-50%, -50%) scale(1.15); }
.marker-dot.active { background: rgba(16,185,129,0.9); border-color: #059669; box-shadow: 0 0 0 3px rgba(16,185,129,0.3); z-index: 3; }
.marker-dot.movable { cursor: grab; }
.marker-dot.movable:active { cursor: grabbing; }
.dot-num { font-size: 12px; font-weight: 800; color: #fff; text-shadow: 0 1px 1px rgba(0,0,0,0.4); pointer-events: none; }

/* Naming Dialog */
.naming-overlay { position: fixed; top: 0; left: 0; right: 0; bottom: 0; background: rgba(0,0,0,0.35); display: flex; align-items: center; justify-content: center; z-index: 100; }
.naming-dialog { background: white; border-radius: 12px; padding: 20px; width: min(320px, 90vw); box-shadow: 0 8px 30px rgba(0,0,0,0.18); display: flex; flex-direction: column; gap: 12px; }
.naming-title { font-weight: 700; font-size: 15px; }
.naming-dialog input { padding: 8px 10px; border: 1px solid #d1d5db; border-radius: 8px; font-size: 14px; width: 100%; box-sizing: border-box; }
.naming-actions { display: flex; gap: 8px; justify-content: flex-end; }
.naming-actions button { padding: 6px 16px; border-radius: 8px; cursor: pointer; font-size: 13px; }

/* Empty wall */
.empty-wall { justify-content: center; align-items: center; min-height: 200px; }

/* Hint */
.hint { margin-top: 12px; padding: 8px 12px; background: rgba(17,24,39,0.05); border: 1px solid rgba(0,0,0,0.08); border-radius: 8px; font-size: 13px; flex-shrink: 0; }

/* Mobile */
@media (max-width: 768px) {
  .area-map-page { padding: 10px; }
  .header { flex-direction: column; align-items: flex-start; }
  .header h2 { font-size: 16px; }
  .header-actions { width: 100%; }
  .header-actions .btn-ghost, .header-actions .btn-primary { flex: 1; text-align: center; font-size: 12px; padding: 7px 6px; }
  .link { font-size: 12px; }
  .main-grid { grid-template-columns: 1fr; }
  .room-panel.collapsed .canvas-scroll-area { height: min(30vh, 200px); min-height: 120px; }
  .canvas-scroll-area { height: min(45vh, 360px); }
  .toolbar { justify-content: center; }
  .toolbar button { flex: 1; text-align: center; }
  .mode-hint { width: 100%; text-align: center; margin-top: 2px; margin-left: 0; }
}
</style>
