<template>
  <el-dialog
    :model-value="visible"
    @update:model-value="$emit('update:visible', $event)"
    :title="mode === 'create' ? '新建知识库' : '编辑 Embedding 配置'"
    width="520px"
    @close="mode === 'create' && $emit('reset')"
  >
    <el-form :model="form" label-width="100px">
      <template v-if="mode === 'create'">
        <el-form-item label="名称">
          <el-input v-model="form.name" placeholder="请输入知识库名称" />
        </el-form-item>
        <el-form-item label="描述">
          <el-input v-model="form.description" type="textarea" placeholder="请输入描述（可选）" />
        </el-form-item>
        <el-divider content-position="left">Embedding 配置</el-divider>
      </template>
      <el-form-item label="嵌入模型">
        <el-select v-model="form.embedding_model" style="width: 100%">
          <el-option label="text-embedding-v4" value="text-embedding-v4" />
        </el-select>
      </el-form-item>
      <el-form-item label="API Key">
        <el-input
          v-model="form.embedding_api_key"
          type="password"
          show-password
          :placeholder="apiPlaceholder"
        />
      </el-form-item>
      <el-form-item label="Base URL">
        <el-input v-model="form.embedding_base_url" placeholder="留空使用默认地址" />
      </el-form-item>
    </el-form>
    <template #footer>
      <el-button @click="$emit('update:visible', false)">取消</el-button>
      <el-button type="primary" @click="$emit('submit')" :loading="loading">
        {{ mode === 'create' ? '确定' : '保存' }}
      </el-button>
    </template>
  </el-dialog>
</template>

<script setup lang="ts">
defineProps<{
  visible: boolean;
  mode: "create" | "edit";
  form: any;
  loading: boolean;
  apiPlaceholder?: string;
}>();

defineEmits<{
  "update:visible": [value: boolean];
  submit: [];
  reset: [];
}>();
</script>
