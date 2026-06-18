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

## 部署文档
- HBuilderX / uniCloud 阿里云部署说明：`docs/deploy.md`

## 不要做
- 不直接拉外部数据源（这是 lof-fetcher 的职责）
- 不超免费额度：云函数 5 万/日、库读 5 万、库写 3 万

## 本地真实 API 服务

M1 联调默认使用本地真实 API，避免消耗线上 uniCloud 配额。启动命令：

```powershell
cd uniCloud-aliyun
$env:LOCAL_API_PORT='8787'
$env:UNICLOUD_INGEST_TOKEN='local-dev-token'
node local-api-server.js
```

Base URL：`http://127.0.0.1:8787`。接口路径与线上一致：`lof-list` / `lof-detail` / `lof-history` / `lof-ingest`。本地 smoke：

```powershell
node uniCloud-aliyun\tests\local-http-smoke.test.js
```


## M2.2 本地分钟快照

追加本地分钟快照，不上云：

```powershell
node uniCloud-aliyun\local-minute-snapshots.js --output outputs\local-minute-snapshots-v2.jsonl
```

每行包含 `ts` 和 30 条 `items`，用于本地联调与后续历史沉淀验证。


## M3 ????????

?? API ?????? `LOCAL_MINUTE_SNAPSHOT_FILE` ??? JSONL ???????? mock DB ????? `lof_realtime`???????? PRD ?6 ???

```powershell
cd uniCloud-aliyun
$env:LOCAL_API_PORT='8787'
$env:LOCAL_MINUTE_SNAPSHOT_FILE='..\outputs\local-minute-snapshots-v2.jsonl'
node local-api-server.js
```

??/?????? `http://127.0.0.1:8787`????? uniCloud?
