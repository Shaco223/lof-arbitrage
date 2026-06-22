<script setup lang="ts">
// 详情页：竞品（集思录）双列布局（PRD §4.4 / PRD 1.2）
// 左列「场内」 / 右列「估值」 / 状态标签栏 / 三段式覆盖率（AC-T1） / 历史折线 / 重仓表
import { computed, nextTick, ref } from 'vue'
import { onLoad } from '@dcloudio/uni-app'
import { getLofDetail, getLofHistory } from '@/api'
import type { LofDetailData, LofHistoryData, SubscribeRedeemStatus } from '@/api/types'
import {
  coverageLevel,
  coverageLevelLabel,
  fmtDateTime,
  fmtNum,
  fmtPct,
  fmtPctSigned,
  fmtSharesYi,
  fmtVolumeWan,
  freshnessLabel,
  shouldRender
} from '@/utils/format'
import { isLowLiquidity, LOW_LIQUIDITY_LABEL } from '@/utils/low-liquidity'

const detail = ref<LofDetailData | null>(null)
const history = ref<LofHistoryData | null>(null)
const loading = ref(false)
const error = ref('')
const showBreakdown = ref(false)
const code = ref('161725')

const coverage = computed(() => detail.value?.realtime.coverage ?? 0)
const coverageClass = computed(() => `coverage-${coverageLevel(coverage.value)}`)
const coverageText = computed(() => coverageLevelLabel(coverageLevel(coverage.value)))

const maxPctileLabel = computed(() => {
  const pctile = detail.value?.pctile_30d
  return pctile === undefined ? '--' : `${Math.round(pctile * 100)} 分位`
})

// 涨跌幅 / 成交额可能在 realtime 子对象，前端做一次兜底
const priceChangePct = computed(() => {
  const d = detail.value
  if (!d) return null
  if (shouldRender(d.price_change_pct)) return d.price_change_pct ?? null
  if (shouldRender(d.realtime?.price_change_pct)) return d.realtime!.price_change_pct ?? null
  return null
})

const volumeAmount = computed(() => {
  const d = detail.value
  if (!d) return null
  if (shouldRender(d.volume_amount)) return d.volume_amount ?? null
  if (shouldRender(d.realtime?.volume_amount)) return d.realtime!.volume_amount ?? null
  return null
})

const isLowLiquidityFlag = computed(() => {
  const d = detail.value
  if (!d) return false
  if (d.status === 'active_low_liquidity') return true
  if (d.status === 'active') return false
  return isLowLiquidity(d.code)
})

// 重仓表是否需要展示新两列：只要有任意一只有真实值就展示该列
const showHoldingChange = computed(() =>
  (detail.value?.holdings_top10 || []).some((h) => shouldRender(h.price_change_pct))
)

const showHoldingContrib = computed(() =>
  (detail.value?.holdings_top10 || []).some((h) => shouldRender(h.contribution_pct))
)

function subscribeText(value?: SubscribeRedeemStatus): string {
  if (value === 'open') return '申购开放'
  if (value === 'suspended') return '暂停申购'
  if (value === 'limited') return '申购限额'
  return ''
}

function redeemText(value?: SubscribeRedeemStatus): string {
  if (value === 'open') return '赎回开放'
  if (value === 'suspended') return '暂停赎回'
  if (value === 'limited') return '赎回限额'
  return ''
}

function statusPillClass(value?: SubscribeRedeemStatus): string {
  if (value === 'open') return 'status-open'
  if (value === 'suspended') return 'status-suspended'
  if (value === 'limited') return 'status-limited'
  return ''
}

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

function sourceQualityLabel(value: LofDetailData['realtime']['source_quality']) {
  if (value === 'stale') return '数据滞后'
  if (value === 'degraded') return '数据降级'
  return '数据正常'
}

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

    <!-- PRD §4.4 双列卡片：左场内 / 右估值 -->
    <view v-if="detail" class="card dual-card">
      <view class="dual-grid">
        <!-- 左列：场内 -->
        <view class="dual-col">
          <view class="dual-title">场内</view>
          <view class="dual-row">
            <text class="label">现价</text>
            <text class="value">{{ fmtNum(detail.realtime.price, 3) }}</text>
          </view>
          <view v-if="shouldRender(priceChangePct)" class="dual-row">
            <text class="label">涨跌幅</text>
            <text class="value" :class="(priceChangePct ?? 0) >= 0 ? 'text-up' : 'text-down'">{{ fmtPctSigned(priceChangePct, 2) }}</text>
          </view>
          <view v-if="shouldRender(volumeAmount)" class="dual-row">
            <text class="label">成交额</text>
            <text class="value">{{ fmtVolumeWan(volumeAmount) }}</text>
          </view>
          <view v-if="shouldRender(detail.circulating_shares)" class="dual-row">
            <text class="label">场内份额</text>
            <text class="value">{{ fmtSharesYi(detail.circulating_shares) }}</text>
          </view>
        </view>

        <!-- 右列：估值 -->
        <view class="dual-col">
          <view class="dual-title">估值</view>
          <view v-if="shouldRender(detail.nav_official)" class="dual-row">
            <text class="label">披露净值</text>
            <text class="value">
              {{ fmtNum(detail.nav_official, 4) }}
              <text v-if="shouldRender(detail.nav_official_date)" class="sub">{{ detail.nav_official_date }}</text>
            </text>
          </view>
          <view class="dual-row">
            <text class="label">估算净值 IOPV</text>
            <text class="value">{{ fmtNum(detail.realtime.iopv, 4) }}</text>
          </view>
          <view v-if="shouldRender(detail.premium_error)" class="dual-row">
            <text class="label">估算误差（盘后）</text>
            <text class="value" :class="(detail.premium_error ?? 0) >= 0 ? 'text-up' : 'text-down'">
              {{ fmtNum(detail.premium_error, 4) }}
              <text v-if="shouldRender(detail.nav_estimate_error_pct)" class="sub">{{ fmtPctSigned(detail.nav_estimate_error_pct, 2) }}</text>
            </text>
          </view>
          <view class="dual-row">
            <text class="label">估算溢价</text>
            <text class="value" :class="(detail.realtime.premium ?? 0) >= 0 ? 'text-up' : 'text-down'">{{ fmtPctSigned(detail.realtime.premium, 2) }}</text>
          </view>
          <view v-if="shouldRender(detail.premium_nav)" class="dual-row">
            <text class="label">净值溢价</text>
            <text class="value" :class="(detail.premium_nav ?? 0) >= 0 ? 'text-up' : 'text-down'">{{ fmtPctSigned(detail.premium_nav, 2) }}</text>
          </view>
        </view>
      </view>

      <!-- 中部状态标签栏 -->
      <view class="status-bar">
        <text
          v-if="shouldRender(detail.subscribe_status)"
          class="status-pill"
          :class="statusPillClass(detail.subscribe_status)"
        >{{ subscribeText(detail.subscribe_status) }}</text>
        <text
          v-if="shouldRender(detail.redeem_status)"
          class="status-pill"
          :class="statusPillClass(detail.redeem_status)"
        >{{ redeemText(detail.redeem_status) }}</text>
        <text v-if="isLowLiquidityFlag" class="status-pill liquidity">{{ LOW_LIQUIDITY_LABEL }}</text>
        <text
          v-if="detail.realtime.source_quality && detail.realtime.source_quality !== 'ok'"
          class="status-pill"
          :class="`quality-${detail.realtime.source_quality}`"
        >{{ sourceQualityLabel(detail.realtime.source_quality) }}</text>
      </view>

      <view class="fresh-line">
        估值时间：{{ fmtDateTime(detail.realtime.ts) }}（{{ freshnessLabel(detail.realtime.ts) }}）
        <text v-if="shouldRender(detail.nav_official_date)" class="sub">· 披露净值日期 {{ detail.nav_official_date }}</text>
      </view>
    </view>

    <!-- 历史折线 + 溢价柱 -->
    <view class="card chart-card" v-if="history">
      <view class="section-head">
        <view class="section-title">现价 / 披露净值 / 溢价历史</view>
        <view class="pctile-box">{{ maxPctileLabel }}</view>
      </view>
      <view class="legend">
        <text class="dot price"></text><text>现价</text>
        <text class="dot iopv"></text><text>披露净值</text>
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

    <!-- 业绩比较基准 -->
    <view v-if="detail" class="card info-card">
      <view class="section-title">业绩比较基准</view>
      <view class="raw">{{ detail.benchmark_raw }}</view>
      <view class="component-row" v-for="item in detail.benchmark_components" :key="item.index_code">
        <text>{{ item.index_code }} · {{ item.name }}</text>
        <text>{{ fmtPct(item.weight, 0) }}</text>
      </view>
    </view>

    <!-- 重仓表（PRD §4.4：列名加 price_change_pct + contribution_pct，缺值列隐藏） -->
    <view v-if="detail" class="card holdings-card">
      <view class="section-title">前十重仓股</view>
      <view class="holding-head" :class="{ 'has-change': showHoldingChange, 'has-contrib': showHoldingContrib }">
        <text class="hd-name">名称</text>
        <text class="hd-num">权重</text>
        <text v-if="showHoldingChange" class="hd-num">涨跌</text>
        <text v-if="showHoldingContrib" class="hd-num">贡献</text>
      </view>
      <view
        class="holding-row"
        v-for="item in detail.holdings_top10"
        :key="item.stock_code"
        :class="{ 'has-change': showHoldingChange, 'has-contrib': showHoldingContrib }"
      >
        <text class="hd-name">{{ item.stock_code }} · {{ item.stock_name }}</text>
        <text class="hd-num">{{ fmtPct(item.weight, 1) }}</text>
        <text
          v-if="showHoldingChange"
          class="hd-num"
          :class="shouldRender(item.price_change_pct) ? ((item.price_change_pct ?? 0) >= 0 ? 'text-up' : 'text-down') : ''"
        >{{ shouldRender(item.price_change_pct) ? fmtPctSigned(item.price_change_pct, 2) : '--' }}</text>
        <text
          v-if="showHoldingContrib"
          class="hd-num"
          :class="shouldRender(item.contribution_pct) ? ((item.contribution_pct ?? 0) >= 0 ? 'text-up' : 'text-down') : ''"
        >{{ shouldRender(item.contribution_pct) ? fmtPctSigned(item.contribution_pct, 3) : '--' }}</text>
      </view>
    </view>
  </view>
</template>

<style scoped lang="scss">
.page { padding: 24rpx; padding-bottom: 48rpx; }
.card { margin-bottom: 20rpx; }
.error-card { color: #f56c6c; }
.title-row { display: flex; align-items: center; gap: 16rpx; justify-content: space-between; }
.fund-name { font-size: 36rpx; font-weight: 700; color: #1f2d3d; }
.fund-meta { color: #909399; font-size: 24rpx; margin-top: 8rpx; }
.coverage-tag { min-width: 160rpx; padding: 12rpx 16rpx; border-radius: 14rpx; display: flex; flex-direction: column; align-items: center; justify-content: center; text-align: center; }
.coverage-num { font-size: 34rpx; font-weight: 700; line-height: 40rpx; }
.coverage-label { font-size: 20rpx; margin-top: 4rpx; }
.coverage-green { background: #f0f9eb; color: #67c23a; }
.coverage-yellow { background: #fdf6ec; color: #e6a23c; }
.coverage-red { background: #fef0f0; color: #f56c6c; }
.breakdown { margin-top: 18rpx; padding: 16rpx; background: #f8fafc; border-radius: 12rpx; }
.breakdown-title { color: #606266; font-size: 24rpx; margin-bottom: 16rpx; }
.breakdown-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 12rpx; }
.breakdown-item { display: flex; flex-direction: column; gap: 6rpx; }
.label { color: #909399; font-size: 24rpx; }
.value { color: #1f2d3d; font-size: 30rpx; font-weight: 600; }
.value .sub { color: #909399; font-size: 22rpx; font-weight: 400; margin-left: 8rpx; }

/* PRD §4.4 双列布局 */
.dual-card { padding: 20rpx; }
.dual-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 16rpx; }
.dual-col { display: flex; flex-direction: column; gap: 12rpx; padding: 14rpx 16rpx; background: #f8fafc; border-radius: 12rpx; }
.dual-title { color: #909399; font-size: 24rpx; padding-bottom: 8rpx; border-bottom: 1rpx dashed #ebeef5; margin-bottom: 4rpx; }
.dual-row { display: flex; align-items: baseline; justify-content: space-between; gap: 12rpx; }
.dual-row .label { color: #909399; font-size: 24rpx; }
.dual-row .value { color: #1f2d3d; font-size: 30rpx; font-weight: 600; text-align: right; }
.text-up { color: #f56c6c; }
.text-down { color: #67c23a; }

.status-bar { display: flex; flex-wrap: wrap; gap: 10rpx; margin-top: 18rpx; }
.status-pill { display: inline-flex; padding: 6rpx 14rpx; border-radius: 999rpx; font-size: 22rpx; background: #f5f7fa; color: #606266; }
.status-pill.status-open { background: #f0f9eb; color: #67c23a; }
.status-pill.status-suspended { background: #fef0f0; color: #f56c6c; }
.status-pill.status-limited { background: #fdf6ec; color: #e6a23c; }
.status-pill.liquidity { background: #f0f7ff; color: #1f6feb; border: 1rpx solid #c8dcff; }
.status-pill.quality-degraded { background: #fdf6ec; color: #e6a23c; }
.status-pill.quality-stale { background: #fef0f0; color: #f56c6c; }

.fresh-line { color: #909399; font-size: 24rpx; margin-top: 18rpx; }
.fresh-line .sub { color: #c0c4cc; font-size: 22rpx; }

.section-head { display: flex; align-items: center; justify-content: space-between; }
.section-title { font-size: 30rpx; font-weight: 600; color: #1f2d3d; margin-bottom: 8rpx; }
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
.component-row { display: flex; align-items: center; justify-content: space-between; padding: 14rpx 0; border-top: 1rpx solid #f0f2f5; color: #606266; font-size: 24rpx; }

/* 重仓表 */
.holding-head, .holding-row { display: grid; grid-template-columns: 1fr 120rpx; gap: 8rpx; padding: 12rpx 0; align-items: center; font-size: 24rpx; }
.holding-head.has-change, .holding-row.has-change { grid-template-columns: 1fr 120rpx 120rpx; }
.holding-head.has-change.has-contrib, .holding-row.has-change.has-contrib,
.holding-head.has-contrib, .holding-row.has-contrib { grid-template-columns: 1fr 120rpx 120rpx 120rpx; }
.holding-head { color: #909399; border-bottom: 1rpx solid #ebeef5; }
.holding-row { border-top: 1rpx solid #f0f2f5; color: #606266; }
.holding-row:first-of-type { border-top: 0; }
.hd-name { color: #303133; }
.hd-num { text-align: right; }

.mini-btn { margin-top: 16rpx; font-size: 24rpx; padding: 0 24rpx; height: 60rpx; line-height: 60rpx; color: #fff; background: #1f2d3d; }
</style>
