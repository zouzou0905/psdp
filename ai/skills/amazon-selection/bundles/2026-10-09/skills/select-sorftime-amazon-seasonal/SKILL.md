---
name: select-sorftime-amazon-seasonal
description: Discover and validate Amazon GB, DE, JP, or CA FBA private-label seasonal opportunities with Sorftime. Use for 季节品、春夏秋冬产品、气候相关商品、周期旺季、季节备货, or when evaluating whether a keyword, ASIN, category, or candidate list has a repeatable four-to-nine-month demand window and enough time to reach FBA. Do not treat holiday-name demand or one-off viral spikes as seasonal evidence.
---

# 亚马逊季节窗口品选品

识别每周期有4–9个有效需求月、跨周期复现、窗口可解释且当前仍来得及入场的季节品。类型成立、市场可进入和本周期来得及是三个独立判断。

## 开始前

先完整读取 `../_amazon-selection-shared/six-agent-control.md`，确认本智能体职责、共用流程和权限边界。

规范一致性是硬门槛：共享合同规定的固定文件名、工作表名称与顺序、字段顺序、颜色、状态和交互路径必须逐字逐项执行；不得沿用历史工作簿命名或自行变体。交付前按当前合同检查，不一致先修复再交付。

1. 完整读取 `../_amazon-selection-shared/common-gates.md`。
2. 完整读取 `../_amazon-selection-shared/market-entry.md`。
3. 完整读取 `../_amazon-selection-shared/candidate-profit-workflow.md`。
4. 批量选品、采购回填或二次利润复核时，完整读取 `../_amazon-selection-shared/batch-review-handoff.md`。
5. 完整读取 `../_amazon-selection-shared/referral-fees.md`、`../_amazon-selection-shared/fba-fees.md`及其指向的结构化JSON费率快照。
6. 完整读取 `references/type-rules.md`。公共规则的分阶段流程适用于本Skill；批量发现先读 `../_amazon-selection-shared/selection-memory.md` 及其审核数据，使用统一候选池，不按方向凑数。
7. 确认站点、分析日、种子、目标季节/销售窗口和是否允许退季留存。
8. 分开记录采购、包装/打标、国内运输、头程、清关、FBA接收天数及14天安全缓冲，避免重复或漏算。

## 正常开发与空运小批验证路径（2026-10-08）

保留正常窗口开发；压缩验证或赶不上常规到售节点的候选，先完整读取`../_amazon-selection-shared/air-small-batch-window.md`，评估空运后的剩余真实需求、首批和采购空间，不只因错过旺季开始而淘汰。按`development_path`分开常规与空运结论；空运成立仍须满足原主类型/市场/利润等门槛，人工询价后方可终审，首年小批验证可为次年复用产品方案创造条件，不默认跨年压货。

## 执行调度绑定（2026-10-08）

完整执行共享six-agent-control.md第4.1a节（selection-execution-v1.2.0）：证据可得性先查、市场预检与包装经济性同步、小批深验、分层交付及有效证据复用；不降低最终launch硬门槛，严格询价、受控试询与实际利润/开发通过分别计数。先检查真实季节窗口和两周期证据可得性，再进入当前可开发机会的小批深验；当前太早、太晚或缺证的保留相应状态，不能用日常或节日机会补本方向名额。

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

1. 固定截止时间，用目标站当地语言扩展季节关键词。
2. 维护目标站季节日历和观察池：旺季前150天进入监控，120–90天正式筛选，90天内进入压缩/空运评估。按买家场景和紧凑物流形态扩展候选，优先扁平、可折叠、可套叠、可压缩方案。
3. 按公共分阶段漏斗完成实体、历史记忆、去重、精确市场密度、售价—重量区间及已知硬失败快筛；先查真实季节窗口是否允许启动研究。锁定目标Offer、pack和合理包装情景，与市场同步反推采购空间并判断其可实现性；选品阶段不核对1688。
4. 建立至少两个完整需求周期的类目、关键词和代表ASIN趋势；不足时按类型规则进入严格、受控或观察层，不拼接伪造曲线。
5. 计算每周期有效月、Top3月份需求占比、窗口重叠、峰值偏移和跨来源一致性。
6. 排除断货、促销、价格跳水、一次性事件和变体合并形成的假季节。
7. 用共享市场模块验证精确市场；新品队列与头部基准必须取相同季节阶段，不能拿淡季新品对旺季头部。
8. 正常路径以真实需求窗口开始日为基准，在距窗口120–90天启动正式选品；并独立计算原始链路、缓冲、所需提前期、最晚采购日和最晚FBA到仓日。迟到候选另按空运小批验证模块检查可售日后的剩余窗口；常规结论保留，不用正常路线成本给空运放行。
9. 类型、时机、市场和目标配置支持继续开发后，输出严格询价；只有一个类型证据作用域因历史粒度限制为人工复核且替代证据满足规则时，才进入受控试询。人工填写实际采购价、确认规格、最终包装三边和包装后实重后，由AI计算实际利润，并核对库存退出成本。
10. 只有实际利润和全部launch必需作用域通过才生成与剩余窗口相匹配的运营销售策略；分别输出类型、时机、市场和开发结论，错过本周期不改变类型分类。

## 强制行为

- 一个周期或单年连续4个月暴涨不能自动证明季节复现。
- 断货、尚未上架或数据缺失的月份不能当淡季。
- 季节品正式选品应在真实需求窗口开始前120–90天启动；早于120天只观察，晚于90天才首次发现的新候选进入压缩验证。
- 120–90天是候选发现和市场验证启动带，不是采购提前期；采购与到售仍使用实际链路+14天缓冲。
- 由具体节日日期或礼赠意图主导时建议节日品Skill。
- 不执行采购；正常节点错过先审空运小批路径，空运也不成立时本周期不通过并保留下一周期候选；缺证仍待补。

## 输出

使用公共输出合同，并额外输出：`evidence_months`、`effective_months_per_cycle`、`top3_month_demand_share`、`peak_start`、`peak_end`、`peak_date`、`yoy_window_overlap`、`yoy_peak_shift`、`selection_open_date`、`selection_start_deadline_date`、`selection_started_date`、`selection_timing_stage`、`raw_chain_days`、`safety_buffer_days`、`required_launch_lead_days`、`days_to_window_start`、`lead_shortfall_days`、`latest_purchase_date`、`latest_fba_arrival_date`、`timing_scope`、`inventory_exit_plan_status`。

## 阶段与证据边界（v0.6）

输出 `research_stage`、`screen_decision`、`review_type`、`memory_match_ids` 与补证动作。候选优先复用“问题型长尾意图→可感知且可执行改进→有依据的pack/组合→低评新品自然入口”结构，但卖家案例仅用于发现并披露幸存者、变体与促销污染。确定直接竞品后立即按共享流程快抓评论、分析重复差评并发散低成本改进；采用改进时必须落到实际报价和验收方法。研究通过或区间粗算通过都不等于 `launch_decision=通过`；目标配置不足时按共享市场的组合证据路线进行人工研究。人工实际询价及最终包装三边/实重未核验时，`profit_validation_status=待人工询价`，不得生成可执行运营策略。只有AI完成实际利润复算并通过全部门槛，才进入开发排序并输出与销售窗口相匹配的运营策略。主类型改路沿用候选ID和有效证据。
