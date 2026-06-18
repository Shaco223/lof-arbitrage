# lof-fetcher · 本机 Python 拉取器

## 职责
- 盘中每分钟拉取 LOF / 重仓股 / 指数行情
- 计算实时 IOPV、溢价率、估算覆盖率
- 通过 uniCloud `ingest/realtime` 接口写入数据库
- 触发告警（Server酱 / 邮件）

## 技术栈
- Python 3.11
- apscheduler / httpx / pandas / loguru / pydantic-settings

## 目录约定（待 dev-004 实现）
```
lof-fetcher/
├── fetcher/
│   ├── __init__.py
│   ├── main.py              # 入口
│   ├── config.py            # pydantic-settings
│   ├── sources/             # 数据源适配（东财/新浪/天天/集思录）
│   ├── engine/              # IOPV / 溢价 / 覆盖率
│   ├── alert/               # 阈值与冷却
│   └── ingest/              # 调用 uniCloud ingest 接口
├── tests/
├── requirements.txt
├── .env.example
└── README.md
```

## 当前状态
- M1 首版骨架已建立：`fetcher/sources`、`fetcher/engine`、`fetcher/alert`、`fetcher/ingest`。
- `engine/coverage.py` 已按 PRD §M2 双公式实现：指数型使用基准+现金，行业/主动型使用前十大+剩余仓位基准补全。
- `engine/premium.py` 提供 IOPV 与溢价率基础计算。
- `scripts/validate_watchlist.py` 可生成 `assets/watchlist-v1-validation.md`，只输出报告，不修改 watchlist。

## 常用命令

```powershell
cd lof-fetcher
pip install -r requirements.txt
python -m pytest -q
$env:PYTHONPATH='.'; python scripts\validate_watchlist.py --watchlist ..\assets\lof-watchlist-v1.csv --output ..\assets\watchlist-v1-validation.md
```

## 元数据验证说明
- 默认数据源：东方财富 `https://fund.eastmoney.com/pingzhongdata/{code}.js`。
- HTTP 客户端统一 `trust_env=False`，避免本机代理污染公开接口访问。
- `pending_verify` 条目只在报告中标记回推，最终是否替换由 dev-001/dev-002 决策。

## 不要做
- 不直接对前端开放接口（前端只读 uniCloud REST API）
- 不在仓库提交 `.env` / `.venv` / `__pycache__`
