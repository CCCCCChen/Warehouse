<template>
  <div class="map-test-page">
    <div class="header">
      <h2>区域与墙面设置 (测试)</h2>
      <div class="header-actions">
        <button class="btn-ghost" type="button" :disabled="loading" @click="loadFromServer">从服务器加载</button>
        <button class="btn-ghost" type="button" :disabled="loading" @click="saveToServer">保存到服务器</button>
        <button class="btn-ghost" type="button" :disabled="loading" @click="exportAreaJson">导出JSON</button>
        <button class="btn-ghost" type="button" :disabled="loading" @click="triggerJsonPick">导入JSON</button>
        <router-link class="link" to="/warehouse">返回主页</router-link>
        <input ref="jsonInput" class="json-input" type="file" accept=".json,application/json" @change="onJsonPicked" />
      </div>
    </div>

    <div class="grid">
      <!-- 第二层级：区域设置 -->
      <div class="panel">
        <div class="panel-title">
          第二层级：房间/区域地图设置
          <div class="zoom-controls">
             <button @click="adjustRoomZoom(-0.1)">-</button>
            <span>{{ Math.round(roomZoom * 100) }}%</span>
             <button @click="adjustRoomZoom(0.1)">+</button>
          </div>
        </div>
        <div class="muted">在下方灰色区域拖拽鼠标画出房间长方形，并命名。选中后拖动可移动位置。</div>
        
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
          <div class="strong">编辑选中区域</div>
          <label>名称 <input v-model.trim="rooms[selectedRoomIndex].name" /></label>
          <button class="btn-danger" @click="deleteRoom(selectedRoomIndex)">删除此区域</button>
        </div>
      </div>

      <!-- 第三层级：墙面设置 -->
      <div class="panel">
        <div class="panel-title">
          第三层级：墙面设置
          <div class="zoom-controls" v-if="selectedRoomIndex !== null">
           <button @click="adjustWallZoom(-0.1)">-</button>
            <span>{{ Math.round(wallZoom * 100) }}%</span>
           <button @click="adjustWallZoom(0.1)">+</button>
          </div>
        </div>
        <div v-if="selectedRoomIndex === null" class="muted">请先在左侧选择一个区域。</div>
        <div v-else>
          <div class="strong mb-2">当前区域：{{ rooms[selectedRoomIndex].name }}</div>
          
          <div class="wall-tabs">
            <button 
              v-for="wall in wallTypes" 
              :key="wall.value"
              class="tab-btn"
              :class="{ active: selectedWallType === wall.value }"
              @click="selectedWallType = wall.value"
            >
              {{ wall.label }}
            </button>
          </div>

          <div class="wall-content" v-if="currentWall">
            <label class="full mb-2">
              墙面背景图 (可上传或填URL)
              <div class="row">
                <input v-model.trim="currentWall.image" placeholder="图片 URL..." />
                <input type="file" accept="image/*" @change="onWallImageUpload" style="width: auto;" />
              </div>
            </label>

            <div class="muted mb-2">在下方图片区域拖拽鼠标画出收纳框，并命名。选中后拖动可移动位置。</div>
            
            <div
              class="canvas-scroll-area"
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
                @mousedown="onSpotMouseDown"
                @mousemove="onSpotMouseMove"
                @mouseup="onSpotMouseUp"
                @mouseleave="onSpotMouseUp"
              >
                <div v-if="!currentWall.image" class="empty-bg">未设置背景图</div>
                
                <div 
                  v-for="(spot, idx) in currentWall.spots" 
                  :key="idx"
                  class="spot-box"
                  :class="{ active: selectedSpotIndex === idx }"
                  :style="boxStyle(spot)"
                  @mousedown.stop="onSpotDragStart($event, idx)"
                  @touchstart.stop.prevent="onSpotDragStartTouch($event, idx)"
                >
                  <div class="spot-name">{{ spot.name }}</div>
                </div>
                <div 
                  v-if="drawingSpot"
                  class="spot-box drawing"
                  :style="boxStyle(drawingSpot)"
                ></div>
              </div>
            </div>

            <div v-if="selectedSpotIndex !== null" class="edit-box mt-2">
              <div class="strong">编辑收纳框</div>
              <label>名称 <input v-model.trim="currentWall.spots[selectedSpotIndex].name" /></label>
              <button class="btn-danger" @click="deleteSpot(selectedSpotIndex)">删除此框</button>
            </div>
          </div>
        </div>
      </div>
    </div>

    <div class="panel mt-4">
      <div class="panel-title">JSON 导入/展示</div>
      <div class="muted mb-2">支持两种格式：1) 直接 rooms 数组；2) /api/config 返回对象（取 area_map 字段）。</div>
      <div class="json-actions mb-2">
        <button class="btn-ghost" type="button" :disabled="loading" @click="exportAreaJson">下载当前JSON</button>
        <button class="btn-ghost" type="button" :disabled="loading" @click="applyPastedJson">粘贴JSON并应用</button>
      </div>
      <textarea v-model.trim="pastedJson" class="json-text" placeholder="在此粘贴 JSON..."></textarea>
      <div v-if="jsonError" class="hint danger">{{ jsonError }}</div>
      <div v-else class="hint">概览：{{ overviewText }}</div>
    </div>

    <div class="panel mt-4">
      <div class="panel-title">生成的配置 JSON</div>
      <pre class="pre">{{ generatedJson }}</pre>
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
      rooms: [
        { name: '客厅', x: 50, y: 50, w: 150, h: 100, walls: {} }
      ],
      loading: false,
      hint: '',
      pastedJson: '',
      jsonError: '',
      wallImageLoadId: 0,
      selectedRoomIndex: null,
      drawingRoom: null,
      startPos: null,

      wallTypes: [
        { label: '北墙', value: 'north' },
        { label: '南墙', value: 'south' },
        { label: '东墙', value: 'east' },
        { label: '西墙', value: 'west' },
        { label: '底面', value: 'floor' },
      ],
      selectedWallType: 'north',
      
      drawingSpot: null,
      selectedSpotIndex: null,
      spotStartPos: null,

      roomZoom: 1.0,
      wallZoom: 1.0,
      
      dragInfo: null,
      roomPinch: null,
      wallPinch: null,
    };
  },
  created() {
    this.loadFromServer();
  },
  computed: {
    currentRoom() {
      if (this.selectedRoomIndex === null) return null;
      return this.rooms[this.selectedRoomIndex];
    },
    currentWall() {
      const room = this.currentRoom;
      if (!room) return null;
      if (!room.walls[this.selectedWallType]) {
        room.walls[this.selectedWallType] = { image: '', spots: [] };
      }
      return room.walls[this.selectedWallType];
    },
    generatedJson() {
      return JSON.stringify(this.rooms, null, 2);
    },
    overviewText() {
      const rooms = Array.isArray(this.rooms) ? this.rooms : [];
      const roomCount = rooms.length;
      let wallCount = 0;
      let spotCount = 0;
      for (const r of rooms) {
        const walls = r && r.walls && typeof r.walls === 'object' ? r.walls : {};
        wallCount += Object.keys(walls).length;
        for (const w of Object.values(walls)) {
          const spots = w && Array.isArray(w.spots) ? w.spots : [];
          spotCount += spots.length;
        }
      }
      return `区域 ${roomCount} 个，墙面 ${wallCount} 个，收纳框 ${spotCount} 个`;
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
    'currentWall.image': {
      immediate: true,
      handler(newVal) {
        this.updateCurrentWallImageSize(newVal);
      }
    },
    selectedRoomIndex() {
      this.$nextTick(() => {
        const w = this.currentWall;
        this.updateCurrentWallImageSize(w ? w.image : '');
      });
    },
    selectedWallType() {
      this.$nextTick(() => {
        const w = this.currentWall;
        this.updateCurrentWallImageSize(w ? w.image : '');
      });
    },
  },
  methods: {
    requestErrorText(e, action) {
      const status = e && e.response ? e.response.status : null;
      const detail = e && e.response && e.response.data && e.response.data.detail ? String(e.response.data.detail) : '';
      if (status === 401) return `${action}失败：未登录或 token 无效`;
      if (status === 403) return `${action}失败：需要 owner 权限`;
      if (status) return `${action}失败：HTTP ${status}${detail ? ` (${detail})` : ''}`;
      const msg = e && e.message ? String(e.message) : '';
      if (msg && /timeout/i.test(msg)) return `${action}失败：请求超时`;
      return `${action}失败：无法连接到服务器（请检查 API 地址/HTTPS/反向代理/后端是否在运行）`;
    },
    downloadBlob(blob, filename) {
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = filename;
      document.body.appendChild(a);
      a.click();
      a.remove();
      setTimeout(() => URL.revokeObjectURL(url), 1500);
    },
    exportAreaJson() {
      const text = JSON.stringify(this.rooms || [], null, 2);
      const blob = new Blob([text], { type: 'application/json;charset=utf-8' });
      const name = `area_map_${new Date().toISOString().slice(0, 10)}.json`;
      this.downloadBlob(blob, name);
    },
    triggerJsonPick() {
      this.jsonError = '';
      const el = this.$refs.jsonInput;
      if (el) {
        el.value = '';
        el.click();
      }
    },
    async onJsonPicked(e) {
      const file = e && e.target && e.target.files ? e.target.files[0] : null;
      if (!file) return;
      this.jsonError = '';
      try {
        const text = await file.text();
        this.pastedJson = text;
        this.applyAreaMapFromText(text);
        this.hint = '已从文件导入';
      } catch (err) {
        this.jsonError = '导入失败：无法读取文件';
      } finally {
        e.target.value = '';
      }
    },
    applyPastedJson() {
      this.jsonError = '';
      try {
        this.applyAreaMapFromText(this.pastedJson || '');
        this.hint = '已应用粘贴内容';
      } catch (err) {
        this.jsonError = err && err.message ? String(err.message) : '导入失败：JSON 不合法';
      }
    },
    applyAreaMapFromText(text) {
      const raw = (text || '').trim();
      if (!raw) throw new Error('导入失败：内容为空');
      let parsed;
      try {
        parsed = JSON.parse(raw);
      } catch (e) {
        throw new Error('导入失败：JSON 解析失败');
      }
      const area = Array.isArray(parsed)
        ? parsed
        : (parsed && typeof parsed === 'object' && Array.isArray(parsed.area_map))
          ? parsed.area_map
          : (parsed && typeof parsed === 'object' && Array.isArray(parsed.rooms))
            ? parsed.rooms
            : null;
      if (!Array.isArray(area)) throw new Error('导入失败：格式不支持（需要 rooms 数组或包含 area_map 的对象）');
      const normalized = this.normalizeRooms(area);
      if (normalized.length === 0) throw new Error('导入失败：没有有效的区域数据');
      this.rooms = normalized;
      this.selectedRoomIndex = null;
      this.selectedSpotIndex = null;
      this.jsonError = '';
    },
    normalizeNumber(v, fallback) {
      const n = Number(v);
      if (!Number.isFinite(n)) return fallback;
      return n;
    },
    normalizeRooms(list) {
      const out = [];
      for (const r of list || []) {
        if (!r || typeof r !== 'object') continue;
        const name = (r.name == null ? '' : String(r.name)).trim() || `区域 ${out.length + 1}`;
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
          const spotsIn = Array.isArray(wv.spots) ? wv.spots : [];
          const spotsOut = [];
          for (const s of spotsIn) {
            if (!s || typeof s !== 'object') continue;
            const sName = (s.name == null ? '' : String(s.name)).trim() || `收纳框 ${spotsOut.length + 1}`;
            const sx = Math.max(0, this.normalizeNumber(s.x, 0));
            const sy = Math.max(0, this.normalizeNumber(s.y, 0));
            const sw = Math.max(10, this.normalizeNumber(s.w, 60));
            const sh = Math.max(10, this.normalizeNumber(s.h, 40));
            spotsOut.push({ name: sName, x: sx, y: sy, w: sw, h: sh });
          }
          const wallOut = { image, spots: spotsOut };
          if (imgW != null && imgH != null && Number.isFinite(imgW) && Number.isFinite(imgH) && imgW > 0 && imgH > 0) {
            wallOut._img_w = imgW;
            wallOut._img_h = imgH;
          }
          wallsOut[k] = wallOut;
        }
        out.push({ name, x, y, w, h, walls: wallsOut });
      }
      return out;
    },
    updateCurrentWallImageSize(url) {
      const wall = this.currentWall;
      if (!wall) return;
      const raw = (url || '').trim();
      if (!raw) {
        delete wall._img_w;
        delete wall._img_h;
        return;
      }
      const id = ++this.wallImageLoadId;
      const img = new Image();
      img.onload = () => {
        if (id !== this.wallImageLoadId) return;
        if (!this.currentWall) return;
        if ((this.currentWall.image || '').trim() !== raw) return;
        const w = img.naturalWidth || img.width;
        const h = img.naturalHeight || img.height;
        if (!Number.isFinite(w) || !Number.isFinite(h) || w <= 0 || h <= 0) return;
        this.currentWall._img_w = w;
        this.currentWall._img_h = h;
      };
      img.onerror = () => {
        if (id !== this.wallImageLoadId) return;
        if (!this.currentWall) return;
        if ((this.currentWall.image || '').trim() !== raw) return;
        delete this.currentWall._img_w;
        delete this.currentWall._img_h;
      };
      img.src = raw;
    },
    firstTouch(e) {
      if (e && e.touches && e.touches[0]) return e.touches[0];
      if (e && e.changedTouches && e.changedTouches[0]) return e.changedTouches[0];
      return null;
    },
    roomPointFromClient(clientX, clientY) {
      const el = this.$refs.roomCanvas;
      if (!el || typeof el.getBoundingClientRect !== 'function') return null;
      const rect = el.getBoundingClientRect();
      return {
        x: (clientX - rect.left) / this.roomZoom,
        y: (clientY - rect.top) / this.roomZoom,
      };
    },
    wallPointFromClient(clientX, clientY) {
      const el = this.$refs.wallCanvas;
      if (!el || typeof el.getBoundingClientRect !== 'function') return null;
      const rect = el.getBoundingClientRect();
      return {
        x: (clientX - rect.left) / this.wallZoom,
        y: (clientY - rect.top) / this.wallZoom,
      };
    },
    adjustRoomZoom(delta) {
      const next = Number(this.roomZoom) + Number(delta);
      this.roomZoom = Math.min(3, Math.max(0.2, Number.isFinite(next) ? next : 1));
    },
    adjustWallZoom(delta) {
      const next = Number(this.wallZoom) + Number(delta);
      this.wallZoom = Math.min(3, Math.max(0.2, Number.isFinite(next) ? next : 1));
    },
    clampZoom(z) {
      const v = Number(z);
      if (!Number.isFinite(v)) return 1;
      return Math.min(3, Math.max(0.2, v));
    },
    onRoomWheel(e) {
      if (!(e.ctrlKey || e.metaKey || e.altKey)) return;
      e.preventDefault();
      const step = e.deltaY < 0 ? 0.08 : -0.08;
      this.roomZoom = this.clampZoom(this.roomZoom + step);
    },
    onWallWheel(e) {
      if (!(e.ctrlKey || e.metaKey || e.altKey)) return;
      e.preventDefault();
      const step = e.deltaY < 0 ? 0.08 : -0.08;
      this.wallZoom = this.clampZoom(this.wallZoom + step);
    },
    touchDistance(t1, t2) {
      const dx = t1.clientX - t2.clientX;
      const dy = t1.clientY - t2.clientY;
      return Math.sqrt(dx * dx + dy * dy);
    },
    onRoomTouchStart(e) {
      if (!e.touches) return;
      if (e.touches.length === 2) {
        e.preventDefault();
        this.roomPinch = {
          dist: this.touchDistance(e.touches[0], e.touches[1]),
          zoom: this.roomZoom,
        };
        return;
      }
      if (e.touches.length !== 1) return;
      if (this.dragInfo) return;
      const t = this.firstTouch(e);
      if (!t) return;
      const p = this.roomPointFromClient(t.clientX, t.clientY);
      if (!p) return;
      e.preventDefault();
      this.startPos = { x: p.x, y: p.y };
      this.drawingRoom = { x: p.x, y: p.y, w: 0, h: 0 };
      this.selectedRoomIndex = null;
    },
    onRoomTouchMove(e) {
      if (!e.touches) return;
      if (this.roomPinch && e.touches.length === 2) {
        e.preventDefault();
        const dist = this.touchDistance(e.touches[0], e.touches[1]);
        const ratio = dist / (this.roomPinch.dist || dist);
        this.roomZoom = this.clampZoom(this.roomPinch.zoom * ratio);
        return;
      }
      if (e.touches.length !== 1) return;
      if (!this.drawingRoom && !(this.dragInfo && this.dragInfo.type === 'room')) return;
      const t = this.firstTouch(e);
      if (!t) return;
      const p = this.roomPointFromClient(t.clientX, t.clientY);
      if (!p) return;
      e.preventDefault();
      if (this.dragInfo && this.dragInfo.type === 'room') {
        const dx = p.x - this.dragInfo.startX;
        const dy = p.y - this.dragInfo.startY;
        this.rooms[this.dragInfo.index].x = Math.max(0, this.dragInfo.origX + dx);
        this.rooms[this.dragInfo.index].y = Math.max(0, this.dragInfo.origY + dy);
        return;
      }
      if (!this.drawingRoom || !this.startPos) return;
      this.drawingRoom.x = Math.min(this.startPos.x, p.x);
      this.drawingRoom.y = Math.min(this.startPos.y, p.y);
      this.drawingRoom.w = Math.abs(p.x - this.startPos.x);
      this.drawingRoom.h = Math.abs(p.y - this.startPos.y);
    },
    onRoomTouchEnd(e) {
      if (this.roomPinch) {
        if (!e || !e.touches || e.touches.length < 2) {
          this.roomPinch = null;
        }
        return;
      }
      if (this.dragInfo && this.dragInfo.type === 'room') {
        this.dragInfo = null;
        return;
      }
      if (!this.drawingRoom) return;
      if (this.drawingRoom.w > 20 && this.drawingRoom.h > 20) {
        this.rooms.push({
          name: `区域 ${this.rooms.length + 1}`,
          x: this.drawingRoom.x,
          y: this.drawingRoom.y,
          w: this.drawingRoom.w,
          h: this.drawingRoom.h,
          walls: {}
        });
        this.selectedRoomIndex = this.rooms.length - 1;
      }
      this.drawingRoom = null;
      this.startPos = null;
    },
    onWallTouchStart(e) {
      if (!e.touches) return;
      if (e.touches.length === 2) {
        e.preventDefault();
        this.wallPinch = {
          dist: this.touchDistance(e.touches[0], e.touches[1]),
          zoom: this.wallZoom,
        };
        return;
      }
      if (e.touches.length !== 1) return;
      if (!this.currentWall || this.dragInfo) return;
      const t = this.firstTouch(e);
      if (!t) return;
      const p = this.wallPointFromClient(t.clientX, t.clientY);
      if (!p) return;
      e.preventDefault();
      this.spotStartPos = { x: p.x, y: p.y };
      this.drawingSpot = { x: p.x, y: p.y, w: 0, h: 0 };
      this.selectedSpotIndex = null;
    },
    onWallTouchMove(e) {
      if (!e.touches) return;
      if (this.wallPinch && e.touches.length === 2) {
        e.preventDefault();
        const dist = this.touchDistance(e.touches[0], e.touches[1]);
        const ratio = dist / (this.wallPinch.dist || dist);
        this.wallZoom = this.clampZoom(this.wallPinch.zoom * ratio);
        return;
      }
      if (e.touches.length !== 1) return;
      if (!this.drawingSpot && !(this.dragInfo && this.dragInfo.type === 'spot')) return;
      const t = this.firstTouch(e);
      if (!t) return;
      const p = this.wallPointFromClient(t.clientX, t.clientY);
      if (!p) return;
      e.preventDefault();
      if (this.dragInfo && this.dragInfo.type === 'spot') {
        const dx = p.x - this.dragInfo.startX;
        const dy = p.y - this.dragInfo.startY;
        this.currentWall.spots[this.dragInfo.index].x = Math.max(0, this.dragInfo.origX + dx);
        this.currentWall.spots[this.dragInfo.index].y = Math.max(0, this.dragInfo.origY + dy);
        return;
      }
      if (!this.drawingSpot || !this.spotStartPos) return;
      this.drawingSpot.x = Math.min(this.spotStartPos.x, p.x);
      this.drawingSpot.y = Math.min(this.spotStartPos.y, p.y);
      this.drawingSpot.w = Math.abs(p.x - this.spotStartPos.x);
      this.drawingSpot.h = Math.abs(p.y - this.spotStartPos.y);
    },
    onWallTouchEnd(e) {
      if (this.wallPinch) {
        if (!e || !e.touches || e.touches.length < 2) {
          this.wallPinch = null;
        }
        return;
      }
      if (this.dragInfo && this.dragInfo.type === 'spot') {
        this.dragInfo = null;
        return;
      }
      if (!this.drawingSpot) return;
      if (this.drawingSpot.w > 10 && this.drawingSpot.h > 10) {
        this.currentWall.spots.push({
          name: `收纳框 ${this.currentWall.spots.length + 1}`,
          x: this.drawingSpot.x,
          y: this.drawingSpot.y,
          w: this.drawingSpot.w,
          h: this.drawingSpot.h,
        });
        this.selectedSpotIndex = this.currentWall.spots.length - 1;
      }
      this.drawingSpot = null;
      this.spotStartPos = null;
    },
    async loadFromServer() {
      this.hint = '';
      this.loading = true;
      try {
        const res = await api.get('/api/config');
        const area = res.data && res.data.area_map;
        if (Array.isArray(area) && area.length > 0) {
          this.rooms = area;
          this.selectedRoomIndex = null;
          this.selectedSpotIndex = null;
        }
        this.hint = '已加载';
      } catch (e) {
        this.hint = this.requestErrorText(e, '加载');
      } finally {
        this.loading = false;
      }
    },
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
        this.hint = '已保存';
      } catch (e) {
        this.hint = this.requestErrorText(e, '保存');
      } finally {
        this.loading = false;
      }
    },
    boxStyle(box) {
      return {
        left: box.x + 'px',
        top: box.y + 'px',
        width: box.w + 'px',
        height: box.h + 'px',
      };
    },
    onRoomMouseDown(e) {
      if (this.dragInfo) return;
      const rect = e.currentTarget.getBoundingClientRect();
      const currentX = (e.clientX - rect.left) / this.roomZoom;
      const currentY = (e.clientY - rect.top) / this.roomZoom;
      this.startPos = { x: currentX, y: currentY };
      this.drawingRoom = { x: currentX, y: currentY, w: 0, h: 0 };
      this.selectedRoomIndex = null;
    },
    onRoomDragStart(e, idx) {
      this.selectedRoomIndex = idx;
      this.selectedSpotIndex = null;
      const rect = e.currentTarget.parentElement.getBoundingClientRect();
      const currentX = (e.clientX - rect.left) / this.roomZoom;
      const currentY = (e.clientY - rect.top) / this.roomZoom;
      this.dragInfo = {
        type: 'room',
        index: idx,
        startX: currentX,
        startY: currentY,
        origX: this.rooms[idx].x,
        origY: this.rooms[idx].y
      };
    },
    onRoomDragStartTouch(e, idx) {
      this.selectedRoomIndex = idx;
      this.selectedSpotIndex = null;
      const t = this.firstTouch(e);
      if (!t) return;
      const p = this.roomPointFromClient(t.clientX, t.clientY);
      if (!p) return;
      this.dragInfo = {
        type: 'room',
        index: idx,
        startX: p.x,
        startY: p.y,
        origX: this.rooms[idx].x,
        origY: this.rooms[idx].y
      };
    },
    onRoomMouseMove(e) {
      const rect = e.currentTarget.getBoundingClientRect();
      const currentX = (e.clientX - rect.left) / this.roomZoom;
      const currentY = (e.clientY - rect.top) / this.roomZoom;
      
      if (this.dragInfo && this.dragInfo.type === 'room') {
        const dx = currentX - this.dragInfo.startX;
        const dy = currentY - this.dragInfo.startY;
        this.rooms[this.dragInfo.index].x = Math.max(0, this.dragInfo.origX + dx);
        this.rooms[this.dragInfo.index].y = Math.max(0, this.dragInfo.origY + dy);
        return;
      }

      if (!this.drawingRoom) return;
      this.drawingRoom.x = Math.min(this.startPos.x, currentX);
      this.drawingRoom.y = Math.min(this.startPos.y, currentY);
      this.drawingRoom.w = Math.abs(currentX - this.startPos.x);
      this.drawingRoom.h = Math.abs(currentY - this.startPos.y);
    },
    onRoomMouseUp() {
      if (this.dragInfo && this.dragInfo.type === 'room') {
        this.dragInfo = null;
        return;
      }
      if (!this.drawingRoom) return;
      if (this.drawingRoom.w > 20 && this.drawingRoom.h > 20) {
        this.rooms.push({
          name: `区域 ${this.rooms.length + 1}`,
          x: this.drawingRoom.x,
          y: this.drawingRoom.y,
          w: this.drawingRoom.w,
          h: this.drawingRoom.h,
          walls: {}
        });
        this.selectedRoomIndex = this.rooms.length - 1;
      }
      this.drawingRoom = null;
      this.startPos = null;
    },
    deleteRoom(idx) {
      this.rooms.splice(idx, 1);
      this.selectedRoomIndex = null;
    },

    onSpotMouseDown(e) {
      if (!this.currentWall || this.dragInfo) return;
      const rect = e.currentTarget.getBoundingClientRect();
      const currentX = (e.clientX - rect.left) / this.wallZoom;
      const currentY = (e.clientY - rect.top) / this.wallZoom;
      this.spotStartPos = { x: currentX, y: currentY };
      this.drawingSpot = { x: currentX, y: currentY, w: 0, h: 0 };
      this.selectedSpotIndex = null;
    },
    onSpotDragStart(e, idx) {
      this.selectedSpotIndex = idx;
      const rect = e.currentTarget.parentElement.getBoundingClientRect();
      const currentX = (e.clientX - rect.left) / this.wallZoom;
      const currentY = (e.clientY - rect.top) / this.wallZoom;
      this.dragInfo = {
        type: 'spot',
        index: idx,
        startX: currentX,
        startY: currentY,
        origX: this.currentWall.spots[idx].x,
        origY: this.currentWall.spots[idx].y
      };
    },
    onSpotDragStartTouch(e, idx) {
      this.selectedSpotIndex = idx;
      const t = this.firstTouch(e);
      if (!t) return;
      const p = this.wallPointFromClient(t.clientX, t.clientY);
      if (!p) return;
      this.dragInfo = {
        type: 'spot',
        index: idx,
        startX: p.x,
        startY: p.y,
        origX: this.currentWall.spots[idx].x,
        origY: this.currentWall.spots[idx].y
      };
    },
    onSpotMouseMove(e) {
      const rect = e.currentTarget.getBoundingClientRect();
      const currentX = (e.clientX - rect.left) / this.wallZoom;
      const currentY = (e.clientY - rect.top) / this.wallZoom;

      if (this.dragInfo && this.dragInfo.type === 'spot') {
        const dx = currentX - this.dragInfo.startX;
        const dy = currentY - this.dragInfo.startY;
        this.currentWall.spots[this.dragInfo.index].x = Math.max(0, this.dragInfo.origX + dx);
        this.currentWall.spots[this.dragInfo.index].y = Math.max(0, this.dragInfo.origY + dy);
        return;
      }

      if (!this.drawingSpot) return;
      this.drawingSpot.x = Math.min(this.spotStartPos.x, currentX);
      this.drawingSpot.y = Math.min(this.spotStartPos.y, currentY);
      this.drawingSpot.w = Math.abs(currentX - this.spotStartPos.x);
      this.drawingSpot.h = Math.abs(currentY - this.spotStartPos.y);
    },
    onSpotMouseUp() {
      if (this.dragInfo && this.dragInfo.type === 'spot') {
        this.dragInfo = null;
        return;
      }
      if (!this.drawingSpot) return;
      if (this.drawingSpot.w > 10 && this.drawingSpot.h > 10) {
        this.currentWall.spots.push({
          name: `收纳框 ${this.currentWall.spots.length + 1}`,
          x: this.drawingSpot.x,
          y: this.drawingSpot.y,
          w: this.drawingSpot.w,
          h: this.drawingSpot.h,
        });
        this.selectedSpotIndex = this.currentWall.spots.length - 1;
      }
      this.drawingSpot = null;
      this.spotStartPos = null;
    },
    deleteSpot(idx) {
      this.currentWall.spots.splice(idx, 1);
      this.selectedSpotIndex = null;
    },
    async onWallImageUpload(e) {
      const f = e && e.target && e.target.files ? e.target.files[0] : null;
      if (!f) return;
      try {
        const fd = new FormData();
        fd.append('file', f);
        const res = await api.post('/api/items/upload_image', fd);
        const url = res.data && res.data.image_url ? String(res.data.image_url) : '';
        if (!url) {
          this.hint = '图片上传失败：未返回图片地址';
          return;
        }
        this.currentWall.image = url;
        this.hint = '墙面图片已上传';
      } catch (err) {
        this.hint = this.requestErrorText(err, '图片上传');
      } finally {
        e.target.value = '';
      }
    }
  }
};
</script>

<style scoped>
.json-input {
  display: none;
}

.json-actions {
  display: flex;
  gap: 10px;
  flex-wrap: wrap;
}

.json-text {
  width: 100%;
  min-height: 140px;
  padding: 10px 12px;
  border-radius: 10px;
  border: 1px solid rgba(0, 0, 0, 0.15);
  background: rgba(255, 255, 255, 0.7);
  box-sizing: border-box;
  resize: vertical;
}

.hint.danger {
  color: #7f0018;
  background: rgba(176, 0, 32, 0.10);
  border: 1px solid rgba(176, 0, 32, 0.18);
  padding: 10px 12px;
  border-radius: 10px;
}

.map-test-page {
  padding: 20px;
  width: 100%;
  max-width: 100%;
  margin: 0;
  display: flex;
  flex-direction: column;
  min-height: 100vh;
  min-height: 100dvh;
  padding-bottom: calc(60px + env(safe-area-inset-bottom, 0px));
  box-sizing: border-box;
}

.header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
  flex-shrink: 0;
}

.header-actions {
  display: flex;
  gap: 10px;
  align-items: center;
  flex-wrap: wrap;
}

.link {
  padding: 8px 12px;
  background: #111827;
  color: white;
  text-decoration: none;
  border-radius: 8px;
}

.grid {
  display: flex;
  flex-direction: column;
  gap: 20px;
  flex: 1;
  min-height: 0;
}

.panel {
  background: rgba(255, 255, 255, 0.8);
  border: 1px solid rgba(0, 0, 0, 0.1);
  border-radius: 12px;
  padding: 16px;
  margin-bottom: 20px;
  display: flex;
  flex-direction: column;
  min-width: 0;
}

.panel-title {
  font-weight: 800;
  font-size: 18px;
  margin-bottom: 10px;
  flex-shrink: 0;
}

.muted {
  color: rgba(0, 0, 0, 0.6);
  font-size: 14px;
  flex-shrink: 0;
}

.strong {
  font-weight: 700;
}

.mb-2 {
  margin-bottom: 12px;
}

.mt-2 {
  margin-top: 12px;
}

.mt-4 {
  margin-top: 24px;
  flex-shrink: 0;
}

.zoom-controls {
  display: inline-flex;
  align-items: center;
  gap: 10px;
  margin-left: 16px;
  font-weight: normal;
  font-size: 14px;
}

.zoom-controls button {
  width: 24px;
  height: 24px;
  border-radius: 4px;
  border: 1px solid #ccc;
  background: white;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
}

.canvas-scroll-area {
  width: 100%;
  flex: none;
  height: min(55vh, 520px);
  min-height: 280px;
  max-width: 100%;
  background: #f0f0f0;
  border: 1px solid #ccc;
  position: relative;
  overflow: auto;
  margin-top: 10px;
  touch-action: pan-x pan-y;
}

.canvas-container {
  width: 2000px;
  height: 2000px;
  background: #f0f0f0;
  position: relative;
  cursor: crosshair;
}

.room-box {
  position: absolute;
  background: rgba(59, 130, 246, 0.3);
  border: 2px solid #3b82f6;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  user-select: none;
}

.room-box.active {
  background: rgba(16, 185, 129, 0.4);
  border-color: #10b981;
}

.room-box.drawing {
  border-style: dashed;
  background: rgba(59, 130, 246, 0.1);
}

.room-name {
  font-weight: bold;
  color: #fff;
  text-shadow: 0 1px 2px rgba(0,0,0,0.8);
  pointer-events: none;
}

.edit-box {
  margin-top: 16px;
  padding: 12px;
  background: rgba(0, 0, 0, 0.05);
  border-radius: 8px;
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.wall-tabs {
  display: flex;
  gap: 8px;
  margin-bottom: 16px;
  flex-wrap: wrap;
}

.tab-btn {
  padding: 6px 12px;
  background: #e5e7eb;
  border: none;
  border-radius: 6px;
  cursor: pointer;
}

.tab-btn.active {
  background: #3b82f6;
  color: white;
}

.wall-content {
  background: #f9fafb;
  padding: 12px;
  border-radius: 8px;
  border: 1px solid #e5e7eb;
}

.row {
  display: flex;
  gap: 10px;
  align-items: center;
}

.row input {
  flex: 1;
}

.wall-canvas {
  background-color: transparent;
  background-size: 100% 100%;
  background-position: top left;
  background-repeat: no-repeat;
  position: relative;
  cursor: crosshair;
}

@media (max-width: 900px) {
  .map-test-page {
    padding: 12px;
    padding-bottom: calc(60px + env(safe-area-inset-bottom, 0px));
  }
  .canvas-scroll-area {
    min-height: 0;
  }
}

.empty-bg {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  color: #9ca3af;
  font-weight: bold;
  pointer-events: none;
}

.spot-box {
  position: absolute;
  background: rgba(239, 68, 68, 0.3);
  border: 2px solid #ef4444;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  user-select: none;
}

.spot-box.active {
  background: rgba(16, 185, 129, 0.4);
  border-color: #10b981;
}

.spot-box.drawing {
  border-style: dashed;
  background: rgba(239, 68, 68, 0.1);
}

.spot-name {
  font-weight: bold;
  color: #fff;
  text-shadow: 0 1px 2px rgba(0,0,0,0.8);
  pointer-events: none;
}

.pre {
  background: #111827;
  color: #10b981;
  padding: 16px;
  border-radius: 8px;
  overflow: auto;
  max-height: 400px;
}

.hint {
  margin-top: 12px;
  padding: 10px 12px;
  background: rgba(17, 24, 39, 0.06);
  border: 1px solid rgba(0, 0, 0, 0.10);
  border-radius: 10px;
}
</style>
