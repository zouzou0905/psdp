# 可比卖家候选发现、评论改进与询价利润闭环

模块版本：`candidate-profit-workflow-v1.9.0`

更新时间：`2026-10-08`

本模块供六个Amazon选品Skill共同使用。它规范候选如何从可比卖家中产生、如何快速抓取评论形成低成本改进方案，以及市场研究后如何通过人工询价和实测包装数据完成真实利润验证；不改变各主类型、市场、合规和时机门槛。批量候选数量、询价前经济性、采购简表及交付检查同时执行`batch-review-handoff.md`。

## 0. 调度与阶段边界

六个Skill统一执行six-agent-control.md第4.1a节（selection-execution-v1.2.0）。从真实购买问题寻找市场线索，先完成精确市场、证据粒度、子体/样本、价格—重量和评论可得性预检，再对现有候选集中完成小批深验；完整M和预注册T仍按market-entry.md建立，不能仅选成功者。包装与采购空间同步初筛，不预设低价或大PCS优先。

quote_ready是询价请求，不是最终开发通过：实际采购价、供应SKU、MOQ/交期、改进报价与最终包装实测属于询价后的核价证据，不能提前要求这些人工数据才允许研究或询价。严格询价须满足全部询价作用域；受控试询仅允许公共规则定义的一个人工复核证据作用域，其他硬门全部通过；观察池不得交采购。三层状态都不能替代最终launch验证。人工未知采购价不得在实际利润公式填0；采购成本取0只用于经济性上限测试。

对缺失数据保存覆盖与补证条件；评论工具无覆盖不等于没有差评，不据此生成虚假改进方案。分批交付实得合格行并滚动累计请求数，遵循batch-review-handoff.md；最终报价、包装与目标售期费用未核齐时实际利润及launch保持待补。

## 1. 从可比卖家学习结构，不继承结论

可比卖家目录可作为候选种子，优先识别以下组合：

```text
明确买家问题或使用场景
→ 可由供应链执行且买家能感知的规格/结构改动
→ 有需求依据的pack或共同完成同一任务的功能组合
→ 较新或低评论Offer已有可解释自然入口
```

研究时记录完整目录或可披露的分页边界、父子体关系、上架时间、价格、评论、销量/购买标记、履约、促销、自然/广告位置、类目和品牌。不得只看店铺首页、爆品或存活款后推导新品成功率。

- 低评论不等于新品；必须核验上架日期和评论继承。
- 购买标记不等于精确销量、自然订单或卖家独占成交。
- 同一父体的不同pack、颜色或尺寸不得冒充多个独立新品样本。
- 店铺结果数变化可能来自上新、下架、重新收录或独立变体卡片；不能直接当净新增父ASIN。
- 标题中的Christmas、gift、disposable、refill、PCS、compatible或best seller只作路由线索，不授予节日、消耗、大PCS、兼容或市场通过。
- RRP、优惠券、限时折扣、Prime专享价和价格跳水须记录`promotion_dependency`，不能用促销成交证明正常售价接受度。
- 从高频上新卖家发现的产品保留`SELLER_SURVIVORSHIP_BIAS`，直到完整新品队列和失败/未知样本得到校正。

每个卖家种子至少输出：

```text
seller_pattern_source, seller_catalog_scope, seller_catalog_as_of,
seller_catalog_survivorship_risk, buyer_problem, use_context,
long_tail_intent, observable_improvement, improvement_verification_method,
pack_or_bundle_rationale, promotion_dependency,
low_review_entry_signal, natural_entry_signal,
seller_pattern_reuse_decision
```

`seller_pattern_reuse_decision=通过`只表示该结构值得进入候选池，不等于`screen_decision`、`market_decision`或`launch_decision=通过`。

## 2. 候选方案的可执行定义

候选不得只写商品名。必须在市场读取结果前定义：

- 买家是谁、在什么场景遇到什么问题；
- 目标Offer的材质、关键尺寸/公差、pack、兼容或共同功能；
- 相比市场方案要改变什么，买家如何感知；
- 改动由哪类需求证据支持；
- 改动预计增加哪些采购、包装、质量或合规成本；
- 用什么样品、量具、压力/密封/耐用/清点或兼容测试核验。

多件装只有在目标pack自身需求成立时保留。功能组合中的组件必须共同完成同一任务；异质凑数、赠品膨胀和只靠漂亮包装不构成差异化。

## 3. 快速评论诊断与低成本改进

### 3.1 先快抓，后深验

候选实体和精确可比市场初步确定后，立即并行进行评论快抓，不能等利润终审才看差评。优先对3–5个最直接可比父ASIN的目标子Offer使用Sorftime `product_reviews`、`product_customers_say`及可取得的Amazon评论证据；可比父体不足时覆盖全部可得样本并降低置信度。Sorftime评论工具只覆盖近一年且最多100条时，必须披露时间、数量和分页边界，不能称完整历史。

首轮快抓以定位问题为目的：优先近期1–3星评论，同时抽取4–5星评价确认买家真正重视的优点，避免只看差评造成选择偏差。每条有效样本记录精确ASIN/变体、星级、日期、评论主题、原始问题摘要、能观察时的已验证购买状态及来源。不得把父体其他规格的缺陷自动归给目标Offer。

将问题至少区分为：

- 产品本体可改进缺陷：材质、尺寸/公差、强度、密封、连接、兼容、易用性、耐久或数量清点；
- 包装与说明问题：破损、漏装、保护不足、步骤不清、尺寸预期不明；
- 购买预期/Listing表达错位；
- 运输、FBA配送、卖家服务、误用、孤立个案或与目标方案无关的问题。

只有跨时间或跨独立父ASIN重复出现、与目标购买问题相关、且供应链能够控制的问题，才进入改进设计。输出`review_quick_scan_status`、`review_coverage`、`review_sample_count`、`low_star_sample_count`、`positive_control_sample_count`、`review_theme_matrix`、`repeat_defect_count`、`cross_asin_defect_support`和`review_bias_flags`。首轮证据弱时可继续深抓，但不得补造频率或把单条差评写成市场普遍痛点。

### 3.2 发散方案与收敛选择

发现可信缺陷后，AI应发散生成原则上至少3个结构不同的解决方案；客观上不足3个时说明限制，不得用换颜色、换文案或同义描述凑数。可从标准材质/厚度、关键尺寸或公差、小结构、包装保护、清点防漏、说明/标识、合理pack及同任务功能组合等方向探索。

每个方案必须形成以下因果链：

```text
重复差评问题 → 具体改动 → 买家可感知收益 → 供应商执行方式
→ 预估增量成本 → 尺寸/重量/FBA影响 → 合规/IP影响 → 样品验收方法
```

低成本不是固定人民币金额。优先选择无需新模具、无需新增认证、使用常见材料或成熟工艺、不会明显增加包装体积重且可用简单样品测试验收的方案。每个方案分别记录`estimated_incremental_cost_cny`和利润敏感性；最终必须取得包含改进规格的实际供应报价。即使改进明显，只要使采购成本、贡献利润、利润率、重量、FBA费档、合规或交期不再通过，就不能作为目标方案。

按差评重复性、买家感知强度、实施可行性、成本、体积重量影响、合规/IP风险和可验收性收敛到一个主方案，必要时保留一个备选。输出：

```text
review_driven_improvement_status, improvement_ideas,
selected_improvement_id, selected_improvement_spec,
improvement_demand_evidence, estimated_incremental_cost_cny,
improvement_cost_sensitivity, supplier_execution_requirement,
sample_acceptance_test, size_weight_impact, compliance_ip_impact,
improvement_selection_reason
```

`review_driven_improvement_status`使用`不适用`、`待评论抓取`、`证据不足`、`已生成待询价`、`已核价可行`、`不通过`。没有可信可改进缺陷时允许`不适用`，不得为了差异化强行改款；但必须保留评论抓取结果和“不改”的理由。

## 4. 利润验证的两阶段

### 4.1 研究阶段粗算

发现与市场研究阶段允许使用有来源的采购、包装和重量区间做低/基准/高三种情景。粗算只能用于提前淘汰、比较补证优先级和生成目标询价规格。

粗算不得标记为实际利润，不得令`launch_decision=通过`。输出`profit_basis=区间粗算`、`profit_validation_status=待人工询价`。

公共最低售价不是询价放行条件。批量交采购前必须按`batch-review-handoff.md`反推最高可接受整包采购价；经济性上限不成立的低价Offer不能因为满足`>USD 4.99`而进入询价表。

包装重量和尺寸不得整体后移。候选通过初步实体/类型筛选后，按`common-gates.md`的询价前包装估算规则，优先用精确子ASIN、同父体pack梯度或至少3个同结构可比Offer建立低/基准/高情景。多PCS重量可用pack梯度分离“单位增量重量”和“基础包装重量”；体积必须按散装、平叠、套叠、压缩或刚性排列结构建模，不能让三边随PCS机械同比放大。

三情景分别计算头程体积重/计费重、初选物流渠道、FBA档位和采购空间。临近渠道或FBA档位边界时按相邻路线中较高成本情景放行。`packaging_confidence=A/B`可正常参加A/B询价优先级；`C`只能用保守情景进入B/C档并明确要求采购核验；`D`不得进入正式`quote_ready`主表。无论置信度如何，均保留`final_package_status=estimated`，不得写成实测或实际利润。

五个新产品方向的标准批次以50个`quote_ready`目标Offer为累计完成条件，详细数量、小批深验、分批交付、有针对性扩池、严格/受控/观察分层和A/B/C询价优先级执行`batch-review-handoff-v2.0.0`。选品阶段不核对1688采购情况。非采购成本已有合理依据、采购成本取0时完整经济性通过、达到30%贡献利润率与最低贡献利润所允许的采购空间为正，并且按材料、工艺、结构、pack、定制、认证和包装负担推理为可实现时，带采购空间进入询价；不得写成实际利润已通过。

### 4.2 人工询价与最终包装补录

类型、时机和市场研究支持继续时，AI必须生成逐Offer的`quote_input_request`并保留实际利润结论为待补，但不暂停尚未达标的选品批次。第一轮采购只填batch-review-handoff.md规定的六个黄色数值；初算有利润空间后，第二阶段核价再补齐以下证据，不把本表变成首轮采购必填清单：

| 字段 | 规则 |
|---|---|
| `supplier_sku_id` | 与目标材质、规格、pack和组件完全一致的供应SKU |
| `quote_source_or_link` | 可追踪的询价来源或报价编号 |
| `quote_date` | 报价日期；过期或条件变化后重询 |
| `quoted_quantity`、`moq` | 本次实际阶梯和最低起订量 |
| `lead_time_days` | 当前规格、pack和数量对应的交期天数 |
| `actual_procurement_price_cny` | 一个Amazon可售目标Offer的实际采购价，不是单个内件价或商品卡最低价 |
| `price_basis` | 说明是否含税、最终零售包装/打标和国内送仓 |
| `target_pack_count`、`target_pack_unit` | 数量必须为正数，单位分列；与Amazon目标Offer和报价SKU一致 |
| `pack_description` | 保存“12件装”“1卷20码”等人类可读描述，不替代数值数量 |
| `confirmed_specification` | 材质、关键尺寸/公差、兼容、组件和质量等级 |
| `improvement_quote_included` | 实际采购价是否已包含选定低成本改进；不适用时说明 |
| `actual_improvement_incremental_cost_cny` | 供应商可拆分时填写每个目标Offer的实际改进增量成本 |
| `packaged_length_cm`、`packaged_width_cm`、`packaged_height_cm` | 最终可售包装外尺寸，三边来自同一包装层级 |
| `packaged_unit_weight_g` | 最终包装后毛重，不是裸品净重 |

条件补录：若采购价不含包装/打标或国内送仓，分别填写`packaging_label_cost_cny_per_unit`和`domestic_shipping_cny_per_unit`；多渠道可选时填写`headhaul_channel`。缺失的条件费用不能填0。

人工回填后将`final_package_status`更新为`supplier-confirmed`或`measured`，并保留原估算值用于偏差复盘。供应商确认值可用于询价后复算；开发终审优先使用同一最终销售包装的实测值。若实测值使头程渠道、FBA费档、2kg门槛或采购空间跨界，必须重新路由和计算，不能沿用询价前结论。

### 4.3 输入类型、询价证据和表格状态

- `actual_procurement_price_cny`只接受大于0的数值。“定制款”“找不到链接”“已下架”“待确认”等文字必须写入`sourcing_status`或`procurement_result_note`，采购价保持缺失；文本进入数值列时标记`NON_NUMERIC_COST_INPUT`并停止利润计算。
- `target_pack_count`只接受大于0的数值；“个/件/张/卷/套”等写入`target_pack_unit`，完整描述写入`pack_description`。仅因单元格非空不得判定pack完整；非数值时标记`NON_NUMERIC_PACK_COUNT`。
- 单个内件报价必须使用`quote_price_basis=单件/内件`并填写数值型`quoted_inner_unit_count`；只有人工确认目标数量和乘法口径后，才可归一为一个Amazon可售单位的整包采购成本。
- 最终长宽高必须是折叠、压缩、装袋或装盒后的外包装尺寸，毛重为同一包装层级。展开尺寸、裸品尺寸或单个内件尺寸标记`UNFOLDED_DIMENSION_USED`或`PACKAGE_DATA_MISSING`，不得路由FBA费档。
- 任何采购平台页面标价或链接都不等于实际询价。`quote_input_status=已核验`至少需要人工回填的可追踪来源、报价日期、MOQ、交期、报价单位/包含项和目标SKU/pack一致性；缺失时标记`QUOTE_EVIDENCE_INCOMPLETE`，最多作为页面参考价或预估成本。
- 工作簿公式必须先用数值与正数校验，再计算成本和状态；缺项返回空值或具体待补状态，不得产生错误、填0或沿用上一行。任何公式错误标记`FORMULA_ERROR`并阻塞利润结论。

AI收到回填后先验证配置一致性。报价与目标Offer或选定改进在材质、规格、pack、组件、包装层级或计量单位不一致，或报价未包含却声称已经包含改进时，输出`QUOTE_CONFIGURATION_MISMATCH`和`profit_validation_status=数据异常`，不得选择更有利的一组数值。单个内件价和整包价不明时额外输出`QUOTE_UNIT_OR_PACK_MISMATCH`；未经人工确认报价单位，不得自动执行“单价×标题件数”。

## 5. AI实际利润计算

只有人工实填字段完整且来源可追踪时，才能输出`profit_basis=人工询价与最终包装实测`并计算实际利润：

计算前必须完整执行`referral-fees.md`与`fba-fees.md`：佣金按用户政策`USER_FIXED_15_PERCENT_2026-09-17`对成交基数统一计算15%，不再按费用类目切换比例；FBA费仍须按目标站、最终销售包装、计费重量、销售时段和用户指定Seller Central帮助来源匹配。不得用竞品FBA费或其他站点费率代替目标Offer费用。Seller Central帮助页需登录时记录状态并使用同站Amazon公开费率卡/已核验快照；档位有歧义、旺季精确费未核清或与Fee Preview冲突时，实际利润保持待补费用。

利润状态必须分两层：`base_fee_estimate_status`使用当前基础费或同站参考费，只能写`预估通过`、`预估不通过`或`待补`；`profit_validation_status`只有在目标销售时段有效费率、费档和所有成本齐全后才可写`通过/不通过`。目标销售窗口存在旺季费或需要Fee Preview时，未填`peak_fee_preview_local`一律为`FBA_PEAK_FEE_UNRESOLVED`、`BASE_FEE_ESTIMATE_ONLY`和`待补费用`。导出候选表时，基础费筛出的产品必须在文件名、标题和状态中写明“预估通过”，不得简称“利润通过”。

### 5.1 FBA费用路由必须成为成本公式的一部分

每个可重算利润表都必须从`fba-fees.md`指向的当前结构化快照读取费用，不能把某次候选的FBA金额粘贴成固定值。人工输入或受控参数至少包括：`site`、`target_sale_date_or_window`、含税/未税售价口径、目标Amazon费率类目、最终包装长宽高、包装后毛重、德国CEP状态、税率/税制口径和汇率。公式依次执行：

1. 按站点和目标销售日期选择仍在有效期内的费率表；目标期间没有已核验费率时返回`FBA_EFFECTIVE_PERIOD_GAP`和`待补费用`。
2. 按目标类目选择普通、特殊类目、低价、服装、危险品或其他适用路线；当前业务范围外路线不得借用相近表。
3. 按当地规则判断尺寸档、重量基础和售价门槛，再计算基础FBA费；售价门槛必须使用该计划规定的含税或未税口径。
4. 先应用适用折扣，再应用站点燃油物流附加费；折扣、附加费和税不能互相替代。
5. 把FBA费用和当地销售税/VAT/消费税分列进入完整贡献利润；PDF未提供的税率不得从FBA表反推。

站点强制路由：

- 英国、德国：低价FBA先检查普通类目或例外类目的含税售价上限，再检查35×25×12cm和400g自动资格。费率卡中的460g/960g信封行不能证明计划资格；超过400g只有精确Fee Preview确认后才能使用低价费。普通信封、低价FBA和列明特殊类目使用实重；其他普通包裹按实重与`长×宽×高÷5000`取大值。基础费后加1.5%。德国CEP未知时使用`DE_ONLY`，不得重复加EUR 0.26。
- 日本：按售价是否不超过¥1,000、最终包装尺寸/三边和重量路由；公开表档位重叠时不得自动选择较低费，必须用Revenue Calculator或Fee Preview。公开FBA表标明已含10%消费税时不得再把同一税重复加到FBA费用上；销售收入税制仍单独记录。
- 加拿大：低价折扣只在售价严格低于CAD $14且精确Offer符合资格时减CAD $0.80；再加3.5%。FBA计费重为实重和体积重较大值，信封/标准件向上进位至100g、超大件至500g。体积除数5000仅为官方示例反推值，精确档位仍需核验。2026-10-15至2027-01-14使用旺季表，2027-01-15起使用非旺季表；用户PDF未包含2026-09-21至2026-10-14当前费率，该期间必须`待补费用`。加拿大FBA表列值不含GST/HST，税项分列。
- 美国：只保存为参考，不属于六个选品Skill的GB/DE/JP/CA成本计算范围，禁止跨站套用。

费用计算至少输出：`target_sale_date_or_window`、`price_tax_basis`、`amazon_fee_category`、`fba_fee_category_route`、`low_price_price_cap`、`low_price_fba_eligibility`、`dimensional_weight_kg`、`fba_billable_weight`、`station_size_tier`、`base_fba_fee_local`、`applicable_discount_local`、`fba_surcharge_rate`、`effective_fba_fee_local`、`fba_rate_period_status`、`tax_inclusion_status`、`fee_snapshot_as_of`和`fee_source`。任一必需输入、有效期或路由缺失时不得返回0或沿用上一行费用。

```text
头程体积重kg = 长cm × 宽cm × 高cm ÷ 所选渠道体积重除数
头程计费重kg = MAX(包装实际重量kg, 头程体积重kg)
头程CNY/件 = 头程计费重kg × 渠道KG单价CNY
```

沿用用户已确认的头程口径：实际重量与体积重量取大值；按实际计费重，不做0.5kg或1kg进位；不计最低收费、旺季附加费和偏远附加费。渠道单价和体积重除数必须来自项目当前费率表；日本、加拿大费率未补齐时头程和实际利润保持待补。

再按公共完整利润公式计算：

```text
贡献利润 = 站点净销售收入
         - Amazon佣金 - 当前有效FBA配送费
         - 实际采购价 - 未包含的包装/打标 - 未包含的国内运费
         - 头程 - 关税/清关 - 仓储分摊 - 退货/破损准备
         - 其他单件费用
```

AI必须回显：站点原币售价、净销售收入、税费口径、固定15%佣金政策ID、佣金基数/金额、FBA费档和版本、Seller Central帮助页访问状态、公开计算器状态、人民币费用、汇率及日期、头程渠道/除数/KG单价、实重、体积重、计费重、每项成本、贡献利润、贡献利润率、保本售价和利润安全垫。任一关键项缺失时只能输出待补，不能称“实际利润”。

Excel交付须把上述逻辑实现为可重算公式，而不是粘贴一次性利润结果。采购人工输入区仅保留共享合同中的六个黄色数值；站点、目标售价、采购数量/计价单位与适用渠道由AI预填并锁定，费用参数置于受控`参数与费率`页，由公式按站点和费档读取。人工六项或AI受控配置更新后，体积重、计费重、头程、FBA、佣金、税费、贡献利润、贡献利润率、保本价和状态必须同步更新。站点费率或税制未核验时公式应保持结果不可用并显示具体缺项。

公式完整性与利润完整性是两个独立检查：工作簿不得出现公式错误；同时，公式能算出基础费结果也不代表目标时段费用已核清。规格状态必须校验数值类型、正数、报价口径和同一包装层级，不能只检查单元格是否为空。

实际利润自动通过仍须同时满足：采购成本`<=CNY 50`、贡献利润`>=USD 1`、贡献利润率`>=30%`和包装实重`<=2kg`，并且其他launch必需作用域均通过。

建议同时输出正常售价、保守售价和轻促销售价三种情景；促销情景不能取代正常售价通过。汇率、售价或报价变化导致越过门槛时重新计算。

## 6. 利润后的运营销售策略

只有`profit_validation_status=通过`后，AI才生成`operating_sales_strategy`。至少包括：

- 正常售价区间、最低保本售价和不破坏30%利润率的最低售价；
- 按保守预计月销、MOQ、销售窗口和库存风险计算的小批量首单建议，不自动采购；
- 核心非品牌自然词、目标Listing卖点和买家可感知的差异化表达；
- 仅将已有评论证据、供应规格和样品验收支持的改进写成卖点；不得把未验证想法宣传为已解决；
- 首批促销是否必要及可承受的单件促销空间；不能从自然位数量推算精确ACOS；
- 15/30/60/90天验证指标、补货触发点、停止补货条件和淘汰条件；
- 季节、节日和热点商品须同时给出剩余窗口、停止补货日和退出方案；
- 消耗品/pack及扩展Offer须分别按精确Offer计算库存和利润，不合并父体或其他pack。

利润待补或不通过时，`operating_strategy_status=未就绪`。利润不通过但市场通过时保留市场结论，并输出降采购价、改pack、减尺寸/重量、提售价或淘汰的敏感性条件；不得为了保留候选修改市场定义。

## 7. 决策状态与原因码

`quote_input_status`：`未触发`、`待人工填写`、`已填写待核验`、`已核验`、`数据异常`。

`profit_validation_status`：`未评估`、`待人工询价`、`待补费用`、`人工复核`、`通过`、`不通过`、`数据异常`。

原因码：`SELLER_PATTERN_CANDIDATE`、`SELLER_SURVIVORSHIP_BIAS`、`PROMOTION_DEPENDENCY`、`LOW_REVIEW_NOT_NEW`、`VARIATION_ENTRY_CONTAMINATION`、`REVIEW_SCAN_REQUIRED`、`REVIEW_COVERAGE_LIMITED`、`REVIEW_VARIATION_CONTAMINATION`、`REVIEW_DEFECT_NOT_REPEATABLE`、`REVIEW_DEFECT_NOT_CONTROLLABLE`、`IMPROVEMENT_IDEA_GENERATED`、`IMPROVEMENT_EVIDENCE_WEAK`、`IMPROVEMENT_COST_UNVERIFIED`、`IMPROVEMENT_NOT_LOW_COST`、`IMPROVEMENT_SELECTED`、`PREQUOTE_ECONOMICS_WEAK`、`QUOTE_INPUT_REQUIRED`、`QUOTE_STALE`、`QUOTE_CONFIGURATION_MISMATCH`、`QUOTE_UNIT_OR_PACK_MISMATCH`、`QUOTE_EVIDENCE_INCOMPLETE`、`NON_NUMERIC_COST_INPUT`、`NON_NUMERIC_PACK_COUNT`、`UNFOLDED_DIMENSION_USED`、`FORMULA_ERROR`、`BASE_FEE_ESTIMATE_ONLY`、`MANUAL_PACKAGE_INPUT_REQUIRED`、`ACTUAL_PROFIT_PASS`、`ACTUAL_PROFIT_FAIL`、`OPERATING_STRATEGY_NOT_READY`。
