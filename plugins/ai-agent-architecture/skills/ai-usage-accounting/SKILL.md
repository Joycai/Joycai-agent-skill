---
name: ai-usage-accounting
description: >-
  Design or review usage metering and cost accounting for LLM, image, and video APIs: normalized usage, price snapshots, reported costs, async settlement, and usage dashboards. Use for cost tracking and reconciliation, not subscription payments, invoicing, or collecting money from customers.
metadata:
  version: "1.1.0"
  updated: "2026-10-25"
---

# AI 用量与成本核算

面向用户自配价格或读取上游报价的成本记录。收款、订阅、税务与发票不属于本 skill。

## 按任务读

| 任务 | 资料 |
| --- | --- |
| 用量行、价格与规格快照、计费组 | [数据模型](references/data-model.md) |
| token / 按次 / 按规格计算、报价优先级 | [核算规则](references/pricing-rules.md) |
| 流式取消、异步结算、幂等与失败处理 | [记录与结算](references/recording.md) |
| 持久化、迁移、币种与汇总缓存 | [存储与迁移](references/storage-and-migration.md) |
| 价格编辑与用量展示 | [UI 参考方案](references/ui.md) |
| 回归风险 | [故障检查](references/pitfalls.md) |

## 核心约束

1. 历史核算使用记录时的价格、数量、规格和币种；改当前价格不重新定价历史。区分预估、上游报告与已核对金额。
2. 未回报与零值分开，未知用量不能在展示中伪装成实际零消耗。
3. 使用统一核算逻辑，明确规格匹配、舍入、币种与报价信任规则；金额来源可追溯。
4. 供应商原始字段由协议适配层提取并规范化，不能让上游任意同名字段覆盖内部可信值。字段位置查 [聊天 API 用量](../llm-api-integration/references/errors-probing-observability.md) 或 [媒体 API](../ai-media-api-integration/SKILL.md)。
5. 记录失败不得遮蔽已取得的生成结果或任务 id；同时必须可观测、可重试且防重复，不能仅吞掉异常。
6. 视频提交先记录任务与预估，不自动认定已收费；按供应商计费规则及实际结果确认、调整或冲销。取消和失败是否收费需要证据。

## 按范围设计

先确定实际需要的计价模式、用量来源、价格快照、可信报价与币种策略，再选择数据结构。参考实现中的 FeeGroup、固定列集合、最具体档位优先、单币种和检查点阈值都可以替换，但要保留可追溯性与一致性。

验证应覆盖可能静默记错的路径，如未知用量、零报价、规格冲突、重复结算、价格变更与存储失败。给出实际验证结果，不把架构建议描述成已完成的测试。
