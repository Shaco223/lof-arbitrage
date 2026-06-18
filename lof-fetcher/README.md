# lof-fetcher · 本机 Python 拉取器

## 职责

- 盘中每分钟拉取 LOF / 重仓股 / 指数行情。
- 计算实时 IOPV、溢价率、估算覆盖率。
- 通过 uniCloud `lof-ingest` 接口写入数据库。
- 触发告警（Server 酱 / 邮件）。

## 技术栈

- Python 3.11
- apscheduler / httpx / pandas / loguru / pydantic-settings

## 目录约定

```text
lof-fetcher/
├── fetcher/
│   ├── main.py              # 入口与样例输出命令
│   ├── config.py            # pydantic-settings
│   ├── sources/             # 数据源适配
│   ├── engine/              # IOPV / 溢价 / 覆盖率
│   ├── pipeline/            # v2 快照与样例输出
│   ├── alert/               # 阈值与冷却
│   └── ingest/              # 调用 uniCloud ingest 接口
├── scripts/
├── tests/
├── requirements.txt
└── README.md
```

## 当前状态

- 默认资产已切到 `assets/lof-watchlist-v2.csv` 与 `assets/benchmark-mapping-v2.csv`。
- `engine/coverage.py` 已按 PRD §M2 双公式实现：指数型使用基准+现金，行业/主动型使用前十大+剩余仓位基准补全。
- `engine/premium.py` 提供 IOPV 与溢价率基础计算。
- `fetcher/pipeline/snapshot.py` 可生成 30 只 LOF 的 realtime snapshot 与 PRD §6 样例响应。
- `scripts/generate_unicloud_mock_data.py` 可刷新 uniCloud 本地 smoke 数据集。
- `scripts/validate_watchlist.py` 保留元数据验证用途，默认报告不作为 M1 联调输入。

## 常用命令

```powershell
cd lof-fetcher
pip install -r requirements.txt
python -m pytest -q
python -m fetcher.main
python -m fetcher.main sample-output --output-dir ..\outputs --ts 2026-06-18T10:31:00+08:00
python -m fetcher.main ac-evidence --output-dir ..\outputs
python scripts\generate_unicloud_mock_data.py
```

## 示例输出

`sample-output` 会生成：

- `outputs/backend-realtime-snapshot-v2.json`
- `outputs/backend-sample-api-lof-list-v2.json`
- `outputs/backend-sample-api-lof-detail-v2.json`
- `outputs/backend-sample-api-lof-history-v2.json`
- `outputs/backend-sample-ingest-realtime-v2.json`

`outputs/*` 默认不入库，作为本地联调交付物传递路径。

## 元数据验证说明

- 默认数据源：东方财富、场内行情、天天基金净值等公开源。
- HTTP 客户端统一 `trust_env=False`，避免本机代理污染公开接口访问。
- watchlist-v2 已由 dev-002 固化；如后续发现资产口径问题，输出报告给 dev-001/dev-002，不直接修改 CSV。

## 运行与运维文档

- 本机运行 SOP：`docs/runbook.md`
- 数据源失败兜底：`docs/source-fallback.md`
- NAV 反推溢价口径：`docs/nav-premium-calibration.md`
- watchlist 验证数据源说明：`docs/watchlist-validation-sources.md`

## 不要做

- 不直接对前端开放 fetcher 本机接口；前端只读 uniCloud URL 化云函数。
- 不直连 uniCloud 数据库写入；拉取器写入只能走 `lof-ingest`。
- 不提交 `.env` / `.venv` / `__pycache__` / 真实 token。
- 不改 PRD §6 字段；字段变更必须走 CCR。


## AC-C2 / AC-S1 ????

```powershell
cd lof-fetcher
python -m fetcher.main ac-evidence --output-dir ..\outputs
```

`ac-evidence` ????

- `outputs/backend-ac-c2-retry-success-v2.jsonl`???? 2 ????? 3 ????
- `outputs/backend-ac-c2-retry-failure-v2.jsonl`??? 3 ????? skipped?`pollute_history=false`?
- `outputs/backend-ac-s1-quota-estimate-v2.json`??????????AC-S1 ?? 3 ?????????
