<template>
  <div class="map-test-page">
    <div class="header">
      <h2>区域与墙面设置 (测试)</h2>
      <div class="header-actions">
        <router-link class="link" to="/warehouse">返回主页</router-link>
      </div>
    </div>

    <div class="grid">
      <!-- 第二层级：区域设置 -->
      <div class="panel">
        <div class="panel-title">第二层级：房间/区域地图设置</div>
        <div class="muted">在下方灰色区域拖拽鼠标画出房间长方形，并命名。</div>
        
        <div 
          class="canvas-container" 
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
            @mousedown.stop="selectRoom(idx)"
          >
            <div class="room-name">{{ room.name }}</div>
          </div>
          <div 
            v-if="drawingRoom"
            class="room-box drawing"
            :style="boxStyle(drawingRoom)"
          ></div>
        </div>

        <div v-if="selectedRoomIndex !== null" class="edit-box">
          <div class="strong">编辑选中区域</div>
          <label>名称 <input v-model.trim="rooms[selectedRoomIndex].name" /></label>
          <button class="danger-btn" @click="deleteRoom(selectedRoomIndex)">删除此区域</button>
        </div>
      </div>

      <!-- 第三层级：墙面设置 -->
      <div class="panel">
        <div class="panel-title">第三层级：墙面设置</div>
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

            <div class="muted mb-2">在下方图片区域拖拽鼠标画出收纳框，并命名。</div>
            
            <div 
              class="wall-canvas"
              :style="{ backgroundImage: currentWall.image ? `url(${currentWall.image})` : 'none' }"
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
                @mousedown.stop="selectSpot(idx)"
              >
                <div class="spot-name">{{ spot.name }}</div>
              </div>
              <div 
                v-if="drawingSpot"
                class="spot-box drawing"
                :style="boxStyle(drawingSpot)"
              ></div>
            </div>

            <div v-if="selectedSpotIndex !== null" class="edit-box mt-2">
              <div class="strong">编辑收纳框</div>
              <label>名称 <input v-model.trim="currentWall.spots[selectedSpotIndex].name" /></label>
              <button class="danger-btn" @click="deleteSpot(selectedSpotIndex)">删除此框</button>
            </div>
          </div>
        </div>
      </div>
    </div>

    <div class="panel mt-4">
      <div class="panel-title">生成的配置 JSON</div>
      <pre class="pre">{{ generatedJson }}</pre>
    </div>
  </div>
</template>

<script>
export default {
  name: 'AreaMapTest',
  data() {
    return {
      rooms: [
        { name: '客厅', x: 50, y: 50, w: 150, h: 100, walls: {} }
      ],
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
    };
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
    }
  },
  methods: {
    boxStyle(box) {
      return {
        left: box.x + 'px',
        top: box.y + 'px',
        width: box.w + 'px',
        height: box.h + 'px',
      };
    },
    // Room Drawing
    onRoomMouseDown(e) {
      const rect = e.currentTarget.getBoundingClientRect();
      this.startPos = { x: e.clientX - rect.left, y: e.clientY - rect.top };
      this.drawingRoom = { x: this.startPos.x, y: this.startPos.y, w: 0, h: 0 };
      this.selectedRoomIndex = null;
    },
    onRoomMouseMove(e) {
      if (!this.drawingRoom) return;
      const rect = e.currentTarget.getBoundingClientRect();
      const currentX = e.clientX - rect.left;
      const currentY = e.clientY - rect.top;
      this.drawingRoom.x = Math.min(this.startPos.x, currentX);
      this.drawingRoom.y = Math.min(this.startPos.y, currentY);
      this.drawingRoom.w = Math.abs(currentX - this.startPos.x);
      this.drawingRoom.h = Math.abs(currentY - this.startPos.y);
    },
    onRoomMouseUp() {
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
    selectRoom(idx) {
      this.selectedRoomIndex = idx;
      this.selectedSpotIndex = null;
    },
    deleteRoom(idx) {
      this.rooms.splice(idx, 1);
      this.selectedRoomIndex = null;
    },

    // Spot Drawing
    onSpotMouseDown(e) {
      if (!this.currentWall) return;
      const rect = e.currentTarget.getBoundingClientRect();
      this.spotStartPos = { x: e.clientX - rect.left, y: e.clientY - rect.top };
      this.drawingSpot = { x: this.spotStartPos.x, y: this.spotStartPos.y, w: 0, h: 0 };
      this.selectedSpotIndex = null;
    },
    onSpotMouseMove(e) {
      if (!this.drawingSpot) return;
      const rect = e.currentTarget.getBoundingClientRect();
      const currentX = e.clientX - rect.left;
      const currentY = e.clientY - rect.top;
      this.drawingSpot.x = Math.min(this.spotStartPos.x, currentX);
      this.drawingSpot.y = Math.min(this.spotStartPos.y, currentY);
      this.drawingSpot.w = Math.abs(currentX - this.spotStartPos.x);
      this.drawingSpot.h = Math.abs(currentY - this.spotStartPos.y);
    },
    onSpotMouseUp() {
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
    selectSpot(idx) {
      this.selectedSpotIndex = idx;
    },
    deleteSpot(idx) {
      this.currentWall.spots.splice(idx, 1);
      this.selectedSpotIndex = null;
    },
    onWallImageUpload(e) {
      const f = e.target.files[0];
      if (f) {
        // Just for frontend preview
        this.currentWall.image = URL.createObjectURL(f);
      }
    }
  }
};
</script>

<style scoped>
.map-test-page {
  padding: 20px;
  max-width: 1200px;
  margin: 0 auto;
}

.header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.link {
  padding: 8px 12px;
  background: #111827;
  color: white;
  text-decoration: none;
  border-radius: 8px;
}

.grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 20px;
}

@media (max-width: 900px) {
  .grid {
    grid-template-columns: 1fr;
  }
}

.panel {
  background: rgba(255, 255, 255, 0.8);
  border: 1px solid rgba(0, 0, 0, 0.1);
  border-radius: 12px;
  padding: 16px;
}

.panel-title {
  font-weight: 800;
  font-size: 18px;
  margin-bottom: 10px;
}

.muted {
  color: rgba(0, 0, 0, 0.6);
  font-size: 14px;
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
}

.canvas-container {
  width: 100%;
  height: 400px;
  background: #f0f0f0;
  border: 1px solid #ccc;
  position: relative;
  overflow: hidden;
  cursor: crosshair;
  margin-top: 10px;
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

.danger-btn {
  background: #ef4444;
  color: white;
  border: none;
  padding: 8px 12px;
  border-radius: 6px;
  cursor: pointer;
  width: fit-content;
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
  width: 100%;
  height: 350px;
  background-color: #e5e7eb;
  background-size: cover;
  background-position: center;
  position: relative;
  overflow: hidden;
  cursor: crosshair;
  border: 1px solid #ccc;
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
</style>
