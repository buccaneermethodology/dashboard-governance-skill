# 规划落盘检查

> 这是实施前的规划时点记录；终态以 `Validation_and_Closeout.md` 为准。

- 本轮范围：设计并写入 G-001、BI-001、SP-001、S-001 及决策索引；未执行修复。
- 基线：v0.4.0 / a0bce4891acc81984c1da6703c610413f95ee45d。
- 状态边界：全部修复项为 todo；没有独立验证、修复完成或发布声明。
- 结构检查：2026-10-01 已通过 `python3 -B scripts/validate_dashboard.py Dashboard --contract examples/contracts/dashboard_governance_contract.json` 与 `python3 -B scripts/validate_artifacts.py Dashboard/Artifacts`，均返回 0。
- 回读检查：9 个 Markdown 文件均非空；本地 Markdown 链接均存在；4 个索引表的列宽一致，所有数据行仍为 todo。
- 工作区边界：`git status --short` 仅显示新增 `Dashboard/`；`git diff --check` 通过，但新增未跟踪文件另用直接读取检查，不能仅靠 git diff 声称覆盖。
- registry 校验：不适用，本项目 Dashboard 未安装 registry；不能把示例 registry 校验算成本目录的 reconciliation。
- advanced v2 校验：不适用，当前为 minimal 核心加可选计划索引，未配置项目 managed authority。
