# 热点母体衍生配件类型与时机规则

Skill逻辑版本：`hot-accessory-v1.0.0`。共享硬门槛版本：`selection-gates-v0.10.0`。热点阈值必须频繁回测。

## 0. 组合适配门

在母体动量和市场深验前先判断是否符合当前经营组合：

- `PORTFOLIO_FAST_COMMODITIZATION_EXCLUDED`：手机、平板、智能手表、相机/运动相机、云台、无人机等消费电子新品发布后，普通壳、膜、支架、收纳、转接、线材、充电周边等会被成熟通用供应链迅速复制并价格内卷。未经用户明确重开，不进入研究深筛或正式询价表；此前iPhone 18、DJI Pocket 4候选不得换型号复用。
- `NICHE_OPEN_AFTERMARKET_PREFERRED`：优先中小安装量但有可验证替换、清洁、维护或耗用需求的开放售后生态，例如净化器过滤棉/滤网、加湿器滤芯、扫地机刷件/滤件。优先不代表降低门槛，仍须满足母体动量、精确配件需求、目标Offer预计月销、自然入口、供给缺口、兼容/IP、包装和利润规则。
- 替换需求稳定但没有近期母体增长或装机扩张时，标记`RECLASS_EVERGREEN`或转消耗品/包装规格路线；不得为保留热点标签虚构趋势。

必须输出`portfolio_fit_status`、`portfolio_exclusion_reason`、`installed_base_replacement_status`和`replacement_cycle_basis`。

## 1. 母体定义与下钻

母体可以是非品牌品类、品牌家族、产品线、具体型号、父ASIN或子ASIN，但必须选择能够解释新增配件需求的最具体层级。宽泛品牌总词只能用于发现和背景，不能代替型号、ASIN或产品线的增长证据。

必须记录`mother_scope`、核心关键词/ASIN、产品功能、上市或增长阶段及装机量代理。品牌总盘平稳而具体新型号增长时，不得因品牌总词未翻倍而提前淘汰。

## 2. 三条发现路径

### 2.1 `BREAKOUT_MOMENTUM`

- 母体核心词最近28天相对此前84天周均基线`>=2.0倍`。
- 母体商品或可比集销量相对基线`>=1.5倍`。
- 热度持续`>=14天`，最近7天相对前7天下降不超过25%。
- 排除促销、广告、降价、断货恢复和一次性事件。

### 2.2 `INSTALLED_BASE_EXPANSION`

用于成熟品牌/品类中的新型号、产品线扩张或新增装机盘。必须同时满足：

- 具体型号/产品线搜索相对基线`>=1.5倍`，或因新上市缺少完整基线而有连续不少于14天的上升证据；
- 具体母体ASIN或可比硬件集销量相对基线`>=1.3倍`；
- 至少两类相互独立的当前信号支持扩张，例如型号词搜索、多个母体父ASIN销量、自然排名、流量词扩散或类目份额；
- 可用母体新增销量、可比前代销量或其他Sorftime证据形成`installed_base_proxy`，并披露估算方法；
- 增长不是单周、纯促销、广告堆量、降价或断货恢复。

该路径不是降低门槛：品牌总量、型号搜索或单个爆款ASIN任一孤立信号均不足以通过。只有月粒度时不能证明14天和最近7天条件，`type_decision=人工复核`并输出`DATA_GRANULARITY_INSUFFICIENT`。

缺日/周证据的`BREAKOUT_MOMENTUM`或`INSTALLED_BASE_EXPANSION`不得进入受控试询；保持观察池，恢复条件为取得对应粒度或转入下一节的稳定售后路径并补齐真实主类型。

### 2.3 `AFTERMARKET_INSTALLED_BASE`

用于用户偏好的净化器滤棉、维护件、替换垫、刷件等量级不大但装机需求存在的开放售后机会。它是本Skill的发现路径，不是假热点。必须同时满足：

- 具体型号/产品线至少12个月稳定或增长，至少两类独立装机代理支持存量仍活跃；
- 有客观替换、磨损、污染、维护或耗用机制，并有至少两类Amazon侧证据；
- 精确型号/跨型号配件词、可比第三方Offer或用户问题证明配件本身有需求，不能只看母体销量；
- 生态属于开放第三方售后，兼容尺寸、支持/不支持型号、商标表达和IP可核验；
- 精确配件市场、自然入口、目标月销、包装和采购空间按共享规则成立。

该路径输出`selection_lane=AFTERMARKET_INSTALLED_BASE`，不输出`PASS_HOT_ACCESSORY`。按真实曲线路由日常主类型；存在180天内耗用/替换机制时可同时复核消耗标签。主类型未通过前进入观察池，补齐后可以在本Skill交付中计一个询价机会，但不得在日常/消耗方向重复计数。普通市场数据按7天时效，不强制72小时热点粒度。

## 3. 生态与依赖分类

- `GENERIC_UNIVERSAL`：无需特定品牌或型号即可使用。
- `OPEN_AFTERMARKET_CROSS_MODEL`：第三方可开发，覆盖同一生态多个型号。
- `OPEN_AFTERMARKET_MODEL_SPECIFIC`：依赖具体型号的物理尺寸或使用场景，但不要求授权、Logo、专有协议或固件认证。
- `CLOSED_OR_PROTECTED`：需要品牌授权、Logo、复制受保护外观、专有连接/通信协议、芯片认证、固件握手，或无法合法表达兼容性。

前3类均可继续；型号专用不自动失败。第4类不通过或转法务复核。分别输出：

- `traffic_dependency`：是否依赖品牌/型号兼容词获得自然流量；
- `physical_fit_dependency`：是否依赖专用尺寸、公差或结构；
- `protocol_dependency`：是否依赖专有电子协议、认证或固件；
- `trademark_usage_status`：无需商标、兼容表达待核验、表达可行、需要授权或不通过。

`BRAND_DEPENDENT`不得再作为笼统硬失败码。只有无法获得第三方兼容流量、必须冒充品牌方或必须使用受限制权利时，才以更具体原因失败。

## 4. 配件需求证据的两条路径

### 4.1 `CONFIRMED_ACCESSORY_GROWTH`

- 配件相关词和配件ASIN销量/评论至少两类独立信号同步增长；
- 配件侧增长代理`>=30%`；
- 母体与配件增长滞后可解释，且不是不同事件驱动；
- 单一汇总增幅或同一来源的重复字段只算一类证据。

### 4.2 `LEADING_SUPPLY_GAP`

用于母体扩张已经成立，而配件需求尚处早期、供给未完全跟上的窗口。必须同时满足：

- 母体通过第2节任一路径；
- 配件解决由母体使用直接产生的保护、收纳、安装、连接、使用改善、替换或耗材问题；
- 至少两类独立需求证据，其中至少一类来自Sorftime当前数据：早期精确配件词、少量配件Offer销量、母体评论中的重复附件问题、可比前代/相邻型号配件市场、自然流量词或类目扩散；
- 能说明合理购买滞后和保守的`attachment_rate_basis`；不得凭常识填写购买率；
- 精确配件市场并非完全缺失，且需求证据强于供给增长；
- 竞品少不能单独证明蓝海，零竞品且零需求证据为`ACCESSORY_MARKET_MISSING`。

领先缺口路线通过时输出`LEADING_ACCESSORY_GAP`并降低置信度。它可以进入精确市场、供应和询价前经济性验证，但在兼容、IP、利润或数据粒度未完成时不得输出launch通过。

## 5. 兼容与关键部件

- 列明功能、接口、尺寸公差、支持与不支持型号。
- 覆盖多个型号是加分项，不是硬性通过条件；单型号配件可在`OPEN_AFTERMARKET_MODEL_SPECIFIC`路线成立。
- 单一母体贡献预计配件需求`>60%`时自动降为人工复核，并验证母体寿命和退市风险。
- 电池、充电器、电源、承重、飞行/行驶控制、医疗或其他安全关键部件必须提高合规和责任风险等级；不能因生态开放而跳过。
- 必须使用Logo、复制受保护外观、需要授权、专有协议或认证芯片：不通过或法务复核。
- 技术兼容但商标兼容表达、专利或外观权状态未核验：人工复核，不得自动判侵权，也不得自动判安全。

## 6. 配件侧市场与蓝海

- `market_definition`必须定义配件本身，允许包含品牌、产品线和型号；不得用母体类目竞争代替。
- “品牌+型号+配件词”的自然搜索可以是有效入口；必须验证第三方Offer确实能获得自然位，不能把母体品牌流量直接计入配件流量。
- 按唯一父ASIN去重，比较需求增速与有效Offer/父ASIN供给增速，输出`accessory_supply_growth_ratio`。
- 蓝海要求需求成立且供给落后，并结合新品/低评论自然销量、Top1/Top3集中度、价格带、差评改进和目标配置验证；不是“搜索结果少”。
- 只有月度数据但共享市场硬指标完整时，`market_decision=人工复核`并输出`HOT_MARKET_GRANULARITY_REVIEW`；新品队列或自然进入证据不完整时为`待补`。
- 母体销量不能填入配件预计月销。

## 7. 剩余需求窗口

```text
raw_chain_days = 采购 + 包装/打标 + 国内运输 + 头程 + 清关 + FBA接收
safety_buffer_days = 14
minimum_sales_window_days = 45
required_hot_window_days = raw_chain_days + safety_buffer_days + minimum_sales_window_days
```

通用热点按`remaining_heat_days_low`验证。对耐用品和已形成装机盘的母体，还要计算`installed_base_tail_days_low`：使用可比前代/相邻型号的配件滞后曲线、母体累计新增销量或配件历史曲线，不得凭常识给出精确寿命。

```text
remaining_demand_days_low = max(remaining_heat_days_low, installed_base_tail_days_low)
timing_decision=通过 only if remaining_demand_days_low > required_hot_window_days
```

必须披露估算方法和数据截止时间。任一关键值缺失时`timing_decision=待补`。仅月度趋势且无不超过72小时的独立当前证据时，时机不得自动通过。热度常态化或形成稳定替换需求时建议日常品。

## 8. Sorftime证据顺序

1. 用关键词列表、历史和趋势从品牌/品类下钻到产品线、型号和母体ASIN。
2. 用商品搜索、商品趋势和类目数据验证母体销量与装机扩张。
3. 用流量词、竞品词、自然结果、评论和前代/相邻型号建立配件需求证据。
4. 用唯一父ASIN和有效Offer分析配件供给增长、集中度与新品入口。
5. 只有上游通过后才反推30%利润后的采购空间，并结合兼容结构、材料、工艺和pack判断是否可能实现；选品阶段不搜索或核对1688，不得虚构已确认货源。

## 9. 原因码

稳定售后路径新增：`PASS_AFTERMARKET_INSTALLED_BASE_LANE`、`PRIMARY_TYPE_ROUTE_REQUIRED`。

`PASS_HOT_ACCESSORY`、`PORTFOLIO_FAST_COMMODITIZATION_EXCLUDED`、`NICHE_OPEN_AFTERMARKET_PREFERRED`、`BREAKOUT_MOMENTUM`、`INSTALLED_BASE_EXPANSION`、`CONFIRMED_ACCESSORY_GROWTH`、`LEADING_ACCESSORY_GAP`、`OPEN_AFTERMARKET_COMPATIBLE`、`BRAND_MODEL_TRAFFIC_VALID`、`ONE_WEEK_SPIKE`、`DATA_GRANULARITY_INSUFFICIENT`、`HOT_MARKET_GRANULARITY_REVIEW`、`PROMO_ONLY_GROWTH`、`AD_DRIVEN_SPIKE`、`NO_CAUSAL_SYNC`、`LEADING_DEMAND_EVIDENCE_MISSING`、`HALF_LIFE_TOO_SHORT`、`COMPATIBILITY_MISSING`、`TRADEMARK_USAGE_REVIEW`、`LOGO_REQUIRED`、`PROTECTED_DESIGN_RISK`、`PROPRIETARY_PROTOCOL`、`AUTHORIZATION_REQUIRED`、`CLOSED_ECOSYSTEM`、`CRITICAL_COMPONENT_REVIEW`、`SINGLE_MAIN_PRODUCT_DEPENDENCE`、`ACCESSORY_MARKET_MISSING`、`RECLASS_EVERGREEN`、`RECLASS_HOLIDAY`。

## 10. 回归用例

1. 非品牌母体连续增长，配件词和ASIN同步、市场可进入且窗口充足：按已验证增长路线通过。
2. 成熟生态总品牌词平稳，但新型号搜索、多个母体ASIN销量和自然排名持续增长；第三方物理适配配件有前代需求与当前早期意图：进入开放式售后领先缺口路线，不因品牌词依赖淘汰。
3. 新型号增长但配件无当前信号、无可比市场、无重复用户问题：`LEADING_DEMAND_EVIDENCE_MISSING`，不得以竞品少宣称蓝海。
4. 配件需要品牌Logo、认证芯片、固件握手或授权：`CLOSED_OR_PROTECTED`，不通过或法务复核。
5. 单周10倍、次周回基线且配件无证据：不通过。
6. 只有月度数据却声称连续3周：人工复核。
7. 流量涨5倍但销量不涨、广告主导、配件词平：不通过。
8. 单型号保护/收纳配件无需专有协议，兼容和商标表达可核验：允许继续，不因覆盖型号少自动失败。
9. 母体强势但配件精确市场、自然入口或预测销量缺失：市场待补。
10. 普通替换件无热点同步或领先缺口证据：沿用候选ID转日常/其他周期验证，不直接判产品永久失败。
11. iPhone、DJI等新品普通周边即使母体暴涨且市场有量：命中当前组合排除，不能进入询价表。
12. 某品牌净化器装机量温和扩张，精确型号滤棉有替换周期、第三方自然需求和供给缺口：可按安装量扩张路线验证；量级较小不自动失败，但目标Offer仍须满足公共月销与利润门槛。
