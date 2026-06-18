<script setup lang="ts">
// 详情页：实时溢价 / 三段式覆盖率（AC-T1）/ 30 天历史
import { computed, nextTick, ref } from 'vue'
import { onLoad } from '@dcloudio/uni-app'
import { getLofDetail, getLofHistory } from '@/api'
import type { LofDetailData, LofHistoryData } from '@/api/types'
import { coverageLevel, coverageLevelLabel, fmtNum, fmtPct, freshnessLabel } from '@/utils/format'

const detail = ref<LofDetailData | null>(null)
const history = ref<LofHistoryData | null>(null)
const loading = ref(false)
const error = ref('')
const showBreakdown = ref(true)
const code = ref('161725')

const coverage = computed(() => detail.value?.realtime.coverage ?? 0)
const coverageClass = computed(() => `coverage-${coverageLevel(coverage.value)}`)
const coverageText = computed(() => coverageLevelLabel(coverageLevel(coverage.value)))

const maxPctileLabel = computed(() => {
  const pctile = detail.value?.pctile_30d
  return pctile === undefined ? '--' : `${Math.round(pctile * 100)} 分位`
})

function drawChart() {
  const items = history.value?.items || []
  if (!items.length) return
  uni
    .createSelectorQuery()
    .select('#historyChart')
    .boundingClientRect((rect) => {
      if (!rect) return
      const width = rect.width || 340
      const height = rect.height || 170
      const ctx = uni.createCanvasContext('historyChart')
      ctx.clearRect(0, 0, width, height)

      const lineTop = 12
      const lineHeight = height * 0.52
      const splitY = height * 0.62
      const barTop = height * 0.68
      const barHeight = height * 0.24
      ctx.setStrokeStyle('#ebeef5')
      ctx.setLineWidth(1)
      ctx.moveTo(0, splitY)
      ctx.lineTo(width, splitY)
      ctx.moveTo(0, barTop + barHeight)
      ctx.lineTo(width, barTop + barHeight)
      ctx.stroke()

      const prices = items.map((item) => item.close_price)
      const iopvs = items.map((item) => item.official_nav)
      const all = prices.concat(iopvs)
      const min = Math.min(...all)
      const max = Math.max(...all)
      const span = Math.max(max - min, 0.001)
      const step = items.length > 1 ? width / (items.length - 1) : width
      const toY = (v: number) => lineTop + (1 - (v - min) / span) * lineHeight

      function drawLine(values: number[], color: string) {
        ctx.beginPath()
        ctx.setStrokeStyle(color)
        ctx.setLineWidth(2)
        values.forEach((value, index) => {
          const x = index * step
          const y = toY(value)
          if (index === 0) ctx.moveTo(x, y)
          else ctx.lineTo(x, y)
        })
        ctx.stroke()
      }

      drawLine(prices, '#f56c6c')
      drawLine(iopvs, '#409eff')

      const maxAbsPremium = Math.max(...items.map((item) => Math.abs(item.premium_close)), 0.001)
      const barStep = width / items.length
      items.forEach((item, index) => {
        const h = Math.max(2, Math.abs(item.premium_close) / maxAbsPremium * barHeight)
        const up = item.premium_close >= 0
        ctx.setFillStyle(up ? '#f56c6c' : '#67c23a')
        ctx.fillRect(index * barStep + 1, up ? barTop + barHeight - h : barTop + barHeight, Math.max(2, barStep - 2), h)
      })

      ctx.draw()
    })
    .exec()
}

const chartFallbackBars = computed(() => {
  const items = history.value?.items || []
  if (!items.length) return []
  const prices = items.map((item) => item.close_price)
  const iopvs = items.map((item) => item.official_nav)
  const all = prices.concat(iopvs)
  const maxAbsPremium = Math.max(...items.map((item) => Math.abs(item.premium_close)), 0.001)
  return items.map((item) => {
    const h = Math.max(6, Math.round(Math.abs(item.premium_close) / maxAbsPremium * 100))
    return { h, up: item.premium_close >= 0 }
  })
})

const latestHistory = computed(() => {
  const items = history.value?.items || []
  return items.length ? items[items.length - 1] : null
})

async function loadPage() {
  loading.value = true
  error.value = ''
  try {
    const [detailData, historyData] = await Promise.all([
      getLofDetail({ code: code.value }),
      getLofHistory({ code: code.value, days: 30, granularity: 'day' })
    ])
    detail.value = detailData
    history.value = historyData
    uni.setNavigationBarTitle({ title: `${detailData.code} 详情` })
    nextTick(() => drawChart())
  } catch (err) {
    error.value = err instanceof Error ? err.message : '详情加载失败'
  } finally {
    loading.value = false
  }
}

function toggleBreakdown() {
  showBreakdown.value = !showBreakdown.value
}

onLoad((q: Record<string, string> | undefined) => {
  code.value = (q && q.code) || '161725'
  loadPage()
})
</script>

<template>
  <view class="page">
    <view v-if="error" class="card error-card">
      <view>{{ error }}</view>
      <button class="mini-btn" :loading="loading" @tap="loadPage">重试</button>
    </view>

    <view v-if="detail" class="card header-card">
      <view class="title-row">
        <view>
          <view class="fund-name">{{ detail.name }}</view>
          <view class="fund-meta">{{ detail.code }} · {{ detail.type }} · 规模 {{ fmtNum(detail.scale_yi, 1) }} 亿</view>
        </view>
        <view class="coverage-tag" :class="coverageClass" @tap="toggleBreakdown">
          <text class="coverage-num">{{ fmtPct(coverage, 0) }}</text>
          <text class="coverage-label">估算覆盖率 · {{ coverageText }}</text>
        </view>
      </view>

      <view v-if="showBreakdown" class="breakdown">
        <view class="breakdown-title">三段式覆盖率明细（tap 可收起）</view>
        <view class="breakdown-grid">
          <view class="breakdown-item">
            <text class="label">前十大权重</text>
            <text class="value">{{ fmtPct(detail.coverage_breakdown.top10_weight, 0) }}</text>
          </view>
          <view class="breakdown-item">
            <text class="label">基准补全权重</text>
            <text class="value">{{ fmtPct(detail.coverage_breakdown.benchmark_assigned_weight, 0) }}</text>
          </view>
          <view class="breakdown-item">
            <text class="label">现金权重</text>
            <text class="value">{{ fmtPct(detail.coverage_breakdown.cash_weight, 0) }}</text>
          </view>
        </view>
      </view>
    </view>

    <view v-if="detail" class="card quote-card">
      <view class="section-title">实时快照</view>
      <view class="quote-grid">
        <view class="quote-item">
          <text class="label">现价</text>
          <text class="value">{{ fmtNum(detail.realtime.price, 3) }}</text>
        </view>
        <view class="quote-item">
          <text class="label">IOPV</text>
          <text class="value">{{ fmtNum(detail.realtime.iopv, 3) }}</text>
        </view>
        <view class="quote-item">
          <text class="label">溢价率</text>
          <text class="value" :class="detail.realtime.premium >= 0 ? 'text-up' : 'text-down'">{{ fmtPct(detail.realtime.premium, 2) }}</text>
        </view>
        <view class="quote-item">
          <text class="label">30天分位</text>
          <text class="value">{{ fmtPct(detail.pctile_30d, 0) }}</text>
        </view>
      </view>
      <view class="fresh-line">更新时间：{{ freshnessLabel(detail.realtime.ts) }} · source_quality={{ detail.realtime.source_quality }}</view>
    </view>

    <view class="card chart-card" v-if="history">
      <view class="section-head">
        <view class="section-title">现价 / IOPV / 溢价历史</view>
        <view class="pctile-box">{{ maxPctileLabel }}</view>
      </view>
      <view class="legend">
        <text class="dot price"></text><text>现价</text>
        <text class="dot iopv"></text><text>IOPV</text>
        <text class="dot premium"></text><text>溢价柱</text>
      </view>
      <canvas id="historyChart" canvas-id="historyChart" class="chart"></canvas>
      <view class="bar-fallback" aria-hidden="true">
        <view
          v-for="(bar, index) in chartFallbackBars"
          :key="index"
          class="fallback-bar"
          :class="bar.up ? 'up' : 'down'"
          :style="{ height: `${bar.h}rpx` }"
        ></view>
      </view>
      <view v-if="latestHistory" class="history-summary">
        最近交易日 {{ latestHistory.date }}：收盘溢价 {{ fmtPct(latestHistory.premium_close, 2) }}，历史分位 {{ fmtPct(latestHistory.premium_pctile_30d, 0) }}
      </view>
    </view>

    <view v-if="detail" class="card info-card">
      <view class="section-title">业绩比较基准</view>
      <view class="raw">{{ detail.benchmark_raw }}</view>
      <view class="component-row" v-for="item in detail.benchmark_components" :key="item.index_code">
        <text>{{ item.index_code }} · {{ item.name }}</text>
        <text>{{ fmtPct(item.weight, 0) }}</text>
      </view>
    </view>

    <view v-if="detail" class="card holdings-card">
      <view class="section-title">前十重仓股</view>
      <view class="holding-row" v-for="item in detail.holdings_top10" :key="item.stock_code">
        <text>{{ item.stock_code }} · {{ item.stock_name }}</text>
        <text>{{ fmtPct(item.weight, 0) }}</text>
      </view>
    </view>
  </view>
</template>

<style scoped lang="scss">
.page { padding: 24rpx; padding-bottom: 48rpx; }
.card { margin-bottom: 20rpx; }
.error-card { color: #f56c6c; }
.title-row { display: flex; align-items: center; gap: 20rpx; }
.fund-name { font-size: 36rpx; font-weight: 700; color: #1f2d3d; }
.fund-meta { color: #909399; font-size: 24rpx; margin-top: 8rpx; }
.coverage-tag { width: 190rpx; min-height: 110rpx; border-radius: 16rpx; padding: 12rpx; display: flex; flex-direction: column; align-items: center; justify-content: center; text-align: center; }
.coverage-num { font-size: 38rpx; font-weight: 700; line-height: 44rpx; }
.coverage-label { font-size: 20rpx; margin-top: 4rpx; }
.coverage-green { background: #f0f9eb; color: #67c23a; }
.coverage-yellow { background: #fdf6ec; color: #e6a23c; }
.coverage-red { background: #fef0f0; color: #f56c6c; }
.breakdown { margin-top: 22rpx; padding: 20rpx; background: #f8fafc; border-radius: 12rpx; }
.breakdown-title { color: #606266; font-size: 24rpx; margin-bottom: 16rpx; }
.breakdown-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 12rpx; }
.breakdown-item { display: flex; flex-direction: column; gap: 6rpx; }
.label { color: #909399; font-size: 24rpx; }
.value { color: #1f2d3d; font-size: 32rpx; font-weight: 700; }
.quote-grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: 16rpx; }
.quote-item { display: flex; flex-direction: column; gap: 8rpx; }
.fresh-line { color: #909399; font-size: 24rpx; margin-top: 18rpx; }
.section-head { display: flex; align-items: center; justify-content: space-between; }
.pctile-box { background: #edf2fc; color: #409eff; padding: 8rpx 16rpx; border-radius: 999rpx; font-size: 24rpx; }
.legend { display: flex; align-items: center; gap: 10rpx; color: #606266; font-size: 24rpx; margin: 4rpx 0 12rpx; }
.dot { width: 18rpx; height: 18rpx; border-radius: 9rpx; display: inline-flex; }
.dot.price { background: #f56c6c; }
.dot.iopv { background: #409eff; }
.dot.premium { background: #e6a23c; }
.chart { width: 100%; height: 340rpx; display: block; }
.bar-fallback { display: flex; align-items: flex-end; gap: 2rpx; height: 100rpx; margin-top: 8rpx; }
.fallback-bar { flex: 1; border-radius: 4rpx 4rpx 0 0; opacity: 0.35; }
.fallback-bar.up { background: #f56c6c; }
.fallback-bar.down { background: #67c23a; }
.history-summary { margin-top: 12rpx; color: #606266; font-size: 24rpx; }
.raw { color: #606266; line-height: 1.6; margin-bottom: 12rpx; }
.component-row, .holding-row { display: flex; align-items: center; justify-content: space-between; padding: 14rpx 0; border-top: 1rpx solid #f0f2f5; color: #606266; font-size: 24rpx; }
.mini-btn { margin-top: 16rpx; font-size: 24rpx; }
</style>
