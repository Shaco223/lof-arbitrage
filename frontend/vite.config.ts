import { defineConfig } from 'vite'
import uni from '@dcloudio/vite-plugin-uni'

// uni-app Vue3 + Vite 配置
// - 同一份源码可编译 H5（一期）与 微信小程序（二期，AC-S3）
// - H5 dev 时 /api 走 uniCloud URL 化云函数（由 .env.* 注入实际地址）
export default defineConfig({
  plugins: [uni()],
  server: {
    host: '0.0.0.0',
    port: 5173
  }
})
