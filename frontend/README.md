# frontend · uniapp H5（一期）/ 微信小程序（二期）

## 职责
- 30 只 LOF 实时溢价 Dashboard
- 单只 LOF 详情页（30 天曲线 + 分位 + 估算覆盖率标签）
- 设置页（阈值 / 推送通道）

## 技术栈（硬约束）
- **必须使用 uniapp**（Vue 3 + setup script + uni-ui + ucharts + pinia）
- 一期编译目标：H5
- 二期编译目标：微信小程序（不改源码 npm run build:mp-weixin 即可，AC-S3）

## 目录约定（HBuilderX uniapp 默认结构，待 dev-003 实现）
```
frontend/
├── pages/
│   ├── index/index.vue          # Dashboard
│   ├── detail/detail.vue        # 详情页
│   └── settings/settings.vue    # 设置页
├── components/                  # 通用组件
├── api/                         # uniCloud 调用封装
├── store/                       # pinia
├── static/                      # 静态资源
├── manifest.json                # uniapp 全局配置
├── pages.json                   # 路由
├── App.vue
├── main.js
└── README.md
```

## 当前状态
- 空骨架，等待 dev-003 在 PRD 1.1 通过后于 `feat/frontend-dashboard` 等分支实现。
- 上一版误启动的 Vite + Vue 3 工程已归档到分支 `wip/legacy-vite-python`，不再使用。

## 不要做
- 不使用 Vite / vue-router / axios（用 uniapp 内置等价物）
- 不直连 lof-fetcher（只调 uniCloud REST API）
