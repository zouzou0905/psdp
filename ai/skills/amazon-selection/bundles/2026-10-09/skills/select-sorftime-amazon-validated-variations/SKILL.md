---
name: select-sorftime-amazon-validated-variations
description: Validate lawful, demand-backed light variations, bundles, packaging changes, UV prints, and laser-mark extensions for already validated Amazon GB, DE, JP, or CA FBA private-label products with Sorftime. Use when the user asks to expand an existing product by color, pattern, size, pack quantity, model fitment, functional combination, packaging, UV, laser, or a small variation matrix. Choose the correct route under Amazon's 2026 review-sharing rules and require every target child or standalone offer to independently pass demand, profit, sourcing, weight, natural-traffic, compliance, and IP gates. Do not use for an unvalidated net-new product.
---

# 亚马逊已验证产品扩展

为已经通过主类型、市场和开发验证的产品设计小规模、合法、可独立盈利的扩展方案。分别判断商业机会、父子关系合法性、评论共享预期和每个目标Offer的独立可行性。

## 开始前

先完整读取 `../_amazon-selection-shared/six-agent-control.md`，确认本智能体职责、共用流程和权限边界。

规范一致性是硬门槛：共享合同规定的固定文件名、工作表名称与顺序、字段顺序、颜色、状态和交互路径必须逐字逐项执行；不得沿用历史工作簿命名或自行变体。交付前按当前合同检查，不一致先修复再交付。

1. 完整读取 `../_amazon-selection-shared/common-gates.md`。
2. 完整读取 `../_amazon-selection-shared/market-entry.md`。
3. 完整读取 `../_amazon-selection-shared/candidate-profit-workflow.md`。
4. 批量选品、采购回填或二次利润复核时，完整读取 `../_amazon-selection-shared/batch-review-handoff.md`。
5. 完整读取 `../_amazon-selection-shared/referral-fees.md`、`../_amazon-selection-shared/fba-fees.md`及其指向的结构化JSON费率快照。
6. 完整读取 `references/type-rules.md`。公共规则的分阶段流程适用于本Skill；批量发现先读 `../_amazon-selection-shared/selection-memory.md` 及其审核数据，使用统一候选池，不按方向凑数。
7. 确认站点、基础父/子ASIN、主类型、当前市场结果、拟扩展属性和目标Offer。
8. 为每个目标Offer准备独立人工询价输入；未填写真实采购价、确认规格、最终销售包装三边和包装后实重时不得认定实际利润通过。
9. 取得目标站点及类目当前允许的变体主题；Sorftime和竞争对手页面不能替代Seller Central规则。

## 执行调度绑定（2026-10-08）

完整执行共享six-agent-control.md第4.1a节（selection-execution-v1.1.0）：证据可得性先查、市场与包装经济性同步、小批深验、分批交付及有效证据复用；不降低任何硬门槛，quote_ready与实际利润/开发通过分别计数。仅对已验证基础产品复用有效证据并补扩展Offer缺口；仍采用单主题、首批最多2–3个证据最强Offer，不套用约10个新产品研究目标或50款累计目标。

数量型任务另完整读取 `../_amazon-selection-shared/selection-run-control.md`：阶段交付不是停止，已授权且有可行动作时继续累计用户请求；仍按单主题2–3个Offer边界，不套用50款目标。运行未启用或真实阻塞须明确报告，初始化/升级不自动恢复选品。

## 成本计算绑定（2026-09-21）

- 本Skill的粗算、询价表、实际利润和开发终审必须执行共享`candidate-profit-workflow-v1.8.0`、`selection-gates-v0.9.2`及`fba-fees.md`当前快照；FBA金额不得粘贴成固定值。
- 可重算表按站点、目标销售日期、含税/未税售价口径、Amazon费率类目、最终包装长宽高/毛重、费率有效期和税制动态路由：英德核验低价计划的售价/例外类目/尺寸/400g资格，日本核验售价档与重叠费档，加拿大核验旺季/非旺季、100g或500g进位、低价折扣和GST/HST分列；美国费率禁止跨站使用。
- 人工修改实际采购价、最终包装尺寸或重量后，体积重、计费重、头程、FBA费、15%佣金、税费、贡献利润、利润率、保本价和结论必须同步更新。缺费率有效期、类目路由、售价税口径、包装数据、税率、汇率或目标站头程费率时返回`待补费用`，不得按0或沿用上一行。
- 采购回填字段类型、询价证据、基础费预估/最终利润分层及公式错误拦截统一执行`candidate-profit-workflow-v1.8.0`和`batch-review-handoff-v1.9.0`，本Skill不复制第二套口径。
- 询价前包装估算统一执行`selection-gates-v0.9.2`：优先精确子ASIN、同父体pack梯度或多个同结构可比Offer，输出低/基准/高重量体积、A–D置信度、预判头程路线/FBA费档和三情景采购空间；C按保守情景进入B/C档，D先补证。最终利润仍只认人工询价后的供应商确认/实测包装数据。

## 批量数量边界（2026-09-22）

本Skill不适用五个新产品方向的“每批50个实际询价”目标。扩展必须依赖已验证基础产品，继续坚持单一变体主题、首批最多2–3个证据最强Offer；为达到50个而扩大变体矩阵会增加评论依赖、库存碎片化和关系违规风险。

## 工作流

1. 固定截止时间，确认基础产品已经通过对应主类型、市场及开发验证，并达到稳定性门槛。
2. 检查基础产品销量、自然流量、利润、评分、退货/差评、断货、促销和变体污染。
3. 将差异分类为颜色/图案、同功能尺寸、同商品包数、型号适配、包装更新、固定UV/激光、个性化输入、功能或组合变化。
4. 对已验证基础产品的拟扩展Offer按公共分阶段流程核对实体、历史记忆、去重和业务风险；关系与市场可和包装情景、采购空间推理同步开展，选品阶段不核对1688。人工询价后、开发终审前再核清精确SKU、实际报价及所有费用。仅记为“已做”而无基础产品验证记录时，先补基础验证，不自动启动矩阵。
5. 核验品牌、产品类型、核心功能、基础标题、客户预期和当前类目变体主题。
6. 为每项扩展选择：合法父子变体、独立ASIN、原ASIN包装更新、Amazon Custom/人工复核或淘汰。
7. 按2026评论规则单独判断`review_sharing_expected`；固定枚举为`预计符合共享资格`、`预计不符合共享资格`、`未知`，任何枚举都不是Amazon实际共享保证。无论预期如何，都按完全不共享情景验证需求。
8. 按共享市场模块为每个目标Offer建立精确可比市场和属性级需求证据。
9. 对市场支持的每个目标Offer独立生成询价表；人工填写后，AI核对询价配置与拟售配置一致，并独立计算实际利润、采购、重量、FBA费、库存和合规/IP风险。
10. 计算对基础SKU的蚕食和增量组合利润；高父体销量不能掩盖新Offer的负增量。
11. 首批只建议一个变体主题、最多2–3个证据最强的Offer；验证后再扩。
12. 先按关系路径分组，再输出逐Offer和批次结论；独立ASIN、包装更新及Custom路线不混入父子变体批次。只有逐Offer实际利润和全部launch必需作用域通过后才输出相应运营销售策略。输出可执行的修订批次，不创建Listing、不下单、不联系供应商。

## 强制行为

- 父体销量、评论或共享评论不能平均分给目标子体。
- 每个拟采购Offer独立预计月销>=30，并独立通过采购<=CNY50、包装<=2kg、利润>=USD1且利润率>=30%。
- 包装外观变化但产品和数量相同、客户无需选择时，不创建重复ASIN。
- 功能、部件或组合内容变化默认不是普通轻变体。
- 固定UV/激光只有在核心功能不变且类目支持相应主题时才可能成为变体。
- 买家输入姓名、文字或照片不得伪装成普通颜色/图案变体。
- 竞争对手的变体结构不证明合规。
- 子体数量不等于独立产品机会数；同时报告父体机会数和子体候选数。

## 输出

使用公共输出合同，并额外输出：`base_asin`、`base_primary_type`、`base_validation_status`、`base_stability_status`、`existing_parent_asin`、`existing_child_count`、`proposed_dimension`、`proposed_child_value`、`difference_description`、`core_function_changed`、`category_theme_supported`、`proposed_variation_theme`、`relationship_route`、`relationship_decision`、`review_policy_as_of`、`review_sharing_expected`、`review_sharing_basis`、`review_independent_case_pass`、`variant_keyword_evidence`、`comparable_parent_count`、`comparable_child_count`、`comparable_child_sales_p25`、`estimated_target_offer_monthly_sales`、`target_offer_share_evidence`、`target_offer_economics`、`cannibalization_rate`、`incremental_portfolio_profit`、`new_children_in_batch`、`matrix_stage`、`offer_decision`、`family_expansion_decision`、`standalone_expansion_decision`、`approved_family_offer_ids`、`rejected_family_offer_ids`、`approved_standalone_offer_ids`、`rejected_standalone_offer_ids`、`rerouted_offer_ids`、`revised_family_batch_decision`、`revised_standalone_batch_decision`。

## 阶段与证据边界（v0.6）

输出 `research_stage`、`screen_decision`、`review_type`、`memory_match_ids` 与补证动作。扩展候选也可复用“问题型长尾意图→可感知且可执行改进→有依据的pack/组合→低评新品自然入口”结构，但卖家案例仅用于发现并披露幸存者、变体与促销污染。确定直接竞品后立即按共享流程快抓评论、分析重复差评并发散低成本改进；采用改进时必须落到逐Offer实际报价和验收方法。研究通过或区间粗算通过都不等于 `launch_decision=通过`；目标配置不足时按共享市场的组合证据路线进行人工研究。每个目标Offer的人工实际询价及最终包装三边/实重未核验时，`profit_validation_status=待人工询价`，不得生成可执行运营策略。只有AI逐Offer复算实际利润并通过全部门槛，才进入修订批次和运营销售策略。主类型改路沿用候选ID和有效证据。
