<script setup lang="ts">
// Dashboard：简洁版排版（v2）—— 核心信息：行=代码/类型/名称 + 现价/IOPV + 估算/净值溢价
// PRD §6 字段保持不变；新字段缺失时不渲染（AC-P5）
import { computed, onMounted, onUnmounted, ref } from 'vue'
import { onPullDownRefresh } from '@dcloudio/uni-app'
import { getLofList } from '@/api'
import type { FundType, ListParams, LofListItem } from '@/api/types'
import {
  fmtNum,
  fmtPct,
  fmtPctSigned,
  fmtVolumeWan,
  freshnessLabel,
  coverageLevel,
  isMarketOpen,
  shouldRender
} from '@/utils/format'
import { isLowLiquidity } from '@/utils/low-liquidity'
import { useSettingsStore } from '@/store/settings'

const settings = useSettingsStore()
const isMockMode = String(import.meta.env.VITE_USE_MOCK).toLowerCase() === 'true'
const apiBase = String(import.meta.env.VITE_API_BASE || '')
const loading = ref(false)
const error = ref('')
const list = ref<LofListItem[]>([])
const lastTs = ref('')
const nowTick = ref(Date.now())
const sort = ref<ListParams['sort']>('premium_desc')
const type = ref<ListParams['type']>('all')

let pollTimer: ReturnType<typeof setInterval> | undefined
let clockTimer: ReturnType<typeof setInterval> | undefined

const typeTabs: Array<{ label: string; value: ListParams['type'] }> = [
  { label: '全部', value: 'all' },
  { label: '指数', value: 'index' },
  { label: '行业', value: 'industry' },
  { label: '主动', value: 'active' }
]

const sortTabs: Array<{ label: string; value: ListParams['sort'] }> = [
  { label: '溢价↓', value: 'premium_desc' },
  { label: '溢价↑', value: 'premium_asc' },
  { label: '代码', value: 'code' }
]

const highSignalCount = computed(() =>
  list.value.filter((item) => signalType(item) !== 'none').length
)

const interfaceModeText = computed(() => {
  if (isMockMode) return 'mock'
  return apiBase.includes('127.0.0.1') ? '本地真实' : 'uniCloud'
})

const refreshText = computed(() => {
  nowTick.value
  return lastTs.value ? freshnessLabel(lastTs.value) : '尚未刷新'
})

const marketOpen = computed(() => {
  nowTick.value
  return isMarketOpen()
})

function typeLabel(value: FundType) {
  return value === 'index' ? '指数' : value === 'industry' ? '行业' : '主动'
}

function signalType(item: LofListItem): 'premium' | 'discount' | 'none' {
  if (item.premium >= settings.premiumThreshold) return 'premium'
  if (item.premium <= -settings.discountThreshold) return 'discount'
  return 'none'
}

function showLowLiquidity(item: LofListItem): boolean {
  if (item.status === 'active_low_liquidity') return true
  if (item.status === 'active') return false
  return isLowLiquidity(item.code)
}

// PRD 1.3：Dashboard 仅在代码旁显示一个简短申购限制标记（不挤额度数字，详情页看具体额度）
// limited -> '限购'；suspended -> '暂停'；closed -> '停售'；open/unknown -> 空（AC-P5 不渲染）
function subscribeBadge(item: LofListItem): string {
  const st = item.subscribe_status
  if (st === 'limited') return '限购'
  if (st === 'suspended') return '暂停'
  if (st === 'closed') return '停售'
  return ''
}

async function loadList(showToast = false) {
  loading.value = true
  error.value = ''
  try {
    const data = await getLofList({ sort: sort.value, type: type.value })
    list.value = data.items
    lastTs.value = data.ts
    if (showToast) uni.showToast({ title: '已刷新', icon: 'success' })
  } catch (err) {
    error.value = err instanceof Error ? err.message : '列表加载失败'
  } finally {
    loading.value = false
    uni.stopPullDownRefresh()
  }
}

function changeType(value: ListParams['type']) {
  type.value = value
  loadList()
}

function changeSort(value: ListParams['sort']) {
  sort.value = value
  loadList()
}

function goDetail(code: string) {
  uni.navigateTo({ url: `/pages/detail/detail?code=${code}` })
}

onPullDownRefresh(() => loadList(true))

onMounted(() => {
  loadList()
  pollTimer = setInterval(() => loadList(), settings.pollIntervalMs)
  clockTimer = setInterval(() => {
    nowTick.value = Date.now()
  }, 1000)
})

onUnmounted(() => {
  if (pollTimer) clearInterval(pollTimer)
  if (clockTimer) clearInterval(clockTimer)
})
</script>

<template>
  <view class="page">
    <!-- 顶部状态条：信号数 + 接口模式 + 最近刷新 + 交易状态 -->
    <view class="topbar">
      <view class="topbar-left">
        <text class="signal-num">{{ highSignalCount }}</text>
        <text class="signal-label">信号</text>
      </view>
      <view class="topbar-right">
        <text class="meta-pill" :class="marketOpen ? 'pill-open' : 'pill-closed'">{{ marketOpen ? '交易中' : '休市' }}</text>
        <text class="meta-pill pill-mode">{{ interfaceModeText }}</text>
        <text class="meta-pill pill-refresh">{{ refreshText }}</text>
        <button class="refresh-btn" :loading="loading" @tap="loadList(true)">刷新</button>
      </view>
    </view>

    <!-- 筛选 + 排序：合并为单行可滚动 -->
    <view class="filter">
      <scroll-view class="chips" scroll-x>
        <view
          v-for="tab in typeTabs"
          :key="'t-' + tab.value"
          class="chip"
          :class="{ active: type === tab.value }"
          @tap="changeType(tab.value)"
        >{{ tab.label }}</view>
        <view class="chip-divider"></view>
        <view
          v-for="tab in sortTabs"
          :key="'s-' + tab.value"
          class="chip"
          :class="{ active: sort === tab.value }"
          @tap="changeSort(tab.value)"
        >{{ tab.label }}</view>
      </scroll-view>
    </view>

    <!-- 状态提示：仅 loading / error 时显示 -->
    <view v-if="loading && list.length === 0" class="state state-loading">正在读取数据…</view>
    <view v-if="error" class="state state-error">列表加载失败：{{ error }}</view>

    <!-- 列表 -->
    <view class="list">
      <view class="list-head">
        <text class="col-name">基金</text>
        <text class="col-num">现价</text>
        <text class="col-num">IOPV</text>
        <text class="col-rate">溢价</text>
      </view>

      <view
        v-for="item in list"
        :key="item.code"
        class="row"
        :class="[`signal-${signalType(item)}`]"
        @tap="goDetail(item.code)"
      >
        <view class="row-main">
          <view class="row-line1">
            <text class="code">{{ item.code }}</text>
            <text class="type-tag" :class="`type-${item.type}`">{{ typeLabel(item.type) }}</text>
            <text v-if="subscribeBadge(item)" class="sub-badge">{{ subscribeBadge(item) }}</text>
            <text v-if="showLowLiquidity(item)" class="low-liquidity-dot" title="低流动性"></text>
          </view>
          <view class="row-line2">{{ item.name }}</view>
          <view class="row-line3">
            <text v-if="shouldRender(item.price_change_pct)" :class="(item.price_change_pct ?? 0) >= 0 ? 'text-up' : 'text-down'">
              {{ fmtPctSigned(item.price_change_pct, 2) }}
            </text>
            <text v-if="shouldRender(item.volume_amount)" class="meta-text">{{ fmtVolumeWan(item.volume_amount) }}</text>
            <text v-if="item.source_quality && item.source_quality !== 'ok'" class="meta-text quality-warn">
              {{ item.source_quality === 'stale' ? '滞后' : '降级' }}
            </text>
          </view>
        </view>
        <text class="cell-num">{{ fmtNum(item.price, 3) }}</text>
        <text class="cell-num">{{ fmtNum(item.iopv, 3) }}</text>
        <view class="cell-premium">
          <text class="p-main" :class="item.premium >= 0 ? 'text-up' : 'text-down'">{{ fmtPct(item.premium, 2) }}</text>
          <text
            v-if="shouldRender(item.premium_nav)"
            class="p-sub"
            :class="(item.premium_nav ?? 0) >= 0 ? 'text-up' : 'text-down'"
          >净 {{ fmtPct(item.premium_nav, 2) }}</text>
        </view>
      </view>

      <view v-if="!loading && !error && list.length === 0" class="empty">暂无数据，请确认本地真实 API 已启动。</view>
    </view>
  </view>
</template>

<style scoped lang="scss">
.page { padding: 16rpx 20rpx 48rpx; }

/* 顶部状态条 */
.topbar { display: flex; align-items: center; justify-content: space-between; gap: 16rpx; padding: 18rpx 24rpx; background: #fff; border-radius: 14rpx; margin-bottom: 16rpx; box-shadow: 0 2rpx 8rpx rgba(0, 21, 41, 0.04); }
.topbar-left { display: flex; align-items: baseline; gap: 8rpx; }
.signal-num { font-size: 44rpx; font-weight: 700; color: #f56c6c; line-height: 1; }
.signal-label { color: #909399; font-size: 22rpx; }
.topbar-right { display: flex; align-items: center; gap: 8rpx; flex-wrap: wrap; justify-content: flex-end; }
.meta-pill { padding: 4rpx 14rpx; border-radius: 999rpx; font-size: 22rpx; color: #606266; background: #f5f7fa; }
.pill-open { color: #67c23a; background: #f0f9eb; }
.pill-closed { color: #e6a23c; background: #fdf6ec; }
.pill-mode { color: #1f6feb; background: #f0f7ff; }
.pill-refresh { color: #909399; }
.refresh-btn { margin: 0; padding: 0 22rpx; height: 56rpx; line-height: 56rpx; font-size: 22rpx; color: #fff; background: #1f2d3d; border-radius: 28rpx; }

/* 筛选条 */
.filter { margin-bottom: 16rpx; }
.chips { white-space: nowrap; padding: 6rpx 0; }
.chip { display: inline-block; padding: 10rpx 22rpx; margin-right: 12rpx; border-radius: 999rpx; background: #fff; color: #606266; font-size: 24rpx; border: 1rpx solid #ebeef5; }
.chip.active { background: #1f2d3d; color: #fff; border-color: #1f2d3d; }
.chip-divider { display: inline-block; width: 1rpx; height: 28rpx; background: #ebeef5; margin: 0 12rpx 0 0; vertical-align: middle; }

/* 状态条 */
.state { padding: 16rpx 24rpx; border-radius: 12rpx; font-size: 24rpx; margin-bottom: 16rpx; }
.state-loading { color: #409eff; background: #ecf5ff; }
.state-error { color: #f56c6c; background: #fef0f0; }

/* 列表 */
.list { background: #fff; border-radius: 14rpx; padding: 0 24rpx; box-shadow: 0 2rpx 8rpx rgba(0, 21, 41, 0.04); }
.list-head { display: grid; grid-template-columns: 1fr 110rpx 110rpx 150rpx; gap: 8rpx; color: #909399; font-size: 22rpx; padding: 18rpx 0 12rpx; border-bottom: 1rpx solid #ebeef5; }
.col-num, .col-rate { text-align: right; }
.row { display: grid; grid-template-columns: 1fr 110rpx 110rpx 150rpx; gap: 8rpx; align-items: center; padding: 22rpx 0; border-bottom: 1rpx solid #f5f7fa; }
.row:last-child { border-bottom: 0; }
.row.signal-premium { background: linear-gradient(90deg, rgba(245,108,108,0.06), transparent 60%); margin: 0 -12rpx; padding-left: 12rpx; padding-right: 12rpx; border-radius: 10rpx; }
.row.signal-discount { background: linear-gradient(90deg, rgba(103,194,58,0.06), transparent 60%); margin: 0 -12rpx; padding-left: 12rpx; padding-right: 12rpx; border-radius: 10rpx; }

.row-main { display: flex; flex-direction: column; gap: 8rpx; min-width: 0; }
.row-line1 { display: flex; align-items: center; gap: 10rpx; }
.code { font-size: 26rpx; font-weight: 700; color: #1f2d3d; letter-spacing: 0.5rpx; }
.type-tag { padding: 2rpx 10rpx; border-radius: 4rpx; font-size: 20rpx; }
.type-index { background: #ecf5ff; color: #409eff; }
.type-industry { background: #fdf6ec; color: #e6a23c; }
.type-active { background: #f0f9eb; color: #67c23a; }
.sub-badge { padding: 2rpx 10rpx; border-radius: 4rpx; font-size: 20rpx; background: #fef0f0; color: #f56c6c; }
.low-liquidity-dot { width: 12rpx; height: 12rpx; border-radius: 6rpx; background: #1f6feb; display: inline-block; }
.row-line2 { font-size: 26rpx; color: #303133; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.row-line3 { display: flex; flex-wrap: wrap; gap: 14rpx; color: #909399; font-size: 22rpx; }
.meta-text { color: #909399; }
.quality-warn { color: #e6a23c; }

.cell-num { text-align: right; font-size: 26rpx; color: #303133; }
.cell-premium { display: flex; flex-direction: column; align-items: flex-end; gap: 4rpx; }
.p-main { font-size: 30rpx; font-weight: 700; }
.p-sub { font-size: 20rpx; opacity: 0.85; }

.empty { padding: 64rpx 24rpx; text-align: center; color: #909399; font-size: 24rpx; }
</style>
