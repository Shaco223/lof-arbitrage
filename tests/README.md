# tests · 端到端 / 跨模块测试

## 职责
- 由 dev-005 维护，覆盖 PRD §9 的 16 条 AC
- 模块内单元测试请放在各模块自己的 tests/（如 lof-fetcher/tests/、cloudfunctions/*/tests/）

## 当前状态
- 空骨架，等 PRD 1.1 通过后再写测试用例（避免按错误的 PRD 写完再返工）。

## 目录约定
```
tests/
├── ac/                  # 16 条 AC 一对一脚本
├── fixtures/            # 离线净值数据 / 模拟行情
├── e2e/                 # 端到端
└── README.md
```
