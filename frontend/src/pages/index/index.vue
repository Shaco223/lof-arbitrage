<script setup lang="ts">
// Dashboard：30 只 LOF 实时排行（mock 阶段精简池，接口结构严格按 PRD §6）
import { computed, onMounted, onUnmounted, ref } from 'vue'
import { onPullDownRefresh } from '@dcloudio/uni-app'
import { getLofList } from '@/api'
import type { FundType, ListParams, LofListItem } from '@/api/types'
import { fmtNum, fmtPct, freshnessLabel, coverageLevel, coverageLevelLabel } from '@/utils/format'
import { useSettingsStore } from '@/store/settings'

const settings = useSettingsStore()
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
  list.value.filter((item) => isAlert(item)).length
)

const refreshText = computed(() => {
  nowTick.value
  return lastTs.value ? `上次刷新 ${freshnessLabel(lastTs.value)}` : '尚未刷新'
})

function typeLabel(value: FundType) {
  return value === 'index' ? '指数' : value === 'industry' ? '行业' : '主动'
}

function isAlert(item: LofListItem) {
  return item.premium >= settings.premiumThreshold || item.premium <= -settings.discountThreshold
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
        <view class="hero-sub">按 PRD §6 mock 接口运行，60s 自动轮询</view>
      </view>
      <view class="hero-badge">
        <text class="badge-num">{{ highSignalCount }}</text>
        <text class="badge-label">触阈值</text>
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
        <text class="text-muted">{{ refreshText }}</text>
        <button class="mini-btn" :loading="loading" @tap="loadList(true)">重试/刷新</button>
      </view>
      <view v-if="error" class="error">{{ error }}</view>
    </view>

    <view class="list card">
      <view class="table-head">
        <text class="col-name">基金</text>
        <text class="col-num">现价</text>
        <text class="col-num">IOPV</text>
        <text class="col-rate">溢价</text>
      </view>

      <view
        v-for="item in list"
        :key="item.code"
        class="fund-row"
        :class="{ alert: isAlert(item) }"
        @tap="goDetail(item.code)"
      >
        <view class="fund-main">
          <view class="name-line">
            <text class="fund-code">{{ item.code }}</text>
            <text class="type-pill">{{ typeLabel(item.type) }}</text>
            <text v-if="isAlert(item)" class="alert-pill">触阈值</text>
          </view>
          <view class="fund-name">{{ item.name }}</view>
          <view class="meta-line">
            <text>30天分位 {{ fmtPct(item.pctile_30d, 0) }}</text>
            <text
              class="coverage-pill"
              :class="`coverage-${coverageLevel(item.coverage)}`"
            >覆盖率 {{ fmtPct(item.coverage, 0) }} · {{ coverageLevelLabel(coverageLevel(item.coverage)) }}</text>
          </view>
        </view>
        <view class="quote-grid">
          <text>{{ fmtNum(item.price, 3) }}</text>
          <text>{{ fmtNum(item.iopv, 3) }}</text>
          <text :class="item.premium >= 0 ? 'text-up' : 'text-down'">{{ fmtPct(item.premium, 2) }}</text>
        </view>
      </view>

      <view v-if="!loading && list.length === 0" class="empty">暂无数据</view>
    </view>
  </view>
</template>

<style scoped lang="scss">
.page { padding: 24rpx; padding-bottom: 48rpx; }
.hero { display: flex; align-items: center; margin-bottom: 20rpx; }
.hero-main { flex: 1; }
.hero-title { font-size: 40rpx; font-weight: 700; color: #1f2d3d; }
.hero-sub { margin-top: 8rpx; color: #909399; font-size: 24rpx; }
.hero-badge { width: 128rpx; height: 128rpx; border-radius: 64rpx; background: #fef0f0; color: #f56c6c; display: flex; flex-direction: column; align-items: center; justify-content: center; }
.badge-num { font-size: 42rpx; font-weight: 700; line-height: 48rpx; }
.badge-label { font-size: 22rpx; }
.toolbar { margin-bottom: 20rpx; }
.tabs { display: flex; flex-wrap: wrap; gap: 12rpx; }
.sort-tabs { margin-top: 16rpx; }
.tab { padding: 12rpx 24rpx; border-radius: 999rpx; background: #f5f7fa; color: #606266; font-size: 26rpx; }
.tab.small { font-size: 24rpx; padding: 10rpx 20rpx; }
.tab.active { background: #1f2d3d; color: #fff; }
.refresh-line { display: flex; align-items: center; justify-content: space-between; margin-top: 18rpx; }
.mini-btn { margin: 0; padding: 0 20rpx; height: 56rpx; line-height: 56rpx; font-size: 24rpx; color: #1f2d3d; background: #eef3f8; }
.error { color: #f56c6c; font-size: 24rpx; margin-top: 12rpx; }
.table-head { display: grid; grid-template-columns: 1fr 100rpx 100rpx 120rpx; gap: 8rpx; color: #909399; font-size: 22rpx; padding-bottom: 16rpx; border-bottom: 1rpx solid #ebeef5; }
.col-num, .col-rate { text-align: right; }
.fund-row { display: grid; grid-template-columns: 1fr 320rpx; gap: 12rpx; padding: 22rpx 0; border-bottom: 1rpx solid #f0f2f5; }
.fund-row.alert { position: relative; }
.fund-row.alert::before { content: ''; position: absolute; left: -24rpx; top: 22rpx; bottom: 22rpx; width: 6rpx; border-radius: 6rpx; background: #f56c6c; }
.name-line { display: flex; align-items: center; gap: 8rpx; }
.fund-code { font-weight: 700; color: #1f2d3d; }
.type-pill, .alert-pill, .coverage-pill { display: inline-flex; padding: 4rpx 10rpx; border-radius: 999rpx; font-size: 20rpx; }
.type-pill { background: #edf2fc; color: #409eff; }
.alert-pill { background: #fef0f0; color: #f56c6c; }
.fund-name { margin-top: 8rpx; color: #303133; font-size: 28rpx; }
.meta-line { display: flex; flex-wrap: wrap; gap: 10rpx; margin-top: 10rpx; color: #909399; font-size: 22rpx; }
.coverage-green { background: #f0f9eb; color: #67c23a; }
.coverage-yellow { background: #fdf6ec; color: #e6a23c; }
.coverage-red { background: #fef0f0; color: #f56c6c; }
.quote-grid { display: grid; grid-template-columns: repeat(3, 1fr); align-items: center; gap: 8rpx; text-align: right; font-size: 26rpx; }
.empty { padding: 48rpx 0; text-align: center; color: #909399; }
</style>
