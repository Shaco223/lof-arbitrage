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
- 空骨架，等待 dev-004 在 PRD 1.1 通过后于 `feat/fetcher-iopv-engine` 等分支实现。

## 不要做
- 不直接对前端开放接口（前端只读 uniCloud REST API）
- 不在仓库提交 `.env` / `.venv` / `__pycache__`
