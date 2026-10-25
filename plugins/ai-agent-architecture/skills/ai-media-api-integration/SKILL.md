---
name: ai-media-api-integration
description: >-
  Design, implement, audit, or debug image-generation, video-generation, and speech-transcription API integrations. Use for media request formats, uploads, async jobs, polling, cancellation, output retrieval, and timestamps. This is API engineering guidance, not a workflow for creating images, cosplay artwork, or videos with existing tools.
metadata:
  version: "1.0.0"
  updated: "2026-10-25"
---

# 媒体模型 API 接入

实现与排查图片生成、视频生成和 ASR 转写接口，包括上传、异步任务、轮询、产物下载和时间码。单纯生成图片、修图或创作视频时不使用本 skill。

## 按任务读

| 任务 | 资料 |
| --- | --- |
| 查平台 × 端点/线格式 × 模型的支持情况 | [媒体矩阵](references/media-matrix.md) |
| 图片生成与编辑、尺寸、参考图、同步/流式返回 | [图片 API](references/image-generation.md) |
| 视频提交、状态轮询、取消与产物 | [视频 API](references/video-generation.md) |
| 录音上传、转写、说话人与时间码 | [ASR API](references/speech-recognition.md) |
| 平台鉴权、套餐和网关变体 | [共享平台索引](../llm-api-integration/references/platform-matrix.md) |
| 通用错误、重试与付费验证 | [错误与观测](../llm-api-integration/references/errors-probing-observability.md) |
| 排查已有故障、核对未知项 | [故障索引](../llm-api-integration/references/pitfalls.md)、[待核实项](../llm-api-integration/references/open-questions.md) |
| 用户要求维护事实 | [共享知识维护规范](../llm-api-integration/references/knowledge-ingestion.md) |

## 工作方式

1. 明确平台、实际端点、模型、生成/编辑/转写模式与同步/异步方式；查矩阵后只读相关正文。
2. 先区分协议保证、特定平台观测与参考实现。未知组合不从同名模型或兼容端点推断。
3. 在发送前验证本地可判定的附件、参数和互斥条件。任务提交与轮询分开，持久化任务标识；重试前确认是否可能重复提交或收费。
4. 按供应商的状态模型处理完成、失败与取消，校验产物类型、有效性与下载时效。向模型输入视频仍属于 [聊天 API 接入](../llm-api-integration/SKILL.md)。
5. 记录原始用量、实际规格及其来源；提交成功不自动等于已收费，核算与结算交给 [用量与成本核算](../ai-usage-accounting/SKILL.md)。

## 约束

- 不做隐式付费能力探测；需要实测时说明请求数量、可能成本及停止条件，遵守已有授权。非法参数请求也不能无证据地保证免费。
- 返回 URL、base64 或任务 id 不等于交付成功；按目标产品需要获取并验证产物，不把参考实现的存储形式强加给项目。
- 保留已交付的部分结果与用量，避免流式取消后丢失记录。上传与下载应沿用项目的网络、凭据和文件访问边界。
- 厂商字段与行为只在对应媒体正文维护；矩阵保留简明结论与指针。没有维护请求时不写回知识库。

现有媒体正文中的类名、数值阈值、UI 和路由表来自参考项目，是实现示例；带日期的观测需按目标组合检查适用性。
