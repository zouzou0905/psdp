# 季节品与节日品：空运小批验证路径

模块版本：`air-small-batch-window-v1.0.0`；更新：2026-10-08。

仅用于真实季节品或节日品的本周期迟到机会。保留正常开发路径，本路径只替代明确标注的常规启动/开发截止和“必须在窗口开始前到售”判断；不豁免主类型、历史长度/粒度、市场进入、自然流量、销量、合规、包装和利润门槛。不用于过早观察期，不自动授权采购、发货、上架或恢复研究。

## 1. 两方向分别路由，共用一次判断

- `development_path=normal_window`：按对应类型的现行启动、开发完成和到售节点执行，首批渠道按时间和完整经济性选择。
- `development_path=air_small_batch_validation`：季节品的压缩/错过窗口开始候选，或节日品错过常规开发完成/到售节点的候选，不立即作最终淘汰；先检查本路径。常规时机结论保留为`normal_timing_decision`，不得回写成按期完成。
- 季节品输出`air_path_direction=seasonal`；节日品输出`air_path_direction=holiday`。分类与原candidate_id不变；同一机会选择不同路线不能重复计入询价数量。
- 若正常路径已成立，通常不为使用空运而新增例外；需要比较时分别保留路线情景。空运不成立但正常路径成立，不能否决正常方案。

## 2. 从预计可售日看剩余需求

`assessment_stage=prequote`用于询价前计划判断；`assessment_stage=launch`用于人工询价、最终包装及实际开发完成后复核。两者都必须使用有依据的保守周期，不把未完成的打样/合规当0。

```text
planned_sellable_date = analysis_date
                     + remaining_development_days
                     + procurement_pack_domestic_days
                     + air_to_fba_receipt_days
                     + remaining_sellable_preparation_days
                     + safety_buffer_days
remaining_sales_days = demand_end_date - planned_sellable_date + 1
```

- 沿用14天安全缓冲；采购+包装+国内处理暂按用户给出的3–5天、空运至FBA接收暂按10天，保守计划用5+10+14=29天，区间为27–29天，**另加**尚未完成的研究/打样/改进/合规及接收后可售准备时间。10天是含到FBA接收的总段，不再重复加清关/接收天数；已包含的处理也不得双算。暂定周期标注来源和可信度，询价后按目标数量、渠道条件及实际进度更新，不能冒充运输保证。
- `demand_end_date`和可售日后需求必须有对应产品、当地售期、同阶段历史证据。节日仍要求两周期日/周证据；季节沿用类型证据要求，月度边界不清且无法保守证明剩余需求时待补。节日日期、全年/整季月销或旺季峰值不能代替剩余需求。
- 可售日已晚于需求截止、剩余需求不足以覆盖有证据的预计首单验证期及首批合理售罄期，或后段只有促销/清仓需求时，不通过本周期路径。公共预计首单<=15天及目标自身保守月销>=30仍须独立成立，不能因仅试卖而豁免。
- `remaining_target_sales_forecast`以共享市场的预注册T和同阶段曲线为依据，单列逐日/周的剩余预测及覆盖。不得简单用峰值月销÷30×剩余天数线性外推；缺失为待补。没有统一新增的“剩余X天即通过”阈值。

## 3. 空运后的询价空间与实际利润

- 询价前按公共包装规则对低/基准/高实重及体积重情景，使用项目有效空运费率/除数、目标销售时段FBA、税费和完整非采购成本，反推30%贡献利润率及最低贡献利润对应的采购上限。采购空间经形态/工艺推理可实现，且其他询价作用域均通过，才可形成`quote_ready`；实际利润仍待人工询价。
- 不能用卡航/海运成本给空运方案放行，不填0补缺失渠道费用，不用竞品净重冒充包装毛重。实际利润仍按人工实价、目标首批对应的MOQ/报价阶梯、最终销售包装及完整成本验证；贡献利润率>=30%、单件贡献利润>=USD1、整包采购<=CNY50、包装<=2kg和其他公共门槛不变。
- 首批按可售日后的保守需求、MOQ、资金暴露和退出成本拟定，拟定数量不得高于有依据的首批可销售数量；MOQ超过该数量且不能拆批时本路径不通过。采购报价阶梯必须与拟定首批匹配，不以次年大单报价证明今年小批利润。
- 正常售出部分的利润底线与首批整体回款/退出情景分别报告。列出开发/打样等一次性费用、滞销数量、清仓/移除/仓储准备及最坏资金暴露；缺必要数据不宣称首批整体盈利。不能将未售库存按正常售价计收益，也不能以预计次年收益填补本周期利润失败。

## 4. 阶段状态与完成条件

- 前置H1/季节时机快筛仅核对该阶段可得的类型、剩余需求与保守开发/到售计划，记录`air_path_screen_decision`和可继续H2/包装经济性研究的理由；不提前要求H4完整市场或人工报价，也不把前置可继续当作quote_ready。H2锁定配置、H3空运经济性及H4完整市场分别补齐后，才应用下一条研究通过条件。若缺少时机必需历史粒度，H1仍待补。
- 研究：类型、市场、包装、空运费用、保守开发/到售计划、剩余需求与首批/退出规划支持时，`air_path_decision=通过`仅表示本阶段路径可行；`timing_decision`按所选路径输出通过。缺任一必需证据则待补/人工复核，不计有效quote_ready；明确失败则不通过。不得先深抓全部评论再发现空运也已无需求。
- 人工询价后：重算实际采购价、MOQ/交期、包装、空运成本与可售日；全部launch作用域通过才可开发终审通过和输出可执行运营策略。未完成开发不得以“首年试卖”标记开发完成。
- 节日常规`development_completion_timing_status=过晚`保留；例外通过记录`AIR_SMALL_BATCH_TIMING_PASS`、本路径版本、所选售期、阶段、证据和审核理由，解释为何剩余窗口足以验证。不是补写虚假的旺季前30天完成日。
- 补货须重新核对到售日、剩余需求、完整利润和止补日，不默认晚期补货。不能沿用首批空运可行结论自动批准第二批。

## 5. 次年复用，不默认跨年压货

首年目的：验证真实售价接受、自然入口/转化、销量节奏、差评与改进、包装和实际成本。记录`first_cycle_learning_plan`及实际观测，未售前不称已验证。

次年优先复用无年份标记、不易过时、保存稳定且两周期需求可重复的产品方案、有效样品规格和研究记录。次年重新核对需求、竞争、价格、费用、报价、合规和时机；不能承诺评论、排名或销量自动延续。

跨年留存库存是另一项决策：只有计入实际仓储/移除、损耗、资金占用、包装/标签有效性及次年再入仓费用后方案成立，才可建议留存；否则按本周期退出。首年开发可为次年创造条件，不等于首年必须备次年货。

## 6. 输出与原因码

上述路线字段与证据放入统一`证据与包装`，不增加采购主表或黄色六项输入。至少保存：`air_window_policy_version`、`development_path`、`air_path_direction`、`assessment_stage`、`normal_timing_decision`、`air_path_decision`、`remaining_development_days`、`planned_sellable_date`、`demand_end_date`、`remaining_sales_days`、`remaining_target_sales_forecast`、`remaining_demand_evidence`、`expected_first_order_days`、`planned_first_batch_qty`、`moq_fit_status`、`air_procurement_space_cny`、`first_batch_cash_risk_scenarios`、`stop_replenishment_date`、`inventory_exit_plan_status`、`first_cycle_learning_plan`、`next_cycle_revalidation_plan`和审核理由。

原因码：`AIR_SMALL_BATCH_TIMING_PASS`、`AIR_REMAINING_DEMAND_MISSING`、`AIR_REMAINING_WINDOW_INSUFFICIENT`、`AIR_RATE_OR_COST_MISSING`、`AIR_PREQUOTE_ECONOMICS_FAIL`、`AIR_MOQ_WINDOW_MISMATCH`、`AIR_ACTUAL_PROFIT_PENDING`、`AIR_ACTUAL_PROFIT_FAIL`、`NEXT_CYCLE_REVALIDATION_REQUIRED`。
