<template>
  <div class="login-container">
    <el-card class="login-card">
      <h2>AI Agent Platform</h2>
      <p class="subtitle">企业级 AI Agent 部署平台</p>
      <el-form>
        <el-form-item>
          <el-input placeholder="用户名" />
        </el-form-item>
        <el-form-item>
          <el-input type="password" placeholder="密码" show-password />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" style="width: 100%">登 录</el-button>
        </el-form-item>
      </el-form>
    </el-card>
  </div>
</template>

<style scoped>
.login-container {
  height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
}
.login-card {
  width: 400px;
  text-align: center;
}
.login-card h2 {
  margin-bottom: 4px;
}
.subtitle {
  color: #909399;
  margin-bottom: 24px;
}
</style>
