# tests · 验收测试骨架（dev-005）

> 适用版本：PRD 1.1（tag `prd-v1.1`）  
> 工作分支：`feat/tests-ac-skeleton`  
> 固定 worktree：`.worktrees/dev-005-test`  
> 职责边界：只做测试验证，不参与需求/开发实现。

## 1. 当前状态

- AC 骨架：已按 PRD §9 实际列项建立 17 个 `AC-*.test.py` 文件；AC-S3 / AC-T1 已填实为可执行测试。
- 契约测试：已按 PRD §6 建立 4 个接口的静态字段结构校验，不依赖真实后端。
- 端到端：已建立拉取器 → ingest → uniCloud → list 的冒烟骨架，当前 pending。
- fixtures：已建立 AC-P1 五只指数 LOF 的离线样本结构，真实分钟数据待 dev-004 提供。

> 说明：PM 派单文字写“16 个 AC”，但 PRD §9 实际列出 17 条：P1/P2、C1/C2、H1/H2、A1/A2/A3、I1/I2/I3/I4、S1/S2/S3、T1。本测试骨架以 PRD §9 为准，保留 17 条。

## 2. 目录结构

```text
tests/
├── ac/                       # PRD §9 AC 一对一骨架，全部 pending
├── contract/                 # PRD §6 静态接口契约测试，当前可执行
├── e2e/                      # 端到端冒烟骨架，当前 pending
├── fixtures/
│   ├── realtime/             # AC-P1 5 只指数 LOF 样本结构
│   ├── holdings/             # 重仓股 fixture 占位
│   └── quotes/               # 行情 fixture 占位
├── _lib/                     # AC 元信息 / 通用工具
├── conftest.py               # pending 自动 skip + 通用 fixture
├── pytest.ini                # testpaths / markers / importlib 配置
└── requirements.txt          # pytest / pytest-asyncio / httpx / pandas
```

## 3. AC 覆盖矩阵

| AC | PRD 章节 | 测试方法摘要 | 通过条件摘要 | 责任模块 | 文件 | 状态 |
| --- | --- | --- | --- | --- | --- | --- |
| AC-P1 | §9.1 | 用官方 NAV 反推真实溢价，对比分钟样本 | `|实时溢价 - 真实溢价| <= 0.5%` | dev-004 | `ac/AC-P1.test.py` | pass |
| AC-P2 | sec 9.1 | watchlist-v2 / benchmark-v2 coverage static check | avg >=90%, count `<70%` <=3, index/industry =1.00 | dev-002/dev-004 | `ac/AC-P2.test.py` | pass |
| AC-C1 | §9.2 | 重放/统计盘中分钟写入行数 | 每分钟 30 行；整分钟缺失 ≤3/日 | dev-004 | `ac/AC-C1.test.py` | pending |
| AC-C2 | §9.2 | mock 数据源失败并观察重试 | 30 秒内重试 3 次；失败写日志并跳过 | dev-004 | `ac/AC-C2.test.py` | pending |
| AC-H1 | §9.3 | 调 history + 前端详情曲线检查 | 30 天无非节假日断点 | both | `ac/AC-H1.test.py` | pending |
| AC-H2 | §9.3 | 离线脚本重算分位并对比 API | 分位 ∈[0,1]，误差 ≤0.01 | dev-004 | `ac/AC-H2.test.py` | pending |
| AC-A1 | §9.4 | 注入溢价 >5% 持续 1 分钟 | ≤2 分钟收到 1 条告警 | dev-004 | `ac/AC-A1.test.py` | pending |
| AC-A2 | §9.4 | 30 分钟内重复触发 | 仅 1 次 sent，其余 cooldown_blocked | dev-004 | `ac/AC-A2.test.py` | pending |
| AC-A3 | §9.4 | 注入非交易时段事件 | 忽略，不发送告警 | dev-004 | `ac/AC-A3.test.py` | pending |
| AC-I1 | §9.5 / §6.1 | 压测 list + schema 校验 | p95 ≤800ms，返回 30 行结构合规 | dev-004 | `ac/AC-I1.test.py` | pending |
| AC-I2 | §9.5 / §6.2 | detail schema + 6 块检查 | 6 块齐全 | dev-004 | `ac/AC-I2.test.py` | pending |
| AC-I3 | §9.5 / §6.3 | history days=30 schema + 行数 | ≥20 个交易日 | dev-004 | `ac/AC-I3.test.py` | pending |
| AC-I4 | §9.5 / §6.4 | ingest 三路径码值校验 | 错 token=4010；缺字段=4001；正常 accepted 等于提交条数 | dev-004 | `ac/AC-I4.test.py` | pending |
| AC-S1 | §9.6 | 统计 3 个交易日 uniCloud 用量 | 云函数/读/写不超免费额度 | dev-004 | `ac/AC-S1.test.py` | pending / hard |
| AC-S2 | §9.6 | 静态扫描架构边界 + H5 编译 | 写入仅走 ingest；前端不直连拉取器 | both | `ac/AC-S2.test.py` | pending |
| AC-S3 | §9.6 | 不改源码执行 mp-weixin 构建 | `npm run build:mp-weixin` 成功 | dev-003 | `ac/AC-S3.test.py` | pass / hard |
| AC-T1 | §9.7 | 静态检查详情页覆盖率标签与三段式字段 | 数值/颜色/三段明细固定展示 | dev-003 | `ac/AC-T1.test.py` | pass / hard |

## 4. PRD §6 契约测试矩阵

| 接口 | PRD 章节 | 测试文件 | 当前检查范围 | 状态 |
| --- | --- | --- | --- | --- |
| `api-lof-list` | §6.1 | `contract/test_api_lof_list_contract.py` | 通用响应、`data.ts`、`items[]` 9 字段、枚举 | pass |
| `api-lof-detail` | §6.2 | `contract/test_api_lof_detail_contract.py` | 6 块、嵌套 coverage/benchmark/holdings/realtime | pass |
| `api-lof-history` | §6.3 | `contract/test_api_lof_history_contract.py` | `code/granularity/items[]` 与历史字段 | pass |
| `ingest-realtime` | §6.4 | `contract/test_ingest_realtime_contract.py` | header、body、success response、错误码集合 | pass |

## 5. 本地运行命令

```powershell
cd F:\CodexWorkspace\10-项目\2026-06-17-LOF基金套利信息\.worktrees\dev-005-test\tests

# 安装测试依赖（如环境未安装）
pip install -r requirements.txt

# 全量自检：AC-S3 / AC-T1 / contract 应 pass；其余 AC/e2e pending 自动 skip
python -m pytest -q

# 仅看 PRD §6 契约测试
python -m pytest -q contract

# 运行硬约束 AC（当前 AC-S3 / AC-T1 pass，AC-S1 pending skip）
python -m pytest -q -m ac_hard

# 按 AC 编号筛选
python -m pytest --collect-only -q -k AC-P1
```

## 6. Bug 上报模板

```markdown
### BUG-xxx [等级]
- AC 编号：AC-xx
- 复现步骤：
- 期望结果：
- 实际结果：
- 等级：阻断 / 严重 / 一般 / 提示
- 责任 Agent：dev-003 / dev-004
- 抄送：dev-001
```

## 7. CI 接入预留

```yaml
# .github/workflows/tests.yml（预留）
# - run: pip install -r tests/requirements.txt
# - run: cd tests && python -m pytest -q --junitxml=../outputs/junit-tests.xml
```

## M1 Integration Readiness

- `m1-integration-readiness.md` tracks AC-I1~I4 / AC-C1~C2 / AC-P2 / AC-S1 integration inputs, pass criteria, and field-drift bug template.
- Before dev-004 provides runnable API / sample output, related AC tests remain pending or static acceptance; no real API assertions are added yet.

## 8. 当前已知限制

- 大部分 AC 骨架不跑真实功能，直到 dev-003 / dev-004 对应模块交付后才逐条移除 `pending`；当前已填实 AC-S3 / AC-T1。
- contract 测试只校验 PRD §6 字段结构，不验证真实后端可用性、性能或数据库状态。
- AC-S1 需要连续 3 个真实交易日统计，当前只能保持 pending。
