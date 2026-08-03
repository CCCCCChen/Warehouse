<template>
  <div class="location-tree-page">
    <div class="header">
      <h2>位置管理</h2>
      <div class="header-actions">
        <button class="btn-ghost" :disabled="loading" @click="toggleBatchMode">
          {{ batchMode ? '取消批量' : '批量导出' }}
        </button>
        <button class="btn" :disabled="loading" @click="openCreateDialog(null)">+ 新建区域</button>
        <router-link class="link" to="/warehouse">返回主页</router-link>
      </div>
    </div>

    <!-- Batch action bar -->
    <div v-if="batchMode && selectedIds.size > 0" class="batch-bar">
      <span>已选 {{ selectedIds.size }} 个位置</span>
      <button class="btn" @click="exportBatchQR">导出选中二维码 (PDF)</button>
    </div>
    <div v-if="batchMode && selectedIds.size === 0 && flatNodes.length > 0" class="batch-bar muted">
      勾选需要导出二维码的位置
    </div>

    <!-- Tree -->
    <div class="tree-panel">
      <div v-if="loading" class="muted" style="padding: 20px;">加载中...</div>
      <div v-else-if="flatNodes.length === 0" class="empty-state">
        <p>暂无位置数据。</p>
        <button
          class="btn"
          style="margin-top: 10px;"
          :disabled="importing"
          @click="importFromConfig"
        >{{ importing ? '导入中...' : '从区域配置导入' }}</button>
        <p class="muted" style="margin-top:6px;">或使用「新建区域」手动创建</p>
      </div>
      <div v-else class="tree-list">
        <div
          v-for="node in flatNodes"
          :key="node.id"
          class="tree-node"
          :class="{ 'has-children': node.hasChildren, 'editing': editingId === node.id }"
          :style="{ paddingLeft: (node.depth * 28 + 12) + 'px' }"
        >
          <!-- Batch checkbox -->
          <input
            v-if="batchMode"
            type="checkbox"
            class="batch-check"
            :checked="selectedIds.has(node.id)"
            @change="toggleSelect(node.id)"
          />

          <!-- Expand/collapse -->
          <span
            class="toggle"
            :class="{ invisible: !node.hasChildren }"
            @click="toggleExpand(node.id)"
          >{{ expanded.has(node.id) ? '▼' : '▶' }}</span>

          <!-- Level tag -->
          <span class="level-tag" :class="'level-' + node.level">{{ levelLabel(node.level) }}</span>

          <!-- Name -->
          <template v-if="editingId === node.id">
            <input
              ref="editInputRef"
              v-model="editName"
              class="inline-input"
              @keyup.enter="saveEdit"
              @keyup.escape="cancelEdit"
              @blur="saveEdit"
            />
          </template>
          <template v-else>
            <span class="node-name" @dblclick="startEdit(node)">{{ node.name }}</span>
          </template>

          <!-- Actions -->
          <span v-if="!batchMode" class="node-actions">
            <button
              class="btn-ghost btn-sm"
              :disabled="node.level === 'sub'"
              @click="openCreateDialog(node)"
              title="新建子位置"
            >+ 子级</button>
            <button class="btn-ghost btn-sm" @click="downloadQR(node.id)" title="下载二维码">QR</button>
            <button class="btn-ghost btn-sm" @click="startEdit(node)" title="重命名">重命名</button>
            <button class="btn-danger btn-sm" @click="deleteNode(node)" title="删除">删除</button>
          </span>
        </div>
      </div>
    </div>

    <!-- Create dialog -->
    <div v-if="showCreateDialog" class="dialog-overlay" @click.self="closeCreateDialog">
      <div class="dialog">
        <div class="dialog-title">{{ createParent ? '新建子位置' : '新建区域' }}</div>
        <div class="dialog-body">
          <label class="full">
            名称
            <input
              ref="createInputRef"
              v-model="createName"
              @keyup.enter="confirmCreate"
              placeholder="输入位置名称..."
            />
          </label>
          <div v-if="createParent" class="muted" style="margin-top: 8px;">
            将创建在「{{ createParent.name }}」下
          </div>
        </div>
        <div class="dialog-actions">
          <button class="btn-ghost" @click="closeCreateDialog">取消</button>
          <button class="btn" :disabled="!createName.trim()" @click="confirmCreate">创建</button>
        </div>
      </div>
    </div>

    <div v-if="hint" class="hint">{{ hint }}</div>
  </div>
</template>

<script>
import { api } from '@/api/http';

const LEVEL_LABELS = { zone: '区域', wall: '墙面', unit: '储物单元', sub: '细分' };

export default {
  name: 'LocationTreePage',

  data() {
    return {
      tree: [],
      expanded: new Set(),
      loading: false,
      hint: '',

      // Inline edit
      editingId: null,
      editName: '',

      // Batch mode
      batchMode: false,
      selectedIds: new Set(),

      // Import
      importing: false,

      // Create dialog
      showCreateDialog: false,
      createParent: null,
      createName: '',
    };
  },

  computed: {
    flatNodes() {
      const result = [];
      const walk = (nodes, depth) => {
        for (const n of nodes) {
          const hasChildren = Array.isArray(n.children) && n.children.length > 0;
          result.push({ ...n, depth, hasChildren });
          if (hasChildren && this.expanded.has(n.id)) {
            walk(n.children, depth + 1);
          }
        }
      };
      walk(this.tree, 0);
      return result;
    },
  },

  mounted() {
    this.loadTree();
  },

  methods: {
    levelLabel(level) {
      return LEVEL_LABELS[level] || level;
    },

    requestErrorText(e, action) {
      const status = e && e.response ? e.response.status : null;
      const detail = e && e.response && e.response.data && e.response.data.detail ? String(e.response.data.detail) : '';
      if (status === 401) return `${action}失败：未登录或 token 无效`;
      if (status === 403) return `${action}失败：需要 owner 权限`;
      if (status) return `${action}失败：HTTP ${status}${detail ? ` (${detail})` : ''}`;
      const msg = e && e.message ? String(e.message) : '';
      if (msg && /timeout/i.test(msg)) return `${action}失败：请求超时`;
      return `${action}失败：无法连接到服务器`;
    },

    async loadTree() {
      this.hint = '';
      this.loading = true;
      try {
        const res = await api.get('/api/locations');
        this.tree = Array.isArray(res.data) ? res.data : [];
        // Auto-expand all nodes on first load
        const autoExpand = new Set();
        const queue = [...this.tree];
        while (queue.length) {
          const n = queue.shift();
          if (n && n.id) autoExpand.add(n.id);
          if (n && Array.isArray(n.children)) queue.push(...n.children);
        }
        this.expanded = autoExpand;
      } catch (e) {
        this.hint = this.requestErrorText(e, '加载位置树');
      } finally {
        this.loading = false;
      }
    },

    toggleExpand(id) {
      const next = new Set(this.expanded);
      if (next.has(id)) {
        next.delete(id);
      } else {
        next.add(id);
      }
      this.expanded = next;
    },

    // ── Inline rename ──

    startEdit(node) {
      if (this.batchMode) return;
      this.editingId = node.id;
      this.editName = node.name;
      this.$nextTick(() => {
        const el = this.$refs.editInputRef;
        if (el) {
          if (Array.isArray(el)) el[0]?.focus?.();
          else el.focus?.();
        }
      });
    },

    async saveEdit() {
      const id = this.editingId;
      const name = (this.editName || '').trim();
      if (!id || !name) {
        this.editingId = null;
        return;
      }
      try {
        await api.put(`/api/locations/${id}`, { name });
        const node = this.findNodeById(this.tree, id);
        if (node) node.name = name;
        this.hint = '已重命名';
      } catch (e) {
        this.hint = this.requestErrorText(e, '重命名');
      }
      this.editingId = null;
    },

    cancelEdit() {
      this.editingId = null;
    },

    findNodeById(nodes, id) {
      for (const n of nodes) {
        if (n.id === id) return n;
        if (Array.isArray(n.children)) {
          const found = this.findNodeById(n.children, id);
          if (found) return found;
        }
      }
      return null;
    },

    // ── Delete ──

    async deleteNode(node) {
      const label = this.levelLabel(node.level);
      const childCount = Array.isArray(node.children) ? node.children.length : 0;
      let msg = `确定删除${label}「${node.name}」？`;
      if (childCount > 0) msg += `\n其下 ${childCount} 个子位置也将被删除。`;
      if (!confirm(msg)) return;

      try {
        await api.delete(`/api/locations/${node.id}`);
        this.removeNodeFromTree(this.tree, node.id);
        // Also remove from expanded if present
        const nextExpanded = new Set(this.expanded);
        nextExpanded.delete(node.id);
        this.expanded = nextExpanded;
        this.hint = `已删除「${node.name}」`;
      } catch (e) {
        this.hint = this.requestErrorText(e, '删除');
      }
    },

    removeNodeFromTree(nodes, id) {
      const idx = nodes.findIndex(n => n.id === id);
      if (idx !== -1) {
        nodes.splice(idx, 1);
        return true;
      }
      for (const n of nodes) {
        if (Array.isArray(n.children) && this.removeNodeFromTree(n.children, id)) {
          return true;
        }
      }
      return false;
    },

    // ── Create ──

    openCreateDialog(parent) {
      this.createParent = parent;
      this.createName = '';
      this.showCreateDialog = true;
      this.$nextTick(() => {
        const el = this.$refs.createInputRef;
        if (el) el.focus?.();
      });
    },

    closeCreateDialog() {
      this.showCreateDialog = false;
      this.createParent = null;
      this.createName = '';
    },

    async confirmCreate() {
      const name = (this.createName || '').trim();
      if (!name) return;

      try {
        const payload = {
          name,
          parent_id: this.createParent ? this.createParent.id : null,
        };
        const res = await api.post('/api/locations', payload);

        if (this.createParent) {
          // Add child to parent node
          if (!Array.isArray(this.createParent.children)) {
            this.createParent.children = [];
          }
          this.createParent.children.push(res.data);
          // Ensure parent is expanded
          const nextExpanded = new Set(this.expanded);
          nextExpanded.add(this.createParent.id);
          this.expanded = nextExpanded;
        } else {
          // Add root zone
          this.tree.push(res.data);
          const nextExpanded = new Set(this.expanded);
          nextExpanded.add(res.data.id);
          this.expanded = nextExpanded;
        }
        this.hint = `已创建「${name}」`;
        this.closeCreateDialog();
      } catch (e) {
        this.hint = this.requestErrorText(e, '创建');
      }
    },

    // ── Import from config ──

    async importFromConfig() {
      this.importing = true;
      this.hint = '';
      try {
        const res = await api.post('/api/locations/import-from-config');
        const data = res.data;
        this.tree = Array.isArray(data.tree) ? data.tree : [];
        // Auto-expand all
        const autoExpand = new Set();
        const queue = [...this.tree];
        while (queue.length) {
          const n = queue.shift();
          if (n && n.id) autoExpand.add(n.id);
          if (n && Array.isArray(n.children)) queue.push(...n.children);
        }
        this.expanded = autoExpand;
        this.hint = `已导入 ${data.imported} 个位置`;
      } catch (e) {
        this.hint = this.requestErrorText(e, '导入配置');
      } finally {
        this.importing = false;
      }
    },

    // ── QR ──

    async downloadQR(id) {
      try {
        const res = await api.get(`/api/locations/${id}/qrcode`, { responseType: 'blob' });
        const url = URL.createObjectURL(res.data);
        const a = document.createElement('a');
        a.href = url;
        a.download = `location-qr-${id}.png`;
        document.body.appendChild(a);
        a.click();
        a.remove();
        setTimeout(() => URL.revokeObjectURL(url), 1500);
        this.hint = '二维码已下载';
      } catch (e) {
        this.hint = this.requestErrorText(e, '下载二维码');
      }
    },

    // ── Batch QR export ──

    toggleBatchMode() {
      this.batchMode = !this.batchMode;
      if (!this.batchMode) {
        this.selectedIds = new Set();
      }
    },

    toggleSelect(id) {
      const next = new Set(this.selectedIds);
      if (next.has(id)) {
        next.delete(id);
      } else {
        next.add(id);
      }
      this.selectedIds = next;
    },

    async exportBatchQR() {
      const ids = [...this.selectedIds];
      if (ids.length === 0) return;
      try {
        const res = await api.post('/api/locations/qrcodes/batch', { ids }, { responseType: 'blob' });
        const url = URL.createObjectURL(res.data);
        const a = document.createElement('a');
        a.href = url;
        a.download = 'location-qrcodes.pdf';
        document.body.appendChild(a);
        a.click();
        a.remove();
        setTimeout(() => URL.revokeObjectURL(url), 1500);
        this.hint = `已导出 ${ids.length} 个位置的二维码 PDF`;
        this.batchMode = false;
        this.selectedIds = new Set();
      } catch (e) {
        this.hint = this.requestErrorText(e, '批量导出');
      }
    },
  },
};
</script>

<style scoped>
.location-tree-page {
  padding: 20px;
  max-width: 900px;
  margin: 0 auto;
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
}

.header h2 {
  margin: 0;
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
  font-size: 13px;
}

/* Batch bar */
.batch-bar {
  display: flex;
  align-items: center;
  gap: 14px;
  padding: 10px 16px;
  background: rgba(59, 130, 246, 0.08);
  border: 1px solid rgba(59, 130, 246, 0.25);
  border-radius: 10px;
  margin-bottom: 16px;
  font-weight: 600;
}

.batch-bar.muted {
  background: rgba(0, 0, 0, 0.03);
  border-color: rgba(0, 0, 0, 0.08);
  font-weight: 400;
  color: rgba(0, 0, 0, 0.5);
}

/* Tree panel */
.tree-panel {
  background: rgba(255, 255, 255, 0.8);
  border: 1px solid rgba(0, 0, 0, 0.1);
  border-radius: 12px;
  overflow: hidden;
}

.empty-state {
  padding: 40px 20px;
  text-align: center;
}

.empty-state p {
  margin: 4px 0;
}

.tree-list {
  padding: 8px 0;
}

.tree-node {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 16px;
  min-height: 40px;
  box-sizing: border-box;
  transition: background 0.1s;
}

.tree-node:hover {
  background: rgba(0, 0, 0, 0.02);
}

.tree-node.editing {
  background: rgba(59, 130, 246, 0.04);
}

/* Toggle */
.toggle {
  width: 18px;
  text-align: center;
  font-size: 11px;
  color: rgba(0, 0, 0, 0.4);
  cursor: pointer;
  user-select: none;
  flex-shrink: 0;
  line-height: 1;
}

.toggle.invisible {
  visibility: hidden;
}

/* Batch checkbox */
.batch-check {
  flex-shrink: 0;
  width: 16px;
  height: 16px;
  cursor: pointer;
  accent-color: #3b82f6;
}

/* Level tag */
.level-tag {
  display: inline-block;
  padding: 2px 8px;
  border-radius: 4px;
  font-size: 11px;
  font-weight: 600;
  flex-shrink: 0;
  line-height: 1.5;
}

.level-zone {
  background: rgba(59, 130, 246, 0.12);
  color: #2563eb;
}

.level-wall {
  background: rgba(139, 92, 246, 0.12);
  color: #7c3aed;
}

.level-unit {
  background: rgba(239, 68, 68, 0.12);
  color: #dc2626;
}

.level-sub {
  background: rgba(107, 114, 128, 0.12);
  color: #6b7280;
}

/* Name */
.node-name {
  flex: 1;
  min-width: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  font-size: 14px;
  cursor: default;
}

.inline-input {
  flex: 1;
  min-width: 0;
  padding: 3px 8px;
  font-size: 14px;
  border: 1px solid #3b82f6;
  border-radius: 6px;
  outline: none;
  background: #fff;
}

/* Node actions */
.node-actions {
  display: flex;
  gap: 4px;
  flex-shrink: 0;
  opacity: 0;
  transition: opacity 0.15s;
}

.tree-node:hover .node-actions {
  opacity: 1;
}

/* Dialog */
.dialog-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.3);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}

.dialog {
  background: #fff;
  border-radius: 14px;
  padding: 24px;
  width: 90%;
  max-width: 400px;
  box-shadow: 0 8px 30px rgba(0, 0, 0, 0.18);
}

.dialog-title {
  font-weight: 800;
  font-size: 17px;
  margin-bottom: 16px;
}

.dialog-body {
  margin-bottom: 20px;
}

.dialog-body label {
  display: flex;
  flex-direction: column;
  gap: 6px;
  font-weight: 600;
  font-size: 13px;
  color: #374151;
}

.dialog-body input {
  padding: 10px 12px;
  border: 1px solid rgba(0, 0, 0, 0.2);
  border-radius: 8px;
  font-size: 14px;
  outline: none;
}

.dialog-body input:focus {
  border-color: #3b82f6;
}

.dialog-actions {
  display: flex;
  gap: 10px;
  justify-content: flex-end;
}

.hint {
  margin-top: 16px;
  padding: 10px 12px;
  background: rgba(17, 24, 39, 0.06);
  border: 1px solid rgba(0, 0, 0, 0.1);
  border-radius: 10px;
  font-size: 13px;
  color: #374151;
}

.muted {
  color: rgba(0, 0, 0, 0.5);
  font-size: 13px;
}

/* Mobile */
@media (max-width: 768px) {
  .location-tree-page {
    padding: 12px;
    padding-bottom: calc(60px + env(safe-area-inset-bottom, 0px));
  }

  .header {
    flex-wrap: wrap;
    gap: 10px;
  }

  .node-actions {
    opacity: 1;
  }

  .node-actions .btn-ghost,
  .node-actions .btn-danger {
    padding: 4px 8px;
    font-size: 11px;
  }
}
</style>
