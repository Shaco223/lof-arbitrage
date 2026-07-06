import { defineConfig, loadEnv } from 'vite'
import uni from '@dcloudio/vite-plugin-uni'

// uni-app Vue3 + Vite 配置
// - 同一份源码可编译 H5（一期）与 微信小程序（二期，AC-S3）
// - H5 dev 时 /api 走 uniCloud URL 化云函数（由 .env.* 注入实际地址）
// - 可选 VITE_DEV_PROXY_TARGET：本机 dev 时把 /api 反向代理到该地址（例如线上服务器）
//   仅本地 .env.development 使用；不提交此值，避免污染其他开发者环境
export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, process.cwd(), '')
  const proxyTarget = env.VITE_DEV_PROXY_TARGET
  return {
    plugins: [uni()],
    server: {
      host: '0.0.0.0',
      port: 5173,
      proxy: proxyTarget
        ? {
            '/api': {
              target: proxyTarget,
              changeOrigin: true
            }
          }
        : undefined
    }
  }
})