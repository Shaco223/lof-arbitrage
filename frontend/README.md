# frontend · uni-app（一期 H5 / 二期微信小程序）

## 职责范围
- Dashboard：LOF 实时溢价列表，字段按 PRD §4.3 / §6.1 展示；mock 默认池已切到 `assets/lof-watchlist-v2.csv` 的 30 只。
- Detail：单只 LOF 实时快照、coverage_breakdown 三段式覆盖率、历史走势与 30 天分位。
- Settings：溢价/折价阈值、推送通道、轮询间隔，本期写入本地 storage。

## 技术栈
- uni-app + Vue 3 + setup script + uni-ui easycom + pinia。
- 图表优先使用跨端 `canvas`，避免 DOM / window / document 等明显 H5-only 写法，预留 AC-S3 小程序构建。
- 业务请求只用 `uni.request`，不使用 vue-router / axios；不直连 `lof-fetcher`。

## 目录结构
```text
frontend/
├── src/
│   ├── pages/
│   │   ├── index/index.vue          # Dashboard 列表
│   │   ├── detail/detail.vue        # 详情页 + coverage_breakdown + 历史图
│   │   └── settings/settings.vue    # 阈值与推送通道
│   ├── api/
│   │   ├── index.ts                 # uniCloud 调用封装：list/detail/history/ingest mock
│   │   └── types.ts                 # PRD §6 字段契约
│   ├── mock/index.ts                # mock 数据，默认同步 watchlist-v2，结构复刻 PRD §6 四接口
│   ├── store/settings.ts            # pinia 本地设置
│   ├── utils/format.ts              # 百分比/覆盖率/交易时段工具
│   ├── App.vue / main.ts / pages.json / manifest.json
│   └── styles/index.scss
├── scripts/check-mock-contract.mjs   # mock 契约自检
├── scripts/sync-watchlist-v2-mock.cjs # 从 assets v2 生成前端 mock 默认池
├── package.json
└── .env.example
```

## 启动方式
```powershell
cd F:\CodexWorkspace\10-项目\2026-06-17-LOF基金套利信息\.worktrees\dev-003-frontend\frontend
npm install
npm run dev:h5
```

浏览器访问 uni-app CLI 输出的本地 H5 地址。

## 验证命令
```powershell
# mock 是否覆盖 PRD §6 list/detail/history/ingest 字段
npm run check:mock-contract

# Real API config check for current dev-004 uniCloud function names
npm run check:real-api-config

# H5 构建
npm run build:h5

# 小程序兼容构建（AC-S3 预留，不改源码）
npm run build:mp-weixin
```

## 接口切换
复制 `.env.example` 为 `.env.development`，联调时填写 dev-004 提供的 uniCloud URL：

```env
VITE_API_BASE=https://xxx.next.bspapp.com
VITE_USE_MOCK=false
VITE_POLL_INTERVAL_MS=60000
# Defaults follow dev-004 current uniCloud function directories; response fields still follow PRD section 6
VITE_API_FN_LIST=lof-list
VITE_API_FN_DETAIL=lof-detail
VITE_API_FN_HISTORY=lof-history
VITE_API_FN_INGEST=lof-ingest
```

- `VITE_USE_MOCK=true`：三页使用 `src/mock/index.ts`，可脱离后端演示。
- `VITE_USE_MOCK=false`：调用 `VITE_API_BASE/api-lof-list`、`api-lof-detail`、`api-lof-history`。
- `ingest-realtime` 真实写入由 dev-004 调用；前端仅保留 mock 契约与封装，不在页面触发。

## watchlist-v2 默认池
- `src/mock/index.ts` 已由 `scripts/sync-watchlist-v2-mock.cjs` 从 `assets/lof-watchlist-v2.csv` 与 `assets/benchmark-mapping-v2.csv` 生成。
- 当前 mock 包含 30 只 LOF；`active_low_liquidity` 在前端 `source_quality` 中展示为 `degraded`，便于区分低流动性标的。
- QDII 已按主干决策后置二期，mock 默认池不主动加入 QDII。

## PRD §6 契约影响
- `api-lof-list`：返回 `ts + items[]`，列表项含 `code/name/type/price/iopv/premium/coverage/pctile_30d/source_quality`。
- `api-lof-detail`：返回 `coverage_top10/coverage_breakdown/benchmark_components/holdings_top10/realtime/pctile_30d` 六块。
- `api-lof-history`：返回 `code/granularity/items[]`，历史项含收盘价、官方净值、收盘溢价、30 天分位。
- `ingest-realtime`：mock 返回 `{ accepted, rejected }`；真实写入不由前端页面调用。
