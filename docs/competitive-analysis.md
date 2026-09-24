# GeoGov 竞品与生态对比分析(docs 版 v3)

> 日期:2026-09-24 · Google AV 能力与覆盖已核实(官方文档,核查日期 2026-09-24)
> 定位铁律:GeoGov 只判断"这个空间事实可信吗";规划/优化/决策全部属于下游

---

## 0. 买方第一个问题:"为什么不直接用谷歌/高德?"

答:**它们做的是地址验证/地理编码(基于 provider 自身的验证能力);GeoGov 做的是治理——验证你 CRM 里的坐标+地址+行政归属,自己跟自己说不说得通。**

| | Google Address Validation / 高德地理编码 | GeoGov |
|---|---|---|
| 判定问题 | 输入地址的完整性、可确认性与待修正之处(provider-level verdict) | 跨字段一致性(坐标 vs 填报区县 vs 地址结构)+ 群体模式(重复坐标/整批偏移) |
| 证据来源 | 单一 Provider-level verdict;其底层数据组合对调用方不完全透明 | 多源独立信号交叉;provider 是 Evidence,不是 Truth |
| 一致性维度 | 不以企业 CRM 中独立的坐标、行政归属字段做跨字段治理 | 以企业自有字段为主体的治理检查 |
| 中国覆盖 | 截至 2026-09-24,Google AV 官方支持范围不含 CN/HK/MO/TW;高德/百度暂无公开 verdict 类产品 | 中国零售点实战验证:GCJ02、8 位市本级码、区县边界全踩过坑 |
| 输出 | 一次调用的 verdict | 证据链报告 + 风险分级 + 优先级整改清单 |
| 可复现性 | 无规则版本/基准回归概念 | 规则冻结 + Gold Set 回归 + provenance |
| 部署 | SaaS | Core 可本地;Provider 调用按其接口出域(见 §6) |

## 1. 地图服务商逐个分析

### 1.1 Google Address Validation API(已核实)

能力(官方文档):verdict(ACCEPT/CONFIRM/CONFIRM_ADD_SUBPREMISES/FIX)、addressComplete、granularity 三级、推断/替换/纠错组件标志、CASS(仅美国/波多黎各)。官方自身建议"修改用户输入需提示确认"——与 GeoGov "不自动改写" 原则一致。

边界(=GeoGov 的空间):
- 单一 Provider-level verdict,底层数据对调用方不透明;无跨 Provider 仲裁
- 不以企业 CRM 独立字段(坐标/行政归属)做跨字段一致性治理
- 群体异常检测、证据链留存、整改工作流、回归基准不是其核心产品抽象
- 截至 2026-09-24,官方支持范围不含 CN/HK/MO/TW(40 国,日印 preview)——对中国零售门店这一 GeoGov 已验证市场不可用

### 1.2 高德 / 百度 / 腾讯

- 提供:地理编码、逆地理编码、POI(GCJ02 生态)
- 截至 2026-09-24,未在公开产品文档中发现类似 Google AV 的显式 verdict 产品
- 缓存、长期保存与审计需遵守各 Provider 的授权与服务条款
- GeoGov 关系:**Provider 插件**(外部地图交叉信号的数据源)

### 1.3 商业地址验证厂商

Loqate(GBG)、Precisely、Melissa、Smarty:**Research backlog——未完成逐项核查,本档不作结论。**

## 2. 通用数据质量框架

| 项目 | 它做什么 | 与 GeoGov 关系 |
|---|---|---|
| Great Expectations | 数据断言/验证,支持 Custom Expectations | 互补,可作下层断言引擎 |
| Soda | Data Reliability DSL(SodaCL) | DSL 设计参考;主仓库 Elastic License 2.0,只借鉴思想 |
| Deequ | Spark 大规模 DQ 验证 | 执行层互补 |
| OpenRefine | 人工清洗/聚类/实体对齐 | 互补 |

关键区分:空间实体可信度、多源证据、provenance、仲裁整改不是其开箱即用的一等领域模型。

## 3. 空间基础设施组件

| 组件 | 定位 | 在 GeoGov 中的角色 |
|---|---|---|
| libpostal | 全球地址解析/标准化 | AddressParserProvider——Observation 生成器,不是本体更不是 truth |
| PROJ / pyproj | 广泛使用的 CRS 转换基础设施(EPSG/ISO 19111) | CRS 基础设施;GCJ02/BD09 单独做 NonStandardCoordinateOperation;结果命名 estimated_wgs84,不覆盖原始坐标 |
| H3 / S2 / Geohash | 空间索引 | SpatialIndexStrategy 之一。**PIP 是行政边界一致性的主要几何判定方法(边界数据本身也有版本/来源/时效,属 Evidence 基础设施);H3 是索引/加速手段**——两者都不是"领域真相" |

## 4. 企业级平台

Salesforce 等拜访决策领域的研究(EVR/Visit Assistant/Layer C/专利/文献)已迁至 `docs/research/field-visit-decision-landscape.md`——它属于拜访调度体系差异化研究,不是 GeoGov 的比较对象。Oracle/Microsoft FSM 等:未核查,不进对外材料。

## 5. 标准支撑

- GB/T 36344-2018:六维 DQ(现行;有修订计划,引用注明版本)
- GB/T 35639-2017《地址模型》:参考并映射 ISO 19160-1:2015,非等同采用
- ISO 19157-1:2023(地理信息 DQ)、ISO 19160-1:2015(地址概念模型)
- ISO 8000 series(通用 DQ 概念)、DAMA DMBOK(治理实践参考,非标准)

## 6. 状态与部署边界

**术语口径(永久统一)**:
- **Formal evaluation** = 芜湖 1,070 店(正式 DQ 评估)
- **Scale exercised** = 118,891 店(管线大规模可运行性验证)

**能力状态表**(README 中各能力的归属):

| 能力 | 状态 |
|---|---|
| S1 边界一致性 / S3 外部地图交叉 / S4 群体异常(重复坐标/坐标系混用) | Validated(芜湖 Formal evaluation) |
| 31 条 DQ 规则冻结、地址本体、评分卡/整改清单 | Implemented + Validated(芜湖) |
| 规则 DSL 五态 / BenchmarkSuite 回归 / EvidenceDependency | Planned(架构设计目标) |
| 第二国家 Profile 零修改接入 | Planned(架构毕业考试) |

**部署**:Core 可本地运行;调用外部 Provider 时查询字段按其接口出域;Evidence 留存遵守各 Provider 授权/缓存条款,必要时仅存允许的派生证据或 hash。

## 7. 对外引用规范

1. 竞品结论标注核查日期与"公开文档范围内";
2. 未核查的不写进对外材料;
3. "未找到公开证据"≠"对方没有此能力";
4. README 首页只放 §0 精简版,本档为依据存档。
