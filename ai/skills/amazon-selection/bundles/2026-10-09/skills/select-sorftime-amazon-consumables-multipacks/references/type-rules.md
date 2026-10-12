# 消耗品与包装规格（含大PCS）规则

方向规则版本：`consumables-packs-v0.5.0`

阈值版本：`selection-gates-v0.10.0`。历史产品回测前均为初始阈值。

## 1. 两种运行模式

- `selection_mode=独立发现`：可以从Amazon当地在售产品、关键词和类目独立发现候选，运行共享市场、pack需求、供应和利润验证，不要求先收到其他对话的候选。
- `selection_mode=标签复核`：接收已有候选和有效的主类型/市场结果，补充消耗、包装规格和大PCS证据。
- 独立发现模式下，`selection_lane_decision`可以在主类型尚未完成时输出`通过`；但最终`launch_decision=通过`仍要求对应日常、季节、节日或热点主类型验证通过。
- `branch_mode`决定评估消耗品、包装规格或两者；`pack_scope`决定比较小包装、标准包装、大PCS或多个档位。

## 2. 决策与传播

先选`selection_lane`：`CONSUMABLE_REPLENISHMENT`、`PACK_SIZE_OPPORTUNITY`或`BOTH`。前者依赖消耗机制，后者依赖目标pack市场，二者不得互相代替。包装规格机会通过且本次未选择消耗标签时，复购周期待补/不适用不阻塞该包装方案；反之，消耗属性成立也不能替代目标pack销量与自然需求。

- `pack_market_fit_status`判断目标pack在当地市场是否成立；`consumable_status`和`large_pcs_status`是可叠加标签，三者独立计算。
- 目标pack是小包装或标准包装时，`large_pcs_status=不适用`或不通过不阻塞该pack方案，除非`selected_launch_strategy_tags`明确包含`大PCS`。
- 未选择标签的待补、复核、不通过或局部异常只保留记录，不做最差状态汇总。
- 已选择标签状态按`数据异常>不通过>待补>人工复核>通过`传导。
- 人工询价后的精确SKU、真实pack、成本、重量或合规矛盾是全局异常，无论标签是否选择都传导；选品阶段不以缺少1688 SKU阻塞。
- `secondary_tags`只授予状态为`通过`的标签。

## 3. 包装规格市场验证

完整M/E/L/T前先计算目标售价、低/基准/高包装情景、FBA档位和30%利润采购空间的`price_weight_envelope`。优先扁平、套叠、可压缩、高密度小体积或单位重量价值较高的结构；保守情景已跨2kg、零采购仍不盈利或采购空间明显不支持目标材质/件数时停止深验。该偏好只改变候选优先级，不豁免当地需求证明。

先按同一购买意图、买家/使用场景、功能、材质、尺寸/克重、用途和有效单位建立精确子体可比集，再根据当地在售分布形成`pack_ladder`。家庭DIY与商业施工、装配、维修或生产场景存在不同购买意图时必须拆分，不得为了证明复购而混算。小/标准/大是市场相对档位，不使用跨类目的固定件数切分。

每个拟售pack自动通过须同时满足：

- 目标pack证据路线复用共享市场第4节：直接可比路线须满足C的Offer/父ASIN/独立经营主体和自然证据；缺多个同款时按组合证据转人工研究，不再额外要求5个完全相同pack。T预测的独立样本条件仍须满足。
- 目标pack按共享市场模块事先定义的T得到保守预计月销`>=30单`，不得使用父体、其他pack或类目总销量代替。
- 至少2个相关核心词存在该pack可解释的自然需求证据，且目标pack的低评论/新进入者证据符合共享市场门槛。
- 售价处于该pack当地可接受价格带；每有效单位价格只作同质比较，不要求小包装比大包装单位价更低。
- 目标供应SKU、包装重量/尺寸和完整利润独立通过公共门槛。

同一产品可以有多个pack候选，但每个Offer必须独立通过；不得把多个pack的销量合并后让单个弱规格通过。首批是否同时上多个pack应按库存复杂度和证据强度排序，不自动铺量。

批量计数默认每个购买问题只保留证据最强的一档pack。第二档只有在买家场景、价格带、目标子体销量和自然入口均可独立验证时才构成另一个机会；单纯件数不同或同父体轻微变化不得重复计数。

## 4. 消耗品分支

自动通过须同时满足：

- 在目标场景的正常使用中耗尽、磨损、污染、失效、必须定期替换，或作为施工、装配、维修、生产等商业作业投入被持续领用并消耗库存。
- 客观使用/更换周期`<=180天`。
- 至少两类独立Amazon侧证据，例如补充/替换意图词、评论更换频率、Customers Say、补充规格销量或多个ASIN的稳定需求。
- 目标pack预计月销`>=30单`；内部片数、使用次数和父体订单不算目标Offer订单。
- 需求与复购证据必须来自Amazon侧或当地市场证据，不能来自供应商；选品阶段不查询1688复购率。

181–365天或只有一类可靠证据：人工复核。>365天、无客观机制或只靠文案：不通过。无法取得真实复购率时明确为代理判断。

同一商品可以因使用场景不同得到不同结论。家庭购买后长期留存、偶尔使用的螺丝通常不构成消耗品；承包商、装配商、维修车间或生产企业持续领用并周期补货的螺丝，可以判为商业消耗品，但必须由商业用途关键词、pack结构、评论/Customers Say、多个相关ASIN的稳定补货需求等至少两类Amazon侧证据支持。不得从“大包装”或“商业买家可能会用”直接推定复购。

## 5. 大PCS分支

- 原始件数通常`>=20`才进入大PCS判断；市场基准很小的特殊品人工解释。
- 剔除赠品、安装附件和不同功能组件，计算`effective_units`。
- 不同规格换算到共同有效单位：使用次数、长度、面积、重量、容量等。
- 大PCS目标pack仍须先通过第3节的`pack_market_fit_status`，真实在售需求优先于主观“大包更划算”判断。
- 无法换算共同单位的异质组件：`large_pcs_status=不适用`，`RECLASS_FUNCTIONAL_BUNDLE`。

```text
pack_ratio = 目标有效单位 / 市场可比子体有效单位中位数
候选每有效单位售价 = 目标零售价 / 目标有效单位
单位价值优势 = 1 - 候选每有效单位售价 / 可比集每有效单位售价中位数
```

大PCS自动通过：有效单位`>=20`、目标pack市场需求通过、目标子体预计月销`>=30`、包装`<=2kg`且完整利润通过。`pack_ratio`和单位价值优势必须报告，用于比较和排序，但不再以固定15%折扣替代当地实际需求。

若目标pack销量主要依赖促销、单位价显著高于同质市场且缺少功能/质量理由，或大包需求无法从父体拆分，转人工复核或不通过。

## 6. 父子体与供应SKU

- 竞争按父ASIN去重；销量、售价、pack、重量和利润落到精确子ASIN。
- 父体销量不能拆到目标pack：`PARENT_CHILD_CONTAMINATION`，不得自动通过。
- 人工询价后若Amazon目标Offer与采购SKU件数/规格冲突：`COUNT_CONTRADICTION`，全局数据异常。
- 赠品膨胀件数：`BONUS_PIECE_INFLATION`，按有效单位重算。
- 商品卡最低价、单件价或其他SKU价不能代替目标pack成本。
- 现价受券、秒杀或断货影响时使用历史正常价复核。

## 7. 主类型与市场复用

- 独立发现时先形成候选和pack结论，再根据需求曲线路由日常、季节、节日或热点主类型验证；主类型缺失只阻塞最终launch，不抹除有效候选。
- 标签复核时，共享市场结果只有在站点、`market_definition`、政策版本、分析日和时效匹配时才能复用。
- 包装规格不同且购买意图或价格带明显变化时必须重建精确市场，不能用一个pack的市场结果覆盖另一个pack。

## 8. 原因码

`PASS_CONSUMABLE_SELECTION_LANE`、`PASS_PACK_MARKET_FIT`、`PACK_MARKET_FIT_UNPROVEN`、`PACK_COHORT_INSUFFICIENT`、`PACK_CHILD_SALES_UNOBSERVED`、`PASS_CONSUMABLE`、`PASS_COMMERCIAL_CONSUMABLE`、`NO_REPEAT_MECHANISM`、`COMMERCIAL_CONSUMPTION_UNPROVEN`、`USE_CONTEXT_MIXED`、`REPEAT_EVIDENCE_WEAK`、`CYCLE_TOO_LONG`、`PASS_LARGE_PCS`、`PACK_COUNT_ONLY`、`COMPARABLE_SET_INVALID`、`UNIT_VALUE_OUTLIER_REVIEW`、`RECLASS_FUNCTIONAL_BUNDLE`、`FUNCTIONAL_COMPONENTS_NOT_COMPARABLE_AS_PCS`、`PARENT_CHILD_CONTAMINATION`、`COUNT_CONTRADICTION`、`BONUS_PIECE_INFLATION`、`VARIATION_PRICE_MISMATCH`、`SUPPLIER_SKU_MISMATCH`、`MARKET_ENTITY_MISMATCH`、`PRIMARY_TYPE_VALIDATION_REQUIRED`、`OPTIONAL_TAG_NOT_SELECTED`。

## 9. 回归用例

1. 一次性杯子：25只装新品队列和自然位通过，100只装目标子体销量不足。25只装可以通过包装规格与消耗品分支，100只装不通过；不得因100只单位价更低反转。
2. 包装袋：50只和200只目标子体均独立达到月销、自然流量与利润门槛，可分别进入候选排序；不得合并两个pack销量。
3. 家庭DIY螺丝：100只装市场需求和利润通过，但购买后长期留存、无180天内客观耗用或补货证据。包装规格/大PCS可通过，消耗品不通过。
4. 商业施工螺丝：目标市场与家庭DIY拆分；100只装有商业用途词、施工/装配评论和多个ASIN稳定补货证据，客观补货周期<=180天。包装规格/大PCS和商业消耗品均可通过。
5. 季节性一次性用品：消耗与pack结论通过，但主类型未验证。`selection_lane_decision=通过`、`launch_decision=待补`，路由季节Skill。
6. 100件异质工具无共同单位：大PCS不适用，不能按100计算。
7. Amazon目标Offer为100片，人工询价确认采购SKU实际80片：全局数据异常，即使大PCS未selected也阻塞；选品阶段尚未询价时不预判该冲突。
