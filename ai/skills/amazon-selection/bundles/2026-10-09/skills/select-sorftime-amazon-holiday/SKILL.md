---
name: select-sorftime-amazon-holiday
description: Discover and validate Amazon GB, DE, JP, or CA FBA private-label holiday and event-driven opportunities with Sorftime. Use for 节日品、节庆定制、圣诞、万圣节、情人节、复活节、母亲节、父亲节、感恩节, or when evaluating genuine event intent, repeatable event-relative demand, short/medium/long shopping windows, too-early or too-late development timing, customization, IP risk, and an inventory exit plan. Reject name-only holiday labels and one-off viral spikes.
---

# 亚马逊节日事件品选品

识别由明确节日用途和节日前购买意图驱动、跨周期复现、当前仍有足够到售时间且退场风险可控的节日机会。

## 开始前

先完整读取 `../_amazon-selection-shared/six-agent-control.md`，确认本智能体职责、共用流程和权限边界。

规范一致性是硬门槛：共享合同规定的固定文件名、工作表名称与顺序、字段顺序、颜色、状态和交互路径必须逐字逐项执行；不得沿用历史工作簿命名或自行变体。交付前按当前合同检查，不一致先修复再交付。

1. 完整读取 `../_amazon-selection-shared/common-gates.md`。
2. 完整读取 `../_amazon-selection-shared/market-entry.md`。
3. 完整读取 `../_amazon-selection-shared/candidate-profit-workflow.md`。
4. 批量选品、采购回填或二次利润复核时，完整读取 `../_amazon-selection-shared/batch-review-handoff.md`。
5. 完整读取 `../_amazon-selection-shared/referral-fees.md`、`../_amazon-selection-shared/fba-fees.md`及其指向的结构化JSON费率快照。
6. 完整读取 `references/type-rules.md`。公共规则的分阶段流程适用于本Skill；批量发现先读 `../_amazon-selection-shared/selection-memory.md` 及其审核数据，使用统一候选池，不按方向凑数。
7. 确认站点、节日、目标年份、种子和完整到售链路。
8. 核验目标站当地节日日期；浮动节日、地方节日和文化差异不得凭记忆猜测。

## 正常开发与空运小批验证路径（2026-10-08）

保留正常窗口开发；错过常规开发完成或到售节点的候选，先完整读取`../_amazon-selection-shared/air-small-batch-window.md`，评估空运后的剩余真实购物需求、首批和采购空间，不只因距旺季不足30天而淘汰。两周期日/周证据、市场、利润和全部launch门槛不变；按`development_path`独立输出常规/空运结论，询价前不冒充开发完成。首年小批验证可为次年复用创造条件，不以次年收益弥补首年亏损。

## 执行调度绑定（2026-10-08）

完整执行共享six-agent-control.md第4.1a节（selection-execution-v1.2.0）：证据可得性先查、事件纯度/市场预检与包装经济性同步、小批深验、分层交付及有效证据复用；不降低任何硬门槛，严格询价、观察池与实际利润/开发通过分别计数。证据可得性检查先于批量扩词，正式深验仍遵循H0–H3之后进入H4；缺必需日/周需求时机证据保留待补，不用月度曲线、事件日或自然曝光日期代替，也不进入受控试询。

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
- 不足50个时只能标记未完成并继续扩池或报告客观缺口；不得用重复ASIN、同父体轻微变体、待补、观察或无经济性的产品凑数。

## 节日品前置漏斗（holiday-front-funnel-v1.2.0）

候选必须依次通过H0–H3，才允许进入评论深抓、完整市场验证和人工采购询价。前置失败、改类或观察期候选不得占用“节日深度候选”名额；选品阶段不核对1688，并保留候选ID、证据和下一动作。

### H0：节日类型纯度

- 先锁定`event_name`、目标站当地`target_event_date`、买家为何必须围绕该事件购买、节日专属使用场景和至少两个周期的趋势线索。
- 标题、图案或关键词仅含节日名称，或者产品全年同样成立，不算节日品；立即输出`RECLASS_EVERGREEN`、`RECLASS_SEASONAL`、`RECLASS_HOT_ACCESSORY`或不通过。
- 年度非节日事件、通用礼品、通用派对用品和四季装饰不得为了批次数量留在节日池。
- 在H0同时检查设计是否陈旧、是否依赖单年流行梗、历史同类亏损、包装是否明显过大及是否只能低价销售；这些信号分别进入设计/经济/包装预检，不能等H4后才发现。

### H1a：粗时间资格

- 在深验前先计算购物窗口、旺季开始日、选品启动带、开发完成目标带和完整到售链路。
- 长窗口尚未进入120–90天选品启动带：仅进入观察池并设置复核日。错过常规开发完成或到售节点时先审空运小批路径；该路径本阶段成立才可继续H2，空运也无剩余有效需求时本周期停止，缺证则待补。正常可预研、可开发及证据充分的压缩验证路径保留。
- 月度双周期、真实事件意图和粗略价格/包装证据只用于候选优先级和观察复核日，不授予询价资格。节日日期不能代替购物窗口开始日或旺季开始日。

### H1b：精确时间验证

- 短、中、长窗口均须两周期日/周级P10–P90购物窗口、旺季开始、当前剩余需求及完整链路；缺失时窗口及时机为待补并进入观察池，不得进入严格或受控询价。

### H2：目标Offer与pack锁定

- 每个候选只锁定一个Amazon可售单位：目标ASIN/Offer、材质、关键规格、`target_pack_count`、目标售价和包装层级。选品阶段不要求对应供应SKU或1688询价入口。
- Amazon目标pack、供应pack、报价单位或包装层级不能一一对应时，标记`QUOTE_UNIT_OR_PACK_MISMATCH`，退出节日深筛队列，先修复配置。
- 不得用标题PCS、父体销量、商品卡最低价或另一变体尺寸推断目标Offer。
- 对高度定制的贺卡、剪贴纸、制卡套件或图案纸艺，不在选品阶段查找1688现货。根据印刷/模切/装配工艺、定制复杂度、目标pack、开发时限和采购空间判断可实现性；可能实现即可进入人工询价，明显需要新模具、高MOQ或超出时限则淘汰。

### H3：询价前经济性

- 使用当前站点费率、税费口径、15%佣金、头程及有来源的包装/采购区间，反推达到30%贡献利润率和最低贡献利润所允许的最高整包采购价。
- 采购成本取0仍不能通过时立即淘汰；最高采购价明显低于同规格供应区间时标记`PREQUOTE_ECONOMICS_WEAK`，不得进入采购表。
- 目标pack需求成立、非采购成本有依据、采购空间为正、经产品形态推理可能实现且包装后实重预计不超过2kg时，可以进入H4深验；采购价、货源、MOQ和交期由实际人工询价验证。

### H4：深度研究与交接

- 对H0–H3通过者执行完整市场进入、自然流量、低评论新品、评论缺陷、低成本改进和询价请求交接；选品阶段不做精确供应核验，精确SKU和实际报价在人工询价后验证。
- 采购回填为“找不到链接”“仅定制”“链接下架”且无合格替代入口时，该行退出当前`quote_ready`完成数并补充新候选；保留原候选ID和失败原因，不能把文字写进采购价或用其占用实际询价名额。
- 每批分别报告`discovered_count`、`h0_type_pass_count`、`h1_timing_pass_count`、`h2_offer_pack_locked_count`、`h3_prequote_pass_count`、`deep_validated_count`、`quote_ready_count`及各阶段淘汰/改类/观察/待补原因。总通过率与“真实节日品通过率”分开报告。
- 用户要求N个节日候选时，N默认指完成H4且可交采购实际询价的`quote_ready`目标Offer；未另行指定时N=50。若实得不足N，批次保持未完成并继续扩池；确有客观耗尽时报告缺口，不降低门槛、不用改类品凑数。

## 工作流

1. 固定分析日和节日日期，用当地语言扩展用途词、礼赠词、装饰词和时间词。
2. 先执行H0–H3节日品前置漏斗，再按公共分阶段漏斗完成实体、历史记忆、去重、品牌/IP及已知硬失败快筛。包装、非采购成本区间与市场同步补证，采购空间按产品形态推理；不匹配货源。通用款缺节日属性时按真实曲线转路，不为节日名额强贴标签。
3. 将日/周级类目、关键词和多ASIN曲线按距节日天数对齐，建立节前、峰值、节后和淡季基线。
4. 验证至少两个完整节日周期的“节前上升—节后下降—下一周期重复”，并从超额需求曲线识别实际购物窗口。
5. 将购物窗口划分为短、中、长窗口；节日名称只作初始路由提示，分类冲突时以历史曲线为准。
6. 区分真实节日购买意图、年度非节日事件和标题中只出现节日名称的通用产品；毕业季等不得自动算节日品。
7. 按共享市场模块建立同一节日阶段、同一相对日期的新品和低评论队列；不能拿节日峰值与淡季队列混比。
8. 分开管理两条时间轴：长窗口在距购物窗口开始120–90天进入正式选品；所有节日品另以历史需求确认的旺季开始日为锚点，目标在旺季开始前60–30天完成开发，并继续计算采购、到仓、补货和退场节点。
9. 类型、窗口、时机、市场和目标配置支持继续开发后，输出人工询价表；第一轮采购只填六个黄色数值完成初算，初算有利润空间后再补SKU、定制/MOQ/交期、规格和报价证据，由AI完成实际利润及退场情景核验。
10. 只有实际利润及全部launch必需作用域通过才生成与购物窗口、止补日和退出计划一致的运营销售策略；分别输出类型、窗口、时机、市场和开发结论，一次性网络梗转热点审查或淘汰。

## 强制行为

- 标题含Christmas、Halloween等词不是节日证据。
- 一个节日周期不能自动证明可复现。
- 圣诞通常是长购物窗口，情人节和母亲节通常是短购物窗口，但这些只能作为先验提示，不能覆盖Sorftime历史证据。
- 月度数据不能可靠区分短窗口；缺少日/周级证据时，窗口分类不得自动通过。
- “提前3–4个月”不是统一硬规则；使用实际购物窗口开始日、开发链路、到售链路和14天缓冲。
- 对已由数据确认的长窗口节日品，正式选品启动带固定为购物窗口开始前120–90天；早于120天只观察，晚于90天才首次发现的新候选进入压缩验证。
- 120–90天是候选发现和市场验证时间，不是采购授权，也不能替代实际开发与到售链路。
- 节日品开发完成目标带固定为实际旺季开始前60–30天。完成开发是指目标Offer、样品/规格、包装、合规、实际询价和最终包装数据均已确认；只完成候选发现或市场研究不得计为完成开发。
- 早于旺季前60天完成可以保留，但进入目标带后必须重验需求、费用、报价、供应和合规；晚于旺季前30天仍未完成的新产品，正常路径时机不通过，另按空运小批模块核验剩余需求与经济性。不得仅用“距节日仍有时间”放行，也不得把空运例外改写为按期完成。
- 距节日很远不等于应立即开发；处于过早观察期时只保留候选并设置下次复核日，不自动进入采购池。
- 类型真实但正常节点错过时先审空运小批路径；全部可行路径均错过有效需求时本周期不通过，保留下一年候选；缺日周证据仍待补。
- Sorftime不能替代版权、商标、专利、宗教或文化审查。
- 定制纸艺不是自动淘汰项。询价前须有成熟工艺、定制复杂度、开发时限与采购空间可能实现的依据，不要求已有精确供应SKU或供应商确认MOQ/交期；这些在人工询价后、实际利润和开发完成判定前核验。明确需要新模具、高MOQ或超出时限的仍淘汰；市场、时机和经济性未通过时不得因节日相关性强而放宽。
- 不执行采购。

## 输出

使用公共输出合同，并额外输出：`event_name`、`event_scope`、`target_event_date`、`repeat_cycles`、`shopping_window_class`、`window_class_source`、`window_start_offset_days`、`window_end_offset_days`、`shopping_window_days`、`shopping_window_start_date`、`shopping_window_end_date`、`selection_open_date`、`selection_start_deadline_date`、`selection_started_date`、`selection_timing_stage`、`peak_start_date`、`peak_start_source`、`development_completion_window_open_date`、`development_completion_deadline_date`、`development_completed_date`、`development_completion_timing_status`、`holiday_window_share`、`window_to_baseline_ratio`、`peak_date_shift_days`、`raw_chain_days`、`research_sample_days`、`safety_buffer_days`、`required_launch_lead_days`、`required_development_lead_days`、`days_to_window_start`、`development_slack_days`、`lead_shortfall_days`、`timing_stage`、`next_timing_review_date`、`latest_development_start_date`、`latest_purchase_date`、`stop_replenishment_date`、`inventory_exit_plan_status`、`holiday_intent_evidence`、`customization_status`。

## 阶段与证据边界（v0.6）

输出 `research_stage`、`screen_decision`、`review_type`、`memory_match_ids` 与补证动作。候选优先复用“问题型长尾意图→可感知且可执行改进→有依据的pack/组合→低评新品自然入口”结构，但卖家案例仅用于发现并披露幸存者、变体与促销污染。确定直接竞品后立即按共享流程快抓评论、分析重复差评并发散低成本改进；采用改进时必须落到实际报价和验收方法。研究通过或区间粗算通过都不等于 `launch_decision=通过`；目标配置不足时按共享市场的组合证据路线进行人工研究。人工实际询价及最终包装三边/实重未核验时，`profit_validation_status=待人工询价`，不得生成可执行运营策略。只有AI完成实际利润复算并通过全部门槛，才进入开发排序并输出与节日购物窗口一致的运营策略。主类型改路沿用候选ID和有效证据。
