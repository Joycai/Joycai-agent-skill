---
name: ai-media-api-integration
description: >-
  Integrate or debug image, video, and speech-transcription APIs: request formats, uploads, async jobs, polling, cancellation, downloads, and timestamps. Use for API engineering, not media creation with existing tools.
metadata:
  version: "1.1.0"
  updated: "2026-10-27"
---

# 媒体模型 API 接入

接入、审查与排查图片生成、视频生成和 ASR API。单纯使用现有工具创作媒体时不使用本 skill。

## 按任务读

| 任务 | 资料 |
| --- | --- |
| 查平台 × 端点/线格式 × 模型的支持情况 | [媒体矩阵](references/media-matrix.md) |
| 图片生成与编辑、尺寸、参考图、同步/流式返回 | [图片 API](references/image-generation.md) |
| 视频提交、轮询、取消与产物 | [视频 API](references/video-generation.md) |
| 录音上传、转写、说话人与时间码 | [ASR API](references/speech-recognition.md) |
| 平台鉴权、套餐和网关变体 | [共享平台索引](../llm-api-integration/references/platform-matrix.md) |
| 通用错误、重试与付费验证 | [错误与观测](../llm-api-integration/references/errors-probing-observability.md) |
| 排查已有故障、核对未知项 | [故障索引](../llm-api-integration/references/pitfalls.md)、[待核实项](../llm-api-integration/references/open-questions.md) |
| 用户要求维护事实 | [共享知识维护规范](../llm-api-integration/references/knowledge-ingestion.md) |

## 工作方式

1. 确定平台、端点、模型、任务类型与同步/异步方式；先查矩阵，再读对应正文。
2. 区分官方契约、实测与参考实现；不将同名模型或兼容端点的结论外推到未测组合。
3. 发送前校验附件、参数和互斥条件。提交与轮询分离，持久化任务 ID；重试前排除重复提交与收费风险。
4. 分别检查 HTTP 错误与任务状态；按任务类型解析结果，校验产物及下载时效。视频理解见 [聊天 API 接入](../llm-api-integration/SKILL.md)。
5. 保留原始用量、产物规格与来源，区分折算用量、独立计费项和实扣；结算见 [用量与成本核算](../ai-usage-accounting/SKILL.md)。

## 约束

- 不做隐式付费能力探测；需要实测时说明请求数量、可能成本及停止条件，遵守已有授权。非法参数请求也不能无证据地保证免费。
- 返回 URL、base64 或任务 id 不等于交付成功；按目标产品需要获取并验证产物，不把参考实现的存储形式强加给项目。
- 保留已交付的部分结果与用量，避免流式取消后丢失记录。上传与下载应沿用项目的网络、凭据和文件访问边界。
- 厂商字段与行为只在对应媒体正文维护；矩阵保留简明结论与指针。没有维护请求时不写回知识库。

正文中的参考实现不构成厂商契约；实测结论仅适用于所记日期和组合。
