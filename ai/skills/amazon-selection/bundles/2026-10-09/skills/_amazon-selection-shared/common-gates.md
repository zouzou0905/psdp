# 亚马逊精铺公共门槛

政策版本：`selection-gates-v0.10.0`

更新时间：`2026-10-08`

FBA费率基准：`fba-fees-2026-09-21`。每次执行须完整读取`fba-fees.md`及其结构化数据`fba-fees-2026-09-21.json`；达到其中的强制复核日期或Amazon发布新费率后，先更新快照再允许自动通过。

佣金核算基准：`selection-fee-policy-2026-09-17`。所有候选统一按成交基数的15%计算，不按类目或价格区间切换佣金率。

这些规则来自用户当前业务约束。候选结构、评论快抓、低成本改进、人工询价、实际利润验证及运营策略交接统一执行`candidate-profit-workflow.md`；批量数量、询价前经济性、采购简表、回填一致性和交付检查统一执行`batch-review-handoff.md`。各类型Skill不得另造一套评论、利润或批量交接口径。历史成功/失败产品尚未完成回测，凡标记为“初始阈值”的数值均不得描述为行业定律。

回归基准：2026-08-31英国站五方向250候选审计中，250/250的`market_decision`均为`待补`；每条都缺完整精确市场、至少2个核心词自然证据、至少3个月连续新品销量、1688精确SKU、包装尺寸/完整到岸成本以及税费/汇率/完整利润。原结果为116个不通过、104个待补、30个建议改类，另有6个跨Skill重复。该样本用于校准漏斗顺序和缺失项拦截；缺证据不是已证明产品失败。2026-09-04人工50款为通过5、不通过35、待审核10；人工认可不替代launch验证。v0.4区分继续研究与开发通过，校准品牌集中、预测队列和目标配置证据；保留经营底线。

## 1. 经营模型

固定采用：

```text
结构化重选品 → 小批量轻启动 → 自然流量验证 → 数据化淘汰
→ 稳定产品做供应链/产品力优化 → 合法扩展产品线
```

- 站点：`GB`、`DE`、`JP`、`CA`；每次 Sorftime 调用显式传站点，不跨站混算。
- FBA、自有品牌、现货起步；稳定后再优化包装、UV印刷、激光打标、组合或合法变体。
- 单品不要求成为爆款，但必须满足自身销量和真实贡献利润门槛。
- 月开发1500款是组合经营目标，不能降低单品门槛，也不能用SKU数量抵消库存、利润或合规风险。
- “轻运营”只表示流程标准化，不表示降低Listing、图片、关键词、质量、库存或合规要求。

### 1.1 当前组合策略排除与偏好（2026-09-28）

- 未经用户另行明确重开，本项目不追逐手机、平板、智能手表、相机/运动相机、云台、无人机等消费电子新品发布后会被通用供应链迅速复制并价格内卷的周边配件，包括但不限于保护壳、贴膜、支架、收纳壳、转接件、线材和普通充电周边。此类候选标记`PORTFOLIO_FAST_COMMODITIZATION_EXCLUDED`，不得进入正式询价表；不能仅以市场大或新品热度高放行。
- 热点配件优先寻找中小安装量但有持续真实需求的开放售后生态，尤其是可替换、清洁、维护或耗用部件，例如净化器过滤棉/滤网、加湿器滤芯、扫地机刷件/滤件及其他无需授权、专有协议或安全关键认证的替换件。示例只表示候选形态，不自动证明需求、兼容、IP、自然流量、利润或热点类型成立。
- 若母体没有可验证的近期增长或装机扩张，但替换需求稳定，沿用候选ID转日常品或消耗品/包装规格路线；不得为了留在热点方向伪造增长。无论量级大小，目标Offer仍须达到公共预计月销、市场进入、利润、包装、合规和IP门槛。

## 2. 分阶段漏斗与统一候选池

开始候选发现时读取 `selection-memory.md` 和它指向的人工审核数据；需要回归或衡量效果时读取 `validation-cases.md`。历史记录只在站点、购买意图和具体配置匹配时应用。

同站建立统一候选池，不为日常、季节、节日、热点、消耗属性平均分配名额。优先从可比卖家的真实在售/成交线索、人工通过品的相邻需求、反复出现且可解决的评论问题生成候选。可取的卖家模式只抽象为“明确买家问题/使用场景 → 买家可感知且供应商可执行的规格或结构改进 → 有场景依据的pack/组合 → 低评论新品和自然入口验证”，不得照搬单个卖家的品类、销量或成功结论。记录买家、场景、规格和拟售配置；关键词含数字、标题写PCS、促销价、购买标记或店铺有销量都不自动加通过标签。两家示例店铺的价格带仅作种子参考，不设统一£6.99–£9.99或低价信封件经营限制。

执行调度统一遵循six-agent-control.md第4.1a节（selection-execution-v1.2.0）：先检查证据可得性，优先现有池的小批完整验证，再有针对性扩池。此调度不改变最终launch阈值；不得把采购后的实际报价/最终包装实测要求提前作为候选发现或询价前阻塞项，也不得因此免除对应询价层级的必需证据。

### 阶段A：发现与初筛

1. 核对关键词、购买意图、ASIN、标题、图片和链接。错配必须先纠正，不沿用错误商品的销量、费用或货源；记录 `KEYWORD_PRODUCT_MISMATCH`。
2. 匹配已做品/历史审核记录，再语义去重。相同问题的不同方案在一个机会下比较；确有不同购买场景或需求的规格可以分别保留，不能只因名称相近合并。
3. 若候选来自卖家目录，记录目录截止日、分页/覆盖边界、父子体归并、促销与履约状态，并披露幸存者偏差。低评论不等于新品、购买标记不等于精确销量、同父体变体不等于独立成功样本、店铺数量变化不等于全部为新品。
4. 先筛禁做属性、不能承运、明确认证/IP硬失败及已证实的市场控制；可补证风险进入专项复核。
5. 选品研究阶段不搜索、不匹配也不核对1688商品、SKU、页面价格、MOQ或供应商；供应查找从候选进入人工采购询价后开始。不得因为没有1688链接、精确SKU或供应入口而阻塞市场研究或询价候选。
6. 锁定一个Amazon可售单位及目标材质、规格、pack和改进要求，并把包装估算前移到询价前经济性。优先使用精确子ASIN包装数据、同父体pack梯度或多个同结构可比Offer，形成低/基准/高三种包装后重量和尺寸情景，预判头程路线、FBA费档及采购空间；不得把商品净重、展开尺寸、父体共享值或其他pack的数据直接当目标包装。估算只用于初筛和询价排序，必须输出`profit_basis=采购空间推理`、`final_package_status=estimated`和`profit_validation_status=待人工询价`。
7. 公共最低售价只判断经营底线。进入询价队列前按`batch-review-handoff.md`反推达到30%贡献利润率及最低贡献利润时允许的最高整包采购价，即`采购空间`。即使采购成本取0仍达不到利润底线或采购空间非正，直接淘汰；采购空间为正时，再根据目标产品的材料、工艺、结构复杂度、pack数量、定制程度、认证要求、包装体积重量和已知常识区间做可实现性推理。判断为可实现即可进入下一步；明显不可实现则淘汰；证据不足但未显示明显不可实现时标记边界/待人工询价，不得以缺少1688证据否决。

阶段A先保存`preflight_market_definition`、`preflight_parent_density_status`、`price_weight_envelope_status`和`market_evidence_block_id`。精确市场边界必须在读取竞争、销量和评论结果前固定；不能在看到父体过多或预测偏低后事后增加无需求依据的尺寸、材质或场景条件。已证实父体数>50、零采购成本仍无利润、包装明显>2kg或历史重复时立即停止后续昂贵验证；只取部分分页或市场边界尚未结构化时为待补，不把未知写成通过或失败。

`screen_decision=通过`表示实体/去重/已知业务风险、目标形态与成熟工艺可实现性和有依据的粗算支持继续研究；信息不足为待补。除实体身份不清、重复且无独立方案、明确硬失败外，阶段A的待补只阻塞依赖该缺失字段的判断，允许开展有独立价值的市场/趋势/包装核验。须输出补证动作，不将待补批量包装成终审候选。公共表中“初筛匹配供应线索”在选品阶段指产品形态及材料/工艺可实现性推理，不要求查询1688或取得供应SKU；精确SKU仍在人工询价后、开发终审前核验。

### 阶段B：市场验证与同步补证

按 `market-entry.md` 确定精确市场、目标预测队列、自然进入和具体配置证据；选品阶段同步补包装与非采购费用，供应确认在人工询价后补。市场可在供应待补时独立通过，launch仍待补。按真实需求周期路由，消耗/pack作为属性；通用替换件不必通过热点因果链。某一路线不成立但另一类型有证据时，沿用同一候选ID转路，不复制凑名额；缺类型证据不等于已经证明另一类型成立。

目标方案必须写成“买家问题 → 可执行改动 → 需求依据 → 新增成本”。候选实体及直接竞品初步确定后即按共享流程先快抓评论，优先近期差评并用好评作对照，再对重复、相关、供应链可控制的缺陷深验。质量差评须记录精确ASIN/变体、具体缺陷、评论覆盖、样本量、时间、反复性、跨ASIN支持、污染、核验/改进方案和成本。不得仅凭低评分或单条差评认定机会或一刀切淘汰，也不得把配送/服务问题、多件装、更好质量、漂亮包装本身当有效差异化。

可信缺陷存在时，AI原则上发散至少3个结构不同的低成本改进，再按需求支持、买家感知、供应可执行性、增量成本、尺寸重量/FBA、合规/IP和样品验收收敛。没有可信缺陷时允许不改，但必须说明证据；不得为了差异化强制改款。改进成本在研究阶段只能粗算，开发终审使用包含选定改进规格的实际人工报价。

市场、类型和时机证据支持继续开发，且采购空间经推理可实现后，AI必须按`candidate-profit-workflow.md`生成目标Offer级`quote_input_request`，交由人工自行寻找货源并填写真实采购询价、最终销售包装三边与包装后实重。选品阶段不得核对1688；任何平台页面价、竞品尺寸或AI推理都不能写入实际利润。

### 阶段C：开发审核

进入开发终审前，至少1个精确供应SKU完成形态、材质、关键公差/兼容、pack、选定改进规格、人工实际询价、最终包装三边和包装后实重核验；若采用评论驱动改进，还须定义可执行的样品验收方法并确认报价已包含该改进。AI再按目标站点、费率快照和完整成本公式计算实际利润。FBA、头程、税费、汇率、退货准备和完整利润齐全；市场、主需求类型、时机及所依赖策略也必须通过。实际利润通过后才生成下一步运营销售策略；未通过则保留市场结论，输出价格、pack、尺寸、重量或供应成本的敏感性改进动作。

采购第一轮主表只校验采购单价、单个重量、整包总重和包装长宽高六个数值；最终利润核验阶段另对pack数量、MOQ、交期和费用字段执行类型硬校验。“定制款”“找不到链接”“已下架”等采购结果只能进入`sourcing_status`或`procurement_result_note`，不能写进采购价。pack数量为正数，单位与“12件装/1卷20码”等描述分列。最终包装尺寸必须是折叠、压缩或装盒后的实际可售外包装尺寸，不得使用展开尺寸、裸品尺寸或单个内件尺寸。任一错误须返回明确缺项或`数据异常`，不能仅以“非空”判定规格完整。

`review_type=研究复核`可提交需商业判断的配置/质量切口，并显式列缺失与next_action；`review_type=开发终审`仅接收本阶段全部证据齐全的候选。`human_review_decision`保留用户原结论，不覆盖系统各作用域。

`research_stage`枚举为发现/初筛、市场验证/补证、开发审核。包装缺失为 `PACKAGE_DATA_MISSING`、费档未核清为 `FBA_TIER_UNRESOLVED`；它们阻塞费用/利润和launch，不能阻塞独立市场研究。价格/货源错配等全局异常必须纠正后再继续依赖它的判断。

## 3. 决策作用域

分别输出：

1. `type_decision`：主需求类型是否成立；属性型Skill可为`未评估`。
2. `timing_decision`：季节、节日、热点等当前窗口是否来得及；不适用时为`未评估`。
3. `market_decision`：精确市场的需求、竞争和自然流量是否支持进入。
4. `tag_decisions`：消耗品、大PCS、变体、组合、定制等标签独立结论。
5. `selection_lane_decision`：独立发现方向本身是否形成有效候选；不适用时为`未评估`。
6. `launch_decision`：公共硬门槛、供应、完整利润、物流、合规及本次依赖策略全部通过后，是否进入开发池。
7. `quote_input_status`：是否已经触发、填写并核验人工询价输入。
8. `profit_validation_status`：实际利润是否完成并达到经营底线。
9. `operating_strategy_status`：只有实际利润及全部launch必需作用域通过后才为`可生成`。

另输出`inquiry_lane`，它不属于launch决策状态：

- `STRICT_QUOTE`（严格询价）：主类型、适用时机、市场、目标配置、包装、风险和询价前经济性均达到自动询价要求。
- `CONTROLLED_TEST_QUOTE`（受控试询）：只允许`type_decision`、`timing_decision`或`market_decision`中的一个为`人工复核`，且原因必须是工具历史粒度/可比样本能力限制；同时存在至少两类互相独立、指向同一购买问题的替代证据。实体、目标Offer/pack、风险/IP/合规、包装A–C、自然需求、采购空间和公共硬门不得待补或失败。
- `WATCHLIST`（观察池）：时间未到、缺少两个替代证据、存在多于一个复核作用域、关键字段待补，或暂不值得询价。

受控试询不得把`人工复核`回写为`通过`，不得用于实际利润或launch自动通过；其与C档边界询价合并后最多占当次采购交付的20%。缺身份、缺目标配置、缺自然需求、风险/IP/合规不清、包装置信度D、零采购仍不盈利或硬门失败时，禁止进入受控试询。

公共状态：`通过`、`待补`、`人工复核`、`建议改类`、`不通过`、`数据异常`、`未评估`。标签分支可额外使用`不适用`。

参与同一聚合的作用域按以下优先级处理：

```text
数据异常 > 不通过 > 建议改类 > 待补 > 人工复核 > 通过
```

`未评估`和标签分支的`不适用`不参加优先级比较：若该作用域确实不适用，则排除；若它是本次结论所必需但尚未评估，则按`待补`处理。以下规则必须同时成立：

- 公共硬门槛和影响精确SKU、成本、重量、物流、合规的全局异常始终传导到`launch_decision`。
- 主需求Skill的`type_decision`、适用时的`timing_decision`、`market_decision`、公共硬门槛、供应与完整利润都属于launch必需作用域；任一未通过均不得输出`launch_decision=通过`。
- `profit_basis=区间粗算`、`quote_input_status!=已核验`或`profit_validation_status!=通过`时，不得输出`launch_decision=通过`，也不得把运营销售策略标记为可执行。
- `type_decision=建议改类`时，当前路线的`launch_decision=建议改类`，并路由到指定主类型Skill重新验证；除非同时存在更高优先级的全局数据异常或硬失败。
- 属性型Skill的标签复核模式可以不重新验证主类型，但必须接收同站点、同市场定义、同政策版本且仍有效的上游主类型结果；缺失时launch按`待补`处理。
- 消耗品与包装规格Skill可使用独立发现模式，从Amazon当地在售结构形成候选并输出`selection_lane_decision`；没有上游主类型结果不阻塞候选发现或pack市场判断，但最终launch仍须路由并通过相应日常、季节、节日或热点主类型验证。
- 小包装、标准包装和大PCS均按目标Offer自身需求、自然流量、供应和完整利润判断。未选择大PCS策略时，不得因大PCS标签未通过而否决已独立通过的小包装或标准包装方案。
- `branch_mode`只表示评估哪些标签；`selected_launch_strategy_tags`才表示本次方案依赖哪些标签。
- 未被选择的可选标签，其待补、人工复核、不通过或标签局部异常不得阻塞其他已通过方案。
- 被选择的标签必须通过；其状态按同一优先级传导到`launch_decision`。
- 总分、方向标签和产品类型均不能抵消硬失败。

`launch_decision=通过`只表示进入开发池，不代表自动采购。除非用户另行明确授权，不得下单、联系供应商或创建采购任务。

## 4. 公共硬门槛

| 项目 | v0.4规则 | 自动化口径 |
|---|---:|---|
| 售价 | 严格 `> USD 4.99` 等值 | 按分析日汇率折算当地挂牌/含税价；不能直接拿GBP/EUR/JPY/CAD与4.99比较 |
| 采购成本 | `<= CNY 50` | 人工实际询价所得、与目标材质/规格/pack一致的整包成本；选品阶段的采购空间推理或商品卡价格不能代替 |
| 单件贡献利润 | `>= USD 1` | 使用完整成本公式，Sorftime展示毛利不能直接代替 |
| 贡献利润率 | `>= 30%` | `贡献利润 / 净销售收入` |
| 预计自身月销量 | `>= 30单` | 目标新品的保守预测；竞品、父体或市场总销量不能直接填入 |
| 相关竞品 | 唯一父ASIN `<= 50` | 同站点、同购买意图、同功能和规格层级；分页去重 |
| 竞品评论 | 相关父ASIN评论中位数 `<= 500` | 必须先建立未按评论数预过滤的市场全集 |
| 品牌集中与进入 | Top1/Top3必报；按市场控制和独立进入证据判断 | Top3<=20%只用于分散/蓝海标签，不再是通用否决线；不得忽视品牌/自营控制或改口径择优 |
| Amazon自营 | 自动通过要求可比市场自营份额为0 | 非0进入人工复核；Amazon自营进入同意图Top20或形成明显控制时不通过 |
| 首单速度 | 预计 `<= 15天` | 至少2个较新、低评论、月销达标且有自然位的精确可比Offer；只能证明代理证据，不能伪造真实首单日 |
| 包装重量 | `<= 2kg` | 询价前以保守包装估算筛除明显超限方案；开发终审只认最终包装后实重。标题、详情与供应SKU矛盾时为数据异常 |
| 包装尺寸/FBA费档 | 按目标站实际费档 | 不设四站统一最长边上限；长宽高缺失或费档未核清为`待补`，数据冲突为`数据异常` |
| 供应路径 | 初筛有匹配线索，开发池前>=1个精确SKU | 市场与供应可同步补证；精确SKU必须匹配目标形态、规格、pack、成本、包装尺寸和实重 |

成熟期广告成本`<=1%`是上市后KPI，不是Sorftime可证明的选品硬门槛。选品阶段只输出自然位和广告暴露代理证据，并标记`AD_RATE_UNOBSERVED`。

### 站点FBA费与尺寸

- 完整使用`fba-fees.md`及对应JSON快照；尺寸只用于判定站点费档、计费重量、附加费和利润，不作为脱离费用的统一淘汰线。
- 每个目标Offer必须记录：`target_sale_date_or_window`、`price_tax_basis`、`amazon_fee_category`、`commission_policy_id`、`commission_rate`、`commission_base_local`、`commission_amount_local`、`commission_source`、`public_calculator_status`、`seller_central_help_status`、`packaged_length_cm`、`packaged_width_cm`、`packaged_height_cm`、`packaged_unit_weight_g`、`dimensional_weight_kg`、`fba_billable_weight`、`station_size_tier`、`fba_fee_category_route`、`de_fee_mode`、`low_price_price_cap`、`low_price_fba_eligibility`、`base_fba_fee_local`、`applicable_discount_local`、`fba_surcharge_rate`、`effective_fba_fee_local`、`fba_fee_to_price`、`fba_rate_period_status`、`tax_inclusion_status`、`fee_snapshot_as_of`、`fee_effective_from`、`fee_source`、`fee_verified_at`。
- 英国、德国使用当前基础费并加1.5%燃油物流附加费；加拿大先减适用低价折扣再加3.5%；日本当前公开表含10%消费税。费率快照更新后以新快照为准。
- 德国CEP参与状态未知时使用较保守的`DE_ONLY`，该列已含EUR 0.26差额，不得重复加收。
- 英国、德国的列明特殊类目、低价FBA和普通费表必须分路由；加拿大体积除数5000仅为官方示例反推且完整尺寸分档未包含在用户PDF中，日本公开费档存在重叠。任何站点费率有效期、售价门槛、类目或档位有歧义时，使用Revenue Calculator或Seller Central Fee Preview核验。
- 加拿大2026-09-21至2026-10-14的当前费率不在用户PDF内，该时段不得套用2027-01-15起非旺季表；返回`FBA_EFFECTIVE_PERIOD_GAP`和`待补费用`。
- `effective_fba_fee_local = (base_fba_fee_local - applicable_discount) * (1 + fba_surcharge_rate)`；`fba_fee_to_price = effective_fba_fee_local / price_local`。不适用折扣时为0。
- `fba_fee_to_price`用于诊断和同站排序，不设置30%或35%之类的统一硬阈值；完整贡献利润和利润率才是硬门槛。
- 40cm商品不能仅因长度自动淘汰；若它进入更高费档，必须按实际有效FBA费和头程重算利润。费率快照过期为`DATA_STALE`，费率来源冲突为`FBA_FEE_CONTRADICTION`。

### 询价前包装估算与物流预判

执行原则为“包装估算前移，最终包装实测后移”。只对通过实体、类型/时机快筛且仍有市场价值的候选做轻量估算；优先复用已抓取的竞品和pack梯度数据，不为每个发现线索额外做全市场包装深挖。

包装证据置信度：

- `A`：同父体或同一商品存在至少两个明确pack梯度，并有精确子Offer包装后重量/尺寸，可反推单位增量和基础包装；
- `B`：至少3个同结构、同材质和相近规格的独立可比Offer数据一致；
- `C`：仅1个可比Offer或相近形态类比，允许进入B/C询价档，但必须采用保守情景并列出人工核验项；
- `D`：只有常识或无可追踪来源，不得进入正式`quote_ready`主表，先补包装证据。

多PCS/规格变化的重量优先按pack梯度反推：

```text
单位增量重量 = (包装重2 - 包装重1) / (数量2 - 数量1)
基础包装重量 = 包装重1 - 单位增量重量 × 数量1
目标包装毛重 = 基础包装重量 + 单位增量重量 × 目标数量
```

只有在同材质、同单件规格、同包装结构且数据层级一致时才可使用；否则按单件净重×数量+内包装+外包装+说明/配件分项估算，并扩大区间。尺寸/体积按结构选择模型：紧固件等高密度散装使用密度、装填率和盒体；袋/纸/贴纸主要让厚度随数量变化；杯碗等套叠品使用基础高度+单件套叠增量；软品使用压缩系数；刚性异形品使用排列和空隙率。不得假设三边与数量线性同比增长。

每个候选至少保存：`packaging_estimate_source`、`packaging_estimate_scope`、`packaging_confidence`、`reference_asins`、`source_pack_count`、`packing_structure`、`estimated_unit_net_weight_g`、`estimated_packaging_base_weight_g`、`estimated_gross_weight_low/base/high_g`、`estimated_length/width/height_low/base/high_cm`、适用的`nesting_factor/compression_factor/fill_factor`、`final_package_status`和估算限制。

对每种情景分别计算头程体积重、计费重、预选渠道、FBA费档和采购空间。接近2kg、渠道切换点或FBA尺寸/重量档位时，同时计算相邻两条可行路线/费档并采用较高成本情景作放行判断，记录`route_switch_condition`与`fba_tier_boundary_distance`。输出`estimated_volumetric_weight_low/base/high_kg`、`estimated_chargeable_weight_low/base/high_kg`、`preliminary_headhaul_channel`、`procurement_space_low/base/high_cny`。最终包装未由人工/供应商确认并与实物同层级实测前，不得将任何估算升级为实际利润。

### 目标Offer支持与通过后排序

- 目标Offer必须把“同一买家问题”落实为可由供应链执行并能被买家感知的规格、材质、pack、兼容、结构或功能差异；“更好看”“质量更好”等空泛描述不能通过，记录`DIFFERENTIATION_VAGUE`。
- 目标配置须通过`market-entry.md`中的直接证据路线；组合证据可支持人工研究，但不能把宽泛市场销量或未验证的尺寸/pack带入自动开发。
- 分阶段、分状态排序：研究队列按需求可信度、补证价值及成本安排；不得将研究分排序混入开发通过榜。只有所有launch必需作用域通过的候选才参加开发排序。默认同站排序权重：自然进入与目标配置证据25、完整利润安全垫20、物流/FBA稳健性20、差异化可执行性15、竞争结构10、供应稳定性10。
- 排序分只决定已通过候选的优先级，不得抵消硬失败、待补、人工复核或数据异常；必须同时输出各分项原始证据，禁止只给总分。

### 完整利润公式

先按站点税制确定净销售收入，不能硬套统一VAT：

```text
贡献利润 = 净销售收入
         - (成交基数 × 15%) - effective_fba_fee_local
         - 采购成本 - 国内运费 - 包装/打标
         - 头程/关税 - 仓储分摊 - 退货/破损准备
         - 其他单件费用
```

必须回显原币金额、币种、汇率日期、FBA费版本、税费口径和公式。采购、包装重/尺寸、头程、FBA费、税费或汇率任一关键项缺失时，利润结论为`待补`，不得用0补齐。

人工询价输入、头程计费重、盈亏平衡价、常态/基准/保守促销情景和利润通过后的运营策略，完整执行`candidate-profit-workflow.md`。头程按`max(包装后实重kg, 长×宽×高/体积重除数) × 渠道人民币每kg单价`计算，按实际计费重，不做0.5kg或1kg进位，也不计最低计费重量、旺季或偏远附加费；仅可使用项目内当前有效渠道费率。日本、加拿大费率未补齐时，相关站点实际利润保持`待补费用`。

## 5. 类目、运输与合规

- 排除：影音、书籍、化工品、液体、粉末、强磁，以及任何需要认证但无法或不计划取得认证的产品。
- 儿童/婴儿且需要认证的产品直接排除。
- 低功率带电、弱磁、易碎可以评估，但当前没有功率/磁力数值定义；属性、承运或包装条件不清时人工复核。
- 避开Amazon自营、强势品牌、品牌专属接口、Logo、角色、版权图案、商标词导流和明显专利/外观风险。
- Sorftime不是专利、商标、版权或认证数据库；不得输出“无侵权”“无需认证”，只能输出风险信号及`待法务/合规核验`。
- 大件高货值和高认证不是当前正向选品方向。包装后>2kg或依赖未计划认证时，方向分不能翻盘。
- 头程成本不设绝对上限，但必须计入完整利润；包装尺寸必须取得并匹配正确FBA费档。

## 6. 数据质量与时效

- 空白、`--`、`N/A`、`未知`解析为缺失，不是0。
- 单位、币种、站点、父子体、件数、供应SKU或日期矛盾时输出`数据异常`，不得选择更有利数值。
- 断货、恢复供货、优惠券、秒杀、降价、广告集中投放、评论继承或合并变体产生的污染进入人工复核。
- 普通市场数据超过7天不得自动通过；热点数据优先不超过72小时。
- FBA费率快照达到`mandatory_recheck_on_or_after`、Amazon公布新费率或Fee Preview与快照冲突时不得自动通过；先复核并更新快照。
- 当前基础FBA费只在与目标销售时段、费率路线和精确Offer完全一致时才能作为最终费用；目标时段存在旺季费、精确费档歧义或Fee Preview要求时，只能输出`base_fee_estimate_status=预估通过/预估不通过/待补`。未取得目标时段有效费或旺季Fee Preview时，`profit_validation_status=待补费用`，不得写成“实际利润通过”。
- 数值列出现文本、公式错误或跨行沿用费用时分别标记`NON_NUMERIC_COST_INPUT`、`FORMULA_ERROR`或`DATA_CONTRADICTION`。交付前必须清除`#REF!`、`#DIV/0!`、`#VALUE!`、`#NAME?`、`#N/A`、`#NUM!`、`#SPILL!`和`#CALC!`；错误未清除时整个利润结论不可用。
- 历史长度或粒度不足时明确限制并降级；禁止插值伪造月份、周数、评论历史或首单日期。
- 购买标记（50+/100+）只表示页面展示的购买档位，不等于精确销量、卖家独占成交、真实新品成功率或自然订单；未显示标记不是零销量。低评论不等于新上架，必须核验日期。店铺存活商品存在幸存者偏差。
- 竞品按唯一父ASIN去重；价格、销量、包数、重量和利润必须尽量落到精确子ASIN/Offer。无法拆分时标记`VARIATION_CONTAMINATION`。
- 产品图片、调研重量、调研FBA费和首次上架时间也必须落到目标子ASIN/精确Offer并记录来源、抓取日期、数据层级及精度。父体/其他变体数据、首条评论日期、最早观测日或工具估算只能在明确标注后作为代理，不能伪装成精确事实。

## 7. Sorftime与采购平台使用边界

先快筛、后深验：

1. `get_time`固定截止时间。
2. 类目/商品发现：`category_search_from_product_name`、`search_categories_broadly`、`product_search_from_name`、`product_search`；`potential_product`仅GB/DE作线索。
3. 初筛：核对词品/链接/ASIN一致、历史记忆、语义去重和业务风险；供应线索及包装/成本区间粗算与市场验证分阶段执行。缺失仅阻塞依赖它的判断，明确硬失败停止。
4. 市场：`category_report`、`category_trend`、`category_keywords`、必要时历史快照。
5. 关键词：`keyword_detail`、`keyword_trend`、`keyword_search_results(position_type=1/2)`。
6. ASIN：`product_detail`、`product_report`、`product_trend`、`product_variations`、`product_traffic_terms`、`competitor_product_keywords`。
7. 评论：`product_reviews`、`product_customers_say`；说明评论工具仅覆盖近一年且最多100条。
8. 选品阶段禁止调用1688搜索、相似商品、详情或变体工具。只有候选已进入人工询价、用户另行提供供应信息或明确要求核验货源时，才在采购复核阶段核对目标SKU、报价口径、MOQ与供货；不得自动联系供应商。

不允许用自然词数、广告位数或一次SERP截图换算精确ACOS、广告费率或自然订单占比。

## 8. 统一输出合同

至少输出：

```text
as_of, site, policy_version, market_module_version, seed, seed_source, market_definition,
research_stage, screen_decision, review_type, human_review_decision,
memory_match_ids, memory_action, changed_conditions, semantic_duplicate_group,
buyer_segment, use_context, buyer_problem, proposed_change, demand_basis, incremental_cost,
seller_pattern_source, seller_catalog_scope, seller_catalog_as_of, seller_catalog_survivorship_risk,
long_tail_intent, observable_improvement, improvement_verification_method, pack_or_bundle_rationale,
promotion_dependency, low_review_entry_signal, natural_entry_signal, seller_pattern_reuse_decision,
quality_defect, quality_evidence, verification_method, rough_cost_scenarios, package_data_source,
product_image_url, product_image_source, product_image_scope, product_image_match_status,
researched_weight_g, researched_weight_basis, researched_weight_source, researched_weight_verified_at,
researched_fba_fee_local, researched_fba_fee_type, researched_fba_fee_tier,
researched_fba_fee_source, researched_fba_fee_as_of,
target_child_first_listed_date, listing_date_precision, listing_date_source, listing_date_scope,
review_quick_scan_status, review_coverage, review_sample_count, low_star_sample_count,
positive_control_sample_count, review_theme_matrix, repeat_defect_count,
cross_asin_defect_support, review_bias_flags, review_driven_improvement_status,
improvement_ideas, selected_improvement_id, selected_improvement_spec,
improvement_demand_evidence, estimated_incremental_cost_cny,
actual_improvement_incremental_cost_cny, improvement_quote_included,
improvement_cost_sensitivity, supplier_execution_requirement, sample_acceptance_test,
size_weight_impact, compliance_ip_impact, improvement_selection_reason,
forecast_cohort_definition, forecast_cohort_ids, forecast_coverage, cohort_sales_p25,
head_control_status, target_evidence_route, qualification_method,
selection_mode, selection_lane, selection_lane_decision,
primary_type, primary_type_source, primary_type_validation_status,
secondary_tags, branch_mode, pack_scope, target_pack_tier, target_pack_count,
pack_market_fit_status, selected_launch_strategy_tags, tag_decisions,
preflight_market_definition, preflight_parent_density_status, price_weight_envelope_status,
market_evidence_block_id, inquiry_lane, inquiry_lane_reason,
controlled_evidence_gap_scope, controlled_alternative_evidence,
required_decision_scopes, decision_propagation,
evidence_window, data_freshness,
type_decision, timing_decision, market_decision, launch_decision,
estimated_new_item_monthly_sales, distinct_parent_asin_count,
median_review_count, top1_brand_share, top3_brand_share, amazon_owned_share,
newcomer_sample_count, low_review_sample_count, conservative_new_sales,
newcomer_success_rate, low_review_organic_proof_count,
relative_entry_index, peer_top5_ratio, blue_ocean_status,
target_configuration_definition, target_configuration_offer_count,
target_configuration_parent_count, target_configuration_sales_proof_count,
target_configuration_organic_keyword_count, target_offer_support_status,
supplemental_observation_count,
organic_evidence, ad_metric_status, first_order_evidence,
price_local, price_usd, procurement_cost_cny, landed_cost,
contribution_profit_usd, contribution_margin,
profit_basis, quote_input_request, quote_input_status, supplier_sku_id, quote_source_or_link,
quote_date, quoted_quantity, moq, lead_time_days, sourcing_status, procurement_result_note,
actual_procurement_price_cny, price_basis, quote_price_basis, quoted_inner_unit_count,
target_pack_unit, pack_description,
confirmed_specification, packaging_label_cost_cny_per_unit, domestic_shipping_cny_per_unit,
headhaul_channel, headhaul_rate_cny_per_kg, headhaul_cost_cny_per_unit,
break_even_price_local, minimum_30pct_margin_price_local, profit_validation_status,
profit_scenarios, profit_safety_buffer, operating_strategy_status, operating_sales_strategy,
packaged_length_cm, packaged_width_cm, packaged_height_cm,
packaged_unit_weight_g, dimensional_weight_kg, billable_weight,
commission_policy_id, commission_rate, commission_base_local,
commission_amount_local, commission_source, public_calculator_status,
seller_central_help_status,
station_size_tier, fba_fee_category_route, de_fee_mode,
low_price_fba_eligibility, base_fba_fee_local, fba_surcharge_rate,
effective_fba_fee_local, peak_fee_preview_local, base_fee_estimate_status,
final_fee_validation_status, fba_fee_to_price, fee_snapshot_as_of,
fee_effective_from, fee_source, fee_verified_at,
supplier_candidates, common_gate_results, type_gate_results,
anomaly_flags, compliance_flags, reason_codes, missing_fields,
confidence, evidence_summary, next_action
```

所有数值带单位和来源。`confidence`只表示证据完整度；不得改变任何决策。

## 9. 上市后验证里程碑

进入开发池后，建议用以下初始观察点生成监控计划，不能在选品阶段假装已完成：

- 第15天：是否取得首单，以及首单是否来自自然/可解释流量。
- 第30天：自然收录、核心词位置、点击与质量问题是否成立。
- 第60天：月销运行速度是否达到30单。
- 第90天：完整贡献利润率、退货、库存周转和补货稳定性是否达标。
- 稳定销售至少60天或完成2次补货后，才进入变体、组合或定制扩展审查。

## 10. 通用原因码

`DATA_MISSING`、`DATA_STALE`、`DATA_CONTRADICTION`、`FX_MISSING`、`COST_INCOMPLETE`、`NON_NUMERIC_COST_INPUT`、`NON_NUMERIC_PACK_COUNT`、`UNFOLDED_DIMENSION_USED`、`FORMULA_ERROR`、`PROFIT_FAIL`、`SALES_LT_30`、`COMPETITORS_GT_50`、`MEDIAN_REVIEWS_GT_500`、`HEAD_CONTROL_BLOCKED`、`AMAZON_OR_STRONG_BRAND`、`ORGANIC_EVIDENCE_WEAK`、`TRAFFIC_ATTRIBUTION_ANOMALY`、`AD_RATE_UNOBSERVED`、`FIRST_ORDER_EVIDENCE_WEAK`、`WEIGHT_GT_2KG`、`PACKAGE_DATA_MISSING`、`COMMISSION_POLICY_MISSING`、`PUBLIC_CALCULATOR_UNAVAILABLE`、`SELLER_CENTRAL_HELP_LOGIN_REQUIRED`、`FBA_TIER_UNRESOLVED`、`FBA_FEE_CONTRADICTION`、`FBA_PEAK_FEE_UNRESOLVED`、`FBA_EFFECTIVE_PERIOD_GAP`、`FBA_CATEGORY_ROUTE_MISSING`、`LOW_PRICE_ELIGIBILITY_CONFLICT`、`TAX_BASIS_MISSING`、`FORBIDDEN_MATERIAL`、`CERTIFICATION_REQUIRED`、`IP_REVIEW_REQUIRED`、`STOCKOUT_DISTORTION`、`PROMO_DISTORTION`、`VARIATION_CONTAMINATION`、`KEYWORD_PRODUCT_MISMATCH`、`DUPLICATE_CANDIDATE`、`SOURCE_NOT_FOUND`、`QUOTE_EVIDENCE_INCOMPLETE`、`BASE_FEE_ESTIMATE_ONLY`、`TARGET_OFFER_SUPPORT_WEAK`、`DIFFERENTIATION_VAGUE`、`SELECTED_STRATEGY_NOT_READY`、`SELLER_PATTERN_DISCOVERY_ONLY`、`SELLER_CATALOG_SURVIVORSHIP_RISK`、`REVIEW_SCAN_REQUIRED`、`REVIEW_COVERAGE_LIMITED`、`REVIEW_VARIATION_CONTAMINATION`、`REVIEW_DEFECT_NOT_REPEATABLE`、`REVIEW_DEFECT_NOT_CONTROLLABLE`、`IMPROVEMENT_EVIDENCE_WEAK`、`IMPROVEMENT_COST_UNVERIFIED`、`IMPROVEMENT_NOT_LOW_COST`、`IMPROVEMENT_SELECTED`、`QUOTE_INPUT_REQUIRED`、`QUOTE_CONFIGURATION_MISMATCH`、`ACTUAL_PROFIT_PENDING`、`ACTUAL_PROFIT_PASS`、`ACTUAL_PROFIT_FAIL`、`OPERATING_STRATEGY_NOT_READY`。

## 11. 尺寸与费用回归用例

- 英国普通商品包装40×30×5cm、实重不超过2kg：应进入标准包裹候选费档并重算利润，不得因最长边超过35cm自动失败。
- 德国CEP状态未知：使用`DE_ONLY`列，且不得再次加EUR 0.26。
- 日本三边和落入公开表重叠行：必须用Revenue Calculator或已观测Seller Central档位，不能自动取较低费用。
- 加拿大商品超出标准件尺寸：至少按小型超大件入口费试算；若实际档位未确认则`待补`，不能继续用标准件费。
- 任一站缺包装长宽高/实重：`PACKAGE_DATA_MISSING`；同一SKU的费用来源矛盾：`FBA_FEE_CONTRADICTION`并输出`数据异常`。

## 12. 效果验证

统一指标和行为回归使用 `validation-cases.md`。人工通过率、开发通过率、数据补齐率、基础错误率和每个合格候选研究耗时分别报告。旧50款用于已知问题回归；新的独立样本才用于估计改善幅度，不预报未经实测的通过率。
