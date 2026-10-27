---
name: llm-api-integration
description: >-
  Design, implement, audit, or debug conversational LLM API integrations and check platform × protocol × model compatibility. Use for request/response formats, streaming, reasoning, structured output, tools, and endpoint failures. Media generation and transcription APIs use ai-media-api-integration; merely mentioning a vendor or using an existing generation tool does not trigger this skill.
metadata:
  version: "2.2.10"
  updated: "2026-10-27"
---

# LLM API 接入

处理对话模型的协议接入、兼容性查询、项目审查与排错。多模态输入属于此处；图片生成、视频生成和转写 API 使用 [媒体接入](../ai-media-api-integration/SKILL.md)。

## 先确定范围

事实的主键是 **平台·渠道·线路 × 协议面 × 模型**。同名模型经不同网关、协议或套餐提供时，能力可能不同；缺少记录表示未知，不能类推。仓库记录包含实测、文档和参考实现，不能统一当作当前已验证事实。查询本轮 OrcaRouter 目标时先读当前支持汇总，再沿证据链接查具体条件；旧报告中的未完成状态以当前验证状态为准。

按任务读取资料，不默认加载整个知识库：

| 任务 | 资料 |
| --- | --- |
| 核实型号、别名、弃用与版本归属 | [模型版本](references/model-versions.md) |
| 接入 Gemini 4 Argon | [型号与能力](references/model-versions.md#gemini-4-argon)、[接口与长输出](references/protocol-differences.md#gemini-4-argon)、[渠道参数差异](references/reasoning.md#gemini-4-argon)（官方文档，未实测） |
| 查看本轮 OrcaRouter 目标模型支持情况 | [实测汇总](references/model-support-status.md) |
| 接入火山套餐 Kimi K3.1 Pro | [实测与接入要点](references/volcengine-kimi-k31-verification.md)（Responses 优先，tool_choice 有缺口） |
| 查询某组合的能力 | [模型能力矩阵](references/model-capability-matrix.md)，按行内指针查正文 |
| 查询地址、鉴权、平台变体与厂商差异 | [平台索引与矩阵](references/platform-matrix.md) |
| 消息、流式、协议字段与鉴权 | [协议差异](references/protocol-differences.md) |
| 思考控制与跨轮载体 | [Reasoning](references/reasoning.md) |
| JSON 与结构化输出 | [结构化输出](references/structured-output.md) |
| 工具定义、结果配对和服务端工具 | [工具协议](references/tools-and-server-tools.md) |
| 错误、原始 usage、重试与探测 | [错误与观测](references/errors-probing-observability.md) |
| 接入架构与新增支持 | [供应商分层](references/provider-layering.md)、[接入路线图](references/migration-roadmap.md) |
| 审查现有实现 | [审查流程](references/audit-playbook.md)、[故障索引](references/pitfalls.md) |
| 证据不足或相互冲突 | [待核实项](references/open-questions.md) |
| 用户要求收录实测、修正知识库 | [知识维护](references/knowledge-ingestion.md)、[变更记录](references/CHANGELOG.md) |

## 工作方式

1. 明确目标组合、请求模式（流式/非流式）和实际端点，查相应事实及证据日期。
2. 查不到或证据不适用于当前组合时，说明未知，提出最小验证方法；付费请求按用户授权和预算执行。
3. 接入时优先按协议族组织适配器，以平台画像表达声明式差异；只有数据不能清晰表达的行为才引入局部扩展，并说明理由。
4. 审查优先检查 HTTP 200 中的失败、静默丢字段和用量口径；发现需关联项目位置、证据范围与影响。
5. 按任务交付实现、诊断或审查结果。查询和审查不自动授权修改本知识库。

## 必要约束与证据边界

- 不透明的签名、密文和跨轮载体原样保存；回传兼容性由适配层按平台、协议、模型及会话约束判断，不能只凭同名模型认定兼容。
- 在继续发送前满足目标协议的工具调用完整性要求。取消后修复未闭合调用或重建合法上下文，不将损坏历史直接重发。
- 原始 usage 字段与平台报价位置在本 skill 维护；归一化后的核算规则见 [用量与成本核算](../ai-usage-accounting/SKILL.md)。
- 实测只证明当时所测组合与样本；文档、源码、实现经验与推断分别标识。证据适用性和复核策略见 [知识维护](references/knowledge-ingestion.md)。

配置实体与迁移归 [供应商配置](../llm-provider-config/SKILL.md)，工具执行和会话生命周期归 [Agent runtime](../agent-runtime-architecture/SKILL.md)。历史章节编号仅用于旧记录追溯；新引用使用文件链接。
