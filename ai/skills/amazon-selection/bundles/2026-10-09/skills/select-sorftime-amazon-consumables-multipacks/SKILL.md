---
name: select-sorftime-amazon-consumables-multipacks
description: Independently discover and validate Amazon GB, DE, JP, or CA FBA private-label opportunities for replenishable consumables and demand-backed pack sizes from small packs through high-piece-count offers with Sorftime, or review those attributes for an existing candidate. Use for 消耗品、一次性用品、多件装、小包装、大PCS、补充装、替换装、耗材、复购周期、包装规格、单位价值. Preserve and validate the evergreen, seasonal, holiday, or trending primary demand type before final launch approval.
---

# 亚马逊消耗品与包装规格选品

从目标站Amazon在售结构和当地真实需求出发，独立发现消耗品及包装规格机会，或复核已有候选。目标Offer可以是小包装、标准包装或大PCS；不得预设件数越多越好。消耗属性、包装规格和主需求周期是不同判断维度。

## 开始前

先完整读取 `../_amazon-selection-shared/six-agent-control.md`，确认本智能体职责、共用流程和权限边界。

规范一致性是硬门槛：共享合同规定的固定文件名、工作表名称与顺序、字段顺序、颜色、状态和交互路径必须逐字逐项执行；不得沿用历史工作簿命名或自行变体。交付前按当前合同检查，不一致先修复再交付。

1. 完整读取 `../_amazon-selection-shared/common-gates.md`。
2. 完整读取 `../_amazon-selection-shared/market-entry.md`。
3. 完整读取 `../_amazon-selection-shared/candidate-profit-workflow.md`。
4. 批量选品、采购回填或二次利润复核时，完整读取 `../_amazon-selection-shared/batch-review-handoff.md`。
5. 完整读取 `../_amazon-selection-shared/referral-fees.md`、`../_amazon-selection-shared/fba-fees.md`及其指向的结构化JSON费率快照。
6. 完整读取 `references/type-rules.md`。公共规则的分阶段流程适用于本Skill；批量发现先读 `../_amazon-selection-shared/selection-memory.md` 及其审核数据，使用统一候选池，不按方向凑数。
7. 确认站点、种子、`selection_mode`（独立发现/标签复核）、`branch_mode`（消耗品/包装规格/两者）和`pack_scope`（小包装/标准包装/大PCS/多档比较）。
8. 独立发现模式可以在没有上游候选时扫描Amazon并形成候选，但最终`launch_decision=通过`前必须按真实需求周期完成日常、季节、节日或热点主类型验证。
9. 标签复核模式优先复用同站点、同市场定义、同政策版本且仍有效的上游主类型与共享市场结果。
10. 明确`selected_launch_strategy_tags`。选择某个目标包装规格不等于必须取得“大PCS”标签。

## 执行调度绑定（2026-10-08）

完整执行共享six-agent-control.md第4.1a节（selection-execution-v1.2.0）：证据可得性先查、价格—重量预检、市场与包装经济性同步、小批深验、分层交付及有效证据复用；不降低最终launch硬门槛，严格询价、受控试询与实际利润/开发通过分别计数。先确认是“消耗补充”还是“包装规格机会”，再按当地需求比较小包、标准包、大PCS；不额外要求5个完全相同PCS，但T独立性与配置可比条件不放宽。

数量型任务另完整读取 `../_amazon-selection-shared/selection-run-control.md`：阶段交付不是停止，已授权且有可行动作时继续累计原目标；运行未启用或真实阻塞须明确报告，初始化/升级不自动恢复选品。

## 成本计算绑定（2026-09-21）

- 本Skill的粗算、询价表、实际利润和开发终审必须执行共享`candidate-profit-workflow-v1.9.0`、`selection-gates-v0.10.0`及`fba-fees.md`当前快照；FBA金额不得粘贴成固定值。
- 可重算表按站点、目标销售日期、含税/未税售价口径、Amazon费率类目、最终包装长宽高/毛重、费率有效期和税制动态路由：英德核验低价计划的售价/例外类目/尺寸/400g资格，日本核验售价档与重叠费档，加拿大核验旺季/非旺季、100g或500g进位、低价折扣和GST/HST分列；美国费率禁止跨站使用。
- 人工修改实际采购价、最终包装尺寸或重量后，体积重、计费重、头程、FBA费、15%佣金、税费、贡献利润、利润率、保本价和结论必须同步更新。缺费率有效期、类目路由、售价税口径、包装数据、税率、汇率或目标站头程费率时返回`待补费用`，不得按0或沿用上一行。
- 采购回填字段类型、询价证据、基础费预估/最终利润分层及公式错误拦截统一执行`candidate-profit-workflow-v1.9.0`和`batch-review-handoff-v2.0.0`，本Skill不复制第二套口径。
- 询价前包装估算统一执行`selection-gates-v0.10.0`：优先精确子ASIN、同父体pack梯度或多个同结构可比Offer，输出低/基准/高重量体积、A–D置信度、预判头程路线/FBA费档和三情景采购空间；C按保守情景进入B/C档，D先补证。最终利润仍只认人工询价后的供应商确认/实测包装数据。

## 批量询价数量要求（2026-09-22）

- 独立发现模式的标准批次以50个去重的`quote_ready`目标Offer为累计完成条件，不以发现50个候选为完成；按`batch-review-handoff-v2.0.0`集中小批深验、有针对性扩池，实得合格行先分批交采购，再继续累计至请求数量。标签复核模式按用户交付的候选数量执行。
- 采购价未知不提前淘汰，选品阶段不核对1688或要求供应入口。只要主类型及时机、市场、目标配置和非采购成本支持，采购成本取0时经济性通过，30%利润后的采购空间为正，且按材料、工艺、结构、pack、定制、认证和包装负担推理可能实现，即带采购空间进入人工询价；明显不可实现时淘汰。
- 不足50个时只能标记未完成并继续扩池或报告客观缺口；不得用同一父体不同件数、无子体需求证据、待补或无经济性的产品凑数。

## 工作流

1. 固定截止时间，从目标站Amazon在售/成交结构、人工通过品相邻需求和评论问题形成统一候选池。优先商业任务明确、扁平/可压缩/可套叠、单位重量售价较高且规格标准化的机会；不以高PCS或低单价本身扩池。杯子、包装袋、螺丝仅是形态示例，不预设大PCS或分配独立名额。
2. 在完整市场研究前按公共漏斗核对实体、历史去重、精确市场父体密度和价格—重量/FBA承受区间，锁定目标pack和包装情景，反推30%利润后的采购空间；选品阶段不搜索或核对1688。明显低价重货先淘汰，接近物流/FBA档位边界用保守情景。
3. 以同一购买意图、买家/使用场景（家庭、商业、施工、生产等）、功能、材质、尺寸/克重和用途建立可比集，解析父ASIN、精确子ASIN、pack数量、有效单位、售价、销量、评论和自然位。
4. 建立`pack_ladder`，分别观察小包装、标准包装和大PCS的在售数量、目标子体销量、新进入者表现、价格带及每有效单位价格。无法拆分子体销量时标记污染，不替目标pack补造需求。
5. 先选择`CONSUMABLE_REPLENISHMENT`、`PACK_SIZE_OPPORTUNITY`或`BOTH`。消耗分支证明客观耗用与复购代理；包装分支独立验证目标pack自身月销、自然流量、价格接受度、单位经济性和同档新品进入性。未选择消耗标签时，不因复购证据不足否决已经成立的包装机会。
6. 对每个拟售pack独立运行共享市场模块。一个产品可比较2–3档pack，但默认只把证据最强的一档计为一个询价机会；只有买家场景、价格带和目标子体需求均独立时，第二档才可另计。
7. 识别真实主需求周期并路由到对应主类型规则。主类型未完成时可以输出发现/包装规格结论，但进入观察池，launch保持`待补`。
8. 独立发现、主类型、市场和目标pack支持继续开发后，为每个目标Offer分别输出严格询价；仅市场组合证据满足公共受控条件时可进入受控试询。人工填写该pack的实际整包采购价、确认规格、最终包装三边和包装后实重后，由AI计算实际利润。不同pack不得共用未经核验的价格、尺寸或重量。
9. 只有目标Offer实际利润及全部launch必需作用域通过才生成该pack的运营销售策略；分别输出独立发现、主类型、市场、消耗属性、包装规格及开发结论，并按公共决策传播规则聚合。

## 强制行为

- Amazon当地在售结构和目标子体需求决定pack选择；小包装、标准包装和大PCS均无预设优先级。
- 标题写disposable、refill或500PCS不能证明消耗或大PCS需求成立。
- 父体销量、价格和评论不能直接归给目标子体；小包装销量不能证明大包装，大包装销量也不能证明小包装。
- 商品卡最低价不能代替目标供应SKU整包成本。
- 件数增加但单件变小、变薄或材质降级时按有效用量归一。
- 异质功能组件不能用总件数冒充大PCS；路由功能组合评估。
- 消耗属性按目标使用场景判断，不按商品名称永久定性。同一螺丝在家庭偶发维修场景可不是消耗品，在施工、装配、维修车间或生产作业中若持续领用并形成可证明补货周期，可以取得商业消耗品标签；件数多本身仍不是消耗证据。
- 小包装或标准包装方案独立通过时，不因未取得大PCS标签而失败；只有本次明确依赖大PCS策略时，大PCS状态才传导。
- 食品接触、紧固件规格、安全承重、材质或其他合规属性必须按精确产品核验，示例类目不豁免公共风险门槛。
- `secondary_tags`只包含状态为`通过`的标签；待补、人工复核、不通过或不适用只出现在`tag_decisions`。
- 不执行采购，不联系供应商。

## 输出

使用公共输出合同，并额外输出：`selection_mode`、`selection_lane`、`selection_lane_decision`、`buyer_segment`、`use_context`、`depletion_mechanism`、`branch_mode`、`pack_scope`、`pack_ladder`、`target_pack_tier`、`target_pack_count`、`pack_market_fit_status`、`pack_demand_evidence`、`selected_launch_strategy_tags`、`primary_type`、`primary_type_source`、`primary_type_validation_status`、`secondary_tags`、`consumable_status`、`repeat_cycle_days`、`repeat_evidence_count`、`repeat_evidence`、`large_pcs_status`、`stated_piece_count`、`effective_units`、`market_median_effective_units`、`pack_ratio`、`retail_unit_price`、`benchmark_unit_price`、`unit_value_advantage`、`variation_integrity_status`、`functional_bundle_route`、`supplier_sku_id`、`supplier_pack_count`、`procurement_pack_cost_cny`。

## 阶段与证据边界（v0.6）

输出 `research_stage`、`screen_decision`、`review_type`、`memory_match_ids` 与补证动作。候选优先复用“问题型长尾意图→可感知且可执行改进→有依据的pack/组合→低评新品自然入口”结构，但卖家案例仅用于发现并披露幸存者、变体与促销污染。确定直接竞品后立即按共享流程快抓评论、分析重复差评并发散低成本改进；采用改进时必须落到目标pack实际报价和验收方法。研究通过或区间粗算通过都不等于 `launch_decision=通过`；目标配置不足时按共享市场的组合证据路线进行人工研究。人工实际询价及最终包装三边/实重未核验时，`profit_validation_status=待人工询价`，不得生成可执行运营策略。只有AI按目标Offer复算实际利润并通过全部门槛，才进入开发排序并输出该pack的运营销售策略。主类型改路沿用候选ID和有效证据。
