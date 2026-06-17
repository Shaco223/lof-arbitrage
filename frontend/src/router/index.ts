import { createRouter, createWebHashHistory, type RouteRecordRaw } from 'vue-router'

// 路由表：默认进入套利看板
const routes: RouteRecordRaw[] = [
  { path: '/', redirect: '/dashboard' },
  {
    path: '/dashboard',
    name: 'Dashboard',
    component: () => import('@/views/DashboardView.vue'),
    meta: { title: '套利看板' }
  },
  {
    path: '/funds',
    name: 'Funds',
    component: () => import('@/views/FundsView.vue'),
    meta: { title: '基金列表' }
  },
  {
    path: '/signals',
    name: 'Signals',
    component: () => import('@/views/SignalsView.vue'),
    meta: { title: '套利信号' }
  },
  {
    path: '/settings',
    name: 'Settings',
    component: () => import('@/views/SettingsView.vue'),
    meta: { title: '监控设置' }
  },
  {
    path: '/:pathMatch(.*)*',
    redirect: '/dashboard'
  }
]

const router = createRouter({
  history: createWebHashHistory(),
  routes,
  scrollBehavior: () => ({ top: 0 })
})

router.afterEach((to) => {
  const title = (to.meta?.title as string) || ''
  document.title = title ? `${title} | LOF 套利监控` : 'LOF 套利监控'
})

export default router
