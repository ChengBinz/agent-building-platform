<template>
  <div class="admin-users">
    <div class="page-header">
      <h3>用户管理</h3>
    </div>

    <el-table :data="users" v-loading="loading" stripe>
      <el-table-column prop="username" label="用户名" width="150" />
      <el-table-column prop="email" label="邮箱" min-width="200" />
      <el-table-column prop="display_name" label="显示名" width="150">
        <template #default="{ row }">
          {{ row.display_name || '-' }}
        </template>
      </el-table-column>
      <el-table-column prop="is_active" label="状态" width="90">
        <template #default="{ row }">
          <el-tag :type="row.is_active ? 'success' : 'danger'" size="small">
            {{ row.is_active ? '启用' : '禁用' }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="is_superuser" label="角色" width="90">
        <template #default="{ row }">
          <el-tag :type="row.is_superuser ? '' : 'info'" size="small">
            {{ row.is_superuser ? '管理员' : '用户' }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="created_at" label="注册时间" width="170">
        <template #default="{ row }">
          {{ formatDateTime(row.created_at) }}
        </template>
      </el-table-column>
      <el-table-column label="操作" width="180" fixed="right">
        <template #default="{ row }">
          <el-button
            text
            size="small"
            :type="row.is_active ? 'warning' : 'success'"
            @click="handleToggleActive(row)"
          >
            {{ row.is_active ? '禁用' : '启用' }}
          </el-button>
          <el-button text size="small" type="danger" @click="handleDelete(row)">
            删除
          </el-button>
        </template>
      </el-table-column>
    </el-table>

    <div class="pagination-wrap">
      <el-pagination
        v-model:current-page="page"
        :page-size="pageSize"
        :total="total"
        layout="total, prev, pager, next"
        @current-change="fetchUsers"
      />
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from "vue";
import { ElMessageBox } from "element-plus";
import { listUsers, updateUserStatus, deleteUser } from "@/api/admin";
import { formatDateTime } from "@/utils/format";
import type { User } from "@/types";

const users = ref<User[]>([]);
const loading = ref(false);
const page = ref(1);
const pageSize = 20;
const total = ref(0);

onMounted(() => {
  fetchUsers();
});

async function fetchUsers() {
  loading.value = true;
  try {
    const { data } = await listUsers(page.value, pageSize);
    users.value = data.items;
    total.value = data.total;
  } catch {
    // handled by interceptor
  } finally {
    loading.value = false;
  }
}

async function handleToggleActive(user: User) {
  try {
    await updateUserStatus(user.id, { is_active: !user.is_active });
    user.is_active = !user.is_active;
  } catch {
    // handled by interceptor
  }
}

async function handleDelete(user: User) {
  try {
    await ElMessageBox.confirm(`确定删除用户 "${user.username}"？`, "警告", {
      confirmButtonText: "确定",
      cancelButtonText: "取消",
      type: "warning",
    });
    await deleteUser(user.id);
    users.value = users.value.filter((u) => u.id !== user.id);
    total.value--;
  } catch {
    // cancelled
  }
}
</script>

<style scoped>
.page-header {
  margin-bottom: 16px;
}

.page-header h3 {
  margin: 0;
}

.pagination-wrap {
  margin-top: 16px;
  display: flex;
  justify-content: flex-end;
}
</style>
