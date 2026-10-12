---
name: select-sorftime-amazon-trending-accessories
description: Discover and validate Amazon GB, DE, JP, or CA third-party accessory opportunities caused by a newly popular or rapidly rising main product, product line, model, or installed base with Sorftime. Use for 热门产品配件、品牌或型号兼容配件、开放式售后生态、爆款配件、流量暴涨配件、近期趋势配件. Cover both universal and lawful open-aftermarket accessories; reject one-week, promotion-only, logo-copying, protected-design, proprietary-protocol, authorization-only, or otherwise closed-ecosystem opportunities.
---

# 亚马逊热点母体衍生配件选品

寻找热门母体、快速增长产品线、新型号或新增装机量带来的第三方配件机会，并证明“母体增长/装机扩张→使用场景产生配件需求→到售后仍有销售窗口”。“通用”表示第三方能够合法开发和销售，不等于必须脱离品牌或型号词获客。品牌兼容、市场、利润、物流、合规和IP仍须分别验证。

Skill逻辑版本：`hot-accessory-v1.0.0`；共享硬门槛继续使用`selection-gates-v0.10.0`，不在本Skill内降低。

## 开始前

先完整读取 `../_amazon-selection-shared/six-agent-control.md`，确认本智能体职责、共用流程和权限边界。

规范一致性是硬门槛：共享合同规定的固定文件名、工作表名称与顺序、字段顺序、颜色、状态和交互路径必须逐字逐项执行；不得沿用历史工作簿命名或自行变体。交付前按当前合同检查，不一致先修复再交付。

1. 完整读取 `../_amazon-selection-shared/common-gates.md`。
2. 完整读取 `../_amazon-selection-shared/market-entry.md`。
3. 完整读取 `../_amazon-selection-shared/candidate-profit-workflow.md`。
4. 批量选品、采购回填或二次利润复核时，完整读取 `../_amazon-selection-shared/batch-review-handoff.md`。
5. 完整读取 `../_amazon-selection-shared/referral-fees.md`、`../_amazon-selection-shared/fba-fees.md`及其指向的结构化JSON费率快照。
6. 完整读取 `references/type-rules.md`。公共规则的分阶段流程适用于本Skill；批量发现先读 `../_amazon-selection-shared/selection-memory.md` 及其审核数据，使用统一候选池，不按方向凑数。
7. 确认站点、最具体的母体层级（品牌家族/产品线/型号/父ASIN/子ASIN）、已知配件线索和采购到可售各环节天数。品牌只是母体线索，不能代替具体增长对象。
8. 热点数据优先不超过72小时；只有月粒度时不得声称连续周结论。
9. 执行当前组合策略：排除手机、平板、智能手表、相机/运动相机、云台、无人机等快速内卷消费电子新品周边；优先中小安装量开放售后生态中的替换、清洁、维护和耗用部件。

## 执行调度绑定（2026-10-08）

完整执行共享six-agent-control.md第4.1a节（selection-execution-v1.2.0）：证据可得性先查、生态/IP和精确市场预检、包装经济性同步、小批深验、分层交付及有效证据复用；不降低最终launch硬门槛，严格询价、受控试询与实际利润/开发通过分别计数。先检查组合适配和生态开放性，再选择爆发动量、新型号装机扩张或稳定装机盘售后路径；最后一条必须补日常/消耗主类型，不能冒充热点通过。

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

1. 固定截止时间，先执行`references/type-rules.md`的组合适配门；被快速内卷消费电子新品周边命中的候选直接排除，不进入正式询价表。对保留候选从品牌家族下钻到真正增长的产品线、型号或ASIN；识别母体核心功能、接口、尺寸和装机量代理，禁止用宽泛品牌总流量掩盖型号级变化。
2. 按`references/type-rules.md`选择三条发现路径：快速爆发、成熟生态中的新型号/装机扩张，或稳定装机盘售后。前两条验证近期持续性并排除单周截图、促销、广告、降价和断货恢复；第三条使用长期装机代理、替换机制和精确售后需求，并路由补齐日常/消耗主类型。
3. 把生态分类为`GENERIC_UNIVERSAL`、`OPEN_AFTERMARKET_CROSS_MODEL`、`OPEN_AFTERMARKET_MODEL_SPECIFIC`或`CLOSED_OR_PROTECTED`。品牌/型号兼容本身不是硬失败；Logo、受保护外观、授权限制、专有协议或无法合法表达兼容性才进入硬失败或法务复核。
4. 发现保护、收纳、安装、连接、使用改善、替换和耗材等候选；将电池、充电、承重、飞行/行驶安全、医疗或其他关键部件单独提高合规等级。按公共漏斗校验实体、历史记忆、去重及硬失败。
5. 为每个配件选择证据路线：`CONFIRMED_ACCESSORY_GROWTH`要求配件侧同步增长；`LEADING_SUPPLY_GAP`用于母体已扩张、功能因果明确而配件供给尚未跟上的早期窗口。后一条路线必须有可比前代/相邻型号、早期精确搜索或用户问题等独立需求证据，不能把“没有竞品”当成需求。
6. 分别记录流量依赖、物理适配依赖、协议依赖和商标表达状态。依赖“品牌+型号+配件词”获得自然流量可以成立，但必须核验第三方兼容表达、IP和Amazon政策；不得把母体品牌词流量直接填成配件自然流量。
7. 按共享市场模块建立配件本身的精确市场，允许精确市场词包含品牌和型号；比较需求增速与唯一父ASIN/有效Offer供给增速，验证低评新品自然入口、集中度及差评改进空间。
8. 计算采购到售链路、14天安全缓冲和至少45天销售窗口。耐用品同时计算母体热点尾部与已形成装机量的滞后配件需求，不因母体搜索从峰值回落就自动判定配件需求结束。
9. 因果链或领先缺口、剩余窗口、市场和目标配置支持继续开发后，计算零采购成本经济性及30%利润后的采购空间，并按兼容参数、材料、工艺、pack和包装负担判断可实现性；可能实现即输出人工询价表，选品阶段不核对1688。核心兼容规格或询价前包装估算缺失时，相关目标配置/费用与询价资格待补；已有合格估算但缺实际采购价或最终包装实测，只使实际利润及launch待补，不阻塞已满足最低条件的询价请求。
10. 只有实际利润及全部launch必需作用域通过才生成运营策略。爆发/扩张路径缺必需日周证据时进入观察池，不使用受控试询绕过；稳定装机盘售后路径只有在日常或消耗主类型另行通过后才可进入严格询价，沿用候选ID和有效证据并只计一个方向。

## 强制行为

- “爆款”“热门”文字或一张截图不是证据。
- 母体上涨但没有配件同步增长，也没有可比型号、早期精确意图或用户问题证明功能需求时，不成立配件机会；不得把领先缺口路线当成免证据通道。
- 月度数据不能插值伪造成周趋势。
- 品牌/型号自然流量依赖不自动失败；必须拆分为流量、物理适配、协议和商标表达依赖。
- 必须使用Logo、复制受保护外观、依赖授权/芯片认证/固件握手/专有协议或无法合法表达兼容性时不通过或法务复核。
- “竞品少”不是蓝海；必须同时证明配件需求、可进入自然流量和供给缺口。
- 热点候选先验证一个通用核心SKU，不直接铺大变体矩阵。
- iPhone等手机新品、平板/手表新品、相机/运动相机、DJI等云台/无人机新品的普通壳、膜、支架、收纳、转接、线材和充电周边属于当前组合排除项；不得因热度、规模或供应容易而提交。
- 优先开放售后生态的过滤、清洁、维护和替换耗材，但必须证明精确型号需求和合法第三方兼容；滤芯/滤棉等名称本身不自动通过。
- 不执行采购。

## 输出

额外标明`selection_lane`（`BREAKOUT_MOMENTUM`、`INSTALLED_BASE_EXPANSION`或`AFTERMARKET_INSTALLED_BASE`）及`primary_type_route_status`；稳定装机盘路径未补日常/消耗主类型时只能进入观察池。

使用公共输出合同，并额外输出：`portfolio_fit_status`、`portfolio_exclusion_reason`、`installed_base_replacement_status`、`replacement_cycle_basis`、`mother_scope`、`main_product_asin_or_keyword`、`mother_momentum_path`、`product_role`、`accessory_candidate`、`accessory_evidence_path`、`main_search_growth_ratio`、`main_sales_growth_ratio`、`trend_duration_days`、`latest_7d_decline`、`installed_base_proxy`、`attachment_rate_basis`、`accessory_growth_ratio`、`accessory_supply_growth_ratio`、`synchronization_lag_days`、`leading_supply_gap_status`、`compatibility_status`、`supported_models`、`single_main_product_share`、`ecosystem_type`、`traffic_dependency`、`physical_fit_dependency`、`protocol_dependency`、`trademark_usage_status`、`remaining_heat_days_low`、`remaining_heat_days_high`、`installed_base_tail_days_low`、`raw_chain_days`、`safety_buffer_days`、`minimum_sales_window_days`、`required_hot_window_days`、`brand_dependency`、`causal_chain_status`。

## 阶段与证据边界（v0.6）

输出 `research_stage`、`screen_decision`、`review_type`、`memory_match_ids` 与补证动作。候选优先复用“问题型长尾意图→可感知且可执行改进→有依据的pack/组合→低评新品自然入口”结构，但卖家案例仅用于发现并披露幸存者、变体与促销污染。确定直接竞品后立即按共享流程快抓评论、分析重复差评并发散低成本改进；采用改进时必须落到实际报价和验收方法。研究通过或区间粗算通过都不等于 `launch_decision=通过`；目标配置不足时按共享市场的组合证据路线进行人工研究。人工实际询价及最终包装三边/实重未核验时，`profit_validation_status=待人工询价`，不得生成可执行运营策略。只有AI完成实际利润复算并通过全部门槛，才进入开发排序并输出与热点剩余窗口一致的运营策略。主类型改路沿用候选ID和有效证据。
