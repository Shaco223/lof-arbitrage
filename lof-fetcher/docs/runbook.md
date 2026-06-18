# lof-fetcher 本机运行 SOP

## 适用范围

本文档用于后端 dev-004、测试 dev-005、前端联调 dev-003 在本机启动或验证 `lof-fetcher/`。当前 M1 为骨架阶段，真实盘中循环任务需在数据源填实后开启。

## 环境要求

- Python：3.11（PRD 硬约束）。若本机暂为 3.10，只允许跑骨架单测，不作为正式运行环境。
- 网络：可访问东方财富 / 新浪等公开接口。
- 不提交文件：`.env`、`.venv/`、`__pycache__/`、真实 token。

## 首次初始化

```powershell
cd lof-fetcher
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
Copy-Item .env.example .env
```

若 Windows 本机没有 `py -3.11`，先安装 Python 3.11 后再继续，不要把系统 Python 3.10 当正式运行环境。

## `.env` 配置

| 变量名 | 必填 | 说明 |
| --- | --- | --- |
| `UNICLOUD_INGEST_URL` | Y | uniCloud URL 化云函数 `lof-ingest` 地址 |
| `UNICLOUD_INGEST_TOKEN` | Y | 与云函数环境变量一致的写入 token |
| `FETCH_INTERVAL_SECONDS` | N | 默认 60 秒 |
| `HTTP_TIMEOUT_SECONDS` | N | 默认 10 秒 |
| `WATCHLIST_PATH` | N | 默认 `../assets/lof-watchlist-v1.csv` |
| `BENCHMARK_MAPPING_PATH` | N | 默认 `../assets/benchmark-mapping-v1.csv` |
| `ALERT_PREMIUM_THRESHOLD` | N | 默认 `0.05` |
| `ALERT_DISCOUNT_THRESHOLD` | N | 默认 `-0.02` |
| `ALERT_COOLDOWN_MINUTES` | N | 默认 `30` |

## 本地验证

```powershell
cd lof-fetcher
python -m pytest -q
$env:PYTHONPATH='.'; python scripts\validate_watchlist.py --watchlist ..\assets\lof-watchlist-v1.csv --benchmark ..\assets\benchmark-mapping-v1.csv --output ..\assets\watchlist-v1-validation.md
python -m fetcher.main
```

预期结果：

- 单测通过。
- `validate_watchlist.py` 只更新验证报告，不修改 `lof-watchlist-v1.csv`。
- `python -m fetcher.main` 能加载 watchlist 与 benchmark mapping 并打印数量。

## 盘中运行流程（数据源填实后）

1. 盘前 09:20 激活 venv，确认 `.env` 指向生产或联调 cloud function。
2. 运行单次 smoke，确认 ingest token 与 URL 正确。
3. 09:30–11:30 / 13:00–15:00 只开启 1 个 fetcher 进程，避免重复写入。
4. 每分钟批量处理 30 只 LOF，最终只发起 1 次 `lof-ingest` 请求。
5. 15:05 后停止盘中任务，等待 18:00 校准任务或手动校准。

## 故障处理

- `4010`：检查 `.env` 中 `UNICLOUD_INGEST_TOKEN` 与云函数环境变量是否一致。
- `4001`：检查 payload 是否符合 PRD §6.4：`ts` + `items[].code/price/iopv/premium/coverage/source_quality`。
- `4290`：降低批次频率或确认是否重复启动多个 fetcher。
- 网络错误：参见 `lof-fetcher/docs/source-fallback.md`。

## 联调交付

- 给前端：只提供 uniCloud URL 化云函数地址，不提供 fetcher 本机地址。
- 给测试：提供 `.env.example`、运行命令、样本 payload、`watchlist-v1-validation.md`。
- 给项目经理：任何 PRD §6 字段变更先走 CCR，不直接改代码契约。
