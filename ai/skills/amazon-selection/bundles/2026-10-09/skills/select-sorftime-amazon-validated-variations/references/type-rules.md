# 已验证产品扩展规则

规则版本：`validated-variations-v0.4.1`

公共阈值版本：`selection-gates-v0.9.2`。

## 1. Amazon 2026变体基线

政策核验日期：`2026-08-19`

Amazon自2026年起按类目把评论共享限制在不影响功能的轻微差异。官方示例包括同商品颜色/图案、保持同一功能的尺寸、包装数量、非核心体验的次要香味及同类产品不同型号适配。显著功能、规格或体验差异不能假设共享评论。

参考：

- https://sellercentral.amazon.com/seller-forums/discussions/t/a572986d-9bb1-4e91-a53f-41c575874dd7
- https://sellercentral.amazon.co.uk/seller-forums/discussions/t/83ba401b-1295-44be-97b1-4ce263ab3c06
- https://sellercentral.amazon.co.jp/seller-forums/discussions/t/09525944-8d5f-4bc4-9224-6b25133dab5c

每次分析记录站点、类目、政策核验日期，分别输出`relationship_decision`和`review_sharing_expected`，并按评论完全不共享情景预测目标Offer。`review_sharing_expected`枚举固定为`预计符合共享资格`、`预计不符合共享资格`、`未知`；“符合资格”不得写成“保证共享”。

## 2. 基础产品准入

- 主类型、共享市场和原Offer开发结论已通过。
- 稳定销售>=60天或完成>=2次补货；不足时人工复核。
- 最近30天月销运行速度>=30。
- 当前完整贡献利润>=USD1且利润率>=30%。
- 至少2个核心词有自然位证据。
- 评分建议>=4.2；低于4.2或差评/退货持续恶化时先质量复核，不自动扩展。
- 无未解释的断货、促销、价格跳水或合并变体污染。

未验证基础产品：`BASE_NOT_VALIDATED`，返回对应主类型Skill，不启动矩阵。

## 3. 关系与路径

合法父子候选须为同一品牌、产品类型、核心设计和功能，可共享基础标题，只在少数明确属性上不同，客户合理预期在同一详情页选择，且类目支持准确主题。

### 合法轻变体候选

- 颜色或固定图案；
- 不改变功能的尺寸；
- 同一商品的制造商包装数量；
- 同一产品类型的型号适配。

仍须核验当前站点和类目主题，评论共享另行判断。

### 默认独立ASIN

- 新功能、新部件、不同配件组合或使用方式；
- 新一代型号或客户体验显著不同；
- 类目没有准确主题。

功能组合必须证明组件共同完成同一任务、无凑数、兼容且整包经济门槛通过；不得用大PCS公式评估异质组件。

### 包装、UV和激光

- 仅外盒、说明书或打标变化，商品和数量相同：原ASIN包装更新，重算成本/尺寸/FBA费，不建重复ASIN。
- 固定颜色/图案、核心产品不变且类目支持：轻变体候选。
- 节日图案改变购买周期：转节日Skill。
- Logo、角色、品牌词或版权图案：法务核验或淘汰。
- 买家输入姓名、文字、照片：Amazon Custom/人工复核。

## 4. 目标Offer独立需求

每个目标Offer须：

- 至少有关键词、可比子体销量、自然搜索中的两个证据层。
- 按共享市场的直接可比/组合证据路线评估属性需求；直接可比路线要求独立父体与经营主体，不使用同一父体子体数凑证明。
- 属性值有独立搜索或选择证据。
- 预计自身月销>=30。
- 评论完全不共享时仍成立。

父体销量不得平均分配；同一父体多个子体不能算多个独立证明。可比子体无法拆分：`VARIATION_CONTAMINATION`。直接可比证据不足时可按共享市场的组合证据路线继续研究，但目标预测及开发保持人工复核/待补；无属性级需求：`CHILD_DEMAND_UNPROVEN`。

## 5. 目标Offer经济与增量

每个Offer独立应用公共门槛，重新计算目标SKU、pack、重量、尺寸、FBA费、完整利润和合规。Top1/Top3份额、头部控制和目标预测T按共享市场v0.4验证；20%仅用于分散/蓝海标签。

```text
incremental_portfolio_profit = 新Offer预计贡献利润
                             - 被蚕食的基础Offer贡献利润
                             - 新增库存/仓储/复杂度成本
```

基础销量从A转移到新Offer不算全部增量。增量组合利润<=0时不自动扩展。

## 6. 轻矩阵范围

自动通过仅适用于：单一主题、单批新增<=3个Offer、每个Offer独立通过、不依赖评论共享、采购空间经推理可能实现且无明显库存碎片化。货源与精确SKU在人工询价后验证。

4个以上、二维交叉矩阵或多功能组合须分阶段/人工复核，`MATRIX_TOO_WIDE`。

### 批次聚合

- `family_expansion_decision`只聚合`relationship_route=合法父子变体`的Offer。
- 独立ASIN进入`standalone_expansion_decision`；包装更新和Custom/人工路线分别报告，不计入父子批次数量。
- `relationship_route`枚举固定为`合法父子变体`、`独立ASIN`、`原ASIN包装更新`、`Amazon Custom/人工复核`、`淘汰`。`relationship_decision`只判断所选路线是否成立；正确改走独立ASIN时为`通过`，不写`建议改类`。
- 提交的父子批次中任一Offer不通过，则原`family_expansion_decision=不通过`；用`approved_family_offer_ids`、`rejected_family_offer_ids`和`revised_family_batch_decision`表达处置。
- 独立ASIN批次使用同一聚合逻辑，并分别输出`approved_standalone_offer_ids`、`rejected_standalone_offer_ids`和`revised_standalone_batch_decision`。
- `rerouted_offer_ids`只表示原提案从父子关系改走其他路线；获批独立ASIN同时出现在`rerouted_offer_ids`和`approved_standalone_offer_ids`。
- 不使用“部分通过”这一未定义状态。可执行动作由修订批次表达。
- `MATRIX_TOO_WIDE`只计算拟加入同一合法父子家族的Offer，不把已路由独立ASIN的组合装计入。
- 某路线原始分组为空时，该路线的原批次和修订批次结论均为`未评估`，对应ID列表为`[]`。
- 原始分组非空但修订后没有任何获批Offer时，`revised_*_batch_decision=不通过`；至少保留一个且保留Offer全部通过时才为`通过`。

## 7. Sorftime证据

- 基础产品：详情、报告、趋势和流量词。
- 变体/属性：`product_variations`、`similar_product_feature`、关键词趋势及自然结果。
- 市场：产品搜索、类目报告/趋势/关键词，按共享规则构造精确可比集。
- 痛点：评论与Customers Say。
- 采购：选品阶段不核对1688；先反推采购空间并判断目标颜色/尺寸/pack/工艺是否可能实现，人工询价后再核验精确SKU与真实成本。

Sorftime没有Seller Central类目变体主题政策接口。未取得当前主题证据时，`relationship_decision=待补`。

## 8. 原因码

`PASS_VALIDATED_VARIATION`、`PASS_STANDALONE_EXTENSION`、`PASS_PACKAGING_UPDATE`、`BASE_NOT_VALIDATED`、`BASE_NOT_STABLE`、`BASE_QUALITY_REVIEW`、`INVALID_VARIATION_RELATIONSHIP`、`THEME_UNSUPPORTED`、`THEME_UNVERIFIED`、`FUNCTIONALITY_CHANGED`、`BUNDLE_REQUIRES_STANDALONE`、`PACKAGING_ONLY_NO_NEW_ASIN`、`CUSTOMIZATION_ROUTE_REQUIRED`、`REVIEW_SHARING_NOT_ELIGIBLE`、`REVIEW_SHARING_UNKNOWN`、`REVIEW_DEPENDENCY_RISK`、`CHILD_DEMAND_UNPROVEN`、`CHILD_SALES_LT_30`、`CHILD_COST_GT_50`、`CHILD_WEIGHT_GT_2KG`、`CHILD_PROFIT_FAIL`、`CANNIBALIZATION_RISK`、`INCREMENTAL_PROFIT_NONPOSITIVE`、`MATRIX_TOO_WIDE`、`VARIATION_CONTAMINATION`、`IP_REVIEW_REQUIRED`。

## 9. 回归用例

1. 稳定收纳盒新增蓝/灰两色，Color主题合法，两色各自月销与经济门槛通过：整批通过。
2. 父体月销300，黄色属性级P25仅18：黄色不通过，不能平均父体销量。
3. 增加安装工具和不同用途配件：独立ASIN/功能组合评估，不建普通父子关系。
4. 只换彩盒和激光Logo、商品数量相同：原ASIN包装更新，不新建子体。
5. 日常杯垫增加圣诞图案：转节日Skill，独立检查窗口/IP和库存退出。
6. 5件装通过，10件装采购55元：只保留5件装；家庭整体利润不能放行10件装。
7. 一次新增5颜色×4尺寸：`MATRIX_TOO_WIDE`，分阶段最多3个Offer。
8. 预计共享评论但完全不共享情景下月销<30：不通过`REVIEW_DEPENDENCY_RISK`。
