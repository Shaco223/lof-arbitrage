# uniCloud 阿里云部署与本地联调说明

## 适用范围

本文档用于在 HBuilderX 部署 `uniCloud-aliyun/` 下的数据库 schema 与云函数，并说明 M1 联调闭环的本地 smoke 方法。

云函数目录名保持当前工程命名：

- `lof-list`
- `lof-detail`
- `lof-history`
- `lof-ingest`

对外契约仍对应 PRD §6 的 `api-lof-list` / `api-lof-detail` / `api-lof-history` / `ingest-realtime`，不新增或改名字段。

## 前置条件

- HBuilderX 已登录 DCloud 账号。
- 已开通 uniCloud 阿里云免费空间。
- 本地仓库已同步到包含 watchlist-v2 / benchmark-v2 的主干。
- 已准备 `UNICLOUD_INGEST_TOKEN`，不要写入仓库。

## 数据库初始化

1. 在 HBuilderX 打开项目根目录或 `uniCloud-aliyun/`。
2. 关联阿里云服务空间。
3. 根据 `database/db_init.json` 创建集合和索引：
   - `lof_meta`
   - `lof_holdings`
   - `lof_realtime`
   - `lof_history`
   - `alert_log`
4. 上传 `database/schema/*.schema.json`。
5. 确认 `lof_realtime` 有 `code+ts` 与 `ts` 索引，`lof_history` 有 `code+date` 唯一索引。

## 云函数部署

1. 右键 `cloudfunctions/lof-list` 上传部署。
2. 右键 `cloudfunctions/lof-detail` 上传部署。
3. 右键 `cloudfunctions/lof-history` 上传部署。
4. 右键 `cloudfunctions/lof-ingest` 上传部署。
5. 给 `lof-ingest` 配置环境变量：
   - `UNICLOUD_INGEST_TOKEN=<与 lof-fetcher .env 一致的 token>`
   - `MAX_INGEST_BATCH_SIZE=100`（可选，默认 100）

## URL 化云函数

为四个函数启用 URL 化访问，并把地址提供给前端和拉取器：

| 云函数 | 调用方 | 说明 |
| --- | --- | --- |
| `lof-list` | 前端 | Dashboard 30 只 v2 列表 |
| `lof-detail` | 前端 | 详情页头部、覆盖率明细、基准组件、重仓股 |
| `lof-history` | 前端 | 30 天历史或当日分钟数据 |
| `lof-ingest` | `lof-fetcher` | 批量写入实时快照 |

`lof-ingest` 必须带 Header：`X-Ingest-Token: <token>`。

## 本地 mock 数据与 smoke

本地 smoke 不连接真实 uniCloud；它使用 `uniCloud-aliyun/tests/mock-unicloud.js` 注入内存数据库，数据来自 `uniCloud-aliyun/tests/sample-dataset.json`。

生成或刷新 mock 数据：

```powershell
python lof-fetcher\scripts\generate_unicloud_mock_data.py
```

运行四个云函数本地 smoke：

```powershell
node uniCloud-aliyun\tests\local-api-smoke.test.js
```

覆盖路径：

- `lof-list` 返回 30 行 v2 池。
- `lof-detail` 返回 `coverage_breakdown`、`benchmark_components`、`holdings_top10`、`realtime`。
- `lof-history?days=30` 返回 30 条日线样例。
- `lof-ingest` 覆盖 token 错误 `4010`、缺字段 `4001`、正常批量写入 `accepted=30`。

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
  -Body (Get-Content -Raw outputs\backend-sample-ingest-realtime-v2.json)
```

预期：`data.accepted = 30`，`data.rejected = 0`。

### 前端读取接口

```powershell
curl "<lof-list-url>?sort=code"
curl "<lof-detail-url>?code=161725"
curl "<lof-history-url>?code=161725&days=30"
```

预期：列表 30 行，详情包含 `coverage_breakdown`，历史不少于 20 个交易日样例。

## 配额控制

- `lof-fetcher` 每分钟合并 30 只 LOF 为 1 次 `lof-ingest` 请求。
- `lof-ingest` 单次使用 `db.collection('lof_realtime').add(docs)` 批量写入。
- 列表、详情、历史仅读当日实时表和必要历史窗口，不拖全历史。
- `lof-history` 的 `days` 最大 60，避免超额读取。

## 常见问题

- 返回 `4010`：token 未配置、配置错空间、Header 名拼写错误。
- 返回 `4001`：payload 字段缺失或类型错误，按 PRD §6.4 对齐。
- 返回 `4040`：`lof_meta` 未初始化或 code 不在 v2 自选池。
- 前端字段为空：先确认 `lof_realtime` 是否已有当日数据，再查 `lof_meta` 是否有 30 行基础元数据。


## AC-C2 / AC-S1 ????

dev-004 ???????????

```powershell
cd lof-fetcher
python -m fetcher.main ac-evidence --output-dir ..\outputs
```

???

- `outputs/backend-ac-c2-retry-success-v2.jsonl`?? 2 ????? 3 ????
- `outputs/backend-ac-c2-retry-failure-v2.jsonl`?3 ????? `skipped`?? `pollute_history=false`?
- `outputs/backend-ac-s1-quota-estimate-v2.json`??????????

AC-S1 ?? 3 ???????????????????????????? dev-005 ?????????

## 本地真实 API 服务（默认联调入口）

为避免继续消耗线上 uniCloud 免费配额，M1 后续前后端/测试联调默认使用本地真实 API 服务。该服务不是前端 mock；它在本机以 HTTP 方式暴露与线上 URL 化云函数一致的四个路径，并复用 `cloudfunctions/` 中的业务实现和 `tests/sample-dataset.json` 数据。

### 启动命令

```powershell
cd uniCloud-aliyun
$env:LOCAL_API_PORT='8787'
$env:UNICLOUD_INGEST_TOKEN='local-dev-token'
node local-api-server.js
```

启动后 base URL：

```text
http://localhost:8787
```

四个接口路径与线上一致：

- `GET /lof-list?sort=code`
- `GET /lof-detail?code=160119`
- `GET /lof-history?code=160119&days=30`
- `POST /lof-ingest`，Header：`X-Ingest-Token: local-dev-token`

### 前端本地真实接口配置

```env
VITE_USE_MOCK=false
VITE_API_BASE=http://localhost:8787
VITE_API_FN_LIST=lof-list
VITE_API_FN_DETAIL=lof-detail
VITE_API_FN_HISTORY=lof-history
VITE_API_FN_INGEST=lof-ingest
```

前端联调只读页面不得调用 `lof-ingest`，也不需要 token。

### 本地 smoke

```powershell
node uniCloud-aliyun\tests\local-http-smoke.test.js
```

覆盖项：

- `lof-list` 返回 30 行 v2 池。
- `lof-detail` 返回 `coverage_breakdown` 与 `realtime`。
- `lof-history?days=30` 返回不少于 20 个交易日样例。
- `lof-ingest` 保留 token 校验：缺 token 返回 `4010`，带本地 token 正常返回 `accepted=30,rejected=0`。
