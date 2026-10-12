# 节日品类型、购物窗口与时机规则

公共阈值版本：`selection-gates-v0.10.0`。方向规则版本：`holiday-window-v0.7.0`。历史产品回测前均为初始阈值；事件纯度和时间预检前移，不改变日/周证据、类型、购物窗口、市场和利润门槛。

## 0. 前置漏斗执行顺序

节日批量发现固定按`H0类型纯度 → H1时间可开发性 → H2目标Offer/pack锁定 → H3询价前经济性 → H4深度研究`执行。不得先做完整竞品、评论或供应深验后才发现产品不是节日品、当前不在开发窗口、目标pack不一致或经济性先天不成立。

- H0不是节日品：保留证据并改路，不计入节日深度候选分母。
- H1过早：进入观察池并设置`next_timing_review_date`，不进入H2。H1正常节点过晚：先审共享空运小批路径；本阶段通过才可继续H2，全部可行路径过晚时本周期停止，缺证保持待补。
- H2无法锁定一个精确Amazon可售单位：先补配置，不进入H3。
- H3只有在保守粗算下存在现实采购空间才通过；公共最低售价不能代替该判断。
- H4才消耗评论深抓和完整M/E/L/T市场验证；通过后交人工询价。选品阶段不核对1688精确SKU。

批次质量至少同时报告：`H0通过率`、`H1通过率（以H0通过者为分母）`、`H2锁定率`、`H3经济性通过率`和`H4深验结果`。不得只用最终通过数/全部发现数评价节日Skill。

## 1. 类型通过条件

- 至少两个完整节日周期；按月分析通常需要>=24个月。
- 产品用途、关键词和多ASIN/类目曲线都指向同一节日。
- 节日窗口需求至少为淡季基线2倍。
- 至少60%的年度需求集中在由数据识别的节日购物窗口。
- 两周期峰值日期偏移<=28天；浮动节日按距节日天数对齐。
- 节前抬升、节后回落，并由多个ASIN支持。

一个周期或12–23个月且多源一致：人工复核。只有节日名称且趋势/意图数据缺失：`待补`；已经取得完整趋势且证明全年平稳、节日集中度和倍率均不成立：优先执行第5节的`建议日常品`，不得退回模糊的待补状态。

## 2. 事件范围与购物窗口分类

先输出`event_scope`：

- `fixed_holiday`：日期固定的节日，如圣诞节、情人节。
- `floating_holiday`：日期逐年变化的节日，如复活节、英国Mothering Sunday；必须按当地目标年日期对齐。
- `annual_nonholiday_event`：毕业季、开学等年度事件。此标签本身不能通过节日品类型；若主要由4–9个月的校历或季节窗口驱动，转季节品复核，`RECLASS_SEASONAL`。

购物窗口必须由产品级证据识别，不能直接由节日名称指定：

1. 将至少两个周期的日/周级销量、搜索量和多ASIN曲线按事件日`D=0`对齐。
2. 估计淡季基线，剔除无法解释的促销、断货和异常价格日；对圣诞窗口特别检查Black Friday等促销重叠。
3. 对高于基线的正向超额需求计算累计占比；`P10`所在日为`window_start_offset_days`，`P90`所在日为`window_end_offset_days`。
4. `shopping_window_days = window_end_offset_days - window_start_offset_days + 1`。两周期窗口类别一致才可自动分类；不一致则人工复核。

初始分类阈值：

- `短窗口`：`shopping_window_days<=42`。
- `中窗口`：`43–70`天。
- `长窗口`：`>=71`天。

圣诞通常作为长窗口先验，情人节、母亲节、父亲节通常作为短窗口先验；先验与曲线不一致时使用曲线结果，并输出`EVENT_WINDOW_PRIOR_MISMATCH`。仅有月度数据时不得自动判定短窗口，输出`EVENT_WINDOW_GRANULARITY_INSUFFICIENT`。

月度双周期可以支持事件纯度初筛、候选排序和下次复核日，但不能授予长窗口、短窗口或询价资格。所有窗口类别和精确时机仍须本节规定的两周期日/周证据；本方向不使用公共`CONTROLLED_TEST_QUOTE`替代该证据。

## 3. 以购物窗口开始日计算开发时机

长窗口节日品先单独计算选品启动带：

```text
selection_open_date = shopping_window_start_date - 120天
selection_start_deadline_date = shopping_window_start_date - 90天
```

- `days_to_window_start>120`：`selection_timing_stage=长窗口观察期`。只建立种子和监控，不启动批量候选深验，`LONG_WINDOW_SELECTION_NOT_OPEN`。
- `days_to_window_start=90–120`：`selection_timing_stage=长窗口选品启动期`。开始候选发现、市场验证、竞品分析、包装经济性与采购空间预估；选品阶段不做货源初配，`LONG_WINDOW_SELECTION_ACTIVE`。
- `days_to_window_start<90`且`selection_started_date`缺失：`selection_timing_stage=长窗口压缩验证期`，人工复核，`LONG_WINDOW_SELECTION_LATE_REVIEW`；只有完整证据已补齐且开发/到售链路仍通过时才可继续。
- 上述规则只适用于`shopping_window_class=长窗口`。短、中窗口继续按实际购物曲线和完整链路判断，不套用120–90天。

选品启动带与开发链路是两个独立时间轴：可以在120–90天开始选品，但尚处于开发观察期；不得因进入选品启动带而推定可以采购。

所有短、中、长窗口节日品还须单独建立“开发完成目标带”。`peak_start_date`必须来自至少两个周期的日/周级关键词、类目和多ASIN需求曲线；不能直接使用节日日期，也不能用标题中的节日名称推定：

```text
development_completion_window_open_date = peak_start_date - 60天
development_completion_deadline_date = peak_start_date - 30天
```

“完成开发”必须同时具备：目标Offer/pack已锁定，样品或最终规格已确认，包装与合规/IP方案已确认，人工实际询价已取得，最终销售包装三边和包装后实重已取得，表格实际利润公式所需站点费率已齐全。仅完成候选发现、市场验证、采购空间推理或区间利润粗算不算完成开发。

- 在`development_completion_window_open_date`之前完成：允许保留，但进入60–30天目标带后必须重验需求、售价、FBA/佣金/税费、报价、供应、合规和最终包装，状态为`DEVELOPED_EARLY_REVALIDATION_REQUIRED`。
- 在旺季前60–30天完成：`development_completion_timing_status=按期完成`。
- 距旺季开始不足30天仍未完成：新产品正常路径时机不通过，`DEVELOPMENT_COMPLETION_TOO_LATE`；另按第3.1节审空运小批路径，不得只因距节日日期仍有30天以上而放行。
- `peak_start_date`或开发完成日缺失：时机待补，`PEAK_START_OR_COMPLETION_DATE_MISSING`。

该目标带约束“何时完成开发”，不替代长窗口120–90天选品启动带，也不替代采购、到仓和14天安全缓冲。若完整到售链路要求更早完成，以更早日期为准。

```text
raw_chain_days = 采购 + 定制/包装/打标 + 国内运输 + 头程 + 清关 + FBA接收
research_sample_days = 供应商筛选 + 打样 + 包装/图稿 + 合规复核
safety_buffer_days = 14
required_launch_lead_days = raw_chain_days + safety_buffer_days
required_development_lead_days = research_sample_days + required_launch_lead_days
days_to_window_start = shopping_window_start_date - analysis_date
development_slack_days = days_to_window_start - required_development_lead_days
lead_shortfall_days = required_launch_lead_days - days_to_window_start
latest_development_start_date = shopping_window_start_date - required_development_lead_days
latest_purchase_date = shopping_window_start_date - required_launch_lead_days
earliest_active_development_date = latest_development_start_date - early_review_buffer_days
```

- `early_review_buffer_days`初始为30天，须通过历史回测调整；它用于避免过早投入，不是统一采购提前期。
- `development_slack_days>30`：`过早观察期`，保留候选、设置`next_timing_review_date=earliest_active_development_date`，不进入采购池，`TOO_EARLY_FOR_ACTIVE_DEVELOPMENT`。
- `development_slack_days=0–30`且`lead_shortfall_days<=0`：`预研/正式开发窗口`，时机可通过；这不构成采购授权。
- `development_slack_days=-1至-14`且`lead_shortfall_days<=0`：开发周期压缩，人工复核，`DEVELOPMENT_LEAD_SHORTFALL_REVIEW`。
- `development_slack_days<=-15`但到售链路仍来得及：正常路径只有不再需要打样、合规或定制变更的已验证现货SKU可人工复核；新产品正常路径不通过，`DEVELOPMENT_WINDOW_MISSED`。新产品另审第3.1节空运路径，不得将剩余打样/合规/定制开发周期归零。
- 少1–14天：人工复核、小批量并明确风险，`LEAD_TIME_SHORTFALL_REVIEW`。
- 少15天以上：正常路径不通过，`MISSED_HOLIDAY_WINDOW`，另审空运路径。连空运预计可售日也晚于需求截止或剩余需求不足时本周期不通过，保留下一年。

链路、购物窗口开始日、旺季开始日或开发完成日缺失时最终时机待补。候选发现与到售链路以购物窗口开始日为准；开发完成目标带以旺季开始日为准；两者都不能用节日日期替代。

### 3.1 空运小批验证

完整读取`../../_amazon-selection-shared/air-small-batch-window.md`。此路径允许正常开发完成目标带过晚、赶不上购物窗口开始但仍有真实剩余需求的机会；它替代相应的常规时机否决，不补写按期完成记录。询价前按保守预计开发完成/可售日和本阶段完整证据判断，实际开发完成日及人工实价/包装属于开发终审；开发尚未完成本身不能阻塞有证据支持的询价计划。日/周购物窗口、旺季开始和需求截止等必需证据仍不可省略，缺少时待补。

本路径成立后可在H1转入H2/H3，H3必须用空运费用反推采购空间；H4和公共/市场规则不变。最终开发完成后按实际进度及剩余需求重验，只有全部launch作用域通过才可输出运营策略。第一年小批验证与次年复用规划分别记录，不能用次年收益抵首年利润。新增路线字段统一放`证据与包装`。

库存策略必须匹配窗口长度：

- 短窗口默认首批小批量验证，不默认安排晚期补货；只有完整补货链路能在`stop_replenishment_date`前到售时才可补货。
- 长窗口可分批入仓和滚动补货，但每次补货仍须满足完整利润、剩余窗口和退出条件。
- 任何窗口都不得仅凭类别预设数量。退出方案至少包含首批量、补货触发点、停止补货日、需求截止日、清仓或跨年留存条件；缺失不得进入开发池。

## 4. 市场阶段一致性

- 新品、低评论群体和头部基准必须处于相同购物窗口类别、相同节日前/峰值阶段和相近距节日天数。
- 当前淡季不能直接否定节日峰值；历史峰值也不能代替当前可进入性。
- 低评论高销量须有自然位，并排除品牌/IP、促销和合并评论。
- 阶段错配：`EVENT_PHASE_MISMATCH`，市场待补。

## 5. 意图、定制和IP

- 标题含节日词但用途通用、全年平稳：建议日常品，`NAME_ONLY_HOLIDAY`。
- 搜索上涨而销量/转化不涨，流量指向品牌/IP角色：不通过，`IP_OR_BRAND_TRAFFIC`。
- 单年网络梗：尚在热度期转热点复核，否则不通过。
- 包装、UV或激光只有在需求成立、MOQ/成本/交期不破坏利润及时机且图案安全时才授予`可定制`标签。
- 高度定制贺卡、剪贴纸、制卡套件和图案纸艺在询价前按成熟工艺、目标规格/pack、定制复杂度、采购空间及开发时限判断可能实现；符合全部询价最低条件即可形成quote_ready，不要求提前取得精确供应SKU或供应商确认MOQ/交期。只有相似图或“可定制”文案不能证明可能实现。人工询价后若无匹配SKU、MOQ/交期不满足或报价超上限，再标记`HOLIDAY_READY_STOCK_NOT_CONFIRMED`及相应采购失败/待补，撤回当前有效询价完成数并补候选；不得冒充实际利润或开发完成。
- 现货入口失败后可以保留市场和节日类型证据，但必须补充替代SKU或替换候选；不能把“定制款/找不到链接”写入数值采购价列，也不能据此生成实际利润。
- 角色、Logo、口号、版权图案、宗教或文化声明：待法务/文化核验。

## 6. Sorftime证据

使用类目趋势/历史报告、关键词趋势/历史词、商品趋势/历史搜索建立日/周级节前、峰值、节后和淡季证据；按距节日天数对齐浮动节日；用自然结果和流量词判断进入；用评论验证用途。选品阶段不核对1688；SKU、定制成本、MOQ与供货在人工询价阶段验证。若Sorftime只能提供月度粒度，可完成节日类型初筛，但短窗口分类和精确开发节点保持待补。

## 7. 原因码

`PASS_HOLIDAY`、`INSUFFICIENT_CYCLES`、`NAME_ONLY_HOLIDAY`、`NO_EVENT_INTENT`、`NO_CROSS_YEAR_REPEAT`、`HOLIDAY_CONCENTRATION_LOW`、`EVENT_WINDOW_GRANULARITY_INSUFFICIENT`、`EVENT_WINDOW_PRIOR_MISMATCH`、`PROMO_EVENT_OVERLAP`、`SHOPPING_WINDOW_CLASS_MISMATCH`、`EVENT_PHASE_MISMATCH`、`LONG_WINDOW_SELECTION_NOT_OPEN`、`LONG_WINDOW_SELECTION_ACTIVE`、`LONG_WINDOW_SELECTION_LATE_REVIEW`、`TOO_EARLY_FOR_ACTIVE_DEVELOPMENT`、`DEVELOPMENT_LEAD_SHORTFALL_REVIEW`、`DEVELOPMENT_WINDOW_MISSED`、`LEAD_TIME_SHORTFALL_REVIEW`、`MISSED_HOLIDAY_WINDOW`、`NO_EXIT_PLAN`、`IP_OR_BRAND_TRAFFIC`、`CULTURAL_REVIEW_REQUIRED`、`ONE_OFF_VIRAL_EVENT`、`CUSTOMIZATION_MOQ_OR_LEAD_FAIL`、`HOLIDAY_READY_STOCK_NOT_CONFIRMED`、`RECLASS_EVERGREEN`、`RECLASS_SEASONAL`、`RECLASS_HOT_ACCESSORY`。

新增：`HOLIDAY_DESIGN_STALE`、`HOLIDAY_LOW_PRICE_TRAP`。

## 8. 回归用例

1. 圣诞用品两周期P10–P90窗口均为80天以上：判长窗口；距实际购物窗口开始125天时只观察，进入120–90天后开始正式选品。
2. 情人节专用品两周期均在节前6周内集中成交：判短窗口；即使距情人节仍远，也按窗口开始日和完整开发链路判断当前是观察期还是开发期。
3. 英国母亲节按每年Mothering Sunday日期对齐后，两周期均为30天窗口：判短窗口；不得按固定月份直接对齐。
4. 当前为8月31日，次年情人节窗口尚未进入`earliest_active_development_date`：保留候选并设置下次复核日，不自动进入开发或采购池。
5. 毕业用品只呈现4–6个月校历季节窗口且无明确单一事件日：`RECLASS_SEASONAL`，不得归为节日品或日常品。
6. 仅有月度趋势、疑似20天购物窗口：窗口分类待补，`EVENT_WINDOW_GRANULARITY_INSUFFICIENT`。
7. 标题含Christmas但用途通用、全年平稳：建议日常品。
8. 节日真实但距购物窗口开始仅7天、到售链路需10天：本周期时机不通过。
9. 只有节日标签无趋势：待补。
10. 节日词暴涨但销量不涨且流量集中品牌角色：不通过。
11. 新品队列来自淡季、头部来自峰值：市场待补。
12. 长窗口节日品距购物窗口开始85天才首次发现：标记压缩验证；若完整选品已在此前完成，则不因当前少于90天重复否决，但仍须通过开发和到售链路。
13. 50个发现项中只有5个具备真实节日意图：H0分母为50、通过5；其余45改路，不能继续占用节日深筛名额，也不能将2个最终通过解释为真实节日品仅4%通过。
14. 目标Amazon Offer为24件装、供应报价无法确认是单件还是24件整包：H2不通过，`QUOTE_UNIT_OR_PACK_MISMATCH`；不得在H3中自动乘24。
15. 某真节日品市场售价较高，但扣除当前FBA、佣金、税费和头程后，允许采购上限低于同规格供应区间：H3不通过，`PREQUOTE_ECONOMICS_WEAK`，不交采购询价。
16. 高度定制圣诞贺卡的采购空间为正，按成熟印刷/模切工艺推理可能实现：可进入人工询价，不因选品阶段没有1688链接退出；人工询价若确认MOQ、交期或真实报价不满足，再标记采购失败并替换。
17. 距旺季开始不足30天、正常开发节点过晚，但两周期日周证据及保守空运可售日后的剩余需求、首批和采购空间支持：可按空运路径研究/询价，保留常规过晚结论，未获实际报价前launch仍待补。
18. 月度趋势显示节日高峰、空运暂定10天，但没有必需日周需求或空运费率：待补，不能因赶得上节日就计quote_ready。
19. 海运利润35%、空运利润29%，并期待次年恢复利润：空运路径不通过，不以首年学习价值或次年收益豁免30%利润底线。
