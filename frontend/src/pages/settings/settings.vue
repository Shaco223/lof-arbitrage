<script setup lang="ts">
// 设置页：本地阈值与推送通道配置（一期本地存储，联调时由拉取器读取/落库）
import { computed, ref } from 'vue'
import { useSettingsStore } from '@/store/settings'
import { fmtPct } from '@/utils/format'

const settings = useSettingsStore()
const channelOptions = ['serverchan', 'email'] as const
const channelIndex = ref(settings.channel === 'email' ? 1 : 0)
const premiumSlider = ref(Math.round(settings.premiumThreshold * 1000))
const discountSlider = ref(Math.round(settings.discountThreshold * 1000))
const pollOptions = [30, 60, 120, 300]
const pollIndex = ref(Math.max(0, pollOptions.findIndex((v) => v * 1000 === settings.pollIntervalMs)))
const target = ref(settings.channelTarget)

const premiumValue = computed(() => premiumSlider.value / 1000)
const discountValue = computed(() => discountSlider.value / 1000)
const selectedPoll = computed(() => pollOptions[pollIndex.value] || 60)

function onChannelChange(e: { detail: { value: string | number } }) {
  const index = Number(e.detail.value)
  channelIndex.value = index
  settings.update({ channel: channelOptions[index] })
}

function onPremiumChange(e: { detail: { value: number } }) {
  premiumSlider.value = Number(e.detail.value)
  settings.update({ premiumThreshold: premiumValue.value })
}

function onDiscountChange(e: { detail: { value: number } }) {
  discountSlider.value = Number(e.detail.value)
  settings.update({ discountThreshold: discountValue.value })
}

function onPollChange(e: { detail: { value: string | number } }) {
  const index = Number(e.detail.value)
  pollIndex.value = index
  settings.update({ pollIntervalMs: selectedPoll.value * 1000 })
}

function onTargetInput(e: { detail: { value: string } }) {
  target.value = e.detail.value
  settings.update({ channelTarget: target.value })
}

function resetSettings() {
  settings.reset()
  channelIndex.value = settings.channel === 'email' ? 1 : 0
  premiumSlider.value = Math.round(settings.premiumThreshold * 1000)
  discountSlider.value = Math.round(settings.discountThreshold * 1000)
  pollIndex.value = Math.max(0, pollOptions.findIndex((v) => v * 1000 === settings.pollIntervalMs))
  target.value = settings.channelTarget
  uni.showToast({ title: '已恢复默认', icon: 'success' })
}
</script>

<template>
  <view class="page">
    <view class="card intro-card">
      <view class="section-title">监控设置</view>
      <view class="text-muted">本页一期写入本地存储；真实推送由 dev-004 告警引擎读取配置后执行。</view>
    </view>

    <view class="card setting-card">
      <view class="setting-title">阈值</view>
      <view class="setting-row col-row">
        <view class="row-head">
          <text>溢价告警阈值</text>
          <text class="value text-up">{{ fmtPct(premiumValue, 1) }}</text>
        </view>
        <slider
          :value="premiumSlider"
          min="10"
          max="100"
          step="5"
          activeColor="#f56c6c"
          backgroundColor="#ebeef5"
          @change="onPremiumChange"
        />
        <view class="hint">默认 +5%，列表中溢价率 ≥ 阈值会标记触阈值。</view>
      </view>

      <view class="setting-row col-row">
        <view class="row-head">
          <text>折价告警阈值</text>
          <text class="value text-down">-{{ fmtPct(discountValue, 1) }}</text>
        </view>
        <slider
          :value="discountSlider"
          min="5"
          max="80"
          step="5"
          activeColor="#67c23a"
          backgroundColor="#ebeef5"
          @change="onDiscountChange"
        />
        <view class="hint">默认 -2%，列表中溢价率 ≤ -阈值会标记触阈值。</view>
      </view>
    </view>

    <view class="card setting-card">
      <view class="setting-title">推送通道</view>
      <view class="setting-row">
        <text>通道</text>
        <picker :range="channelOptions" :value="channelIndex" @change="onChannelChange">
          <view class="picker-value">{{ channelOptions[channelIndex] }}</view>
        </picker>
      </view>
      <view class="setting-row col-row">
        <text>通道目标</text>
        <input
          class="target-input"
          :value="target"
          :placeholder="settings.channel === 'serverchan' ? 'Server酱 SendKey（本地存储）' : '邮箱地址（本地存储）'"
          @input="onTargetInput"
        />
      </view>
      <view class="hint">不记录真实密钥到仓库；该字段仅保存在本机/本端 storage。</view>
    </view>

    <view class="card setting-card">
      <view class="setting-title">刷新策略</view>
      <view class="setting-row">
        <text>Dashboard 轮询</text>
        <picker :range="pollOptions" :value="pollIndex" @change="onPollChange">
          <view class="picker-value">{{ selectedPoll }} 秒</view>
        </picker>
      </view>
      <view class="hint">PRD §4.2 / AC-I1：前端轮询 60s 一次；这里保留本地可调。</view>
    </view>

    <view class="card snapshot-card">
      <view class="setting-title">当前配置快照</view>
      <view class="snapshot-line">溢价：{{ fmtPct(settings.premiumThreshold, 1) }}</view>
      <view class="snapshot-line">折价：-{{ fmtPct(settings.discountThreshold, 1) }}</view>
      <view class="snapshot-line">通道：{{ settings.channel }}</view>
      <view class="snapshot-line">轮询：{{ settings.pollIntervalMs / 1000 }} 秒</view>
      <button class="reset-btn" @tap="resetSettings">恢复默认</button>
    </view>
  </view>
</template>

<style scoped lang="scss">
.page { padding: 24rpx; padding-bottom: 48rpx; }
.card { margin-bottom: 20rpx; }
.setting-title { font-size: 30rpx; font-weight: 700; color: #1f2d3d; margin-bottom: 16rpx; }
.setting-row { display: flex; align-items: center; justify-content: space-between; padding: 18rpx 0; border-top: 1rpx solid #f0f2f5; }
.col-row { align-items: stretch; flex-direction: column; gap: 12rpx; }
.row-head { display: flex; align-items: center; justify-content: space-between; }
.value { font-weight: 700; }
.hint { color: #909399; font-size: 24rpx; line-height: 1.5; }
.picker-value { min-width: 180rpx; padding: 12rpx 20rpx; border-radius: 999rpx; background: #f5f7fa; color: #1f2d3d; text-align: center; }
.target-input { height: 72rpx; padding: 0 20rpx; border-radius: 10rpx; background: #f5f7fa; color: #303133; }
.snapshot-line { color: #606266; font-size: 26rpx; line-height: 1.9; }
.reset-btn { margin-top: 20rpx; background: #1f2d3d; color: #fff; font-size: 28rpx; }
</style>
