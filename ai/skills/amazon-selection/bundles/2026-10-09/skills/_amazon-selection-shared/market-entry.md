# 共享市场可进入性规则

模块版本：`market-entry-v0.6.0`
公共规则：`selection-gates-v0.10.0`；更新：2026-10-08。

判断精确市场和目标方案的进入证据，不代替供应、利润、合规和需求周期验证。样本数与30单等校准口径需要独立回测；不得为提高通过率挑选成功样本。

## 1. 市场定义和研究前提

`market_definition`在看结果前限定站点、购买意图、核心功能、关键规格/材质、价格带、pack层级和必要场景。记录查询词、分页覆盖及纳入/排除规则；不得为降低品牌份额或提高预测销量事后收窄市场。

完整M/E/L/T前先执行轻量预检：核对产品与关键词一致、历史重复、目标售价与保守包装的经济承受区间，并用可取得分页估计唯一父ASIN密度。预检已确认父体>50或零采购成本仍无利润时停止该配置；分页未完、查询返回结构无法归并或边界含多种购买意图时只标记待补。预检通过不是market通过，只用于减少在明显失败市场上的趋势、评论和深度调用。

`market_definition`可按“买家/对象＋问题＋场景＋关键规格”构造，但每个限定条件必须有购买意图或商品结构依据。先登记边界再读取结果；不得看到竞争太高后凭空增加颜色、文案、微小尺寸或无需求证据的用途。

- 身份明确、无已知硬失败的候选可在供应/包装待补时研究市场。市场通过不能自动解除费用、利润或launch的待补。
- Node、泛词、类目Top100只用于发现。不同意图必须拆分；同时避免把非关键颜色或文案差异当作全新市场。
- 从未按评论、销量或潜力预过滤的可比全集 `M` 计算父ASIN数、评论中位数和品牌销售额份额。按唯一父ASIN去重，每父体选择事先规则确定的最近似子Offer，不能选择销量最高子体。
- 已完成可取得的相关分页仍不能视作覆盖了全部Amazon库存；须披露采样边界。分页未完成、只取店铺成功款或接口高销量截断，标记 `ENTRANT_COHORT_CENSORED`，不得自动通过。
- 卖家ASIN总数、一个店铺的存活款或购买标记占比不能作为完整市场或新品成功率。
- 卖家目录只用于发现“问题型长尾意图、可感知改进和有依据的pack/组合”候选，不自动进入M/E/L/T。每个来自卖家的候选记录`seller_pattern_source`、目录截止日、分页覆盖、父子体归并、促销状态及幸存者偏差；只有重新按本模块建立的精确市场证据才能支持通过。
- 促销价、优惠券、购买标记和低评论仅是观测信号。促销依赖须单列；同父体变体、店铺新增索引和评论继承不得当成独立新品或自然进入样本。

## 2. 四类证据和预测队列

从M建立：
- `E`：上架<=180天的全部可比新进入者，不按评论/当前销量过滤。
- `L`：E中已观测评论<=30的Offer；缺评论数不当0。当前低评论不等于进入时低评论，历史缺失标记 `REVIEW_AT_ENTRY_UNOBSERVED`。
- `C`：同买家问题且关键规格、材质、pack、兼容、功能和价格足够接近的目标配置Offer。不能用大市场销量证明目标子体。
- `X`：181–365天或评论31–100的补充观察；仅用于需求/差评/规格参考，不替代新品或低评论进入证明。

独立建立预测队列 `T`：从E按提前登记的目标配置、售价带、FBA履约、使用场景、上市时长/销售阶段和可比产品能力条件选取，称 `forecast_cohort_definition`。必须在读取各样本销量结果前固定条件和ASIN；不得以销量、评分高低、成功/失败、是否有购买标记作为纳入条件，也不能按自然位只留下成功者。L只用于进入证明，不直接代替T。

### 观测窗口

- 常规预测对每Offer用最近连续3个完整有效月的销量中位数 `sales_i`；真实零销量保留，缺失/未上架不能填0，断货或极端促销不能无说明删除。记录污染及覆盖率。
- 将不足3个完整月的早期新品与可评估队列分开。早期销量、50+/100+购买标记可支持研究，不能冒充三个月记录或线性外推稳定月销。
- 只有事先定义的可评估T全部取得所需窗口且无未解释污染，才计算可用于自动判断的 `target_forecast_p25=P25(sales_i in T)`；使用线性插值分位数（PERCENTILE.INC）。样本至少5个独立父ASIN、至少2个独立经营主体；3–4个只能人工研究，少于3个待补。
- 同一父体多个子体、同一卖家多个重复链接不增加独立样本。卖家独立性未知时为人工复核。
- 有缺失或数据截断时可报告已观测分布，但预测资格保持待补；记录可评估总数、已观测数、缺失数及早期数，禁止只删失败/缺失后自动通过。
- `estimated_new_item_monthly_sales = conservative_new_sales = target_forecast_p25`，不再等于整个E的P25；不能用某个竞品销量乘主观份额覆盖。若两队列恰好相同，允许结果相同。
- 季节/节日使用相同需求阶段及各类型所需窗口，不能淡旺季混比。热点沿用类型规则的28天/周粒度，窗口不足时依原规则人工复核，不能强塞三个月或伪造周数据。
- E可评估队列的 `cohort_sales_p25` 只诊断整体进入难度，不直接否决有充分独立证据的T。E中尚早或未知的样本单列；整个E未完整可评估时，`newcomer_success_rate=null`，仅报告 `observed_evaluable_success_rate` 及明确分母，不能称完整新品成功率。

## 3. 品牌集中和自然进入

保留公共竞争门槛：相关唯一父ASIN<=50，父ASIN评论中位数<=500。保留公共Amazon自营规则，不能因放宽品牌份额而放行自营控制市场。

- 品牌先合并可核验别名、大小写，再固定计算Top1/Top3销售额份额。不得混销量份额或隐去头部品牌；品牌/份额缺失为待补。
- `top3_brand_share<=20%`仅授予 `brand_dispersion_status=通过`。超过20%不再单独令market/launch失败；此时分散标签不通过，但仍验证进入性。
- `head_control_status`为 `可进入`、`控制阻断`、`待核验`。必须给出至少2个相关非品牌核心词的自然SERP、头部控制及独立新进入者的证据。
- 存在>=3个来自>=2个独立经营主体的低评论新品，满足各自有效窗口月销>=30，并在上述词获得可解释自然位，且无未解决的品牌专属/价格战不可盈利/自营控制，可判可进入。
- 实际观察证明流量依赖不可替代品牌词/专有接口，或价格压到目标方案完整利润不成立，则控制阻断/硬失败。新进入者或排名证据缺失时应待核验，不把未知当垄断或放行。
- 品牌集中高时须明确说明这些非头部进入者如何与目标配置可比；只在不相关词曝光不算反证。

自然证明使用 `keyword_search_results(position_type=1)` 与 `product_traffic_terms` / `competitor_product_keywords`交叉核验，position_type=2仅作广告对照。核心词可为真正有需求的非品牌规格长尾词，不强制用宽泛大词，也不能将同一个入口重复计数。只有销量或购买标记、品牌词、单次截图或自然词总数都不足以证明稳定自然订单。无可解释入口时标记 `TRAFFIC_ATTRIBUTION_ANOMALY`，不能默认自然成交。不能换算精确广告费率或ACOS。

## 4. 目标配置的两条证据路线

`target_evidence_route=直接可比`：
- C至少3个有有效销量证明的可比Offer，覆盖>=2个独立父ASIN与>=2个独立经营主体。
- 关键尺寸/公差、材质、兼容、pack和使用功能符合事先定义；精确子Offer销量可拆分，且有>=2个相关非品牌自然词入口支持。
- 达到以上条件可输出 `target_offer_support_status=通过`，但T预测和其他市场条件仍须独立通过。

`target_evidence_route=组合证据`：
- 同用途成交证据 + 目标关键规格/pack的搜索或买家选择证据 + 可执行供应/改进方案，三者指向同一购买问题。
- 明确与已有方案的差异、未验证假设及补证动作。精确兼容、公差、安全规格不能由邻近型号代替；父体或其他pack销量不能分配给目标。
- 用于缺乏多个同款的新品研究；三部分有依据时 `target_offer_support_status=人工复核`，缺部分证据为待补。不授予自动market/launch通过。
- 人工认可研究方向也不自动填补月销预测或利润；后续满足直接可比/T条件或另获用户明确批准的有记录人工开发决策，再分别记录机器与人工结论。

组合证据路线在以下全部条件成立时，可进入`CONTROLLED_TEST_QUOTE`，但`market_decision`仍为`人工复核`：同用途成交、目标关键规格/pack选择和自然需求三部分均有来源；至少两类证据来自独立工具对象或独立ASIN；预注册T至少3个独立父ASIN且覆盖至少2个经营主体；保守预测达到30单；不存在父子体销量分配、品牌/自营控制或流量归因异常。该路线只支持小比例实际询价学习，不构成自动market或launch通过；缺任一条件回到观察池。

多件装Skill和扩展Skill复用本节，不额外叠加“必须5个完全相同pack”的门槛。不同购买量和场景的pack仍独立验证。

## 5. 市场自动通过

同时满足：
1. M定义、覆盖和数据质量完整；父ASIN数<=50、评论中位数<=500。
2. 品牌份额完整、head_control_status=可进入，Amazon自营符合公共规则。
3. E>=5、L>=5；至少3个低评论新品有合格销量及自然证据，覆盖至少2个独立经营主体。
4. T满足观测窗口/样本/完整性规则且保守预测>=30单/月。
5. 至少2个相关非品牌核心词的自然证据通过。
6. 至少2个较新低评可比Offer支持轻启动/首单代理；无法观察首单日期时不得把代理写成真实15天首单保证。
7. 目标配置按直接可比路线通过。

自动通过规则不因受控试询改变。`CONTROLLED_TEST_QUOTE`只应用第4节的有界人工研究路线，并受公共20%合并比例限制。

样本少或组合证据路线保留研究/人工复核，不自动launch通过；已证实硬失败才不通过。`market_decision`独立于供应是否待补。蓝海标签另须分散指标<=20%与低评论进入支持；只有用户明确选择“冷门蓝海”策略时，蓝海标签才额外传导launch。

辅助诊断可保留：
`relative_entry_index = median(valid sales_i in L)/median(top5 comparable sales in M)`；
`peer_top5_ratio = mean(top5 valid sales_i in L)/mean(top5 sales in M)`。
窗口同阶段、分母非0且样本足够才算；仅用于诊断，不能单独放行或否决。

## 6. 输出和异常

除公共字段，输出：
`market_result_id, market_module_version, market_definition, market_query_log, market_coverage,`
`market_evidence_block_id, preflight_market_definition, preflight_parent_density_status, price_weight_envelope_status,`
`newcomer_sample_count, low_review_sample_count, evaluable_count, observed_count, early_count, missing_count,`
`forecast_cohort_definition, forecast_cohort_ids, forecast_exclusions, forecast_coverage, forecast_window,`
`target_forecast_p25, conservative_new_sales, cohort_sales_p25, newcomer_success_rate, observed_evaluable_success_rate,`
`top1_brand_share, top3_brand_share, brand_dispersion_status, head_control_status, head_control_evidence,`
`organic_keyword_count, organic_newcomer_count, independent_operator_count, low_review_organic_proof_count,`
`target_evidence_route, target_offer_support_status, target_configuration_definition,`
`target_configuration_offer_count, target_configuration_parent_count, target_configuration_sales_proof_count,`
`target_configuration_organic_keyword_count, supplemental_observation_count, first_order_evidence,`
`relative_entry_index, peer_top5_ratio, market_decision, blue_ocean_status, reason_codes, missing_fields`。

若候选来自卖家模式，额外输出：`seller_pattern_source, seller_catalog_scope, seller_catalog_as_of, seller_catalog_survivorship_risk, promotion_dependency, seller_pattern_reuse_decision`。这些字段只描述发现来源，不替代M/E/L/T和自然流量证据。

复用结果必须同站、同市场定义、同政策版本、同数据截止/时效；不得用旧版通过覆盖新版缺证。父子体不可拆、评论继承、断货、促销、价格变化和数据缺失均保留原始证据，不择优取值。

原因码：
`PASS_MARKET_ENTRY`、`PASS_BLUE_OCEAN`、`MARKET_DEFINITION_CONTAMINATED`、
`NEWCOMER_SAMPLE_INSUFFICIENT`、`LOW_REVIEW_SAMPLE_INSUFFICIENT`、`ENTRANT_COHORT_CENSORED`、
`REVIEW_AT_ENTRY_UNOBSERVED`、`FORECAST_COHORT_PRESELECTION_REQUIRED`、`FORECAST_DATA_INCOMPLETE`、
`FORECAST_SAMPLE_INSUFFICIENT`、`HEAD_CONTROL_BLOCKED`、`HEAD_CONTROL_UNVERIFIED`、
`BRAND_SHARE_BASIS_MISMATCH`、`TOP3_BRAND_SHARE_MISSING`、`ORGANIC_NEWCOMERS_LT_3`、
`TARGET_CONFIGURATION_SAMPLE_INSUFFICIENT`、`TARGET_OFFER_SUPPORT_WEAK`、
`TARGET_COMPOSITE_EVIDENCE_REVIEW`、`TRAFFIC_ATTRIBUTION_ANOMALY`、
`MARKET_ENTITY_MISMATCH`、`VARIATION_CONTAMINATION`、`REVIEW_SHARING_CONTAMINATION`、
`SELLER_PATTERN_DISCOVERY_ONLY`、`SELLER_CATALOG_SURVIVORSHIP_RISK`、`PROMOTION_DEPENDENCY_UNRESOLVED`。
