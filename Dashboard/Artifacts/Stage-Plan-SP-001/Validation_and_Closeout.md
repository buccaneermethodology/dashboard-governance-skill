# G-001 验证与收口

## 最终结论

- `slice_verdict`: PASS。
- `session_terminal`: true；S-001、SP-001、G-001 已满足完成规则。
- `remaining_must_haves`: 无。
- `scope_delta`: 无；AC-01 至 AC-09 均保留并通过。
- `next_slice`: 无。
- `human_decision_required`: false。
- Claim Ceiling：仅证明本仓库示例 registry 在已测本地文件系统、可捕获错误路径上的恢复行为；不证明进程强杀、机器崩溃、掉电、并发外部写入、下游部署或发布。

独立 Validation reviewer 对最终代码候选给出 `PASS_FOR_M3_FINAL_CANDIDATE`。第一次复核曾发现两项阻断：transaction 删除后 fsync 失败会给出不可执行恢复命令，以及 recover 可跟随 Dashboard 内部 target symlink。Builder 修复并补充回归后，Reviewer 独立复测确认两项 finding 均关闭。M4 随后同步 Dashboard，并重跑 Dashboard 与 artifact 门禁。

## Implementation Delta

| 模块 | 最终变化 | 影响 |
| --- | --- | --- |
| `examples/Dashboard-advanced/tools/session_registry.py` | 加入完整暂存、持久 journal/备份、失败回滚、pending recovery 门禁、显式 `recover`、目标/备份路径与 symlink 校验、真实写入诊断及 no-op 不写入 | 正常双 drift 一次收敛；可捕获失败回滚或留下可执行恢复材料 |
| `scripts/test_registry.py` | 加入真实临时目录上的 AC 标注故障矩阵 | 覆盖非法输入、暂存/提交/fsync/回滚/清理失败、日志逃逸、目标 symlink、mtime 和磁盘字节 |
| `docs/registry-reconcile-recovery.md` | 冻结兼容性、写入、恢复、诊断与未覆盖边界 | 操作者可区分已回滚、需恢复和成功结果 |
| `docs/contracts/G-001/` | 六文件 contract-first 包 | 冻结完整 must-have ledger、结构化 journal 和验收策略 |
| `Dashboard/` | 记录 Goal、SP、BI、Session、决策、验证和收口 | 仅为执行记忆与证据索引，不替代运行时证据 |

基线 v0.4.0 / `a0bce4891acc81984c1da6703c610413f95ee45d` 经独立临时目录注入第二次写入失败，得到：`exit=1 index_changed=true manifest_changed=false`，仅输出 `ERROR: injected second write failure`。这证明 P2-01 在基线可复现；候选相同类别路径由回滚/恢复测试覆盖。

最终候选 SHA-256：

| 文件 | SHA-256 |
| --- | --- |
| `examples/Dashboard-advanced/tools/session_registry.py` | `974381fbc0fbd2a7f12097cce80ed03997d6c8ae7e842b506b587632c79921d7` |
| `scripts/test_registry.py` | `271f6bdffe21dba15d01920127283d0c0d28f485c3d1f5b0c94a948f10ad9438` |
| `docs/registry-reconcile-recovery.md` | `3665796dec3bc12fed38466e261e866454565b36c34e3015d61984209d15c538` |
| `docs/contracts/G-001/constitution.json` | `2d6d06a71180bd5e5206e20ac38a9b7cb9bc7e6288a3a5b8b730d456dc5323df` |
| `docs/contracts/G-001/module-contract.json` | `cb40752fbe439d259149e931be36672ccfa08ff0212482ca20b827d198dbea60` |
| `docs/contracts/G-001/artifact.schema.json` | `06ba5bf1bf42eae1858ea1bf27174ea1638c338941861390ccd558ca31328f1d` |
| `docs/contracts/G-001/example.valid.json` | `ff29643cadad19f8968fb605add5d7134f04dc3a7b9fcc245d2a83d948247e8c` |
| `docs/contracts/G-001/golden.json` | `bd222d244992d68dfcf4c77e5c8598586ca7c83da6cd058454a8da20c6a96ac9` |
| `docs/contracts/G-001/acceptance-policy.json` | `d5aeb377387f8691ca4d1a558bc081f475b4b43dcd16e6aa6ea8c94a91d00fa9` |

## 验收映射

| AC | 终态 | 证据 |
| --- | --- | --- |
| AC-01 | PASS | status-only 用例断言 check 只读、一次 apply、权威字节不变、check/validate 通过 |
| AC-02 | PASS | explicit archive move 用例断言双 drift 一次 apply 收敛 |
| AC-03 | PASS | 重复 ID、畸形行、未知状态/archive、损坏 manifest、apply symlink、journal 逃逸、recover target symlink 均失败且受保护字节不变 |
| AC-04 | PASS | journal、两个目标暂存、首次/第二次提交、两个目标 replace 后 fsync 故障均回到调用前字节，无混合投影 |
| AC-05 | PASS | rollback/cleanup failure 保留材料、阻断门禁、输出真实 changed paths；recover 不解析损坏 manifest；恢复后一次 apply 收敛 |
| AC-06 | PASS | 恢复重试和 check/validate 通过；no-drift apply 的字节和 mtime 不变；正常成功无 recovery 残留 |
| AC-07 | PASS | replace 成功后 fsync 失败报告 `write_performed=true`；回滚后 `final_change=false`；不存在错误 false 或错误成功声明 |
| AC-08 | PASS | `scripts/test_registry.py` 映射 AC 并检查字节、mtime、材料、诊断和既有 DKG/registry 拒绝路径；基线缺陷另行复现 |
| AC-09 | PASS | 独立 Reviewer 检查最终 diff、临时目录磁盘行为、完整门禁、包范围和未覆盖边界；M4 完成 Dashboard 同步与重验 |

## 最终门禁

以下检查均返回 0：

- Skill、minimal/advanced Dashboard、Work Breakdown 和 authority bundle 检查。
- `scripts/test_registry.py`、advanced registry check/validate、DKG 既有拒绝回归。
- example 和项目 artifact validators。
- deterministic release-package test。
- G-001 contract package validator，输出 `CFD-VALID`；该结果仅证明结构关系。
- 项目 Dashboard validator、Python compile、工作树 whitespace 检查。

发布包测试确认构建边界仍只有 `skill/dashboard-governance`。本次 registry、测试、G-001 契约和 Dashboard 文件不在 v0.4.0 安装包内容中；没有提交、发布或下游同步，不能称为已发布修复。

## 方向级复核

BI-001 的当前范围是示例 registry 的写入可靠性与可验证恢复。SP-001 已完成，两个 P2 均关闭，未出现同一方向内仍需本次继续执行的必需项，因此单独将 BI-001 标记 `done`。崩溃一致性、并发锁、下游采用和发布均是新范围，只有出现具体需求时才创建新 Session。
