# uniCloud 阿里云部署说明

## 适用范围

本文档用于在 HBuilderX 中部署 `uniCloud-aliyun/` 下的数据库 schema 与云函数骨架。当前云函数名称为 `lof-list` / `lof-detail` / `lof-history` / `lof-ingest`，与前端 mock 可通过 URL 化云函数进行联调。

## 前置条件

- HBuilderX 已登录 DCloud 账号。
- 已开通 uniCloud 阿里云免费空间。
- 本地仓库已同步到包含 `df72a4b` 之后的主干。
- 已准备 `UNICLOUD_INGEST_TOKEN`，不要写入仓库。

## 目录检查

```text
uniCloud-aliyun/
├── cloudfunctions/
│   ├── lof-list/
│   ├── lof-detail/
│   ├── lof-history/
│   └── lof-ingest/
└── database/
    ├── db_init.json
    └── schema/
```

每个云函数目录内都带独立 `response.js`，便于 HBuilderX 单函数上传，不依赖兄弟目录。

## 数据库初始化

1. 在 HBuilderX 打开项目根目录或 `uniCloud-aliyun/`。
2. 关联阿里云服务空间。
3. 根据 `database/db_init.json` 创建集合与索引：
   - `lof_meta`
   - `lof_holdings`
   - `lof_realtime`
   - `lof_history`
   - `alert_log`
4. 上传 `database/schema/*.schema.json`。
5. 确认 `lof_realtime` 有 `code+ts` 与 `ts` 索引，`lof_history` 有 `code+date` 唯一索引。

## 云函数部署

1. 右键 `cloudfunctions/lof-list` → 上传部署。
2. 右键 `cloudfunctions/lof-detail` → 上传部署。
3. 右键 `cloudfunctions/lof-history` → 上传部署。
4. 右键 `cloudfunctions/lof-ingest` → 上传部署。
5. 为 `lof-ingest` 配置环境变量：
   - `UNICLOUD_INGEST_TOKEN=<与 lof-fetcher .env 一致的 token>`
   - `MAX_INGEST_BATCH_SIZE=100`（可选，默认 100）

## URL 化云函数

为四个函数启用 URL 化访问，并把地址提供给前端/拉取器：

| 云函数 | 调用方 | 说明 |
| --- | --- | --- |
| `lof-list` | 前端 | Dashboard 列表 |
| `lof-detail` | 前端 | 详情页头部与覆盖率明细 |
| `lof-history` | 前端 | 30 天历史或当日分钟数据 |
| `lof-ingest` | `lof-fetcher` | 批量写入实时快照 |

`lof-ingest` 必须带 Header：`X-Ingest-Token: <token>`。

## 部署后 smoke

### ingest 鉴权失败

```powershell
curl -Method POST `
  -Uri "<lof-ingest-url>" `
  -Headers @{ "Content-Type" = "application/json"; "X-Ingest-Token" = "bad" } `
  -Body '{"ts":"2026-06-18T10:31:00+08:00","items":[]}'
```

预期：`code = 4010`。

### ingest 正常写入

```powershell
curl -Method POST `
  -Uri "<lof-ingest-url>" `
  -Headers @{ "Content-Type" = "application/json"; "X-Ingest-Token" = "<token>" } `
  -Body '{"ts":"2026-06-18T10:31:00+08:00","items":[{"code":"161725","price":0.823,"iopv":0.805,"premium":0.0224,"coverage":1,"source_quality":"ok"}]}'
```

预期：`data.accepted = 1`。

## 配额控制

- `lof-fetcher` 每分钟合并 30 只 LOF 为 1 次 `lof-ingest` 请求。
- `lof-ingest` 单次使用 `db.collection('lof_realtime').add(docs)` 批量写入。
- 前端列表/详情/历史只读 uniCloud，不直连本机 fetcher。
- `lof-history` 的 `days` 最大 60，避免把全历史拖出。

## 常见问题

- 返回 `4010`：token 未配置、配置错空间、Header 名拼写错误。
- 返回 `4001`：payload 字段缺失或类型错误，按 PRD §6.4 对齐。
- 返回 `4040`：`lof_meta` 未初始化或 code 不在自选池。
- 部署后前端字段为空：先确认 `lof_realtime` 是否已有当日数据，再查 `lof_meta` 是否有 30 行基础元数据。
