# Amazon选品统一佣金核算政策

当前生效政策：`selection-fee-policy-2026-09-17.json`。适用所有选品智能体、所有候选、所有当前研究站点和全部类目。

## 1. 唯一生效口径

根据用户于2026-09-17确认的内部利润核算口径，Amazon佣金统一按销售基数的15%计算。选品利润表不再按类目、价格区间或最低单件佣金切换比例，也不因Amazon费用类目尚未确认而暂停佣金计算。

```text
commission_rate = 0.15
commission_amount_local = commission_base_local × 0.15
```

`commission_base_local`使用利润表中的目标成交总额；FBA商品通常等于含税商品售价。若买家另付配送费或礼品包装费，须并入基数。折扣场景按折后成交总额分别计算。

这是用户指定的内部选品模型，不代表Amazon所有类目的真实公开佣金均为15%。即使Fee Preview或公开类目表显示更低或更高费率，选品通过/不通过仍使用固定15%，除非用户再次修改政策。实际观测费率可以另存审计字段，但不得覆盖模型佣金。

## 2. 输出字段

每个目标Offer至少记录：

`commission_policy_id=USER_FIXED_15_PERCENT_2026-09-17`、`commission_rate=0.15`、`commission_base_local`、`commission_amount_local`、`commission_source=USER_POLICY`。

原`referral-fees-2026-09-16.json`仅作为Amazon公开类目费率的历史审计快照，不参与当前选品利润计算。佣金不再使用`REFERRAL_CATEGORY_UNRESOLVED`或`REFERRAL_FEE_CONTRADICTION`阻塞自动核算；若固定政策文件缺失，记录`COMMISSION_POLICY_MISSING`。
