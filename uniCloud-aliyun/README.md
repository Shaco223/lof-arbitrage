# uniCloud-aliyun · 后端云空间工程

## 职责
- 数据库（lof_meta / lof_holdings / lof_realtime / lof_history / alert_log）
- REST 云函数（list / detail / history / ingest）
- 每日 18:00 校准定时任务

## 技术栈
- uniCloud 阿里云免费空间
- Node.js 18 云函数
- JQL（MongoDB 兼容）

## 目录约定（待 dev-004 实现）
```
uniCloud-aliyun/
├── cloudfunctions/
│   ├── api-lof-list/
│   ├── api-lof-detail/
│   ├── api-lof-history/
│   ├── ingest-realtime/      # 拉取器写入接口（带签名）
│   └── cron-daily-calibrate/ # 每日校准
├── database/
│   ├── db_init.json
│   └── schema/               # JQL Schema
└── README.md
```

## 当前状态
- 数据库初始化：`database/db_init.json`。
- JQL Schema：`lof_meta` / `lof_holdings` / `lof_realtime` / `lof_history` / `alert_log`。
- 云函数骨架：`lof-list` / `lof-detail` / `lof-history` / `lof-ingest`。
- `lof-ingest` 使用 `X-Ingest-Token` 校验，只接受 PRD §6.4 的批量 payload，并一次性 `add(docs)` 写入。

## 云函数返回约定
- 成功：`{ "code": 0, "message": "ok", "data": { ... } }`
- 参数错误：`4001`
- 鉴权失败：`4010`
- 资源不存在：`4040`
- 服务异常：`5000`

## 不要做
- 不直接拉外部数据源（这是 lof-fetcher 的职责）
- 不超免费额度：云函数 5 万/日、库读 5 万、库写 3 万
