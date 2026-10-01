# 项目 Dashboard

## 当前前沿（Current Frontier）

- 修复目标：[G-001](Artifacts/Stage-Plan-SP-001/Goal.md)：消除 registry 多文件写入失败后的不受控部分投影，并补齐故障回归。
- 关系：G-001 → [SP-001](Stage_Plans.md) → [S-001](Sessions.md)，归属长期方向 [BI-001](Big_Ideas.md)。
- G-001、SP-001、S-001 已完成全部验收；BI-001 经单独方向级复核后关闭。最终证据见 [Validation_and_Closeout.md](Artifacts/Stage-Plan-SP-001/Validation_and_Closeout.md)。
- 当前无必需后续 Session。若出现下游采用、发布或崩溃/并发一致性需求，应以新范围、新契约启动，不能扩大本次 PASS。

## 治理边界

本目录记录本仓库实际工作，不替换 `examples/Dashboard*` 的通用示例。显式采用 `examples/contracts/dashboard_governance_contract.json` 的生命周期与字段默认值；当前采用 minimal 核心加可选 Stage Plan 索引，不声明 advanced v2 权威配置或合规。计划中的里程碑与职责见 Goal 文档；将来若启用 advanced v2，须先完成项目权威配置与 Work_Breakdown 校验，不能复用示例身份冒充项目授权。

本 Dashboard 未安装 Session registry，无 index/archive/manifest 或 DKG；不声明执行过本目录的 reconcile。运行时修复对象是示例 registry，不能把两者混淆。

状态与计划是执行记忆；后续 M1 冻结的实现契约应写入 `docs/`，Dashboard 保留链接。本轮未改变产品契约。

## 检查

```bash
python3 -B scripts/validate_dashboard.py Dashboard --contract examples/contracts/dashboard_governance_contract.json
python3 -B scripts/validate_artifacts.py Dashboard/Artifacts
git diff --check
```

规划校验结果见 [规划落盘记录](Artifacts/Stage-Plan-SP-001/Planning_Check.md)，不代表两个 P2 已修复。
