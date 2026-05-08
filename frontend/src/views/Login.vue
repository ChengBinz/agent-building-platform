<template>
  <div class="login-container">
    <el-card class="login-card">
      <h2>AI Agent Platform</h2>

      <!-- 用户/管理员切换标签 -->
      <el-tabs v-model="activeTab" class="login-tabs" @tab-change="handleTabChange">
        <el-tab-pane label="用户登录" name="user" />
        <el-tab-pane label="管理员登录" name="admin" />
      </el-tabs>

      <!-- ==================== 用户登录 ==================== -->
      <template v-if="activeTab === 'user' && !isRegister">
        <el-form ref="userLoginFormRef" :model="userLoginForm" :rules="loginRules" @keyup.enter="handleUserLogin">
          <el-form-item prop="username">
            <el-input v-model="userLoginForm.username" placeholder="用户名" :prefix-icon="User" />
          </el-form-item>
          <el-form-item prop="password">
            <el-input v-model="userLoginForm.password" type="password" placeholder="密码" show-password :prefix-icon="Lock" />
          </el-form-item>
          <el-form-item>
            <el-button type="primary" style="width: 100%" :loading="auth.loading" @click="handleUserLogin">登 录</el-button>
          </el-form-item>
        </el-form>
        <p class="toggle-text">还没有账号？<el-button link type="primary" @click="isRegister = true">注册账号</el-button></p>
      </template>

      <!-- ==================== 用户注册 ==================== -->
      <template v-if="activeTab === 'user' && isRegister">
        <el-form ref="userRegFormRef" :model="userRegForm" :rules="registerRules" @keyup.enter="handleUserRegister">
          <el-form-item prop="username">
            <el-input v-model="userRegForm.username" placeholder="用户名" :prefix-icon="User" />
          </el-form-item>
          <el-form-item prop="email">
            <el-input v-model="userRegForm.email" placeholder="邮箱" :prefix-icon="Message" />
          </el-form-item>
          <el-form-item prop="password">
            <el-input v-model="userRegForm.password" type="password" placeholder="密码" show-password :prefix-icon="Lock" />
          </el-form-item>
          <el-form-item prop="display_name">
            <el-input v-model="userRegForm.display_name" placeholder="显示名称（选填）" :prefix-icon="User" />
          </el-form-item>
          <el-form-item>
            <el-button type="primary" style="width: 100%" :loading="auth.loading" @click="handleUserRegister">注 册</el-button>
          </el-form-item>
        </el-form>
        <p class="toggle-text">已有账号？<el-button link type="primary" @click="isRegister = false">返回登录</el-button></p>
      </template>

      <!-- ==================== 管理员登录 ==================== -->
      <template v-if="activeTab === 'admin' && !isRegister">
        <el-form ref="adminLoginFormRef" :model="adminLoginForm" :rules="loginRules" @keyup.enter="handleAdminLogin">
          <el-form-item prop="username">
            <el-input v-model="adminLoginForm.username" placeholder="管理员用户名" :prefix-icon="User" />
          </el-form-item>
          <el-form-item prop="password">
            <el-input v-model="adminLoginForm.password" type="password" placeholder="密码" show-password :prefix-icon="Lock" />
          </el-form-item>
          <el-form-item>
            <el-button type="danger" style="width: 100%" :loading="auth.loading" @click="handleAdminLogin">管理员登录</el-button>
          </el-form-item>
        </el-form>
        <p class="toggle-text">还没有管理员账号？<el-button link type="danger" @click="isRegister = true">注册管理员</el-button></p>
      </template>

      <!-- ==================== 管理员注册 ==================== -->
      <template v-if="activeTab === 'admin' && isRegister">
        <el-form ref="adminRegFormRef" :model="adminRegForm" :rules="adminRegisterRules" @keyup.enter="handleAdminRegister">
          <el-form-item prop="username">
            <el-input v-model="adminRegForm.username" placeholder="用户名" :prefix-icon="User" />
          </el-form-item>
          <el-form-item prop="email">
            <el-input v-model="adminRegForm.email" placeholder="邮箱" :prefix-icon="Message" />
          </el-form-item>
          <el-form-item prop="password">
            <el-input v-model="adminRegForm.password" type="password" placeholder="密码" show-password :prefix-icon="Lock" />
          </el-form-item>
          <el-form-item prop="display_name">
            <el-input v-model="adminRegForm.display_name" placeholder="显示名称（选填）" :prefix-icon="User" />
          </el-form-item>
          <el-form-item prop="admin_code">
            <el-input v-model="adminRegForm.admin_code" type="password" placeholder="管理员注册码" show-password :prefix-icon="Key" />
          </el-form-item>
          <el-form-item>
            <el-button type="danger" style="width: 100%" :loading="auth.loading" @click="handleAdminRegister">注册管理员</el-button>
          </el-form-item>
        </el-form>
        <p class="toggle-text">已有管理员账号？<el-button link type="danger" @click="isRegister = false">返回登录</el-button></p>
      </template>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { reactive, ref } from "vue";
import { useRouter } from "vue-router";
import { User, Lock, Message, Key } from "@element-plus/icons-vue";
import { ElMessage, type FormInstance, type FormRules } from "element-plus";
import { useAuthStore } from "@/stores/auth";

const router = useRouter();
const auth = useAuthStore();

// Tab 状态
const activeTab = ref<"user" | "admin">("user");
const isRegister = ref(false);

// 表单引用
const userLoginFormRef = ref<FormInstance>();
const userRegFormRef = ref<FormInstance>();
const adminLoginFormRef = ref<FormInstance>();
const adminRegFormRef = ref<FormInstance>();

// 用户登录表单
const userLoginForm = reactive({ username: "", password: "" });
// 用户注册表单
const userRegForm = reactive({ username: "", email: "", password: "", display_name: "" });
// 管理员登录表单
const adminLoginForm = reactive({ username: "", password: "" });
// 管理员注册表单
const adminRegForm = reactive({ username: "", email: "", password: "", display_name: "", admin_code: "" });

// 登录校验规则
const loginRules: FormRules = {
  username: [{ required: true, message: "请输入用户名", trigger: "blur" }],
  password: [{ required: true, message: "请输入密码", trigger: "blur" }],
};

// 普通注册校验规则
const registerRules: FormRules = {
  username: [{ required: true, message: "请输入用户名", trigger: "blur" }],
  email: [
    { required: true, message: "请输入邮箱", trigger: "blur" },
    { type: "email", message: "请输入有效的邮箱地址", trigger: "blur" },
  ],
  password: [
    { required: true, message: "请输入密码", trigger: "blur" },
    { min: 6, message: "密码至少6位", trigger: "blur" },
  ],
};

// 管理员注册校验规则
const adminRegisterRules: FormRules = {
  username: [{ required: true, message: "请输入用户名", trigger: "blur" }],
  email: [
    { required: true, message: "请输入邮箱", trigger: "blur" },
    { type: "email", message: "请输入有效的邮箱地址", trigger: "blur" },
  ],
  password: [
    { required: true, message: "请输入密码", trigger: "blur" },
    { min: 6, message: "密码至少6位", trigger: "blur" },
  ],
  admin_code: [{ required: true, message: "请输入管理员注册码", trigger: "blur" }],
};

// 切换 Tab 重置状态
function handleTabChange() {
  isRegister.value = false;
}

// 用户登录
async function handleUserLogin() {
  const valid = await userLoginFormRef.value?.validate().catch(() => false);
  if (!valid) return;
  const ok = await auth.login(userLoginForm.username, userLoginForm.password, true);
  if (ok && auth.isAdmin) {
    ElMessage.error("该账号是管理员，请使用管理员登录");
    auth.logout(true);
  } else if (ok) {
    ElMessage.success("登录成功");
    router.replace("/chat");
  }
}

// 用户注册
async function handleUserRegister() {
  const valid = await userRegFormRef.value?.validate().catch(() => false);
  if (!valid) return;
  const ok = await auth.register({
    username: userRegForm.username,
    email: userRegForm.email,
    password: userRegForm.password,
    display_name: userRegForm.display_name || undefined,
  });
  if (ok) {
    router.replace("/chat");
  }
}

// 管理员登录
async function handleAdminLogin() {
  const valid = await adminLoginFormRef.value?.validate().catch(() => false);
  if (!valid) return;
  const ok = await auth.login(adminLoginForm.username, adminLoginForm.password, true);
  if (ok && auth.isAdmin) {
    ElMessage.success("登录成功");
    router.replace("/admin/users");
  } else if (ok && !auth.isAdmin) {
    ElMessage.error("该账号不是管理员，请使用用户登录");
    auth.logout(true);
  }
}

// 管理员注册
async function handleAdminRegister() {
  const valid = await adminRegFormRef.value?.validate().catch(() => false);
  if (!valid) return;
  const ok = await auth.registerAdmin({
    username: adminRegForm.username,
    email: adminRegForm.email,
    password: adminRegForm.password,
    display_name: adminRegForm.display_name || undefined,
    admin_code: adminRegForm.admin_code,
  });
  if (ok) {
    router.replace("/admin/users");
  }
}
</script>

<style scoped>
.login-container {
  height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
}
.login-card {
  width: 420px;
  text-align: center;
}
.login-card h2 {
  margin-bottom: 4px;
}
.subtitle {
  color: #909399;
  margin-bottom: 8px;
}
.login-tabs {
  margin-bottom: 8px;
}
.toggle-text {
  margin-top: 12px;
  font-size: 13px;
  color: #909399;
}
</style>
