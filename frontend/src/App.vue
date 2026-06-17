<script setup lang="ts">
// 应用根组件：左侧菜单 + 右侧内容
import { ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'

const router = useRouter()
const route = useRoute()
const collapsed = ref(false)

const handleSelect = (index: string) => {
  router.push(index)
}
</script>

<template>
  <el-container class="layout">
    <el-aside :width="collapsed ? '64px' : '220px'" class="aside">
      <div class="logo">
        <span v-if="!collapsed">LOF 套利监控</span>
        <span v-else>LOF</span>
      </div>
      <el-menu
        :default-active="route.path"
        :collapse="collapsed"
        background-color="#001529"
        text-color="#cfd8dc"
        active-text-color="#ffd04b"
        router
        @select="handleSelect"
      >
        <el-menu-item index="/dashboard">
          <el-icon><Histogram /></el-icon>
          <template #title>套利看板</template>
        </el-menu-item>
        <el-menu-item index="/funds">
          <el-icon><Tickets /></el-icon>
          <template #title>基金列表</template>
        </el-menu-item>
        <el-menu-item index="/signals">
          <el-icon><Bell /></el-icon>
          <template #title>套利信号</template>
        </el-menu-item>
        <el-menu-item index="/settings">
          <el-icon><Setting /></el-icon>
          <template #title>监控设置</template>
        </el-menu-item>
      </el-menu>
    </el-aside>

    <el-container>
      <el-header class="header">
        <el-button text @click="collapsed = !collapsed">
          <el-icon size="20">
            <Fold v-if="!collapsed" />
            <Expand v-else />
          </el-icon>
        </el-button>
        <div class="header-title">LOF 基金折溢价套利信息平台</div>
        <div class="header-right">
          <el-tag type="success" effect="dark">实时数据</el-tag>
        </div>
      </el-header>
      <el-main class="main">
        <router-view v-slot="{ Component }">
          <transition name="fade" mode="out-in">
            <component :is="Component" />
          </transition>
        </router-view>
      </el-main>
    </el-container>
  </el-container>
</template>

<style scoped>
.layout {
  height: 100vh;
}
.aside {
  background-color: #001529;
  transition: width 0.2s ease;
}
.logo {
  height: 56px;
  line-height: 56px;
  text-align: center;
  color: #fff;
  font-weight: 600;
  letter-spacing: 1px;
  background-color: #002140;
}
.header {
  background: #fff;
  border-bottom: 1px solid #eaecef;
  display: flex;
  align-items: center;
  gap: 16px;
}
.header-title {
  font-size: 16px;
  font-weight: 600;
  color: #303133;
}
.header-right {
  margin-left: auto;
}
.main {
  background: #f5f7fa;
  padding: 16px;
  overflow: auto;
}
.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.18s ease;
}
.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}
</style>
