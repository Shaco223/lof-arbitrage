import { defineStore } from 'pinia'
import type { MonitorSettings } from '@/api/types'

const STORAGE_KEY = 'lof.monitor.settings'

const defaultSettings: MonitorSettings = {
  premiumThreshold: 0.05,
  discountThreshold: 0.02,
  channel: 'serverchan',
  channelTarget: '',
  pollIntervalMs: 60000
}

function loadFromStorage(): MonitorSettings {
  try {
    const raw = uni.getStorageSync(STORAGE_KEY)
    if (raw) return { ...defaultSettings, ...JSON.parse(raw) }
  } catch (e) {
    /* ignore */
  }
  return { ...defaultSettings }
}

export const useSettingsStore = defineStore('settings', {
  state: (): MonitorSettings => loadFromStorage(),
  actions: {
    update(patch: Partial<MonitorSettings>) {
      Object.assign(this, patch)
      this.persist()
    },
    reset() {
      Object.assign(this, defaultSettings)
      this.persist()
    },
    persist() {
      try {
        uni.setStorageSync(
          STORAGE_KEY,
          JSON.stringify({
            premiumThreshold: this.premiumThreshold,
            discountThreshold: this.discountThreshold,
            channel: this.channel,
            channelTarget: this.channelTarget,
            pollIntervalMs: this.pollIntervalMs
          })
        )
      } catch (e) {
        /* ignore */
      }
    }
  }
})
