<script setup lang="ts">
// 全局生命周期：仅打印当前模式，便于联调时确认 mock/真实接口走向
import { onLaunch, onShow } from '@dcloudio/uni-app'

onLaunch(() => {
  // eslint-disable-next-line no-console
  console.log('[App] launch, mock =', import.meta.env.VITE_USE_MOCK)
})

onShow(() => {
  // 进入前台
})
</script>

<style lang="scss">
@import './styles/index.scss';
</style>
