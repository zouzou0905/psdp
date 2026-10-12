# GB、DE、JP、CA FBA配送费基准

基础费率数据版本：fba-fees-2026-09-21

结构化数据：fba-fees-2026-09-21.json

2026旺季叠加快照：fba-fees-peak-2026-09-16.json

用户指定政策与Seller Central来源：selection-fee-policy-2026-09-17.json

快照整理：2026-09-21。四份用户提供的Amazon费率PDF已完成全文提取和全部69页视觉复核。英德低价资格再次核实；加拿大增加2026旺季与2027-01-15起非旺季费率、计费重量进位和税费口径；美国只作站点隔离的参考，不进入当前GB/DE/JP/CA智能体。旧快照保留用于历史复现，当前执行只读取本文件指向的新快照。

本次PDF审计结论：

- `英+欧低价商品FBA费用.pdf`是当前低价计划的有效补证，必须同时判断含税售价、类目、35×25×12cm和400g自动资格上限；较重信封费行仍保留但不能自动判资格。
- `英+欧FBA费用分类.pdf`正文为2025费率变更，主要用于历史尺寸分档背景，不能覆盖2026费率卡。
- `加拿大FBA费.pdf`同时给出2026-10-15至2027-01-14旺季费率和2027-01-15起非旺季费率，但没有给出2026-09-21至2026-10-14当前费表；该缺口必须用Fee Preview补齐。
- `美国FBA费.pdf`的三档售价、非旺季/旺季费率、服装和危险品表仅限美国站，不得跨站套用。

本文件只覆盖Amazon当地站销售的单件FBA配送费。佣金、仓储、入库配置、退货、移除、税费和其他可选费用必须在完整利润中另算。当前业务包装后实重仍须不超过2kg。

## 0. 用户指定的Seller Central官方来源

- 美国站费率变更/费率入口：https://sellercentral.amazon.com/help/hub/reference/GABBX6GZPA8MSZGW
- 美国站FBA配送费帮助入口：https://sellercentral.amazon.com/help/hub/reference/G201112670
- 英国站FBA费率入口：https://sellercentral.amazon.co.uk/help/hub/reference/GABBX6GZPA8MSZGW

这些链接是当前选品规则的优先官方来源。页面可能要求Seller Central登录；无法读取正文时记录`SELLER_CENTRAL_HELP_LOGIN_REQUIRED`，继续使用同站点的Amazon公开费率卡或已核验快照做有来源的测算，不得声称已读取登录后费率。美国站链接仅用于美国站，英国站链接仅用于英国站；禁止跨站套费率。用户重复提供的英国链接只保留一条规范化记录。

## 1. 强制使用顺序

初筛可按有来源的最终包装/成本区间做情景测算，与市场验证同步补证；不得把区间当实测。每个目标Offer在开发终审前完成下列精确核验：

1. 核对目标站、销售类目、含税售价、目标供应SKU和最终包装后长宽高/实重。
2. 目标站存在上列用户指定Seller Central帮助页时，优先核对其当前费率、生效日期和尺寸重量口径；页面需登录但当前无法读取时，明确记录登录状态。
3. 读取JSON中对应站点、费率生效日、附加费及类目例外；不得跨站套表。
4. 计算或取得计费重量，匹配station_size_tier和base_fba_fee_local。
5. 应用低价计划、德国CEP/DE Only模式、类目特殊表和燃油物流附加费，得到effective_fba_fee_local。
6. 使用有效FBA费进入完整贡献利润，并计算fba_fee_to_price。
7. 档位、计费重量或类目费表有歧义时，使用目标站Revenue Calculator或Seller Central Fee Preview；未核清只能待补。

禁止用统一“最长边35cm”作四站硬门槛。尺寸的作用是确定站点费档和物流成本；只要包装实重、完整利润、头程、合规等公共硬门槛通过，40cm商品不能仅因长度自动淘汰。

## 2. 英国与德国

官方来源：[Amazon Europe FBA Rate Card](https://m.media-amazon.com/images/G/02/sell/images/260410-FBA-Rate-Card-EN.pdf)，2026-04-17起执行。

- 表列值为基础配送费；当前有效费=基础费×1.015。
- 普通信封：33×23×2.5cm；大信封增至4cm，超大信封增至6cm。
- 小包裹：35×25×12cm；普通标准包裹：45×34×26cm。
- 普通包裹和非特殊超大件的体积重：长×宽×高cm÷5000，通常与实重取较大值。
- 信封、低价FBA和官方列明的特殊包裹类目使用实重。
- 德国必须记录DE_CEP或DE_ONLY；不确定时用更保守的DE_ONLY，不得再重复加€0.26。
- 门窗/淋浴配件、鞋类、家具配件、家纺、包装材料、打印机配件、可重复使用工作手套、服饰箱包等列明类目走JSON中的selected_category_parcel_fees。
- 低价费表与计划资格分别保存：轻信封至100g，标准信封210/460g，大信封及超大信封至960g，小包裹150/400g。按每行尺寸和实重匹配，不能把信封行截成400g，也不能把960g套给小包裹。
- 普通类目价格上限英国£20/德国€20；例外类目英国£10/德国€11，完整例外列表见JSON。必须同时验证资格和目标费档。
- [英国资格FAQ](https://sell.amazon.co.uk/low-price-fba-rates)及[德国资格FAQ](https://sell.amazon.de/en/fba-gebuhren-fur-niedrigpreisige-artikel)仍写35×25×12cm、400g，与费率卡较重信封行存在口径差异。400g以内按全部价格/尺寸/类目条件判断；超过400g且满足460/960g信封费行时记录 `FBA_ELIGIBILITY_CONFLICT`，保留费行但低价资格不自动通过，必须用精确Offer的Revenue Calculator/Fee Preview确认。官方营销页的例图不能推翻资格FAQ。
- 对上述冲突，研究阶段可展示普通FBA费的有标注保守情景；最终实际费用未核清时利润/launch待补，独立市场研究可继续。任何来源出现费用矛盾不能只选较低值。

在当前不超过2kg经营范围内优先级为：

    33×23×6cm以内信封
    → 35×25×12cm以内小包裹
    → 45×34×26cm以内标准包裹
    → 超大件仅在实际FBA费、头程和完整利润通过时保留

## 3. 日本

官方来源：[Amazon Japan pricing](https://sell.amazon.co.jp/pricing)，2026费率，表内已含10%消费税。

- 小型：25×18×2cm且不超过250g，售价>¥1,000时¥288，售价<=¥1,000时¥222。
- 标准扁平档：35×30×3.3cm且不超过1kg，分别为¥318/¥252。
- 其他公开行按包装后三边和20/30/40/50/60cm及不超过2kg分档：
  - 售价>¥1,000：¥410/415/420/425/430。
  - 售价<=¥1,000：¥344/358/371/379/391。
- JSON同时保存Standard三边和至100cm、Oversize至200cm及Supersize至260cm的公开费率。日本公开表在Standard、Oversize和Supersize存在重叠的三边和行；有歧义时不能自行选择较低费档，必须使用Revenue Calculator或已观测的Seller Central档位。

日本筛选不能使用欧洲最长边或矩形阈值代替三边和规则。

## 4. 加拿大

官方来源：[Amazon Canada pricing](https://sell.amazon.ca/pricing)及[燃油物流附加费公告](https://sellercentral.amazon.ca/seller-forums/discussions/t/1c718d6b-ed69-4a07-b906-9052a59edac2)。

- 表列值为基础配送费；2026-04-17起有效费=（基础费-适用的低价折扣）×1.035。PDF列值不含这项3.5%附加费。
- 售价严格低于CAD $14时，基础配送费减CAD $0.80。
- 公开页未明确所有低价折扣例外；超大件只有在Revenue Calculator或Fee Preview确认时才应用CAD $0.80折扣。
- 2026旺季为2026-10-15至2027-01-14；2027非旺季表从2027-01-15开始。2026-09-21至2026-10-14的当前费率未包含在用户PDF中，精确利润必须标记`CURRENT_RATE_NOT_PRESENT_IN_USER_PDF_REQUIRE_FEE_PREVIEW`。
- 2027非旺季信封费按100g分档至500g；标准件按100g分档至1,500g。1,500g以上：首1,500g基础费CAD $10.32，此后每增加100g加CAD $0.09。
- 2026旺季信封费按100g分档为CAD $4.73/$4.99/$5.31/$5.60/$5.95；标准件100g至1,500g为CAD $6.28/$6.49/$6.74/$7.13/$7.65/$7.84/$8.17/$8.43/$8.74/$8.99/$9.10/$9.37/$9.58/$9.85/$10.17，超过1,500g首段CAD $11.00、之后每100g加CAD $0.09。
- 标准件上限参考45.72×35.56×20.32cm、9kg；当前业务仍执行更严格的实重不超过2kg。
- 超出标准件至少进入小型超大件，首500g基础费CAD $15.43，之后每500g加CAD $0.46。
- 加拿大公开价格页把信封尺寸定义链接到需JavaScript/登录的Seller Central页面；未取得当前官方信封尺寸或Revenue Calculator确认时，不得仅凭第三方尺寸自动判信封档。
- 加拿大计费重量为实重与体积重较大者；信封/标准件向上进位至100g，超大件向上进位至500g。
- PDF示例反推体积重为长×宽×高cm÷5000，但正文没有明示除数，因此只记录`INFERRED_FROM_OFFICIAL_EXAMPLES_NOT_EXPLICITLY_STATED`；精确Offer仍须用Revenue Calculator/Fee Preview核验。
- 加拿大FBA表列值不含GST/HST；适用税费由Amazon另加，利润表必须把税作为独立可编辑输入。

## 5. 美国参考隔离

美国PDF已核对，但不属于当前选品站点范围。其2026非旺季为1月15日至10月14日，旺季为2026-10-15至2027-01-14，费率按售价`< $10`、`$10–$50`、`> $50`分三档；恰好$10和$50落在中档。2026-04-17起另加3.5%燃油物流附加费，体积重按立方英寸÷139。普通、服装、危险品必须走各自表。所有数据仅保存在`us_reference_only`，禁止用于GB、DE、JP或CA。

## 6. 费率时效

- 普通分析必须回显fee_snapshot_as_of、fee_effective_from、fee_source和fee_verified_at；快照整理日不等于所有站点重新核验日。JSON使用v2资格结构，读取eu.low_price_fba.eligibility及逐行max_unit_weight_g，不能再读取旧全局400g字段。
- 2026英国、德国旺季公开公告已于2026-09-16核验，旺季窗口及适用范围读取`fba-fees-peak-2026-09-16.json`。公告给出的£0.12/£0.07/€0.27是平均加价，只能用于明确标注的粗算情景；精确Offer在旺季launch前仍须用Amazon Revenue Calculator或Fee Preview取得精确峰值FBA费。
- 公开Revenue Calculator按ASIN查询失败时记录`PUBLIC_CALCULATOR_UNAVAILABLE`并按公开费率卡计算常规费；若目标销售窗口落在旺季且精确峰值费未取得，记录`FBA_PEAK_FEE_UNRESOLVED`，利润不得自动通过。
- Amazon Revenue Calculator或Fee Preview与快照冲突时，记录FBA_FEE_CONTRADICTION并暂停自动通过，不能选择较低值。
