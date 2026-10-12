# 季节品类型与时机规则

公共阈值版本：`selection-gates-v0.10.0`。方向规则版本：`seasonal-window-v0.5.0`。历史产品回测前均为初始阈值；空运小批和受控试询均不改变最终launch门槛。

## 1. 类型通过条件

- 至少24个月或两个完整需求周期。
- 每个周期有4–9个有效需求月。
- Top3月份需求占全年`>=45%`。
- 两周期有效月份窗口重叠`>=60%`。
- 峰值月份偏移不超过1个月；气候漂移须人工解释。
- 类目、核心词和至少3个代表ASIN的曲线方向一致。

Top3月份占比必须在每个完整周期内分别计算，两个周期都须达标，不得把24个月合并后掩盖其中一个弱周期：

```text
top3_share_cycle_i = 该周期销量最高3个月之和 / 该周期总销量
window_overlap = 两周期有效月份集合的交集月数 / 并集月数
```

固定季节用同一日历月份集合；气候型季节先按当地气候阶段归一化，再计算交并比。销量缺月、断货或促销污染未修正时，不计算有利占比，转人工复核。

12–23个月且其他条件成立只能人工复核；不足12个月为待补。有效月只描述市场需求，自身月销`>=30`由共享市场模块在同一季节阶段验证。

### 1.1 证据分层

- `STRICT_SEASONAL`：完全满足第1节，允许继续严格询价。
- `CONTROLLED_SEASONAL_REVIEW`：精确关键词只有12–23个月，但类目或精确产品市场具有两个完整周期、至少3个独立代表ASIN跨周期一致，且窗口、峰值和当前阶段一致；`type_decision=人工复核`。其余询价作用域全部严格通过时，可作为唯一缺口进入受控试询。
- `SEASONAL_WATCHLIST`：不足上述替代证据、窗口尚未开放、只有宽泛类目曲线或单周期证据；不得进入采购主表。

受控季节复核不改变launch门槛。后续取得完整关键词两周期后重判；不能把类目趋势拼接成精确关键词历史。

## 2. 时机

季节品以数据确认的`peak_start`作为需求窗口开始日，并计算正式选品启动带：

```text
selection_open_date = peak_start - 120天
selection_start_deadline_date = peak_start - 90天
```

- `days_to_window_start>120`：`selection_timing_stage=季节观察期`。只保留种子和监控，不启动批量候选深验，`LONG_WINDOW_SELECTION_NOT_OPEN`。
- `days_to_window_start=90–120`：`selection_timing_stage=季节选品启动期`。开始候选发现、市场验证、竞品分析、包装经济性与采购空间预估；选品阶段不做货源初配，`LONG_WINDOW_SELECTION_ACTIVE`。
- `days_to_window_start<90`且`selection_started_date`缺失：`selection_timing_stage=季节压缩验证期`，人工复核，`LONG_WINDOW_SELECTION_LATE_REVIEW`；只有证据已补齐且到售链路仍通过时才可继续。
- 已在120–90天完成选品的候选，不因后续自然进入90天以内而重复判定为选品迟到；此后只按开发、采购和到售链路继续判断。

`peak_start`必须落到目标站当地日期。只有月度数据时，以最早有效需求月的第一天作为保守计划锚点并输出`SEASON_START_DATE_GRANULARITY_LIMITED`；该日期可用于提前提醒，但不得宣称已识别精确需求启动日。

120–90天管理“何时开始选品”，下列链路公式管理“是否来得及到售”，二者不得互相替代。

```text
raw_chain_days = 采购 + 包装/打标 + 国内运输 + 头程 + 清关 + FBA接收
safety_buffer_days = 14
required_launch_lead_days = raw_chain_days + safety_buffer_days
lead_shortfall_days = required_launch_lead_days - days_to_window_start
```

- `lead_shortfall_days<=0`：时机通过。
- 少1–14天：人工复核，`LEAD_TIME_SHORTFALL_REVIEW`，缩小首批并说明风险。
- 少15天以上：正常路径时机不通过，`MISSED_SEASON_WINDOW`；另完整读取`../../_amazon-selection-shared/air-small-batch-window.md`，若空运后剩余真实需求足以支持小批验证且该模块全部条件成立，可按空运路径继续。两条路线分别记录，空运也不成立时保留下一周期。

链路关键项缺失时最终时机待补。距窗口>=45天继续、30–44天复核、<30天暂缓仅用于已经完成选品后的到售快筛，不能作为新季节品的选品启动规则，也不能替代最终测算。

必须有首批量、补货触发点、需求截止日、清仓或次年留存条件；无退出方案时launch待补。

### 2.1 空运小批验证

对于晚于90天才发现或预计无法赶在需求窗口开始前到售的候选，按共享空运模块单独验证；本路径明确替代常规迟到/窗口开始前到售的时机否决，不适用于过早观察期。即使需求窗口已开始，只要保守预计可售日后仍有证据支持的真实需求、首单验证和首批合理售罄空间，可以继续本周期研究/询价；实际利润和开发终审仍等人工实价及包装确认。不得仅用整季高销量或第二年计划放行。完整新增路线字段依共享模块保存到`证据与包装`。

## 3. 市场阶段一致性

- 新进入者、低评论群体与市场头部必须使用相同季节阶段的最近3个有效月。
- 当前淡季只有旺季头部数据，或反之：`SEASON_PHASE_MISMATCH`，市场待补。
- 不能用旺季峰值外推全年，也不能用淡季当前销量否定真实旺季。

## 4. 改类与伪季节

- 有效月>=10：建议日常品，`RECLASS_EVERGREEN`。
- 有效月<=3且节日用途/日期主导：建议节日品，`RECLASS_HOLIDAY`。
- 单年事件或达人流量：尚在有效期时转热点复核，否则`ONE_OFF_SEASON`不通过。
- 其余月份断货/未上架：人工复核，`STOCKOUT_DISTORTION`。
- 窗口只与秒杀、降价或广告重投重合：不通过或人工复核，`PROMO_DISTORTION`。

## 5. Sorftime证据

使用类目趋势/历史报告、关键词趋势、商品趋势和历史搜索比较同阶段；用自然结果、流量词和竞品词验证进入；用变体工具排查污染。选品阶段不核对1688，成本判断采用30%利润后的采购空间及可实现性推理。

## 6. 原因码

`PASS_SEASONAL`、`INSUFFICIENT_24M_HISTORY`、`ACTIVE_MONTHS_OUTSIDE_4_9`、`NO_YOY_REPEAT`、`WEAK_SEASON_CURVE`、`ONE_OFF_SEASON`、`SEASON_PHASE_MISMATCH`、`SEASON_START_DATE_GRANULARITY_LIMITED`、`LONG_WINDOW_SELECTION_NOT_OPEN`、`LONG_WINDOW_SELECTION_ACTIVE`、`LONG_WINDOW_SELECTION_LATE_REVIEW`、`LEAD_TIME_SHORTFALL_REVIEW`、`MISSED_SEASON_WINDOW`、`NO_EXIT_PLAN`、`PROMO_DISTORTION`、`STOCKOUT_DISTORTION`、`VARIATION_CONTAMINATION`、`RECLASS_EVERGREEN`、`RECLASS_HOLIDAY`、`RECLASS_HOT_ACCESSORY`。

## 7. 回归用例

1. 连续两年4–9月各6个有效月，多词与多ASIN同步：类型通过。
2. 单年连续4个月暴涨、上一年同期无峰：不通过季节。
3. 恰好4个有效月且两周期复现：类型通过；3个月不通过季节。
4. 原始链路24天+14天缓冲，距窗口25天：时机人工复核。
5. 原始链路38天+14天缓冲，距窗口25天：本周期时机不通过。
6. 新品队列来自淡季、头部来自旺季：市场待补。
7. 需求窗口6月1日开始：2月1日进入正式选品启动带，最迟应在3月3日前启动选品；具体日期按实际年份日历计算，不固定写死月份。
8. 距窗口85天才首次发现的新季节品：压缩验证、人工复核；若候选已在120–90天完成选品，则继续按到售链路判断，不重复标记迟到。
9. 本季已经开始但预计空运可售日后仍有同阶段证据支持的小批需求，空运采购空间及其余询价作用域通过：可按空运路径进入询价，不因错过窗口开始自动淘汰；实际利润仍待人工询价。
10. 空运可到仓但剩余需求不足以验证首单及合理消化首批，或MOQ大于有依据的可销售首批量：空运路径不通过，本周期不能因“为明年准备”放行。
