<script setup lang="ts">
// Dashboard：30 只 LOF 实时排行，接口结构严格按 PRD §6（PRD 1.2 字段对齐升级）。
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
  coverageLevelLabel,
  isMarketOpen,
  shouldRender
} from '@/utils/format'
import { isLowLiquidity, LOW_LIQUIDITY_LABEL } from '@/utils/low-liquidity'
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
  { label: '溢价降序', value: 'premium_desc' },
  { label: '溢价升序', value: 'premium_asc' },
  { label: '代码', value: 'code' }
]

const highSignalCount = computed(() =>
  list.value.filter((item) => signalType(item) !== 'none').length
)

const premiumSignalCount = computed(() =>
  list.value.filter((item) => signalType(item) === 'premium').length
)

const discountSignalCount = computed(() =>
  list.value.filter((item) => signalType(item) === 'discount').length
)

const interfaceModeText = computed(() => {
  if (isMockMode) return 'mock'
  return apiBase.includes('127.0.0.1') ? '本地真实 API' : '真实 uniCloud'
})

const marketStatusText = computed(() => {
  nowTick.value
  return isMarketOpen() ? '交易时段：信号按 60s 刷新' : '非交易时段，数据可能滞后'
})

const refreshText = computed(() => {
  nowTick.value
  return lastTs.value ? `上次刷新 ${freshnessLabel(lastTs.value)}` : '尚未刷新'
})

function typeLabel(value: FundType) {
  return value === 'index' ? '指数' : value === 'industry' ? '行业' : '主动'
}

function sourceQualityLabel(value: LofListItem['source_quality']) {
  if (value === 'stale') return '数据滞后，不可盲用'
  if (value === 'degraded') return '数据降级，不可盲用'
  if (value === 'ok') return '正常'
  return ''
}

function sourceQualityClass(value: LofListItem['source_quality']) {
  if (value === 'stale') return 'quality-stale'
  if (value === 'degraded') return 'quality-degraded'
  return 'quality-ok'
}

function signalType(item: LofListItem): 'premium' | 'discount' | 'none' {
  if (item.premium >= settings.premiumThreshold) return 'premium'
  if (item.premium <= -settings.discountThreshold) return 'discount'
  return 'none'
}

function signalLabel(item: LofListItem) {
  const t = signalType(item)
  if (t === 'premium') return '高溢价'
  if (t === 'discount') return '高折价'
  return ''
}

/**
 * 低流动性优先读后端真实 status 字段；缺失/不识别时回退本地名单。
 * 后端已返真实值，避免双源出现矛盾。
 */
function showLowLiquidity(item: LofListItem): boolean {
  if (item.status === 'active_low_liquidity') return true
  if (item.status === 'active') return false
  return isLowLiquidity(item.code)
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
    <view class="hero card">
      <view class="hero-main">
        <view class="hero-title">LOF 实时溢价监控</view>
        <view class="hero-sub">{{ interfaceModeText }} · 60s 自动轮询 · 手动刷新可用</view>
        <view class="hero-stats">
          <text>信号 {{ highSignalCount }} 个</text>
          <text>溢价 {{ premiumSignalCount }}</text>
          <text>折价 {{ discountSignalCount }}</text>
          <text>{{ refreshText }}</text>
        </view>
        <view class="market-tip" :class="isMarketOpen() ? 'market-open' : 'market-closed'">{{ marketStatusText }}</view>
      </view>
      <view class="hero-badge">
        <text class="badge-num">{{ highSignalCount }}</text>
        <text class="badge-label">信号数量</text>
      </view>
    </view>

    <view class="toolbar card">
      <view class="tabs">
        <view
          v-for="tab in typeTabs"
          :key="tab.value"
          class="tab"
          :class="{ active: type === tab.value }"
          @tap="changeType(tab.value)"
        >{{ tab.label }}</view>
      </view>
      <view class="tabs sort-tabs">
        <view
          v-for="tab in sortTabs"
          :key="tab.value"
          class="tab small"
          :class="{ active: sort === tab.value }"
          @tap="changeSort(tab.value)"
        >{{ tab.label }}</view>
      </view>
      <view class="refresh-line">
        <view class="refresh-copy">
          <text class="text-muted">{{ refreshText }}</text>
          <text class="mode-pill">接口：{{ interfaceModeText }}</text>
          <text class="history-note">历史沉淀：本地优先，线上后置</text>
        </view>
        <button class="mini-btn" :loading="loading" @tap="loadList(true)">{{ error ? '重试' : '手动刷新' }}</button>
      </view>
      <view v-if="loading && list.length === 0" class="state-box loading-box">正在读取本地真实 API 数据...</view>
      <view v-if="error" class="state-box error">列表加载失败：{{ error }}</view>
    </view>

    <view class="list card">
      <view class="table-head">
        <text class="col-name">基金 / 涨跌 / 成交</text>
        <text class="col-num">现价</text>
        <text class="col-num">IOPV</text>
        <text class="col-rate">估算 / 净值溢价</text>
      </view>

      <view
        v-for="item in list"
        :key="item.code"
        class="fund-row"
        :class="[`signal-${signalType(item)}`]"
        @tap="goDetail(item.code)"
      >
        <view class="fund-main">
          <view class="name-line">
            <text class="fund-code">{{ item.code }}</text>
            <text class="type-pill">{{ typeLabel(item.type) }}</text>
            <text v-if="signalType(item) !== 'none'" class="alert-pill" :class="`alert-${signalType(item)}`">{{ signalLabel(item) }}</text>
          </view>
          <view class="fund-name">{{ item.name }}</view>
          <view class="meta-line">
            <text
              v-if="shouldRender(item.price_change_pct)"
              class="chg-pill"
              :class="(item.price_change_pct ?? 0) >= 0 ? 'text-up' : 'text-down'"
            >涨跌 {{ fmtPctSigned(item.price_change_pct, 2) }}</text>
            <text v-if="shouldRender(item.volume_amount)" class="volume-pill">成交 {{ fmtVolumeWan(item.volume_amount) }}</text>
            <text>30天分位 {{ fmtPct(item.pctile_30d, 0) }}</text>
            <text
              class="coverage-pill"
              :class="`coverage-${coverageLevel(item.coverage)}`"
            >覆盖率 {{ fmtPct(item.coverage, 0) }} · {{ coverageLevelLabel(coverageLevel(item.coverage)) }}</text>
            <text class="quality-pill" :class="sourceQualityClass(item.source_quality)">数据 {{ sourceQualityLabel(item.source_quality) || '正常' }}</text>
          </view>
          <view v-if="showLowLiquidity(item)" class="liquidity-line">
            <text class="liquidity-pill">{{ LOW_LIQUIDITY_LABEL }}</text>
          </view>
        </view>
        <view class="quote-grid">
          <text class="quote-cell">{{ fmtNum(item.price, 3) }}</text>
          <text class="quote-cell">{{ fmtNum(item.iopv, 3) }}</text>
          <view class="premium-stack">
            <text :class="['premium-text', item.premium >= 0 ? 'text-up' : 'text-down']">估 {{ fmtPct(item.premium, 2) }}</text>
            <text
              v-if="shouldRender(item.premium_nav)"
              :class="['premium-nav', (item.premium_nav ?? 0) >= 0 ? 'text-up' : 'text-down']"
            >净 {{ fmtPct(item.premium_nav, 2) }}</text>
          </view>
        </view>
      </view>

      <view v-if="!loading && !error && list.length === 0" class="empty">暂无数据，请确认本地真实 API 已启动并返回 PRD §6 列表结构。</view>
    </view>
  </view>
</template>

<style scoped lang="scss">
.page { padding: 24rpx; padding-bottom: 48rpx; }
.hero { display: flex; align-items: center; margin-bottom: 20rpx; }
.hero-main { flex: 1; }
.hero-title { font-size: 40rpx; font-weight: 700; color: #1f2d3d; }
.hero-sub { margin-top: 8rpx; color: #909399; font-size: 24rpx; }
.hero-stats { display: flex; flex-wrap: wrap; gap: 10rpx; margin-top: 14rpx; color: #606266; font-size: 22rpx; }
.hero-stats text { padding: 6rpx 12rpx; border-radius: 999rpx; background: #f5f7fa; }
.market-tip { display: inline-flex; margin-top: 14rpx; padding: 8rpx 14rpx; border-radius: 12rpx; font-size: 22rpx; }
.market-open { color: #67c23a; background: #f0f9eb; }
.market-closed { color: #e6a23c; background: #fdf6ec; }
.hero-badge { width: 140rpx; height: 140rpx; border-radius: 70rpx; background: linear-gradient(135deg, #f56c6c, #e6a23c); color: #fff; display: flex; flex-direction: column; align-items: center; justify-content: center; box-shadow: 0 10rpx 24rpx rgba(245, 108, 108, 0.22); }
.badge-num { font-size: 42rpx; font-weight: 700; line-height: 48rpx; }
.badge-label { font-size: 22rpx; }
.toolbar { margin-bottom: 20rpx; }
.tabs { display: flex; flex-wrap: wrap; gap: 12rpx; }
.sort-tabs { margin-top: 16rpx; }
.tab { padding: 12rpx 24rpx; border-radius: 999rpx; background: #f5f7fa; color: #606266; font-size: 26rpx; }
.tab.small { font-size: 24rpx; padding: 10rpx 20rpx; }
.tab.active { background: #1f2d3d; color: #fff; }
.refresh-line { display: flex; align-items: center; justify-content: space-between; margin-top: 18rpx; }
.refresh-copy { display: flex; flex-direction: column; gap: 8rpx; }
.mode-pill { align-self: flex-start; padding: 4rpx 10rpx; border-radius: 999rpx; background: #ecf5ff; color: #409eff; font-size: 22rpx; }
.history-note { color: #909399; font-size: 22rpx; }
.mini-btn { margin: 0; padding: 0 24rpx; height: 62rpx; line-height: 62rpx; font-size: 24rpx; color: #fff; background: #1f2d3d; }
.state-box { margin-top: 16rpx; padding: 18rpx; border-radius: 14rpx; font-size: 24rpx; }
.loading-box { color: #409eff; background: #ecf5ff; }
.error { color: #f56c6c; background: #fef0f0; }
.table-head { display: grid; grid-template-columns: 1fr 100rpx 100rpx 160rpx; gap: 8rpx; color: #909399; font-size: 22rpx; padding-bottom: 16rpx; border-bottom: 1rpx solid #ebeef5; }
.col-num, .col-rate { text-align: right; }
.fund-row { display: grid; grid-template-columns: 1fr 360rpx; gap: 12rpx; padding: 22rpx 0; border-bottom: 1rpx solid #f0f2f5; }
.fund-row.signal-premium, .fund-row.signal-discount { position: relative; margin: 0 -10rpx; padding-left: 10rpx; padding-right: 10rpx; border-radius: 18rpx; }
.fund-row.signal-premium { background: #fff7f7; box-shadow: inset 0 0 0 2rpx #fde2e2; }
.fund-row.signal-discount { background: #f0f9eb; box-shadow: inset 0 0 0 2rpx #e1f3d8; }
.fund-row.signal-premium::before, .fund-row.signal-discount::before { content: ''; position: absolute; left: -4rpx; top: 22rpx; bottom: 22rpx; width: 8rpx; border-radius: 8rpx; }
.fund-row.signal-premium::before { background: #f56c6c; }
.fund-row.signal-discount::before { background: #67c23a; }
.name-line { display: flex; align-items: center; gap: 8rpx; }
.fund-code { font-weight: 700; color: #1f2d3d; }
.type-pill, .alert-pill, .coverage-pill, .quality-pill, .chg-pill, .volume-pill { display: inline-flex; padding: 4rpx 10rpx; border-radius: 999rpx; font-size: 20rpx; }
.type-pill { background: #edf2fc; color: #409eff; }
.alert-pill { font-weight: 700; }
.alert-premium { background: #fef0f0; color: #f56c6c; }
.alert-discount { background: #f0f9eb; color: #67c23a; }
.fund-name { margin-top: 8rpx; color: #303133; font-size: 28rpx; }
.meta-line { display: flex; flex-wrap: wrap; gap: 10rpx; margin-top: 10rpx; color: #909399; font-size: 22rpx; }
.coverage-green { background: #f0f9eb; color: #67c23a; }
.coverage-yellow { background: #fdf6ec; color: #e6a23c; }
.coverage-red { background: #fef0f0; color: #f56c6c; }
.quality-ok { background: #f4f4f5; color: #606266; }
.quality-degraded { background: #fdf6ec; color: #e6a23c; }
.quality-stale { background: #fef0f0; color: #f56c6c; }
.chg-pill { background: #f5f7fa; }
.chg-pill.text-up { background: #fef0f0; color: #f56c6c; }
.chg-pill.text-down { background: #f0f9eb; color: #67c23a; }
.volume-pill { background: #f0f7ff; color: #1f6feb; }
.liquidity-line { margin-top: 8rpx; }
.liquidity-pill { display: inline-flex; padding: 4rpx 10rpx; border-radius: 999rpx; font-size: 20rpx; background: #f0f7ff; color: #1f6feb; border: 1rpx solid #c8dcff; }
.quote-grid { display: grid; grid-template-columns: repeat(3, 1fr); align-items: center; gap: 8rpx; text-align: right; font-size: 26rpx; }
.quote-cell { align-self: center; }
.premium-stack { display: flex; flex-direction: column; align-items: flex-end; gap: 4rpx; }
.premium-text { font-size: 28rpx; font-weight: 700; }
.premium-nav { font-size: 22rpx; opacity: 0.85; }
.empty { padding: 48rpx 24rpx; text-align: center; color: #909399; background: #fafafa; border-radius: 16rpx; }
</style>
