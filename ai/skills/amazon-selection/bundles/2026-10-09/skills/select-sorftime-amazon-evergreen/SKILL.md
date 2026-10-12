---
name: select-sorftime-amazon-evergreen
description: Discover and validate Amazon GB, DE, JP, or CA FBA private-label evergreen opportunities with Sorftime. Use for 日常品、常年款、全年稳定需求、非季节选品, or when evaluating whether a keyword, ASIN, category, or candidate list has at least ten effective demand months, low-review organic entrants, low competition, complete profit, and acceptable risk. Reclassify repeatable seasonal, holiday, or short-lived trend demand instead of forcing an evergreen result.
---

# 亚马逊日常微蓝海选品

筛选全年稳定、自然流量可进入、竞争未充分且符合完整利润与风险门槛的日常品。日常品类型只描述需求周期；市场是否能进入和产品是否能开发必须另外判断。

## 开始前

先完整读取 `../_amazon-selection-shared/six-agent-control.md`，确认本智能体职责、共用流程和权限边界。

规范一致性是硬门槛：共享合同规定的固定文件名、工作表名称与顺序、字段顺序、颜色、状态和交互路径必须逐字逐项执行；不得沿用历史工作簿命名或自行变体。交付前按当前合同检查，不一致先修复再交付。

1. 完整读取 `../_amazon-selection-shared/common-gates.md`。
2. 完整读取 `../_amazon-selection-shared/market-entry.md`。
3. 完整读取 `../_amazon-selection-shared/candidate-profit-workflow.md`。
4. 批量选品、采购回填或二次利润复核时，完整读取 `../_amazon-selection-shared/batch-review-handoff.md`。
5. 完整读取 `../_amazon-selection-shared/referral-fees.md`、`../_amazon-selection-shared/fba-fees.md`及其指向的结构化JSON费率快照。
6. 完整读取 `references/type-rules.md`。公共规则的分阶段流程适用于本Skill；批量发现先读 `../_amazon-selection-shared/selection-memory.md` 及其审核数据，使用统一候选池，不按方向凑数。
7. 确认站点、分析日、种子类型（关键词/ASIN/Node ID/候选清单/广泛扫描）和深度（快筛/深验）。
8. 未给站点时不得跨站混算；合理推断一个站点并显式说明，否则请求补充。

## 执行调度绑定（2026-10-08）

完整执行共享six-agent-control.md第4.1a节（selection-execution-v1.2.0）：证据可得性先查、精确市场预检、市场与包装经济性同步、小批深验、分层交付及有效证据复用；不降低最终launch硬门槛，严格询价、受控试询与实际利润/开发通过分别计数。优先核验日常精确市场的历史完整性、新品与自然入口；采购空间有依据的已有目标优先补证，不预设某个低价带，不把核心词有历史当作全部类型证据完整。

数量型任务另完整读取 `../_amazon-selection-shared/selection-run-control.md`：阶段交付不是停止，已授权且有可行动作时继续累计原目标；运行未启用或真实阻塞须明确报告，初始化/升级不自动恢复选品。

## 成本计算绑定（2026-09-21）

- 本Skill的粗算、询价表、实际利润和开发终审必须执行共享`candidate-profit-workflow-v1.9.0`、`selection-gates-v0.10.0`及`fba-fees.md`当前快照；FBA金额不得粘贴成固定值。
- 可重算表按站点、目标销售日期、含税/未税售价口径、Amazon费率类目、最终包装长宽高/毛重、费率有效期和税制动态路由：英德核验低价计划的售价/例外类目/尺寸/400g资格，日本核验售价档与重叠费档，加拿大核验旺季/非旺季、100g或500g进位、低价折扣和GST/HST分列；美国费率禁止跨站使用。
- 人工修改实际采购价、最终包装尺寸或重量后，体积重、计费重、头程、FBA费、15%佣金、税费、贡献利润、利润率、保本价和结论必须同步更新。缺费率有效期、类目路由、售价税口径、包装数据、税率、汇率或目标站头程费率时返回`待补费用`，不得按0或沿用上一行。
- 采购回填字段类型、询价证据、基础费预估/最终利润分层及公式错误拦截统一执行`candidate-profit-workflow-v1.9.0`和`batch-review-handoff-v2.0.0`，本Skill不复制第二套口径。
- 询价前包装估算统一执行`selection-gates-v0.10.0`：优先精确子ASIN、同父体pack梯度或多个同结构可比Offer，输出低/基准/高重量体积、A–D置信度、预判头程路线/FBA费档和三情景采购空间；C按保守情景进入B/C档，D先补证。最终利润仍只认人工询价后的供应商确认/实测包装数据。

## 批量询价数量要求（2026-09-22）

- 标准批次以50个去重的`quote_ready`目标Offer为累计完成条件，不以发现50个候选为完成；按`batch-review-handoff-v2.0.0`集中小批深验、有针对性扩池，实得合格行先分批交采购，再继续累计至请求数量。
- 采购价未知不提前淘汰，选品阶段不核对1688或要求供应入口。只要主类型及时机、市场、目标配置和非采购成本支持，采购成本取0时经济性通过，30%利润后的采购空间为正，且按材料、工艺、结构、pack、定制、认证和包装负担推理可能实现，即带采购空间进入人工询价；明显不可实现时淘汰。
- 不足50个时只能标记未完成并继续扩池或报告客观缺口；不得用重复ASIN、同父体轻微变体、待补或无经济性的产品凑数。

## 工作流

1. 用Sorftime固定截止时间，记录费用、汇率及政策版本。
2. 从“买家/对象＋问题＋场景＋关键规格”形成长尾机会，在读取销量结果前锁定精确市场边界；先做词品一致、历史去重、唯一父ASIN密度和售价—包装经济承受区间预检。已证实父体>50或零采购仍无空间立即分流，不能研究完趋势后才发现市场过宽。
3. 按公共分阶段漏斗核对实体和已知硬失败；锁定目标Offer、pack与合理包装情景，与市场/趋势核验同步反推采购空间。选品阶段不核对1688；实际采购价和最终包装留待人工询价回填。
4. 建立至少12个月的类目、关键词和代表ASIN趋势，按类型规则计算有效月与需求集中度。
5. 纠正断货、上新、促销、价格跳水、广告集中和父子体合并污染；证据不足不补造月份。
6. 按共享市场模块重建精确可比市场、新进入者群体和低评论群体，判断自然流量与蓝海进入性。同一精确市场的M/E/L与自然词保存为证据块，多个真实独立方案只复用该块，各自重建C、T和包装经济性。
7. 按共享市场模块，用事先定义且含失败样本的目标预测队列T计算保守销量；完整新品队列E只诊断市场难度，不把头部、父体或购买标记当自身预测。
8. 市场、类型和目标配置支持继续开发后，按共享候选利润流程输出严格询价；仅市场因组合证据样本限制而人工复核、且满足公共受控试询全部条件时进入受控试询。其他待补进入观察池。
9. 人工填写实际采购价、确认规格、最终销售包装三边和包装后实重后，AI核验配置并计算实际利润。仅在实际利润及全部launch必需作用域通过后生成运营销售策略；否则输出利润敏感项和补证动作。分别输出类型、市场和开发结论；符合其他周期时给出`建议改类`。

## 强制行为

- Listing存活12个月、年度总销量或每月零星订单不能证明日常品。
- 缺少12个月趋势时不得自动判日常品。
- 同行“低评论TOP5/头部TOP5”比值只作诊断，不得单独放行。
- 类型通过不能令市场或开发结论自动通过。
- 只建议进入开发池，不执行采购。

## 输出

使用公共输出合同，并额外给出：`evidence_months`、`effective_months`、`top3_month_demand_share`、`category_keyword_asin_consistency`、`representative_asin_count`、`evergreen_status`、`preflight_market_definition`、`preflight_parent_density_status`、`market_evidence_block_id`、`inquiry_lane`。

批量任务先按决策状态分桶，再在同一状态内按利润安全垫和证据完整度排序；任何总分不得把硬失败排入通过组。

## 阶段与证据边界（v0.6）

输出 `research_stage`、`screen_decision`、`review_type`、`memory_match_ids` 与补证动作。候选优先复用“问题型长尾意图→可感知且可执行改进→有依据的pack/组合→低评新品自然入口”结构，但卖家案例仅用于发现并披露幸存者、变体与促销污染。确定直接竞品后立即按共享流程快抓评论、分析重复差评并发散低成本改进；采用改进时必须落到实际报价和验收方法。研究通过或区间粗算通过都不等于 `launch_decision=通过`；目标配置不足时按共享市场的组合证据路线进行人工研究。人工实际询价及最终包装三边/实重未核验时，`profit_validation_status=待人工询价`，不得生成可执行运营策略。只有AI完成实际利润复算并通过全部门槛，才进入开发排序并输出运营销售策略。主类型改路沿用候选ID和有效证据。
