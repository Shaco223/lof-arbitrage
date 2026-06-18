/* eslint-disable */
/// <reference types='@dcloudio/types' />
import 'vue'

declare module '*.vue' {
  import { DefineComponent } from 'vue'
  const component: DefineComponent<{}, {}, any>
  export default component
}

interface ImportMetaEnv {
  readonly VITE_API_BASE: string
  readonly VITE_USE_MOCK: string
  readonly VITE_POLL_INTERVAL_MS: string
}
interface ImportMeta {
  readonly env: ImportMetaEnv
}
