# 决策索引

| ID | Topic | Status | Options | Decision | Rationale | Next Step | Notes |
| --- | --- | --- | --- | --- | --- | --- | --- |
| DEC-001 | 多文件写入的恢复实现 | `done` | 暂存加备份回滚；持久恢复日志加受控恢复 | 采用暂存、持久备份/日志、失败回滚及显式 recover | 回滚也可能失败，恢复不能依赖损坏 manifest；逐文件替换不等于跨文件原子性 | 按 docs/registry-reconcile-recovery.md 实现与验证 | 2026-10-01 M1 冻结；进程崩溃、掉电、并发写入明确不在保证范围 |
