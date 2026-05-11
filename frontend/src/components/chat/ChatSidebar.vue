<template>
  <div class="chat-sidebar">
    <div class="sidebar-header">
      <el-button type="primary" @click="$emit('createAgent')" :icon="Plus">
        新建智能体
      </el-button>
    </div>
    <div class="sidebar-body" v-loading="agentStore.loading">
      <div
        v-for="agent in agentStore.agents"
        :key="agent.id"
        class="agent-group"
        :class="{ expanded: agentStore.currentAgent?.id === agent.id }"
      >
        <div class="agent-item" @click="$emit('selectAgent', agent.id)">
          <div class="agent-avatar">
            <el-avatar :size="28" :src="agent.avatar">
              {{ agent.name.charAt(0) }}
            </el-avatar>
          </div>
          <div class="agent-info">
            <div class="agent-name">{{ agent.name }}</div>
            <div class="agent-meta">
              {{ agent.provider ? agent.provider + '/' + agent.model_name : '未配置模型' }}
            </div>
          </div>
          <div class="agent-actions" @click.stop>
            <el-button text size="small" @click="$emit('editAgent', agent)">
              <el-icon><Setting /></el-icon>
            </el-button>
            <el-button text size="small" type="danger" @click="$emit('deleteAgent', agent.id)">
              <el-icon><Delete /></el-icon>
            </el-button>
          </div>
        </div>
        <div v-if="agentStore.currentAgent?.id === agent.id" class="conv-sublist">
          <div class="conv-sublist-header">
            <span>对话列表</span>
            <el-button text size="small" type="primary" @click="$emit('createConv')">
              <el-icon><Plus /></el-icon>
            </el-button>
          </div>
          <div
            v-for="conv in agentStore.conversations"
            :key="conv.id"
            class="conv-item"
            :class="{ active: currentConvId === conv.id }"
            @click="$emit('selectConv', conv.id)"
          >
            <div class="conv-title">{{ conv.title }}</div>
            <div class="conv-meta">{{ conv.message_count }} 条消息</div>
            <span class="conv-delete" @click.stop>
              <el-button text type="danger" size="small" @click="$emit('deleteConv', conv.id)">
                <el-icon><Delete /></el-icon>
              </el-button>
            </span>
          </div>
          <el-empty v-if="agentStore.conversations.length === 0" description="暂无对话" :image-size="48" />
        </div>
      </div>
      <el-empty v-if="!agentStore.loading && agentStore.agents.length === 0" description="暂无智能体，点击上方按钮创建" />
    </div>
  </div>
</template>

<script setup lang="ts">
import { Plus, Delete, Setting } from "@element-plus/icons-vue";
import { useAgentStore } from "@/stores/agent";
import type { Agent } from "@/types";

defineProps<{
  currentConvId?: string;
}>();

defineEmits<{
  createAgent: [];
  selectAgent: [id: string];
  editAgent: [agent: Agent];
  deleteAgent: [id: string];
  createConv: [];
  selectConv: [id: string];
  deleteConv: [id: string];
}>();

const agentStore = useAgentStore();
</script>

<style scoped>
.chat-sidebar {
  width: 320px;
  border-right: 1px solid #e4e7ed;
  display: flex;
  flex-direction: column;
}

.sidebar-header {
  padding: 12px;
  border-bottom: 1px solid #e4e7ed;
}

.sidebar-header .el-button {
  width: 100%;
}

.sidebar-body {
  flex: 1;
  overflow-y: auto;
}

.agent-group {
  border-bottom: 1px solid #f0f2f5;
}

.agent-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px 12px;
  cursor: pointer;
  transition: background 0.15s;
}

.agent-item:hover {
  background: #f0f2f5;
}

.agent-group.expanded .agent-item {
  background: #ecf5ff;
}

.agent-avatar {
  flex-shrink: 0;
}

.agent-info {
  flex: 1;
  min-width: 0;
}

.agent-name {
  font-size: 14px;
  font-weight: 500;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.agent-meta {
  font-size: 12px;
  color: #909399;
  margin-top: 2px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.agent-actions {
  flex-shrink: 0;
  opacity: 0;
  display: flex;
  gap: 2px;
}

.agent-item:hover .agent-actions {
  opacity: 1;
}

.conv-sublist {
  background: #fafbfc;
  padding: 0 0 8px 0;
}

.conv-sublist-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 6px 12px 6px 44px;
  font-size: 12px;
  color: #909399;
}

.conv-item {
  padding: 8px 12px 8px 44px;
  cursor: pointer;
  position: relative;
  font-size: 13px;
  transition: background 0.15s;
}

.conv-item:hover {
  background: #f0f2f5;
}

.conv-item.active {
  background: #d9ecff;
}

.conv-title {
  font-size: 13px;
  font-weight: 500;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  padding-right: 28px;
}

.conv-meta {
  font-size: 11px;
  color: #909399;
  margin-top: 2px;
}

.conv-delete {
  position: absolute;
  right: 4px;
  top: 50%;
  transform: translateY(-50%);
  opacity: 0;
}

.conv-item:hover .conv-delete {
  opacity: 1;
}
</style>
