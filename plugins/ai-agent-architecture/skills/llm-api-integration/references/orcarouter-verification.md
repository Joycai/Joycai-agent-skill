# OrcaRouter 小规模验证：2026-10-25

> 后续 [扩展验证](orcarouter-extended-verification.md) 已覆盖流式等能力；下文“未测”仅描述本轮初测。后续发现 Gemini 工具样例回显 3.5，Fable any 未强制，不能沿用初测做统一结论。

【实测】平台 `https://api.orcarouter.ai`；8 次非流式生成请求，每例 n=1，上限 256 token，无自动重试，未执行返回的工具。使用用户提供的凭证；本文不保存凭证、签名或思考原文。日期按 Asia/Shanghai 记录。

先 GET `/v1/models`，鉴权通过，返回 212 个目录项。未找到 `google/gemini-3.7-flash`，本轮未试调用；目录缺失不等于接口一定拒绝。

## 结果

| 案例 ID | 请求模型 / 协议 | HTTP | 响应模型标识 | 结果 | 网关报价 USD |
| --- | --- | --- | --- | --- | --- |
| ORCA-1025-01 | `openai/gpt-6.1-sol` · `/v1/responses` | 200 | `gpt-6.1-sol` | 正文 OK；正常结束 | 0.000072 |
| ORCA-1025-02 | `anthropic/claude-opus-4.8` · `/v1/messages` | 200 | `claude-opus-4-8` | 正文 OK；正常结束 | 0.000180 |
| ORCA-1025-03 | `anthropic/claude-fable-5` · `/v1/messages` | 200 | `claude-fable-5` | 正文 OK；正常结束 | 0.000360 |
| ORCA-1025-04 | `anthropic/claude-fable-5.1` · `/v1/messages` | 200 | `claude-fable-5-1` | 正文 OK；正常结束 | 0.000380 |
| ORCA-1025-05 | `google/gemini-3.5-flash` · `/v1beta/models/google/gemini-3.5-flash:generateContent` | 200 | `gemini-3.6-flash` | 正文 OK；正常结束 | 0.001090 |
| ORCA-1025-06 | `qwen/qwen3.8-27b` · `/v1/chat/completions` | 200 | `qwen3.8-flash` | 正文 OK；正常结束 | 0.000082 |
| ORCA-1025-07 | `deepseek/deepseek-v4.1-flash-1017` · `/v1/chat/completions` | 200 | `deepseek-v4-1-flash-261017` | 正文 OK；正常结束 | 0.000026 |
| ORCA-1025-08 | `anthropic/claude-fable-5.1` · `/v1/messages` | 200 | `claude-fable-5-1` | tool_use: report({value: OK})；未执行 | 0.006550 |

费用字段来自请求头 `X-OrcaRouter-Include-Cost: true` 下的 `usage.cost_usd` / `usageMetadata.costUsd`，合计 **0.008740 USD**；未与账户账单核对，不称为已确认实扣。目录价格也只是网关声明。

## 可复现请求范围

鉴权使用 Bearer；JSON 请求；Messages 带 `anthropic-version: 2023-06-01`。基本测试提示词均为 `Reply with exactly OK.`。

- Responses：`input` 为提示词，`reasoning.effort=low`，`max_output_tokens=256`。
- Messages：单条 user，`max_tokens=256`，未传 thinking。
- Gemini：单条 user text part，`generationConfig.maxOutputTokens=256`。
- Chat Completions：单条 user，`max_tokens=256`，未传思考开关。
- 强制工具案例：Fable 5.1，user 为 `Call report with value OK.`；工具 report 的 input_schema 为 object，必填字符串 value；`tool_choice={type:tool,name:report}`，`max_tokens=256`。单一工具加明确提示词仍可能在 auto 模式调用，因此本例证明“该参数请求被接受并返回对应调用”，不能单独证明强制语义生效。

## 结论与边界

- **ORCA-1025-01**：GPT 6.1 Sol 的 Responses 基本调用成功，回显 low；没有验证 Chat Completions 工具限制、schema 或流式。
- **ORCA-1025-02–04**：Opus 4.8、Fable 5、Fable 5.1 Messages 基本调用成功；简单题 thinking_tokens 为 0，不证明 adaptive 被关闭。
- **ORCA-1025-05**：Gemini 3.5 Flash 请求回显 `gemini-3.6-flash`，与 [官方版本映射](model-versions.md#gemini-versions) 一致。本例不能算 3.5 原权重测试，也没有验证 Gemini 3.7。
- **ORCA-1025-06**：请求 `qwen/qwen3.8-27b`，回显 `qwen3.8-flash`。标记身份不一致、待供应方解释；不能据此证明 27B 权重可用，也不能仅凭回显断言实际换了权重。目录中的 `obsidian/Qwen3.8-27B` 本次未测。此目录 ID 不证明 Qwen 官方托管 ID。
- **ORCA-1025-07**：DeepSeek 请求 1017 目录 ID，回显 `deepseek-v4-1-flash-261017`。只记录网关返回标识，不独立证明真实权重或把它当官方请求 ID。
- **ORCA-1025-08**：Fable 5.1 强制工具请求返回 200 / tool_use，复现旧网关观测与 [官方拒绝契约](tools-and-server-tools.md#official-model-updates) 的差异。原因可能涉及网关改写或后端差异，未查明；不修改官方结论。未测 enabled + budget_tokens。

回包字段形似厂商不能证明请求或响应完整透传，也不能独立认证后端模型身份。本轮不评估质量、上下文容量、视觉、流式、跨轮回传或工具执行效果。
