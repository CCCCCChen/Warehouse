<template>
  <div class="items-page">
    <h2>物品管理</h2>

    <div class="actions">
      <button @click="refresh">刷新列表</button>
    </div>

    <form class="form" @submit.prevent="onSubmit">
      <div class="row">
        <label>
          名称
          <input v-model.trim="form.name" required />
        </label>
        <label>
          数量
          <input v-model.number="form.quantity" type="number" min="0" required />
        </label>
      </div>
      <label class="full">
        描述
        <input v-model.trim="form.description" placeholder="可选" />
      </label>

      <div class="row">
        <button type="submit">{{ form.id ? '更新' : '新增' }}</button>
        <button v-if="form.id" type="button" @click="resetForm">取消编辑</button>
      </div>
    </form>

    <div v-if="loading" class="hint">加载中...</div>
    <div v-else-if="items.length === 0" class="hint">暂无物品</div>

    <table v-else class="table">
      <thead>
        <tr>
          <th>ID</th>
          <th>名称</th>
          <th>描述</th>
          <th>数量</th>
          <th>操作</th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="it in items" :key="it.id">
          <td>{{ it.id }}</td>
          <td>{{ it.name }}</td>
          <td>{{ it.description || '-' }}</td>
          <td>{{ it.quantity }}</td>
          <td class="ops">
            <button @click="startEdit(it)">编辑</button>
            <button class="danger" @click="remove(it.id)">删除</button>
          </td>
        </tr>
      </tbody>
    </table>
  </div>
</template>

<script>
import { api } from '@/api/http';

export default {
  name: 'ItemsPage',
  data() {
    return {
      loading: false,
      items: [],
      form: {
        id: null,
        name: '',
        description: '',
        quantity: 0,
      },
    };
  },
  created() {
    this.refresh();
  },
  methods: {
    async refresh() {
      this.loading = true;
      try {
        const res = await api.get('/api/items');
        this.items = res.data;
      } catch (e) {
        console.error('Failed to load items:', e);
      } finally {
        this.loading = false;
      }
    },
    resetForm() {
      this.form = {
        id: null,
        name: '',
        description: '',
        quantity: 0,
      };
    },
    startEdit(it) {
      this.form = {
        id: it.id,
        name: it.name,
        description: it.description || '',
        quantity: it.quantity,
      };
    },
    async onSubmit() {
      try {
        if (this.form.id) {
          const id = this.form.id;
          const payload = {
            name: this.form.name,
            description: this.form.description || null,
            quantity: this.form.quantity,
          };
          await api.put(`/api/items/${id}`, payload);
        } else {
          const payload = {
            name: this.form.name,
            description: this.form.description || null,
            quantity: this.form.quantity,
          };
          await api.post('/api/items', payload);
        }
        this.resetForm();
        await this.refresh();
      } catch (e) {
        console.error('Failed to submit item:', e);
      }
    },
    async remove(id) {
      try {
        await api.delete(`/api/items/${id}`);
        await this.refresh();
      } catch (e) {
        console.error('Failed to delete item:', e);
      }
    },
  },
};
</script>

<style scoped>
.items-page {
  padding: 20px;
}

.actions {
  margin: 10px 0 20px;
}

.form {
  background: rgba(255, 255, 255, 0.7);
  padding: 12px;
  border-radius: 8px;
  margin-bottom: 20px;
}

.row {
  display: flex;
  gap: 12px;
  margin-bottom: 10px;
  flex-wrap: wrap;
}

.full {
  display: block;
  margin-bottom: 10px;
}

label {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

input {
  padding: 8px 10px;
  border-radius: 6px;
  border: 1px solid rgba(0, 0, 0, 0.15);
}

.hint {
  color: #444;
  padding: 10px 0;
}

.table {
  width: 100%;
  border-collapse: collapse;
  background: rgba(255, 255, 255, 0.7);
  border-radius: 8px;
  overflow: hidden;
}

.table th,
.table td {
  padding: 10px;
  border-bottom: 1px solid rgba(0, 0, 0, 0.08);
  text-align: left;
}

.ops {
  display: flex;
  gap: 8px;
}

.danger {
  background: #b00020;
  color: white;
  border: none;
  padding: 6px 10px;
  border-radius: 6px;
}
</style>

