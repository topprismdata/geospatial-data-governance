# 协议对齐与证据/候选 Crosswalk（WP01 交付物）

2026-10-12 ｜ 模块①数据管理整合计划 WP01 ｜ 配套: `protocol/dq_verdict_protocol_v1.json`

## 1. 裁决词汇对齐（四仓 → 统一协议）

权威映射表在 `protocol/dq_verdict_protocol_v1.json` 的 `vocabulary_alignment` 节（机器可读），本文是摘要。

| 仓库 | 本地词汇 | 统一词汇 (prism:dq) |
|---|---|---|
| **SSI**（基线） | ALLOW / ALLOW_WITH_LIMITS / REVIEW / **BLOCK_FOR_PROFILE** | 原名保留；BLOCK_FOR_PROFILE→**BLOCK**（profile 入 scope） |
| **SSI**（基线） | NONE / QUARANTINE_SCOPE / SUSPEND_SOURCE / REPAIR_REQUIRED / INVESTIGATION_REQUIRED | QUARANTINE_SCOPE→**QUARANTINE**（范围入 scope） |
| GeoGov | batch_verdict: PASS / 有条件合格 / 不合格 | ALLOW / ALLOW_WITH_LIMITS / BLOCK |
| spatial-ca | PASSED / PASSED_WITH_INVALID_ROWS_DROPPED / INCLUDING_CONFIRMED_OUTLIER / BLOCKED_BY_DATA_QUALITY / STRUCTURE_ONLY | ALLOW / ALLOW_WITH_LIMITS / ALLOW_WITH_LIMITS（附离群声明）/ BLOCK / ALLOW_WITH_LIMITS（禁绝对 km） |
| SRAF | validate_region_pack 逐项快速失败 | 任一失败→BLOCK（含原因清单）；全过→进入后续体检（非最终 ALLOW） |
| mousheng | 置信 High / Medium / Low | ALLOW / ALLOW_WITH_LIMITS / ALLOW_WITH_LIMITS（覆盖率<20% 强制附限制） |

五条不变量（fail-closed、Hard Gate 覆盖、BLOCK 不发布、原始记录不静默覆盖、决策不可变 supersedes）见协议文件 `invariants` 节。

## 2. 证据合同 crosswalk：prism-ontology × topprismwiki

| 要素 | prism-ontology（schema 层） | topprismwiki（实例准入层） | 对齐方式 |
|---|---|---|---|
| 证据是什么 | `prism:core/Evidence` + `evidenceSource` + `sampleCount`（概念/属性契约） | 证据合同 = 来源身份 + 证据锚点 + 内容哈希 + 主体/客体 + 时间适用范围 + 审阅决定 | **schema vs 实例分层**：wiki 证据合同的每个字段用 prism 词汇表达；EvidenceID (`EV-...-<hash8>`) 内容寻址，与 wiki 内容哈希要素直接兼容 |
| 来源治理 | `sources.yaml`（Ctrip/Dianping/AMap 数据源标识） | 来源批准账本（批准/排除/重新准入事件） | wiki 批准账本是 sources.yaml 条目的实例级准入台账；ID 用 sources.yaml 的 source key |
| 审阅 | —（概念层无审阅流） | 审阅包 + 审阅决定（合同要素之一） | 审阅是 wiki 领地；审阅决定作为证据合同的一部分被 prism:Evidence 引用 |
| 发布不可变 | dist 不可变 + checksums.sha256（概念发行） | Formal Vault 确定性提交器 + 原子提交/回滚 | 同一哲学在两层的实例化：概念发行走 prism 两段式，事实条目走 wiki 原子提交 |

**结论**：不合并。证据的**语义**引用 prism-ontology URI，证据的**准入与账本**留在 topprismwiki。

## 3. 候选提升状态机对齐

| | prism-ontology | topprismwiki |
|---|---|---|
| 候选资产 | `prism:insight/ElevationCandidate`（洞察提升候选） | `relation_candidate`（候选关系层，candidates.json） |
| 永不自动晋升 | 概念：候选≠正式（SHACL 反坍缩同哲学） | 机制：共同出现永不自动晋升 relation_candidate |
| 状态机 | 6 态提案：proposed → accepted / aligned_to_existing / profile_local / mapping_local / rejected / deferred | 6 态生命周期：formalized / duplicate / conflicting / relation_candidate / evidence_insufficient / non_durable |

**统一规则（WP01 裁定）**：
1. 候选→正式的提升**只允许**经 wiki 的审阅提交（候选层 candidates.json → 审阅包 → Formal Vault），提升后的事实条目引用 prism URI；
2. 概念层的**词汇**提升走 prism 6 态提案（MS-PROP）；事实层的**条目**提升走 wiki 6 态生命周期——两台状态机分别管词汇与事实，禁止跨层旁路；
3. 两台状态机中「rejected/deferred」与「duplicate/conflicting/evidence_insufficient/non_durable」语义不互通：概念被拒≠事实不成立，反之亦然。跨层引用时必须显式注明所处状态机。

## 4. 验收对照（WP01）

- [x] 协议 schema 冻结 v1：`protocol/dq_verdict_protocol_v1.json`（含 5 条不变量 + 四仓对齐表）
- [x] 31/31 规则有版本与测试样例：`rules/rule_samples_v1.jsonl`（DQ-Rxxx@dq-rules-v1，31 行）
- [x] ID 命名空间走 MS-PROP：`prism-ontology/proposals/datagovernance/MS-PROP-023-...yaml`（status: proposed）
- [x] wiki crosswalk + 候选状态机统一：本文 §2/§3
