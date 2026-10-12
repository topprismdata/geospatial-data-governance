# GeoGov

让空间数据在进入业务决策之前,先证明自己可信。

Evidence-first governance for coordinates, addresses and spatial entities.

GeoGov 是一个开源的 Geospatial Data Trust Framework。

它不只检查"经纬度有没有值",而是判断:

**这个坐标、这个地址、这个行政归属,是否可信地描述了同一个现实对象?**

并进一步回答:如果不能信,证据是什么?应该先修哪一批?

## 1. Why we build this — 为什么做 GeoGov

企业 CRM 里的门店坐标经常有一个危险特征:**看起来完整,实际上不可信。**

经纬度字段不为空,格式合法,地图上也能画出一个点。但这个点可能根本不属于这家门店。

在一次 1,070 家门店的芜湖全量数据质量评估中,我们发现:

- **188 家(17.6%)**:坐标落在与 CRM 填报区县不一致的行政区域;
- **395 家(36.9%)**:地址缺少足够的定位结构(只有小区、村、商圈或地标,没有完整道路门牌);
- **30 条记录**:出现跨区门店复用同一坐标的异常;
- 还发现了 (110,110) 这类**纬度本身就不合法**的坐标。

真正的问题不是"地图上有几个红点",而是这些空间事实会继续流入:销售路线优化、市场分区、配送规划、网点分析、选址模型和 AI Agent。**一旦输入事实错了,下游系统可能非常认真地算出一个错误答案。**

传统数据质量工具擅长检查"latitude 是否为空、格式是否合法";地图 API 擅长回答"这个坐标在哪里"。但企业真正缺的是第三个问题的答案:

> **"我系统里的这个位置,到底能不能信?"**

这就是 GeoGov 要解决的问题。

## 2. Value — GeoGov 的价值是什么

**对业务人员**:不要求懂 GIS。给 GeoGov 一份门店清单,得到质量评分卡 + 异常地图 + 按优先级排序的整改清单。每个问题都尽量用业务语言解释:为什么它可疑?哪些证据支持这个判断?应该优先人工确认、重新采点,还是补充地址?

**对数据团队**:GeoGov 不把检测结果当成黑盒。判断过程完整保留 Observation → Evidence → Finding → Rule Evaluation:使用了哪个数据源、什么时间取得证据、哪个规则哪个版本产生了判断、为什么进入某个风险等级。**缺少证据时,明确表达为 UNKNOWN,而不是伪装成"通过"。**

**对下游系统**:GeoGov 输出的不是"又一份 DQ 报表",而是经过质量治理的空间事实。在世界模型、调度引擎、分区算法或决策系统消费坐标之前,先过一道空间事实可信度检查。

> GeoGov does not decide what the business should do.
> It determines whether the spatial facts used in that decision are trustworthy enough to enter the world model.

## 3. Why us — 为什么是我们做

**真实问题,而不是合成 Demo。** GeoGov 不是从一个抽象的"空间数据治理框架"概念开始的,它来自真实业务数据上的问题复盘,而不是先设计抽象框架再寻找示例。

正式评估样本为芜湖 1,070 家门店,用于形成可审计的数据质量评估和规则验证;相关数据管线同时在 118,891 家门店主数据上运行过,用于检验处理流程在大规模真实空间主数据上的可运行性。**两类证据用途不同,我们不把它们混成一个统计口径。**

**我们同时负责下游。** GeoGov 不是孤立的数据清洗项目。TopPrism 还在构建共享语义契约(prism-ontology)、决策就绪门控(spatial-decision-intelligence)以及下游的空间分区、调度、路线等决策引擎。这意味着我们不仅看到"数据质量规则有没有通过",还直接看到**一个错误坐标怎样污染市场分区、路线规划和最终业务判断**。GeoGov 的目标不是让 DQ 报表更漂亮,而是阻止不可信的空间事实继续流入决策链。

**真实业务边界已经进入设计。** 很多空间数据问题不是一个距离公式能解决的:GCJ02 / WGS84 等坐标系差异;地址、坐标和现实 Place 不是同一个概念;一个现实对象可能存在多个地址表达和多个坐标观测;不设区地级市等特殊行政区划结构;多家不同门店共享完全相同坐标意味着批量数据污染而非普通定位误差。这些不是框架发布后再补的 edge case,它们正是 GeoGov 架构形成的原因。

## 4. Why this approach works better — 为什么这种方法更适合空间数据治理

**为什么不直接用谷歌/高德?** 它们做的是地址验证/地理编码——基于 provider 自身的验证能力判断输入地址的完整性、可确认性与待修正之处(Google Address Validation API 返回 ACCEPT/CONFIRM/FIX 裁决;高德/百度暂无公开的 verdict 类产品);GeoGov 做的是治理——验证"**你 CRM 里的坐标+地址+行政归属,自己跟自己说不说得通**"。而且 Google AV 的官方支持范围**不含中国**(截至 2026-09-24 核查,CN/HK/MO/TW 均不在支持列表)——在中国零售场景它不可用;高德/腾讯是 GeoGov 的证据来源(Provider),不是裁判。它们解决不了跨字段一致性、群体异常、证据仲裁和整改闭环。

GeoGov 不试图替代已有工具,而是把已有基础设施放在正确的位置,自己补上缺失的那一层:

| 工具层 | 擅长 | GeoGov 在上面增加什么 |
|---|---|---|
| **Google AV / 高德 / 腾讯**(地图服务) | 地理编码、逆编码、地址解析、单源 verdict | 多源交叉仲裁:provider 是 Evidence 不是裁判;跨字段一致性 + 群体异常 + 整改闭环 |
| **GX / Soda / Deequ**(通用 DQ) | 字段与表级断言 | 空间实体可信度、多源证据、provenance、仲裁 |
| **libpostal / PROJ / H3**(基础设施) | 地址解析 / CRS 转换 / 空间索引 | 作为 Provider 与 Strategy 被消费;保留 CRS provenance,转换不覆盖原始事实 |

详细对比(Google AV 逐项核实、高德/百度、Loqate/Precisely 等商业厂商、Salesforce 深度核查)见 `docs/competitive-analysis.md`。

GeoGov 重点做好四件事:

**1. Evidence first。** 任何 Provider 的结果都只是 Evidence,不是 Truth。腾讯地图说某家店属于 A 区,不意味着现实世界一定如此;另一个地图源得出相同结果,也不必然代表两个证据完全独立。GeoGov 保存:谁说的、什么时候说的、依据什么说的,然后再形成 Finding。

**2. 单一信号不直接定罪。** 从不同角度观察同一个空间实体:📍 行政边界一致性(坐标实际落在哪个行政区域)、🗺️ 外部地图证据(地图服务和 POI 是否支持当前位置)、👥 群体异常(多家不同门店共享同一点、整批数据一起偏移等模式)。最终风险等级来自证据组合,而不是某个 API 的一次返回值。

**3. Address ≠ Coordinate ≠ Place。** 一个字符串地址 ≠ 一个经纬度点 ≠ 现实世界中的 Place。同一个现实对象可以存在多种地址表达、多次坐标观测、不同数据源的空间描述。GeoGov 治理这些 Observation 之间的关系,而不是粗暴选择一个字段作为"真值"。

**4. Core 与 Country Profile 分离。** 架构目标 country-neutral · entity-neutral · provider-neutral。核心 Kernel 不知道中国、门店、腾讯地图、GCJ02、某个具体国家标准——这些通过 Provider / Signal / Rule / Country Profile 进入系统。当前真正经过业务验证的 Profile 是 China retail point data。**未来只有当第二个国家 Profile 在 Core 零修改的情况下可以接入,GeoGov 才真正通过"全球通用"的架构考试。**

## 5. How it works — 3 秒理解 GeoGov

```
门店 / 空间实体数据
地址 · 坐标 · 行政区
        │
        ▼
┌──────────────────────────────┐
│        多源空间 Evidence       │
│                              │
│  📍 边界验证    🗺️ 外部地图    │
│  👥 群体异常                   │
└──────────────────────────────┘
        │
        ▼
 Observation → Evidence → Finding
        │
        ▼
    正常 / 待核实 / 优先整改
        │
        ▼
  质量评分卡 · 异常地图 · 整改清单
```

架构全景图(纯 HTML,无外部依赖):[docs/architecture_diagram.html](docs/architecture_diagram.html)

## 6. What you provide / What you get

**最小输入**——一份 Excel / CSV:实体或门店 ID、经度、纬度、地址、省/市/区县等行政归属。

**可选增强数据**:门店名称、其他可验证空间事实。

**输出**:
- **质量评分卡**:总体有没有系统性问题?
- **空间异常地图**:问题集中在哪里?
- **Evidence 明细**:为什么判断它可疑?
- **整改清单**:应该先修谁?

## 7. What GeoGov is NOT

- 不是路线优化器——路线规划由下游优化系统负责;
- 不是地图服务——它消费地图 Provider,但不替代地图 Provider;
- 不是 Great Expectations 的空间版替代品——通用 DQ 工具仍可作为治理体系的一部分;
- 不是自动纠错机器人——默认流程是:发现问题 → 给出证据 → 排定优先级 → 人或业务系统决定是否写回;
- 尤其不会因为某一个地图 API 返回了不同结果,就静默覆盖 CRM 原始坐标。

## 8. Evidence & Boundaries — 我们目前真正验证到了哪里

**已验证业务 Profile:中国零售点数据。** 正式数据质量评估:芜湖 1,070 家门店(188 条坐标与填报区县不一致、395 条地址定位结构缺陷、30 条跨区坐标复用异常)。机器规则采用全量检查,人工抽样用于验证检测器本身的误报和漏报,而不是用抽样结果代替全量检测。

**当前边界**:

```
Architecture target: country-neutral, entity-neutral, provider-neutral.
Current validated profile: China retail point data.
```

这两句话不能混为一谈。

## 9. Standards

GeoGov 不把标准直接写死进 Kernel,而是通过 Profile 做标准映射:

- **GB/T 36344-2018**《信息技术 数据质量评价指标》——规范性、完整性、准确性、一致性、时效性、可访问性;
- **GB/T 35639-2017**《地址模型》——中国地址数据模型与地址组分设计参考;
- **ISO 19157-1:2023** — Geographic information — Data quality,地理信息质量语义参考;
- **ISO 19160-1:2015** — Addressing — Conceptual model,country-neutral 地址概念模型参考。

GeoGov 的地址 ontology 在这些模型之间建立映射;映射不意味着标准彼此等同。

**国标不是引用装饰,而是规则的分级依据。** GeoGov 的 31 条冻结规则(DQ 规则)逐条映射到 GB/T 36344-2018 的质量维度:

| GB/T 36344-2018 维度 | GeoGov 对应实现 | 实测发现(芜湖 1,070 店) |
|---|---|---|
| **准确性** | S1 行政边界一致性(坐标 PIP 判定 vs 填报区县);(110,110) 类非法坐标检出 | 188 条坐标与填报区县不一致 |
| **完整性** | 地址定位要素规则(道路/门牌/建筑组分计数) | 395 条地址定位结构缺陷 |
| **一致性** | S4 群体异常(跨区坐标复用、坐标系混用检出) | 30 条跨区坐标复用异常 |
| **规范性** | 经纬度取值域校验、行政区划码归一(含不设区地级市 8 位码) | 全量执行 |
| **时效性** | Observation/Provider 级 provenance(取证时间、数据版本、边界有效期) | 全量执行 |
| **可访问性** | Provider 可用性与服务状态(区分"门店可访问性"与"Provider 服务质量",不混层) | 全量执行 |

严重度分级(C1 关键 / C2 重要 / C3 一般)与 Hard Gate 机制即建立在该维度分类之上;完整映射见 `docs/` 下 DQ 规则冻结文件(`dq_rules_v1_frozen.json`)。

## 10. Position at TopPrism

```
prism-ontology (共享 Observation / Evidence / Quality 语义)
        │
        ▼
     GeoGov(空间事实可信治理)
        │
        ▼
spatial-decision-intelligence(这个事实是否足以支持当前决策?)
        │
        ▼
Downstream spatial decision engines(分区 · 调度 · 路线等决策系统)
```

边界非常明确:GeoGov 回答"数据可信吗";Decision Readiness 回答"这些数据足够支撑这个决定吗"。这是两个不同问题。

## 11. Architecture principle

```
GeoFeature → Observation → Evidence → QualityFinding → RuleEvaluation → QualityDisposition(质量处置:PASS / REVIEW / REMEDIATE / UNKNOWN)
```

一句话:**Detection is not Truth.**

## 12. Operational boundaries

- Core 可本地运行;但调用外部地图 Provider 时,相应查询字段会按 Provider 接口发生外部传输——Core 本地 ≠ Provider 调用本地;
- 外部地图 Provider 可能要求 API Key,并可能产生调用费用;
- Evidence 留存必须遵守各 Provider 的授权、缓存与服务条款;必要时仅保存允许保存的派生证据或 hash;
- Provider 返回结果受其自身数据质量、版本和服务条款影响;
- 原始坐标、原始 CRS 和原始地址应被保留,不应被推断结果静默覆盖;
- GeoGov 的高风险判断是治理证据,不应自动替代现场确认。

## 13. Repository direction

> **状态说明（2026-10-12）**：本仓当前为**规范仓库**——交付物为 DQ 规则库、地址本体与治理文档；
> 以下目录结构与包名/CLI 为**规划中的执行层方向，尚未实现**（无 `src/`、无 `profiles/`、无 tests/CI）。
> 成熟度见 `topprism.yaml`（maturity: specification-frozen）。

```
src/geogov/ (core · providers · signals · rules)   [规划中，未实现]
profiles/ (cn · retail)                            [规划中，未实现]
examples/ · docs/                                  [部分存在：docs/]
topprism.yaml · CITATION.cff
```

仓库 `topprismdata/geospatial-data-governance`(随组织 kebab-case 命名惯例),未来包名 `geogov`、CLI `geogov`（均未实现），License **MIT**。

## GeoGov in one sentence

GeoGov 是空间数据进入企业世界模型和决策系统之前的可信入口。

不是先问"这个坐标合法吗",而是继续追问:

> **"这个坐标,真的属于这个现实对象吗?"**
