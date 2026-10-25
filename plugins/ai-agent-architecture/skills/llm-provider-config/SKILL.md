---
name: llm-provider-config
description: >-
  Design or migrate LLM provider configuration: credentials, endpoints, protocol routes, model settings, and capability profiles. Use for multi-protocol credentials, per-route settings, duplicate-provider merging, or configuration UI. Protocol wire behavior and actual vendor capabilities belong to the API integration skills.
metadata:
  version: "1.1.0"
  updated: "2026-10-25"
---

# LLM 供应商配置

设计接入配置的实体、参数归属、迁移、合并及设置界面。按任务复杂度选方案：单端点单协议可以保留简单供应商记录；需要多协议或多部署时再拆分实体。

## 推荐模型

- **平台画像**：端点默认值、能力声明及证据引用；结构由本 skill 维护，厂商事实从 [API 平台索引](../llm-api-integration/references/platform-matrix.md) 读取。
- **渠道**：用户配置的接入与凭据引用，用稳定 channelId 标识；不要把密钥明文当数据库主键。
- **线路**：协议与端点/部署组合，用稳定 routeId 标识。仅在每族恰有一个端点的简化产品中，才可用协议族代替 routeId。
- **模型**：稳定 modelId、当前线路及各线路参数。切线路不改变模型身份。

## 按任务读

| 任务 | 资料 |
| --- | --- |
| 实体、字段归属、平台画像 | [数据模型](references/data-model.md) |
| 存储、迁移、兼容与备份 | [存储与迁移](references/storage-and-migration.md) |
| 切线路与保留参数 | [线路切换](references/route-switching.md) |
| 合并供应商与引用改写 | [合并](references/merge.md) |
| 配置界面 | [UI 参考方案](references/ui.md) |
| 排错与评审 | [故障索引](references/pitfalls.md) |

## 设计与迁移约束

- 先确认是否需要同协议的多个区域或部署；需要时所有线路参数、引用、合并键都使用 routeId，不能只扩容线路列表。
- 字段归属以实际语义决定，支持文档、接口契约或实测证据。价格、上下文上限也可能随端点变化，不能只凭模型同名就共享。
- 用户授权与平台能力分开表示。未知能力不伪装成已验证支持；私有字段仅发往适用的平台与协议组合。
- 新线路的参数默认未设置；只有兼容性明确且符合用户意图的字段才迁移或共享。
- 数据重构保持可观察的请求语义；对确需字节一致的签名等路径单独验证。不能确定的映射保留原值并说明，不擅自合并。
- 合并前明确目标、冲突与引用改写范围；已有明确用户授权时执行，无授权时呈现合并方案。

资料中的“每族一条线路”、只读画像、固定视图与具体迁移版本是原项目的参考实现。采用前先核对适用前提，避免把简化模型强加给复杂部署。
