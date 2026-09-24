# 拜访决策领域研究存档(visit-scheduling 体系)

> 2026-09-24 · 从 GeoGov competitive-analysis 迁出(GPT 三轮检查 P0-11/12:非 GeoGov 比较对象)
> 归属:visit-scheduling-optimizer / 拜访决策体系差异化研究

---

## Salesforce 深度核查结论

研究方法:仅采信官方 Help / Trailhead / 产品页 / 专利文本;未公开算法不从"Einstein/AI"名字反推;区分事实/推断/未验证。

| 问题 | Einstein Visit Recommendations | Retail Execution Visit Assistant |
|---|---|---|
| 本质 | Store×Date 拜访价值/优先级推荐;规则策略或模型策略(Einstein Discovery 支持 GLM/GBM/XGBoost/Random Forest) | 2026 已扩展至 Visit Management 等;标准 Topic 含 Account Performance/Compliance/Last Visit Summary/Product Upsell(勿再概括为纯"取数总结") |
| 是 AI PJP/路线优化器? | 否(Continuous Routing/Priority Scheduling 是另一付费层) | 否 |
| 公开用 Bayesian? | 无证据(有概率输出 ≠ Bayesian learning) | 无证据 |
| 计划 vs 实际数据? | Visit 对象有 Planned/Actual 双时间戳,数据充分 | 可查询历史 |
| 标准"计划采纳率"KPI / 对比可视化? | 未找到 OOTB | 未找到 |
| **行为学习闭环**(计划-实际偏差→学习业代空间/星期行为→改下轮计划)? | 截至 2026-09-24,审阅的公开文档中未找到产品化闭环说明(Layer C) | 同左 |

**Layer 分解**:A Observation ✅ / B Recommendation ✅ / C Behavioral Learning——公开产品证据不足,为本体系差异化所在。

**专利**:US 12,298,982 B2(推荐多样性+可解释性)、US 11,769,013(多租户 chatbot action)——相关 IP,不能证明产品使用。
**论文**:EVR/Visit Assistant 专属同行评议论文未检索到。

## 学术支撑(计划-实际学习层)

- 贝叶斯方法(分层先验/收缩/在线更新)、流动性建模文献——支撑 S2 行为信号与经验学习层方法论(内部研究,详见 visit-scheduling-optimizer docs)
