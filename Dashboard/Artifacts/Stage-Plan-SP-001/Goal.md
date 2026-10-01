# G-001：registry 多文件写入失败安全与回归覆盖

## 目标与当前状态

在 `examples/Dashboard-advanced/tools/session_registry.py` 及 `scripts/test_registry.py` 中关闭两个 P2：正常多投影 drift 一次 apply 后通过 check/validate；可捕获写入失败不遗留无法识别或恢复的部分更新；所有成功、失败与恢复结果均与磁盘事实一致，并具有可重复的故障回归证据。

关系：G-001 → SP-001 → S-001；BI-001 为长期方向。S-001 是唯一端到端交付单元，两个问题共享完成条件。测试不是独立交付后的可选尾项。

- Status：`done`。
- Delivery State：M1–M4 已完成；示例 registry、故障回归、恢复契约及收口证据已落盘。
- Claim Ceiling：G-001 对本仓库示例实现及已测本地文件系统故障路径 PASS；不是崩溃/掉电/并发安全、下游安装或发布证明。
- Authority / Blocker：用户授权执行 G-001；DEC-001 已冻结，无未决阻断。
- Evidence：[Validation_and_Closeout.md](Validation_and_Closeout.md) 绑定最终候选摘要、独立复核和逐项 AC 结论。
- Next：无必需后续 Session；若出现下游采用或崩溃一致性需求，另立范围和契约。

## 原问题与归属

| 问题 | 基线源码 | 已知证据及边界 | 修复归属 |
| --- | --- | --- | --- |
| P2-01：部分写入后失败 | registry 第 198–200 行顺序写 index、manifest；第 234–236 行统一返回失败 | 内存注入第二次写入失败，index 已更新而 manifest 未更新；validate 失败，解除故障后重试可恢复。不是磁盘故障实测 | registry 示例实现及采用该实现的下游；本 Goal 只改本仓库 |
| P2-02：缺少失败回归 | test_registry.py 第 57–62 行只测试 index drift 的正常修复 | 没有多投影失败、部分写入、恢复与磁盘状态断言 | 本仓库测试与必要的故障夹具 |

current 与 archive 均为权威输入。仅改 Done 不自动归档；显式迁移到既有受管 archive 才会同时改变索引位置与 manifest 计数。未知 archive 必须拒绝，不能当成可修复 drift。

v0.4.0 没有 `write_performed` 字段或结构化收据，不能把不存在的错误收据归为已证实缺陷。此 Goal 要求诊断真实；是否新增机器可读结果在 M1 决定。如新增，须区分实际写入历史、最终净变化、回滚和恢复状态，不能以“已回滚”为由把发生过的写入标成 false。

发布脚本以 `skill/dashboard-governance` 为源；registry 示例及测试不在规定的安装包范围内。本次 review 取得远端资产元数据但下载失败，未核验远端包内容。后续不得把源码修复表述为已发布安装包修复。

## 范围与兼容性

运行时范围：registry 的预检、完整渲染、暂存、提交、恢复及错误诊断；测试范围：真实临时目录上的确定性故障注入、CLI 行为、磁盘回读与既有拒绝路径。稳定契约写入 `docs/`；本批次保存计划和执行证据。

保持 current/archive 权威、索引/manifest 派生语义，保留现有命令、成功返回 0 与失败非 0、合法输入限制、索引排序及 manifest 内容契约。check 和 validate 保持只读；reconcile 不隐式生成 DKG。

不实现自动归档，不迁移下游项目，不改全局已安装 Skill，不创建收据系统作为额外产品，不修改版本、不提交、不发布。仅在诊断或恢复行为改变时同步相关文档。Dashboard closeout 不是运行时修复证据。

故障模型包括可捕获 OSError、写入中途失败、提交替换失败和恢复自身失败。进程强杀、掉电、并发写入不在本轮保证范围，须在契约明确；不得声称崩溃一致性或多文件瞬时原子性。若设计发现必须扩大这些范围，记录 Scope Delta 后请求范围决定，不静默删除原验收项。

## 验收矩阵（全部为必需）

| ID | 场景 | 必须满足的结果 |
| --- | --- | --- |
| AC-01 | 合法样例中仅把 doing 改为 Done | check 非 0 且只读；一次 apply 为 0；随后 check/validate 为 0；current/archive 字节不变，无自动归档 |
| AC-02 | 显式迁移记录到既有受管 archive，造成 index 与 manifest drift | check 非 0 且无写入；一次 apply 后两个投影正确，check/validate 为 0；不能依赖第二次 apply 完成正常工作 |
| AC-03 | 重复 ID、畸形行、未知状态、未知 archive、符号链接及损坏输入 manifest | 所有模式拒绝非法输入；apply 在提交前失败且不改变权威和派生文件；恢复日志不能用于绕过输入合法性 |
| AC-04 | 各暂存写入、首次提交、第二次提交发生异常，包括写入部分字节后抛错 | CLI 非 0；在恢复能力正常时所有受管文件回到调用前字节；不得截断原 manifest；故障后磁盘回读证明没有混合新旧投影 |
| AC-05 | 第二次提交失败且回滚或清理也失败 | 非 0 并明确 recovery_required、已变更路径、备份/恢复位置和确定恢复步骤；不输出成功或无写入假象；保留恢复材料，check/validate 不误报健康；解除故障后按文档恢复，再一次正常 apply 通过 |
| AC-06 | 故障解除后的重试，以及成功后的无 drift 重复 apply | 不丢记录、不重复记录；check/validate 通过；无 drift apply 不重写受管文件，字节与 mtime 不变；恢复残留按约定清理 |
| AC-07 | stdout/stderr、退出码与可选结构化结果 | 对照真实磁盘差异及写入事件，成功仅在回读确认后报告；失败准确区分提交前拒绝、已回滚和需恢复；若新增 write_performed，不得错误声明 false |
| AC-08 | 回归证据与兼容性 | 新故障测试在基线上暴露 P2-01，在候选上通过；既有 registry/DKG 拒绝测试仍通过；完成 AC-01 至 AC-07 的逐项用例映射，不仅断言返回码 |
| AC-09 | 最终候选与归属复核 | 独立于 Builder 的复核者检查最终 diff、磁盘证据与所有 AC；记录实现摘要、验证结论、未覆盖边界和包范围；Dashboard 与结论一致，无未解决必需项 |

AC-04 的“回到调用前”不表示输入 drift 已修复：失败恢复后 validate 仍可因原 drift 失败，这是正确结果。AC-05 不许用“重跑 apply”替代可执行恢复程序，也不许依赖解析已损坏的 manifest 才能恢复备份。

## S-001 里程碑与职责

| Milestone | 顺序 | 完成产物与条件 | 当前状态 |
| --- | --- | --- | --- |
| M1 | 1 | 冻结 docs 恢复契约、DEC-001、故障注入点、结果语义及 AC 用例映射；落实复核者职责 | 已满足 |
| M2 | 2 | 实现候选和回归测试；基线失败/候选通过证据；完成 Builder 自检 | 已满足 |
| M3 | 3 | 独立复核最终候选；运行全部适用检查，回读真实临时目录文件；逐项给出通过/失败 | 已满足；最终 verdict 为 PASS_FOR_M3_FINAL_CANDIDATE |
| M4 | 4 | 汇总 Implementation Delta、Scope Delta 和验证摘要；复核最终文件后同步 S/SP/Goal/BI 的状态与下一步 | 已满足；见 Validation_and_Closeout.md |

Design 负责 M1 契约；Builder 负责代码与自检；Validation 由未承担实现的复核者执行，不以 Builder 自检替代；Closure 负责证据映射与状态收口。均为计划职责，本轮未创建或执行独立验证任务。若无复核者，M3 未满足，不关闭 Session。

后续执行的检查至少包括：

```bash
python3 -B scripts/test_registry.py
python3 -B scripts/validate_dashboard.py examples/Dashboard-advanced --contract examples/contracts/dashboard_governance_contract.json --require-registry
python3 -B examples/Dashboard-advanced/tools/session_registry.py reconcile --repo examples/Dashboard-advanced --contract examples/contracts/dashboard_governance_contract.json --check
python3 -B examples/Dashboard-advanced/tools/session_registry.py validate --repo examples/Dashboard-advanced --contract examples/contracts/dashboard_governance_contract.json
python3 -B scripts/test_release_package.py
python3 -B scripts/validate_dashboard.py Dashboard --contract examples/contracts/dashboard_governance_contract.json
python3 -B scripts/validate_artifacts.py Dashboard/Artifacts
git diff --check
```

故障用例必须在临时目录执行，不污染示例。M3 固定候选源码/测试摘要；后续改动使相关验证失效，须重跑受影响用例和最终复核。发布包测试仅证明本地打包边界，不是远端发布验证。

## 完成与停止规则

G-001/SP-001/S-001 仅在全部 AC 通过、M1–M4 满足且最终候选复核通过后才能标记 done；BI-001 另作方向级复核，不能自动关闭。2026-10-01 的最终证据满足该规则，方向级复核也确认当前范围无剩余工作。

Implementation Delta、Scope Delta、候选摘要、测试证据、影响与未覆盖边界记录在 Validation_and_Closeout.md。Scope Delta 为无；没有把必需项转移到后续 Session。

遇到需要改权威行、放宽拒绝规则、写出范围、发布/安装操作或扩大故障模型时停止该越界动作并请求范围决定；环境失败与实现失败分开记录。无故障或实现证据时不以文档代替验收。
