<script setup lang="ts">
// 详情页：竞品（集思录）双列布局（PRD §4.4 / PRD 1.2）
// 左列「场内」 / 右列「估值」 / 状态标签栏 / 三段式覆盖率（AC-T1） / 历史折线 / 重仓表
import { computed, ref } from 'vue'
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
  fmtLimitAmount,
  fmtSharesYi,
  fmtSharesWan,
  fmtSharesIncrWan,
  fmtVolumeWan,
  freshnessLabel,
  shouldRender
} from '@/utils/format'
import { isLowLiquidity, LOW_LIQUIDITY_LABEL } from '@/utils/low-liquidity'
import { displayFundName, displayQdiiReferenceIndexName } from '@/utils/qdii-display'

const detail = ref<LofDetailData | null>(null)
const history = ref<LofHistoryData | null>(null)
const loading = ref(false)
const error = ref('')
const showBreakdown = ref(false)
const code = ref('161725')
const qdiiRiskText = '非交易所 IOPV，存在跟踪误差'

const displayDetailName = computed(() => detail.value ? displayFundName(detail.value.code, detail.value.name) : '--')
const coverage = computed(() => detail.value?.realtime.coverage ?? 0)
const coverageClass = computed(() => `coverage-${coverageLevel(coverage.value)}`)
const coverageText = computed(() => coverageLevelLabel(coverageLevel(coverage.value)))

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

const showQdiiEstimateCard = computed(() => {
  const d = detail.value
  if (!d) return false
  return [
    d.qdii_estimate_nav,
    d.qdii_estimate_premium,
    d.qdii_reference_index_code,
    d.qdii_reference_index_name,
    d.qdii_reference_index_change_pct,
    d.qdii_fx_change_pct,
    d.qdii_estimate_source,
    d.qdii_nav_date
  ].some((value) => shouldRender(value))
})

// PRD 1.3 限额周期文案
function periodText(p?: string | null): string {
  if (p === 'day') return '单日'
  if (p === 'week') return '单周'
  if (p === 'month') return '单月'
  return '单期'
}

// PRD 1.3 申购标签：open/unknown/null 返回空（AC-P5 不渲染）
function subscribeLabel(d: LofDetailData): string {
  const st = d.subscribe_status
  if (st === 'suspended') return '暂停申购'
  if (st === 'closed') return '停止申购'
  if (st === 'limited') {
    if (shouldRender(d.subscribe_limit_amount)) {
      return '限大额 ' + periodText(d.subscribe_limit_period) + ' ≤ ' + fmtLimitAmount(d.subscribe_limit_amount)
    }
    return '限大额'
  }
  return ''
}

// PRD 1.3 赎回标签：去掉 limited，open/limited/unknown/null 不渲染
function redeemLabel(d: LofDetailData): string {
  const st = d.redeem_status
  if (st === 'suspended') return '暂停赎回'
  if (st === 'closed') return '停止赎回'
  return ''
}

function statusPillClass(value?: SubscribeRedeemStatus): string {
  if (value === 'open') return 'status-open'
  if (value === 'suspended' || value === 'closed') return 'status-suspended'
  if (value === 'limited') return 'status-limited'
  return ''
}

const historyRows = computed(() => {
  const items = history.value?.items || []
  // AC-P5: reverse so newest day is on top; null fields render as -- via fmt helpers.
  return [...items].reverse()
})

const latestHistory = computed(() => {
  const items = history.value?.items || []
  // AC-P5: skip trailing null days (T+1 dang-ri has no official_nav/premium_close yet).
  for (let i = items.length - 1; i >= 0; i--) {
    const it = items[i]
    if (typeof it.premium_close === 'number' && !Number.isNaN(it.premium_close)) return it
  }
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
          <view class="fund-name">{{ displayDetailName }}</view>
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
          <view v-if="shouldRender(detail.shares_onexchange)" class="dual-row">
            <text class="label">场内份额(万份)</text>
            <text class="value">{{ fmtSharesWan(detail.shares_onexchange) }}</text>
          </view>
          <view v-if="shouldRender(detail.shares_incr_daily)" class="dual-row">
            <text class="label">当日新增份额</text>
            <text class="value" :class="(detail.shares_incr_daily ?? 0) >= 0 ? 'text-up' : 'text-down'">{{ fmtSharesIncrWan(detail.shares_incr_daily) }}</text>
          </view>
          <view v-if="shouldRender(detail.circulating_shares)" class="dual-row">
            <text class="label">场内份额(亿份)</text>
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
          v-if="subscribeLabel(detail)"
          class="status-pill"
          :class="statusPillClass(detail.subscribe_status)"
        >{{ subscribeLabel(detail) }}</text>
        <text
          v-if="redeemLabel(detail)"
          class="status-pill"
          :class="statusPillClass(detail.redeem_status)"
        >{{ redeemLabel(detail) }}</text>
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

      <!-- PRD 1.4 规则区：申赎确认日（参考）；严禁标“到账可卖日”（§11 R10 红线） -->
      <view v-if="shouldRender(detail.purchase_confirm_day) || shouldRender(detail.redeem_confirm_day)" class="rule-line">
        <text class="rule-title">申赎确认日（参考）</text>
        <text v-if="shouldRender(detail.purchase_confirm_day)" class="rule-item">申购 {{ detail.purchase_confirm_day }}</text>
        <text v-if="shouldRender(detail.redeem_confirm_day)" class="rule-item">赎回 {{ detail.redeem_confirm_day }}</text>
      </view>
    </view>


    <view v-if="detail && showQdiiEstimateCard" class="card qdii-card">
      <view class="section-title">QDII 估算</view>
      <view class="qdii-warning">{{ qdiiRiskText }}</view>
      <view class="qdii-grid">
        <view class="qdii-item wide">
          <text class="label">参考指数</text>
          <text class="value">
            {{ displayQdiiReferenceIndexName(detail) }}
            <text v-if="shouldRender(detail.qdii_reference_index_code)" class="sub">{{ detail.qdii_reference_index_code }}</text>
          </text>
        </view>
        <view class="qdii-item">
          <text class="label">参考指数估算溢价</text>
          <text
            class="value"
            :class="shouldRender(detail.qdii_estimate_premium) ? ((detail.qdii_estimate_premium ?? 0) >= 0 ? 'text-up' : 'text-down') : ''"
          >{{ shouldRender(detail.qdii_estimate_premium) ? fmtPctSigned(detail.qdii_estimate_premium, 2) : '--' }}</text>
        </view>
        <view class="qdii-item">
          <text class="label">估算净值</text>
          <text class="value">{{ fmtNum(detail.qdii_estimate_nav, 4) }}</text>
        </view>
        <view class="qdii-item">
          <text class="label">指数涨跌</text>
          <text
            class="value"
            :class="shouldRender(detail.qdii_reference_index_change_pct) ? ((detail.qdii_reference_index_change_pct ?? 0) >= 0 ? 'text-up' : 'text-down') : ''"
          >{{ shouldRender(detail.qdii_reference_index_change_pct) ? fmtPctSigned(detail.qdii_reference_index_change_pct, 2) : '--' }}</text>
        </view>
        <view class="qdii-item">
          <text class="label">汇率变动</text>
          <text
            class="value"
            :class="shouldRender(detail.qdii_fx_change_pct) ? ((detail.qdii_fx_change_pct ?? 0) >= 0 ? 'text-up' : 'text-down') : ''"
          >{{ shouldRender(detail.qdii_fx_change_pct) ? fmtPctSigned(detail.qdii_fx_change_pct, 2) : '--' }}</text>
        </view>
        <view class="qdii-item">
          <text class="label">净值日期</text>
          <text class="value">{{ shouldRender(detail.qdii_nav_date) ? detail.qdii_nav_date : '--' }}</text>
        </view>
        <view class="qdii-item">
          <text class="label">估算来源</text>
          <text class="value">{{ shouldRender(detail.qdii_estimate_source) ? detail.qdii_estimate_source : '--' }}</text>
        </view>
      </view>
    </view>

    <view class="card history-card" v-if="history">
      <view class="section-head">
        <view class="section-title">收盘价 / 披露净值 / 溢价历史</view>
      </view>
      <view v-if="latestHistory" class="history-summary">
        最近交易日 {{ latestHistory.date }}：收盘溢价 {{ fmtPct(latestHistory.premium_close, 2) }}
      </view>
      <view class="hist-head">
        <text class="hist-date">日期</text>
        <text class="hist-num">收盘价</text>
        <text class="hist-num">净值</text>
        <text class="hist-num">收盘溢价</text>
        <text class="hist-num">预估溢价</text>
        <text class="hist-num">偏差</text>
        <text class="hist-num">新增份额</text>
      </view>
      <view class="hist-row" v-for="row in historyRows" :key="row.date">
        <text class="hist-date">{{ row.date }}</text>
        <text class="hist-num">{{ fmtNum(row.close_price, 3) }}</text>
        <text class="hist-num">{{ fmtNum(row.official_nav, 4) }}</text>
        <text
          class="hist-num"
          :class="shouldRender(row.premium_close) ? ((row.premium_close ?? 0) >= 0 ? 'text-up' : 'text-down') : ''"
        >{{ shouldRender(row.premium_close) ? fmtPctSigned(row.premium_close, 2) : '--' }}</text>
        <text
          class="hist-num"
          :class="shouldRender(row.premium_estimate_close) ? ((row.premium_estimate_close ?? 0) >= 0 ? 'text-up' : 'text-down') : ''"
        >{{ shouldRender(row.premium_estimate_close) ? fmtPctSigned(row.premium_estimate_close, 2) : '--' }}</text>
        <text
          class="hist-num"
          :class="shouldRender(row.premium_deviation) ? ((row.premium_deviation ?? 0) >= 0 ? 'text-up' : 'text-down') : ''"
        >{{ shouldRender(row.premium_deviation) ? fmtPctSigned(row.premium_deviation, 2) : '--' }}</text>
        <text
          class="hist-num"
          :class="shouldRender(row.shares_incr_daily) ? ((row.shares_incr_daily ?? 0) >= 0 ? 'text-up' : 'text-down') : ''"
        >{{ shouldRender(row.shares_incr_daily) ? fmtSharesIncrWan(row.shares_incr_daily) : '--' }}</text>
      </view>
    </view>

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
.rule-line { display: flex; flex-wrap: wrap; align-items: center; gap: 12rpx; margin-top: 12rpx; font-size: 24rpx; color: #606266; }
.rule-title { color: #909399; }
.rule-item { background: #f5f7fa; color: #606266; padding: 4rpx 12rpx; border-radius: 6rpx; font-size: 22rpx; }

.qdii-card { padding: 20rpx; border: 1rpx solid #d8e7ff; background: #fbfdff; }
.qdii-warning { margin: 8rpx 0 16rpx; padding: 12rpx 16rpx; border-radius: 10rpx; background: #fff7e6; color: #b26a00; font-size: 24rpx; }
.qdii-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 14rpx; }
.qdii-item { display: flex; flex-direction: column; gap: 6rpx; padding: 14rpx 16rpx; border-radius: 12rpx; background: #f4f8ff; }
.qdii-item.wide { grid-column: span 2; }

.section-head { display: flex; align-items: center; justify-content: space-between; }
.section-title { font-size: 30rpx; font-weight: 600; color: #1f2d3d; margin-bottom: 8rpx; }
.history-summary { margin: 4rpx 0 12rpx; color: #606266; font-size: 24rpx; }
/* 历史逐日列表（代替原折线图 + 溢价柱） */
.hist-head, .hist-row { display: grid; grid-template-columns: 1.05fr 0.85fr 0.85fr 0.95fr 0.95fr 0.85fr 0.95fr; gap: 6rpx; padding: 12rpx 0; align-items: center; font-size: 21rpx; }
.hist-head { color: #909399; border-bottom: 1rpx solid #ebeef5; }
.hist-row { border-top: 1rpx solid #f0f2f5; color: #606266; }
.hist-row:first-of-type { border-top: 0; }
.hist-date { color: #303133; }
.hist-num { text-align: right; }

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
